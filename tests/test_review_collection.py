"""Expansion and publication metadata must not bypass release review checks."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/datasets"))

from build_review_batch import review_batch_cases
from validate_dataset import load_jsonl, validate_records


def test_new_families_remain_unassigned_and_separate_from_the_pilot():
    pilot = load_jsonl(ROOT / "data/W01_Evaluation_Dataset_Pilot_v0.2.1.jsonl")
    batch = review_batch_cases()
    original_ids = {r["id"] for r in pilot}
    original_families = {r["evaluation_labels"]["family_id"] for r in pilot}
    assert not original_ids.intersection(r["id"] for r in batch)
    assert not original_families.intersection(r["evaluation_labels"]["family_id"] for r in batch)
    assert len({r["evaluation_labels"]["family_id"] for r in batch}) == 20
    assert all(r["evaluation_labels"]["subset"] == "unassigned" for r in batch)
    collection = pilot + batch
    report = validate_records(collection, "draft")
    assert report["valid"]
    assert report["unapproved_count"] == 32
    assert report["pending_native_zh_count"] == 13
    assert report["family_count"] == 31
    assert load_jsonl(ROOT / "data/W01_Evaluation_Dataset_Draft_v0.3.jsonl") == collection
    release = validate_records(collection, "release")
    assert {"release_review", "human_review", "release_count"} <= {e["code"] for e in release["errors"]}


def test_omitted_public_author_identity_does_not_grant_native_approval():
    batch = review_batch_cases()
    assert all(r["evaluation_labels"]["review"]["author_id"] is None for r in batch)
    assert all(s["author_id"] is None for r in batch for s in r["evaluation_labels"]["sources"] if s["kind"] == "original_scenario")
    assert validate_records(batch, "draft")["valid"]
    chinese = next(r for r in batch if r["language"] == "zh")
    chinese["evaluation_labels"]["review"].update(status="approved", reviewer_ids=["Jingwei Huang"])
    report = validate_records(batch, "draft")
    assert "schema" in {e["code"] for e in report["errors"]}
