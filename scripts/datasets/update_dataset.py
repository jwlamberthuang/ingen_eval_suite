"""Apply guarded content edits to a preview JSONL without overwriting review work.

A revision specifies base_dataset_sha256 and edits with id, changes, path,
before, and after. Identity, split, and approval fields cannot be edited here.
"""

import argparse
import copy
import json
from pathlib import Path

from dataset_io import ROOT, digest, load_config, records_bytes, require_valid
from validate_dataset import load_jsonl, unique_object

EDITABLE_PATHS = {
    "/query", "/context", "/ideal_response", "/construction_notes", "/input_metadata",
    "/evaluation_labels/required_facts", "/evaluation_labels/passages",
    "/evaluation_labels/sources", "/evaluation_labels/behavior_criteria",
    "/evaluation_labels/forbidden_claims", "/evaluation_labels/conflict_resolution",
}


def apply_review(records, revision):
    revised = copy.deepcopy(records)
    by_id = {record["id"]: record for record in revised}
    if len(by_id) != len(revised):
        raise ValueError("Duplicate case IDs in the base collection")
    if not revision.get("edits"):
        raise ValueError("Revision contains no edits")
    seen_ids = set()
    for edit in revision["edits"]:
        identifier = edit["id"]
        if identifier not in by_id or identifier in seen_ids:
            raise ValueError(f"Unknown or duplicate revision case: {identifier}")
        seen_ids.add(identifier)
        record = by_id[identifier]
        if not edit["changes"]:
            raise ValueError(f"Revision case has no changes: {identifier}")
        seen_paths = set()
        for change in edit["changes"]:
            path = change["path"]
            if path not in EDITABLE_PATHS or path in seen_paths:
                raise ValueError(f"Unsupported or duplicate revision path: {path}")
            seen_paths.add(path)
            target = record
            parts = path.lstrip("/").split("/")
            for part in parts[:-1]:
                target = target[part]
            key = parts[-1]
            if target.get(key) != change["before"]:
                raise ValueError(f"Field changed since review: {identifier} {path}")
            if change["after"] == change["before"]:
                raise ValueError(f"Unchanged revision field: {identifier} {path}")
            target[key] = copy.deepcopy(change["after"])
        review = record["evaluation_labels"]["review"]
        review.update(status="needs_revision", reviewer_ids=[], notes="Content changed since recorded language review. Review the updated wording and annotations before approval.")
        if record["language"] == "zh":
            review["native_zh_review_status"] = "pending"
    require_valid(revised, "collection")
    return revised


def update(base, revision_path, output):
    base, revision_path, output = map(Path, (base, revision_path, output))
    if output.exists() or output.resolve() == base.resolve():
        raise ValueError("Refusing to overwrite existing dataset or review work")
    revision = json.loads(revision_path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    if digest(base) != revision.get("base_dataset_sha256"):
        raise ValueError("Base collection differs from the version reviewed")
    records = apply_review(load_jsonl(base), revision)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as handle:
        handle.write(records_bytes(records))
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path)
    parser.add_argument("--revision", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    base = args.base or ROOT / "data" / load_config()["collection"]["file"]
    try:
        records = update(base, args.revision, args.output)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(1, f"{exc}\n")
    print(f"Wrote {len(records)} cases to {args.output}; changed cases need renewed review")


if __name__ == "__main__":
    main()
