"""Validate the master collection and derive the matching pilot and manifests.

The master JSONL is the source of truth. This script never regenerates dialogue
from an older Python draft or overwrites the master during a metadata refresh.
"""

import argparse
import hashlib
import json
from pathlib import Path

from dataset_io import ROOT, digest, json_bytes, load_config, make_manifest, records_bytes, require_valid
from validate_dataset import load_jsonl


def prepare(source, config):
    collection = load_jsonl(source)
    require_valid(collection, "collection")
    lookup = {record["id"]: record for record in collection}
    try:
        pilot = [lookup[identifier] for identifier in config["pilot_case_ids"]]
    except KeyError as exc:
        raise ValueError(f"Configured pilot case is missing: {exc.args[0]}") from exc
    require_valid(pilot, "pilot")
    source_bytes = source.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    pilot_bytes = records_bytes(pilot)
    payloads = {}
    for role, records, payload in [("collection", collection, source_bytes), ("pilot", pilot, pilot_bytes)]:
        name = config[role]["file"]
        payloads[name] = payload
        payloads[Path(name).with_suffix(".manifest.json").name] = json_bytes(
            make_manifest(records, name, hashlib.sha256(payload).hexdigest(), config, role, source_hash)
        )
    return payloads


def build(output_dir, source=None, config=None, refresh=False):
    config = config or load_config()
    source = Path(source or ROOT / "data" / config["collection"]["file"])
    output_dir = Path(output_dir)
    payloads = prepare(source, config)
    master_name = config["collection"]["file"]
    if refresh:
        if (output_dir / master_name).resolve() != source.resolve():
            raise ValueError("Refresh must target the master dataset's own directory")
        pilot_path = output_dir / config["pilot"]["file"]
        pilot_manifest = pilot_path.with_suffix(".manifest.json")
        if pilot_path.exists():
            if not pilot_manifest.exists():
                raise ValueError("Existing pilot has no manifest; preserve and reconcile it first")
            previous = json.loads(pilot_manifest.read_text(encoding="utf-8"))
            if digest(pilot_path) != previous.get("dataset_sha256"):
                raise ValueError("Pilot was edited directly; merge those edits into the master before refresh")
        del payloads[master_name]
    else:
        existing = [str(output_dir / name) for name in payloads if (output_dir / name).exists()]
        if existing:
            raise ValueError(f"Refusing to overwrite existing files: {existing}")
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        path = output_dir / name
        if refresh:
            temporary = path.with_name(path.name + ".tmp")
            with temporary.open("xb") as handle:
                handle.write(payload)
            temporary.replace(path)
        else:
            with path.open("xb") as handle:
                handle.write(payload)
    return [output_dir / name for name in payloads]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Alternative reviewed collection for a preview build")
    parser.add_argument("--output-dir", type=Path, help="Fresh directory; defaults to ignored .local/build")
    parser.add_argument("--refresh", action="store_true", help="Explicitly refresh derived pilot and manifests beside the master")
    args = parser.parse_args()
    config = load_config()
    source = args.source or ROOT / "data" / config["collection"]["file"]
    output = args.output_dir or (source.parent if args.refresh else ROOT / ".local/build")
    try:
        paths = build(output, source, config, args.refresh)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"{exc}\n")
    print(f"Validated collection; wrote {len(paths)} files in {output}")


if __name__ == "__main__":
    main()
