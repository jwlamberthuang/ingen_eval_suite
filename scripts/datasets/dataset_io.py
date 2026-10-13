"""Shared paths, deterministic serialization, and dataset manifests."""

import hashlib
import json
from pathlib import Path

from validate_dataset import ROOT, SCHEMA, unique_object, validate_records

CONFIG_PATH = ROOT / "dataset_config.json"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def records_bytes(records):
    return "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records).encode("utf-8")


def load_config(path=CONFIG_PATH):
    config = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    filenames = [config[role]["file"] for role in ("collection", "pilot")]
    if len(set(filenames)) != 2:
        raise ValueError("Collection and pilot need different filenames")
    for filename in filenames:
        if Path(filename).name != filename or not filename.endswith(".jsonl"):
            raise ValueError("Dataset filenames must be plain JSONL filenames")
    identifiers = config["pilot_case_ids"]
    if len(identifiers) != 12 or len(set(identifiers)) != 12:
        raise ValueError("Configuration needs twelve distinct pilot case IDs")
    return config


def require_valid(records, profile):
    report = validate_records(records, profile)
    if not report["valid"]:
        raise ValueError(f"{profile} validation failed: {report['errors']}")
    return report


def make_manifest(records, dataset_path, dataset_hash, config, role, source_hash):
    profile = "collection" if role == "collection" else "pilot"
    review = config["language_review"].copy()
    review["applies_to_current_source"] = review["dataset_sha256"] == source_hash
    release = config.get("release_review", {}).copy()
    release["applies_to_current_source"] = release.get("dataset_sha256") == source_hash
    if role == "collection" and release["applies_to_current_source"]:
        profile = "release"
    report = require_valid(records, profile)
    status = "changed_since_language_review"
    if review["applies_to_current_source"]:
        status = "language_reviewed_draft"
    if release["applies_to_current_source"]:
        status = "release" if role == "collection" else "reviewed_pilot"
    return {
        "dataset_name": "Week 1 bilingual dialogue evaluation",
        "dataset_version": config[role]["version"],
        "schema_version": "1.1.0",
        "dataset_file": Path(dataset_path).name,
        "dataset_sha256": dataset_hash,
        "schema_file": "schemas/w01_dialogue_case.schema.json",
        "schema_sha256": digest(SCHEMA),
        "status": status,
        "profile": profile,
        **{key: report[key] for key in (
            "record_count", "base_count", "variant_count", "family_count",
            "base_domain_counts", "base_difficulty_counts", "base_cell_counts",
            "base_edge_tag_counts", "base_tagged_case_count", "unapproved_count", "pending_native_zh_count",
            "unconfirmed_native_zh_authorship_count",
        )},
        "source_dataset_file": config["collection"]["file"],
        "source_dataset_sha256": source_hash,
        "language_review": review,
        "release_review": release,
        "split_policy": config.get("split_policy"),
        "base_subset_counts": {
            subset: sum(r["evaluation_labels"]["subset"] == subset for r in records
                        if r["evaluation_labels"]["record_kind"] == "base")
            for subset in ("calibration", "held_out", "unassigned")
        },
        "dialogue_target": config["dialogue_target"],
        "construction_inputs": [
            {"file": str(path.relative_to(ROOT)), "sha256": digest(path)}
            for path in [CONFIG_PATH, *sorted((ROOT / "scripts/datasets").glob("*.py"))]
        ],
        "notes": [
            "The collection JSONL is the authoritative editable source; the pilot is derived from the configured case IDs.",
            "Authorship confirmation, language review, and release annotation checks are recorded separately; no independent human agreement study is claimed.",
            "No model generations, metric scores, or audio evaluations are included.",
        ],
    }
