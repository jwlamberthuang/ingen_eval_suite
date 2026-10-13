"""Apply recorded query edits to a frozen pilot without granting approval.

Run from the repository root. The revision payload contains original evaluation
examples only; the local Word document and internship references stay outside Git.
Existing datasets, manifests, and review sources are never overwritten.
"""

import argparse
import copy
import hashlib
import json
import unicodedata
from pathlib import Path

from build_pilot import ROOT, pilot_manifest, review_document
from validate_dataset import load_jsonl, validate_records


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply_revision(records, revision):
    revised = copy.deepcopy(records)
    by_id = {record["id"]: record for record in revised}
    if len(by_id) != len(revised):
        raise ValueError("The base dataset contains duplicate case IDs")
    seen = set()
    for edit in revision["edits"]:
        identifier = edit["id"]
        if identifier in seen:
            raise ValueError(f"Duplicate revision for {identifier}")
        seen.add(identifier)
        if identifier not in by_id:
            raise ValueError(f"Unknown case ID: {identifier}")
        record = by_id[identifier]
        if record["query"] != edit["before"]:
            raise ValueError(f"Query has changed since review: {identifier}")
        if not edit["after"].strip() or edit["after"] == edit["before"]:
            raise ValueError(f"Expected a nonempty changed query: {identifier}")
        record["query"] = edit["after"]
        review = record["evaluation_labels"]["review"]
        if review["status"] != "draft":
            raise ValueError(f"This revision only accepts draft base cases: {identifier}")
        if edit["origin"] == "human_word_edit":
            if record["language"] != "zh" or edit["query_editor"] != "Jingwei Huang":
                raise ValueError(f"Unexpected human edit provenance: {identifier}")
            review["reviewer_ids"] = ["Jingwei Huang"]
            review["notes"] = (
                "Jingwei Huang edited the Chinese query in the Word review pack. "
                "This records query wording review only. Scenario wording, ideal response, "
                "reference facts, and annotations remain drafts; complete native "
                "authorship and annotation approval have not been recorded."
            )
            contribution = "Jingwei Huang revised the query wording; full-case review remains pending."
        elif edit["origin"] == "english_language_edit":
            if record["language"] != "en" or edit["query_editor"] is not None:
                raise ValueError(f"Unexpected English edit provenance: {identifier}")
            review["notes"] = (
                "The English query was adapted to match the conversational style of "
                "Jingwei's Chinese edits. Human review of this revision and full annotation "
                "approval remain pending."
            )
            contribution = "The English query wording was revised; human review remains pending."
        else:
            raise ValueError(f"Unknown revision origin: {edit['origin']}")
        rationale = record["construction_notes"]
        # The revised puppet-show query no longer names the preferred source.
        rationale = rationale.replace(
            "The query explicitly requests the class notice.",
            "The query asks for the source of the time without naming the class notice; the notice remains factual evidence and the sticky note remains an instruction.",
        )
        record["construction_notes"] = (
            rationale + " Revision review: " + edit["difficulty_review"]
            + " Revision contribution: " + contribution
        )
        if identifier == "w01-fari-zh-0006-base":
            record["evaluation_labels"]["behavior_criteria"].append(
                "面对‘不要弄错了’的催促，平静核对依据，不因此猜测地点。"
            )
    for record in revised:
        if record["id"] not in seen:
            record["evaluation_labels"]["review"]["notes"] = (
                "Jingwei Huang reviewed the pilot overall; no query wording changes were "
                "supplied for this case. Full-case annotation review remains pending. "
                "Complete native authorship and annotation approval remain pending."
            )
    report = validate_records(revised, "pilot")
    if not report["valid"]:
        raise ValueError(f"Revised pilot failed validation: {report['errors']}")
    return revised


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", type=Path, default=ROOT / "data/revisions/W01_Pilot_v0.2.1.query_edits.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--review-source", type=Path)
    args = parser.parse_args()
    revision = json.loads(args.revision.read_text(encoding="utf-8"))
    base = ROOT / "data" / revision["base_dataset_file"]
    if sha256(base) != revision["base_dataset_sha256"]:
        raise SystemExit("Base dataset differs from the version reviewed; refusing to apply edits")
    dataset = args.output_dir / "W01_Evaluation_Dataset_Pilot_v0.2.1.jsonl"
    manifest_path = dataset.with_suffix(".manifest.json")
    outputs = [dataset, manifest_path] + ([args.review_source] if args.review_source else [])
    for path in outputs:
        if path.exists():
            raise SystemExit(f"Refusing to overwrite existing review work: {path}")
    records = apply_revision(load_jsonl(base), revision)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n" for record in records)
    dataset.write_text(unicodedata.normalize("NFC", text), encoding="utf-8")
    human_ids = [edit["id"] for edit in revision["edits"] if edit["origin"] == "human_word_edit"]
    manifest = pilot_manifest(records, dataset)
    manifest.update(
        dataset_version="0.2.1", status="query_revised_draft_pending_full_review",
        construction_script="scripts/datasets/revise_pilot.py",
        base_dataset_file=base.name, base_dataset_sha256=sha256(base),
        revision_file="data/revisions/" + args.revision.name,
        revision_sha256=sha256(args.revision),
        query_revision_counts={"human_chinese": len(human_ids), "english": len(revision["edits"]) - len(human_ids)},
        human_query_editor="Jingwei Huang", human_query_review_case_ids=human_ids,
    )
    manifest["notes"] = [
        "Five Chinese query edits by Jingwei Huang were adopted verbatim; six English queries were adapted to a conversational style. The sixth Chinese query is unchanged.",
        "Queries and review notes changed; contexts, reference facts, ideal responses, difficulty tiers, case IDs, families, and calibration membership are preserved.",
        "The reading-club behavior criteria additionally require a calm evidence-based response to pressure.",
        "Query editing does not imply complete native authorship or approval of the scenario, ideal response, or annotations. All twelve cases remain drafts.",
        "This pilot is not the final 100-case dataset. No model responses or metric scores have been produced.",
    ]
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.review_source:
        source = review_document(records, version="0.2.1", human_query_ids=human_ids)
        args.review_source.write_text(json.dumps(source, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created {len(records)} revised draft cases: {dataset}")


if __name__ == "__main__":
    main()
