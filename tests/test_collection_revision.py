"""Review replay preserves evaluation identity and rejects stale or unsafe edits."""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/datasets"))

from revise_collection import apply_review
from validate_dataset import load_jsonl, validate_records


def inputs():
    return (
        load_jsonl(ROOT / "data/W01_Evaluation_Dataset_Draft_v0.3.jsonl"),
        json.loads((ROOT / "data/revisions/W01_Draft_v0.4.review_edits.json").read_text()),
    )


def test_review_replay_preserves_case_identity_and_does_not_grant_release_approval():
    base, revision = inputs()
    original = copy.deepcopy(base)
    revised = apply_review(base, revision)
    assert base == original
    for before, after in zip(base, revised, strict=True):
        assert tuple(before[k] for k in ("id", "domain", "difficulty")) == tuple(after[k] for k in ("id", "domain", "difficulty"))
        for key in ("family_id", "subset", "answerability", "expected_behavior"):
            assert before["evaluation_labels"][key] == after["evaluation_labels"][key]
        assert before["evaluation_labels"]["review"]["native_zh_review_status"] == after["evaluation_labels"]["review"]["native_zh_review_status"]
    assert load_jsonl(ROOT / "data/W01_Evaluation_Dataset_Draft_v0.4.jsonl") == revised
    report = validate_records(revised, "draft")
    assert report["valid"] and report["unapproved_count"] == 32
    assert report["family_count"] == 31 and report["pending_native_zh_count"] == 13
    release = validate_records(revised, "release")
    assert {"release_review", "human_review"} <= {e["code"] for e in release["errors"]}


@pytest.mark.parametrize("mistake", ["stale", "duplicate", "approval"])
def test_invalid_review_is_rejected_without_mutating_the_source(mistake):
    base, revision = inputs()
    original = copy.deepcopy(base)
    edit = revision["edits"][0]
    if mistake == "stale":
        edit["changes"][0]["before"] = "A stale field value"
    elif mistake == "duplicate":
        edit["changes"].append(copy.deepcopy(edit["changes"][0]))
    else:
        edit["changes"].append({"path": "/evaluation_labels/review/status", "before": "draft", "after": "approved"})
    with pytest.raises(ValueError):
        apply_review(base, revision)
    assert base == original
