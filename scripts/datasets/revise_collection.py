"""Apply a versioned dialogue review without overwriting drafts or granting approval."""

import argparse
import copy
import json
from pathlib import Path

from build_pilot import ROOT
from build_review_batch import digest, manifest, write_records
from validate_dataset import load_jsonl, validate_records


EDITABLE_PATHS = {
    "/query", "/context", "/ideal_response", "/construction_notes",
    "/evaluation_labels/required_facts", "/evaluation_labels/sources",
    "/evaluation_labels/behavior_criteria", "/evaluation_labels/forbidden_claims",
    "/evaluation_labels/review/notes", "/evaluation_labels/review/reviewer_ids",
}


def apply_review(records, revision):
    revised = copy.deepcopy(records)
    by_id = {record["id"]: record for record in revised}
    if len(by_id) != len(revised):
        raise ValueError("Duplicate case IDs in the base collection")
    seen_ids = set()
    for edit in revision["edits"]:
        identifier = edit["id"]
        if identifier not in by_id or identifier in seen_ids:
            raise ValueError(f"Unknown or duplicate revision case: {identifier}")
        seen_ids.add(identifier)
        record = by_id[identifier]
        if record["evaluation_labels"]["review"]["status"] != "draft":
            raise ValueError(f"Expected a draft case: {identifier}")
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
            if target[key] != change["before"]:
                raise ValueError(f"Field changed since review: {identifier} {path}")
            if change["after"] == change["before"]:
                raise ValueError(f"Unchanged revision field: {identifier} {path}")
            target[key] = copy.deepcopy(change["after"])
    report = validate_records(revised, "draft")
    if not report["valid"]:
        raise ValueError(f"Revised collection failed validation: {report['errors']}")
    return revised


def revision_manifest(records, path, version, inputs, revision, revision_path):
    result = manifest(records, path, version, inputs)
    result.update(
        created_on=revision["revision_date"],
        status="language_revised_draft_pending_full_review",
        construction_script="scripts/datasets/revise_collection.py",
        revision_file="data/revisions/" + revision_path.name,
        revision_sha256=digest(revision_path),
        dialogue_target=revision["dialogue_target"],
        human_word_review_case_ids=revision["human_word_review_case_ids"],
        human_word_field_edit_count=revision["human_word_field_edit_count"],
        english_style_case_count=revision["english_style_case_count"],
    )
    result["notes"].extend([
        "Human Word wording edits are preserved verbatim. Supporting annotations are aligned separately; full-case approval remains pending.",
        "English cases use concise spoken dialogue and child-appropriate explanations. Mixed queries use English content words within Chinese sentences.",
        "Equivalent spoken and numeric times or quantities express the same required facts. Audio quality and audio latency are outside this text collection.",
        "Case IDs, families, difficulty tiers, and draft subset assignments are preserved.",
    ])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", type=Path, default=ROOT / "data/revisions/W01_Draft_v0.4.review_edits.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    revision = json.loads(args.revision.read_text(encoding="utf-8"))
    base = ROOT / "data" / revision["base_dataset_file"]
    if digest(base) != revision["base_dataset_sha256"]:
        raise SystemExit("Base collection differs from the version reviewed")
    collection_path = args.output_dir / "W01_Evaluation_Dataset_Draft_v0.4.jsonl"
    batch_path = args.output_dir / "batches/W01_Review_Batch_02_v0.2.jsonl"
    paths = [collection_path, collection_path.with_suffix(".manifest.json"),
             batch_path, batch_path.with_suffix(".manifest.json")]
    for path in paths:
        if path.exists():
            raise SystemExit(f"Refusing to overwrite existing review work: {path}")
    collection = apply_review(load_jsonl(base), revision)
    batch_ids = set(revision["batch_case_ids"])
    batch = [record for record in collection if record["id"] in batch_ids]
    if len(batch) != len(batch_ids) or len(batch_ids) != 20:
        raise SystemExit("Expected twenty distinct existing batch case IDs")
    write_records(collection_path, collection)
    write_records(batch_path, batch)
    inputs = [{"dataset_file": "data/" + base.name, "dataset_sha256": digest(base)},
              {"revision_file": "data/revisions/" + args.revision.name, "revision_sha256": digest(args.revision)}]
    for records, path, version in [(collection, collection_path, "0.4.0"), (batch, batch_path, "0.2.0")]:
        result = revision_manifest(records, path, version, inputs, revision, args.revision)
        # Collection-wide edits are recorded in the revision; these counts describe this artifact.
        artifact_ids = {r["id"] for r in records}
        result["human_word_review_case_ids"] = [i for i in revision["human_word_review_case_ids"] if i in artifact_ids]
        result["english_style_case_count"] = sum(r["language"] == "en" for r in records)
        path.with_suffix(".manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Created revised 32-case collection and 20-case batch; all remain review drafts.")


if __name__ == "__main__":
    main()
