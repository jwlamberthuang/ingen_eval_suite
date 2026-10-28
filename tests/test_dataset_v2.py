"""V2 draft acceptance, truthful review state, and preservation of frozen data."""

from copy import deepcopy
import json
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest

from scripts.datasets.v2 import manage_dataset as v2


@pytest.fixture
def pilot():
    return v2.read_records(v2.ROOT / v2.config()["pilot"])[0]


def test_pilot_covers_contract_without_claiming_release(pilot):
    report = v2.validate_records(pilot, "pilot")
    assert report["valid"], report["errors"]
    assert report["new_type_counts"] == {"rag": 4, "stum_spatial": 2, "stum_temporal": 1,
                                          "seom_entities": 2, "htd_task_alignment": 3}
    assert report["new_language_counts"] == {"en": 8, "zh": 4}
    assert report["new_subset_counts"] == {"calibration": 12}
    assert report["unapproved_count"] == 0
    assert report["pending_native_zh_count"] == 0
    assert not report["release_ready"]


def test_release_rejects_incomplete_pilot_even_after_review(pilot):
    report = v2.validate_records(pilot, "release")
    assert not report["valid"]
    assert any("100 preserved legacy" in e for e in report["errors"])
    assert not any("review pending" in e for e in report["errors"])


@pytest.mark.parametrize("index", range(12))
def test_every_new_reference_satisfies_its_own_typed_contract(pilot, index):
    record = pilot[index]
    assert not list(v2.schema_validator().iter_errors(record))
    assert not v2.semantic_errors(record)


@pytest.mark.parametrize("mutation", ["missing_type", "wrong_type", "hidden_input", "extra_root"])
def test_schema_rejects_missing_or_leaking_fields(pilot, mutation):
    record = deepcopy(pilot[3])
    if mutation == "missing_type":
        record.pop("evaluation_type")
    elif mutation == "wrong_type":
        record["evaluation_type"] = "seom_entities"
    elif mutation == "hidden_input":
        record["task_input"]["answer"] = "left_of"
    else:
        record["approved_by"] = "invented"
    assert list(v2.schema_validator().iter_errors(record))


@pytest.mark.parametrize("mutation", ["spatial_gold", "alias_collision", "event_description",
                                    "evidence_index", "rag_evidence", "rag_source", "probe_score"])
def test_semantic_inconsistencies_are_rejected(pilot, mutation):
    if mutation == "spatial_gold":
        pilot[3]["reference"]["answer"] = "right_of"
    elif mutation == "alias_collision":
        pilot[6]["reference"]["entities"][1]["aliases"].append("Nora")
    elif mutation == "event_description":
        pilot[5]["task_input"]["event_descriptions"].pop("e1")
    elif mutation == "evidence_index":
        pilot[3]["reference"]["derivation"]["evidence_indices"] = [99]
    elif mutation == "rag_evidence":
        pilot[0]["reference"]["required_facts"][0]["evidence_passage_ids"] = ["p999"]
    elif mutation == "rag_source":
        pilot[0]["reference"]["passages"][0]["source_ids"] = ["missing-source"]
    else:
        pilot[2]["reference"]["metric_probes"][0]["ideal_property_score"] = 1
    assert not v2.validate_records(pilot, "pilot")["valid"]


def test_family_cohort_and_calibration_budget_are_guarded(pilot):
    pilot[4]["annotations"]["family_id"] = pilot[3]["annotations"]["family_id"]
    pilot[4]["annotations"]["subset"] = "held_out"
    report = v2.validate_records(pilot, "pilot")
    assert not report["valid"]
    assert any("crosses" in e for e in report["errors"])
    assert any("entirely in calibration" in e for e in report["errors"])


def test_new_chinese_review_cannot_inherit_original_attestation(pilot):
    record = pilot[1]
    review = record["annotations"]["review"]
    review.update(status="approved", reviewer_ids=["fixture-reviewer"], reviewed_on="2026-10-26",
                  content_sha256=v2.content_hash(record), native_zh_authorship_status="pending",
                  native_zh_author_id=None, native_zh_review_status="pending")
    assert any("Chinese approval requires" in e for e in v2.semantic_errors(record))
    review.update(native_zh_authorship_status="confirmed", native_zh_author_id="fixture-author",
                  native_zh_review_status="approved")
    assert not v2.semantic_errors(record)
    record["query"] += " changed"
    assert any("content hash" in e for e in v2.semantic_errors(record))


def test_lossless_legacy_prefix_and_original_ids_are_required(pilot):
    legacy, raw = v2.read_records(v2.ROOT / v2.config()["legacy_dataset"])
    combined = raw + v2.records_bytes(pilot)
    assert v2.validate_records(legacy + pilot, raw=combined)["valid"]
    changed = deepcopy(legacy)
    changed[0]["query"] += " changed"
    assert not v2.validate_records(changed + pilot, raw=combined)["valid"]
    assert not v2.validate_records(legacy + pilot, raw=b" " + combined)["valid"]
    newcomer = deepcopy(legacy[0])
    newcomer["id"] = "w01-fari-en-0999-base"
    assert not v2.validate_records([newcomer])["valid"]


def test_assembly_is_exact_and_never_overwrites(tmp_path):
    cfg = v2.config()
    output = tmp_path / "preview.jsonl"
    report = v2.assemble(v2.ROOT / cfg["pilot"], output)
    assert report["valid"] and report["record_count"] == 112 and report["legacy_bytes_checked"]
    assert output.read_bytes() == ((v2.ROOT / cfg["legacy_dataset"]).read_bytes() +
                                   (v2.ROOT / cfg["pilot"]).read_bytes())
    with pytest.raises(FileExistsError):
        v2.assemble(v2.ROOT / cfg["pilot"], output)


def test_manifest_rejects_stale_schema_or_tooling(pilot):
    path = v2.ROOT / v2.config()["pilot"]
    raw = path.read_bytes()
    report = v2.validate_records(pilot, "pilot", raw)
    manifest = v2.make_manifest(path, raw, report)
    assert v2.verify_manifest(manifest, path, raw, report)
    manifest["schema_sha256"] = "0" * 64
    assert not v2.verify_manifest(manifest, path, raw, report)
    manifest = v2.make_manifest(path, raw, report)
    manifest["construction_inputs"][-1]["sha256"] = "0" * 64
    assert not v2.verify_manifest(manifest, path, raw, report)


def test_published_pilot_manifest_matches_current_source(pilot):
    path = v2.ROOT / v2.config()["pilot"]
    raw = path.read_bytes()
    report = v2.validate_records(pilot, "pilot", raw)
    manifest = v2.loads(path.with_suffix(".manifest.json").read_text())
    assert v2.verify_manifest(manifest, path, raw, report)


def test_word_review_is_synchronized_and_has_requested_fonts(pilot):
    path = v2.ROOT / "docs/week-03/W03_Dataset_Pilot_Review_v0.1.docx"
    w = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with ZipFile(path) as archive:
        core = archive.read("docProps/core.xml").decode()
        assert "pilot-sha256:" + v2.digest((v2.ROOT / v2.config()["pilot"]).read_bytes()) in core
        root = ET.fromstring(archive.read("word/document.xml"))
        all_text = "".join(t.text or "" for t in root.iter(w + "t"))
        for record in pilot:
            assert record["query"] in all_text
            assert record["id"] in all_text
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


def edit_payload(pilot, path, before, after):
    return {"base_sha256": v2.digest(v2.records_bytes(pilot)), "edits": [
        {"id": pilot[1]["id"], "path": path, "before": before, "after": after}]}


def test_guarded_edits_preserve_user_text_and_reset_review(pilot, tmp_path):
    source, edits, output = (tmp_path / name for name in ("source.jsonl", "edits.json", "preview.jsonl"))
    source.write_bytes(v2.records_bytes(pilot))
    payload = edit_payload(pilot, ["query"], pilot[1]["query"], "请帮我问问，门禁密码怎么改？")
    edits.write_bytes(v2.json_bytes(payload))
    original = source.read_bytes()
    assert v2.apply_edits(source, edits, output)["valid"]
    revised = v2.read_records(output)[0]
    assert revised[1]["query"] == payload["edits"][0]["after"]
    assert revised[0] == pilot[0] and source.read_bytes() == original
    assert revised[1]["annotations"]["review"]["native_zh_authorship_status"] == "pending"
    assert revised[1]["annotations"]["review"]["status"] == "draft"


@pytest.mark.parametrize("mutation", ["base_hash", "before", "split", "review"])
def test_guarded_edit_failures_write_nothing(pilot, tmp_path, mutation):
    source, edits, output = (tmp_path / name for name in ("source.jsonl", "edits.json", "preview.jsonl"))
    source.write_bytes(v2.records_bytes(pilot))
    payload = edit_payload(pilot, ["query"], pilot[1]["query"], "revised query")
    if mutation == "base_hash":
        payload["base_sha256"] = "0" * 64
    elif mutation == "before":
        payload["edits"][0]["before"] = "stale text"
    else:
        payload["edits"][0]["path"] = ["annotations", "subset" if mutation == "split" else "review"]
    edits.write_bytes(v2.json_bytes(payload))
    with pytest.raises(ValueError):
        v2.apply_edits(source, edits, output)
    assert not output.exists()


@pytest.mark.parametrize("value", ['{"a":1,"a":2}', '{"value":NaN}', '{"value":Infinity}'])
def test_strict_json_loading(value):
    with pytest.raises(ValueError):
        v2.loads(value)
