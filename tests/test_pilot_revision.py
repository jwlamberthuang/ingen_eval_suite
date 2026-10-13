"""Query review must preserve evidence and cannot grant annotation approval."""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/datasets"))

from revise_pilot import apply_revision
from validate_dataset import load_jsonl, validate_records


@pytest.fixture
def inputs():
    records = load_jsonl(ROOT / "data/W01_Evaluation_Dataset_Pilot_v0.1.1.jsonl")
    revision = json.loads((ROOT / "data/revisions/W01_Pilot_v0.2.1.query_edits.json").read_text())
    return records, revision


def test_query_revision_preserves_evidence_and_approval_boundary(inputs):
    records, revision = inputs
    before = copy.deepcopy(records)
    revised = apply_revision(records, revision)
    assert records == before, "The frozen source records must not be mutated"
    for old, new in zip(records, revised):
        for field in ("id", "domain", "language", "difficulty", "context", "ideal_response", "input_metadata"):
            assert new.get(field) == old.get(field)
        labels = new["evaluation_labels"]
        for field in ("family_id", "subset", "required_facts", "passages", "sources", "answerability", "expected_behavior", "accepted_behaviors", "edge_case_tags"):
            assert labels[field] == old["evaluation_labels"][field]
        assert labels["review"]["status"] == "draft"
        assert labels["review"]["native_zh_author_id"] is None
        if new["language"] == "zh":
            assert labels["review"]["native_zh_review_status"] == "pending"
    report = validate_records(revised, "pilot")
    assert report["valid"]
    assert report["unapproved_count"] == 12
    assert report["pending_native_zh_count"] == 6
    assert load_jsonl(ROOT / "data/W01_Evaluation_Dataset_Pilot_v0.2.1.jsonl") == revised


@pytest.mark.parametrize("mutation,message", [
    (lambda records, revision: records[0].update(query="A newer human edit"), "Query has changed since review"),
    (lambda records, revision: revision["edits"].append(copy.deepcopy(revision["edits"][0])), "Duplicate revision"),
    (lambda records, revision: revision["edits"][0].update(id="w01-fari-en-0099-base"), "Unknown case ID"),
    (lambda records, revision: revision["edits"][0].update(origin="human_word_edit", query_editor="Jingwei Huang"), "Unexpected human edit provenance"),
])
def test_revision_rejects_stale_or_misattributed_changes(inputs, mutation, message):
    records, revision = inputs
    mutation(records, revision)
    with pytest.raises(ValueError, match=message):
        apply_revision(records, revision)
