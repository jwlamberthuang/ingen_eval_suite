"""Full draft allocations, pilot preservation, review separation, and manifests."""

from collections import Counter
import json
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest

from scripts.datasets.v2 import manage_dataset as v2
from src.extended_evaluator import score_extended_case


@pytest.fixture
def collection():
    return v2.read_records(v2.ROOT / v2.config()["collection"])


def test_full_draft_has_exact_allocations_and_truthful_review_status(collection):
    records, raw = collection
    report = v2.validate_records(records, "collection", raw)
    assert report["valid"], report["errors"]
    assert report["record_count"] == 200 and report["legacy_count"] == report["new_count"] == 100
    assert report["unapproved_count"] == 0 and report["pending_native_zh_count"] == 0
    assert report["new_subset_counts"] == {"calibration": 20, "held_out": 80}
    assert not report["release_ready"]
    assert Counter(r["language"] for r in records) == {"en": 130, "zh": 70}


def test_collection_preserves_both_original_and_revised_pilot_bytes(collection):
    records, raw = collection
    cfg = v2.config()
    prefix = (v2.ROOT / cfg["legacy_dataset"]).read_bytes() + (v2.ROOT / cfg["pilot"]).read_bytes()
    assert raw.startswith(prefix)
    assert len(records[112:]) == 88
    assert [int(r["id"].split("-")[-2]) for r in records[112:]] == list(range(113, 201))


def test_collection_profile_refuses_missing_case_even_while_draft(collection):
    records, raw = collection
    assert not v2.validate_records(records[:-1], "collection", raw)["valid"]


def test_release_still_requires_review_after_counts_pass(collection):
    records, raw = collection
    # Removing one actual attestation must still block an otherwise reviewed
    # collection. Use a non-pilot English fixture so no other invariant changes.
    records[112]["annotations"]["review"].update(status="draft", reviewer_ids=[], reviewed_on=None, content_sha256=None)
    report = v2.validate_records(records, "release", raw)
    assert not report["valid"] and not report["release_ready"]
    assert len(report["errors"]) == 1
    assert all("review pending" in e for e in report["errors"])


def test_changed_pilot_cannot_hide_in_full_collection(collection):
    records, raw = collection
    records[101]["query"] += " changed"
    report = v2.validate_records(records, "collection", raw)
    assert any("revised pilot" in e for e in report["errors"])


def test_split_membership_cannot_drift_while_keeping_group_quotas(collection):
    records, raw = collection
    new = records[112:]
    a = next(r for r in new if r["annotations"]["allocation_group"] == "hard_rag" and
             r["language"] == "en" and r["annotations"]["subset"] == "calibration")
    b = next(r for r in new if r["annotations"]["allocation_group"] == "hard_rag" and
             r["language"] == "en" and r["annotations"]["subset"] == "held_out")
    a["annotations"]["subset"], b["annotations"]["subset"] = b["annotations"]["subset"], a["annotations"]["subset"]
    report = v2.validate_records(records, "collection", raw)
    assert any("recorded family allocation" in e for e in report["errors"])


def test_probes_are_separate_atomic_support_challenges(collection):
    records, _ = collection
    adversarial = [r for r in records[100:] if r["annotations"]["allocation_group"] == "adversarial_rag"]
    assert len(adversarial) == 10
    assert {r["language"] for r in adversarial} == {"en", "zh"}
    supports = Counter(c["support"] for r in adversarial for p in r["reference"]["metric_probes"] for c in p["claims"])
    assert all(supports[k] for k in ("supported", "unsupported", "contradicted"))
    assert all("response" not in r and "model_output" not in r for r in records[100:])
    assert len({(r["query"], tuple(r["context"])) for r in records}) == 200


def test_rag_answer_contract_is_consistent_with_reviewed_pilot(collection):
    records, _ = collection
    rag = [r for r in records[100:] if r["evaluation_type"] == "rag"]
    assert all(r["task_input"] == rag[0]["task_input"] for r in rag)


@pytest.mark.parametrize("text", ["You finished the puzzle.", "Your badge is here.",
                                  "Nora asked her sister.", "用户带了水瓶，你还没签到。",
                                  "周阿姨拿着她的通知单。"])
def test_evidence_requires_explicit_referents(collection, text):
    records, _ = collection
    record = records[100]
    record["context"] = [text]
    assert v2.evidence_referent_errors(record)
    assert any("Explicit evidence referent" in e for e in v2.semantic_errors(record))


def test_new_evidence_and_events_use_names_while_dialogue_keeps_pronouns(collection):
    records, _ = collection
    assert all(not v2.evidence_referent_errors(r) for r in records[100:])
    record = next(r for r in records if "-0186-" in r["id"])
    assert "she" in record["query"].lower()
    assert not v2.evidence_referent_errors(record)
    assert not v2.EVIDENCE_PRONOUNS.search("老张和一只猫，没有描述其他人或物。")


def test_visible_event_description_requires_explicit_actor(collection):
    records, _ = collection
    record = next(r for r in records if "-0140-" in r["id"])
    assert record["task_input"]["event_descriptions"]["e1"] == "用户拍手"
    record["task_input"]["event_descriptions"]["e1"] = "你拍手"
    assert any("event_descriptions.e1" in e for e in v2.evidence_referent_errors(record))


def test_location_aliases_do_not_turn_a_door_into_a_window_location(collection):
    records, _ = collection
    record = next(r for r in records if r["id"] == "w03-htd-task-alignment-fari-zh-0163-base")
    prediction = {"tasks": [
        {"action": "open_window", "arguments": {"location": "客厅门"}},
        {"action": "close_door", "arguments": {"location": "客厅"}},
    ]}
    result = score_extended_case(record, json.dumps(prediction, ensure_ascii=False))
    # A bad first task cannot satisfy g1; its dependent door-closing goal also
    # receives no credit. This protects both argument meaning and precedence.
    assert result["metrics"]["goal_coverage"]["value"] == 0
    assert result["task_success"]["value"] == 0


def test_collection_manifest_matches_current_dataset_and_inputs(collection):
    records, raw = collection
    path = v2.ROOT / v2.config()["collection"]
    report = v2.validate_records(records, "release", raw)
    manifest = v2.loads(path.with_suffix(".manifest.json").read_text())
    assert v2.verify_manifest(manifest, path, raw, report)
    assert v2.config()["pilot"] in {item["file"] for item in manifest["construction_inputs"]}


def test_release_reviews_are_complete_and_bound_to_current_content(collection):
    records, raw = collection
    report = v2.validate_records(records, "release", raw)
    assert report["valid"] and report["release_ready"] and not report["errors"] and not report["warnings"]
    assert all(r["annotations"]["review"]["content_sha256"] == v2.content_hash(r) for r in records[100:])


def test_full_rebuild_is_exact_and_never_overwrites(tmp_path):
    output = tmp_path / "reproduced"
    assert v2.reproduce_collection(output)["valid"]
    for role in ("collection", "pilot"):
        source = v2.ROOT / v2.config()[role]
        assert (output / source.name).read_bytes() == source.read_bytes()
        assert (output / source.with_suffix(".manifest.json").name).read_bytes() == source.with_suffix(".manifest.json").read_bytes()
    with pytest.raises(FileExistsError):
        v2.reproduce_collection(output)


def test_full_master_edit_preserves_every_untouched_line(collection, tmp_path):
    records, raw = collection
    source = v2.ROOT / v2.config()["collection"]
    edits, output = tmp_path / "edits.json", tmp_path / "edited.jsonl"
    edits.write_bytes(v2.json_bytes({"base_sha256": v2.digest(raw), "edits": [{
        "id": records[112]["id"], "path": ["query"], "before": records[112]["query"],
        "after": "Has my parcel arrived, and who signed for it?"}]}))
    assert v2.apply_edits(source, edits, output)["valid"]
    original, changed = raw.splitlines(keepends=True), output.read_bytes().splitlines(keepends=True)
    assert original[:112] == changed[:112] and original[113:] == changed[113:]
    assert original[112] != changed[112] and source.read_bytes() == raw


def test_additions_review_contains_all_88_cases_and_requested_fonts(collection):
    records, raw = collection
    word = v2.ROOT / "docs/week-03/W03_Dataset_Additions_Review_v0.1.docx"
    w = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with ZipFile(word) as archive:
        assert "collection-sha256:" + v2.digest(raw) in archive.read("docProps/core.xml").decode()
        root = ET.fromstring(archive.read("word/document.xml"))
        text = "".join(t.text or "" for t in root.iter(w + "t"))
        for r in records[112:]:
            assert r["id"] in text and r["query"] in text
        for run in root.iter(w + "r"):
            text = "".join(t.text or "" for t in run.iter(w + "t"))
            if not text.strip():
                continue
            fonts = run.find(w + "rPr/" + w + "rFonts")
            assert fonts is not None
            if any("\u3400" <= c <= "\u9fff" for c in text):
                assert fonts.get(w + "eastAsia") == "Songti SC"
            elif any(c.isascii() and c.isalpha() for c in text):
                assert fonts.get(w + "ascii") == "Times New Roman"
