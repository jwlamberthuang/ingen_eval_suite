"""Known expected acceptance/rejection cases for the pilot data contract."""

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/datasets"))


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


validator = module("validate_dataset", "scripts/datasets/validate_dataset.py")
from dataset_io import digest, load_config, make_manifest


@pytest.fixture
def records():
    return validator.load_jsonl(ROOT / "data" / load_config()["pilot"]["file"])


def codes(records, profile="draft"):
    return {error["code"] for error in validator.validate_records(records, profile)["errors"]}


def test_pilot_is_reviewed_and_structurally_valid(records):
    report = validator.validate_records(records, "pilot")
    assert report["errors"] == []
    assert report["record_count"] == 12
    assert report["family_count"] == 11
    assert report["base_domain_counts"] == {"fari-en": 3, "fari-zh": 3, "senpai-en": 3, "senpai-zh": 3}
    assert report["base_difficulty_counts"] == {"easy": 4, "medium": 4, "hard": 4}
    assert report["base_tagged_case_count"] == 8
    assert report["unapproved_count"] == 0
    assert report["pending_native_zh_count"] == 0
    assert report["unconfirmed_native_zh_authorship_count"] == 0


@pytest.mark.parametrize("mutation,expected", [
    (lambda r: r[0].update(language="zh"), "schema"),
    (lambda r: r[0]["evaluation_labels"]["required_facts"][0].update(evidence_passage_ids=["p999"]), "evidence_reference"),
    (lambda r: r[0]["evaluation_labels"]["passages"][0].update(context_index=9), "passage_indices"),
    (lambda r: r[0]["evaluation_labels"]["required_facts"][0].update(source_ids=["missing"]), "source_reference"),
    (lambda r: r[0]["evaluation_labels"].update(accepted_behaviors=["abstain"]), "behavior"),
    (lambda r: r[0]["evaluation_labels"]["review"].update(difficulty_rule="H1"), "tier_rule"),
    (lambda r: r[0]["evaluation_labels"].update(rubric_criteria=["fari_coherence"]), "coherence_history"),
    (lambda r: r[4]["evaluation_labels"].update(subset="held_out"), "family_leakage"),
    (lambda r: r[3]["evaluation_labels"]["sources"][1].update(accessed_on="2026-02-30"), "schema"),
    (lambda r: r[0]["evaluation_labels"]["required_facts"][0].update(fact_id="f002"), "duplicate_annotation_id"),
    (lambda r: r[0]["evaluation_labels"]["required_facts"][0].update(context_support="unsupported", evidence_passage_ids=[]), "context_support"),
])
def test_invalid_annotation_is_rejected(records, mutation, expected):
    mutation(records)
    assert expected in codes(records)


def test_duplicate_case_ids_are_rejected(records):
    records.append(copy.deepcopy(records[0]))
    assert "duplicate_case_id" in codes(records)


def test_unreviewed_chinese_cannot_be_approved(records):
    review = records[3]["evaluation_labels"]["review"]
    review.update(status="approved", reviewer_ids=["human-reviewer"], notes="Reviewed English labels only.", native_zh_author_id=None, native_zh_review_status="pending")
    assert "schema" in codes(records)


def test_pilot_cannot_pass_as_release(records):
    problems = codes(records, "release")
    assert {"release_count", "release_edges"} <= problems


def test_missing_edge_type_is_detected(records):
    records[3]["evaluation_labels"]["edge_case_tags"] = []
    assert "edge_coverage" in codes(records, "pilot")


@pytest.mark.parametrize("text", ['{"id": "a", "id": "b"}\n', '{"value": NaN}\n', '[1, 2]\n'])
def test_strict_jsonl_rejects_ambiguous_input(tmp_path, text):
    path = tmp_path / "invalid.jsonl"
    path.write_text(text)
    with pytest.raises(ValueError, match="Line 1"):
        validator.load_jsonl(path)


def test_changed_context_is_detected_by_manifest(tmp_path, records):
    path = tmp_path / "pilot.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    manifest = {"dataset_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    assert validator.check_manifest(path, manifest)
    records[0]["context"][0] = "Nora now prefers gardening."
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    assert not validator.check_manifest(path, manifest)


@pytest.mark.parametrize("field,expected", [
    ("dataset_sha256", "manifest_hash"),
    ("schema_sha256", "manifest_schema_hash"),
])
def test_cli_rejects_changed_manifest_hash(tmp_path, records, monkeypatch, field, expected):
    path = tmp_path / "pilot.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    config = load_config()
    source = ROOT / "data" / config["collection"]["file"]
    manifest = make_manifest(records, path, digest(path), config, "pilot", digest(source))
    manifest[field] = "0" * 64
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))
    report_path = tmp_path / "report.json"
    monkeypatch.setattr(validator.sys, "argv", [
        "validate_dataset", str(path), "--profile", "pilot",
        "--manifest", str(manifest_path), "--report", str(report_path),
    ])
    assert validator.main() == 1
    assert expected in {e["code"] for e in json.loads(report_path.read_text())["errors"]}


def test_variant_cannot_change_parent_query(records):
    variant = copy.deepcopy(records[0])
    variant["id"] = "w01-fari-en-0001-v01"
    variant["query"] = "A different request"
    variant["evaluation_labels"].update(record_kind="context_variant", base_case_id=records[0]["id"])
    records.append(variant)
    assert "variant_invariant" in codes(records)
