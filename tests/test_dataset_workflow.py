"""Prevent lost edits, stale pilot data, and accidental review approval."""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/datasets"))

from build_dataset import build
from dataset_io import digest, load_config, records_bytes
from update_dataset import apply_review, update
from validate_dataset import COLLECTION_CELLS, load_jsonl, validate_records


@pytest.fixture
def config():
    return load_config()


@pytest.fixture
def collection(config):
    return load_jsonl(ROOT / "data" / config["collection"]["file"])


def revision_for(records, identifier=None, path="/query", after="A revised wording for review"):
    record = next(r for r in records if r["id"] == identifier) if identifier else records[0]
    target = record
    for part in path.lstrip("/").split("/"):
        target = target[part]
    return {"edits": [{"id": record["id"], "changes": [{"path": path, "before": copy.deepcopy(target), "after": after}]}]}


def test_complete_collection_and_shared_pilot_are_consistent(collection, config):
    report = validate_records(collection, "collection")
    assert report["valid"] and report["base_cell_counts"] == COLLECTION_CELLS
    assert report["record_count"] == 100 and report["family_count"] == 99
    assert report["unapproved_count"] == 0
    assert report["pending_native_zh_count"] == 0
    assert report["unconfirmed_native_zh_authorship_count"] == 0
    lookup = {r["id"]: r for r in collection}
    pilot = load_jsonl(ROOT / "data" / config["pilot"]["file"])
    assert pilot == [lookup[i] for i in config["pilot_case_ids"]]
    assert all(r["evaluation_labels"]["review"]["reviewer_ids"] == ["Huang"] for r in collection)


def test_collection_profile_rejects_a_missing_case(collection):
    report = validate_records(collection[:-1], "collection")
    assert {"collection_size", "collection_cell"} <= {e["code"] for e in report["errors"]}


def test_language_review_does_not_establish_native_authorship(collection):
    chinese = next(r for r in collection if r["language"] == "zh")
    assert chinese["evaluation_labels"]["review"]["native_zh_review_status"] == "approved"
    chinese["evaluation_labels"]["review"]["status"] = "approved"
    chinese["evaluation_labels"]["review"]["native_zh_author_id"] = None
    assert "schema" in {e["code"] for e in validate_records(collection)["errors"]}


def test_build_is_reproducible_and_preserves_authoritative_bytes(tmp_path, config):
    paths = build(tmp_path, config=config)
    assert len(paths) == 4
    for path in paths:
        assert path.read_bytes() == (ROOT / "data" / path.name).read_bytes()
    before = {p.name: p.read_bytes() for p in paths}
    with pytest.raises(ValueError, match="Refusing to overwrite"):
        build(tmp_path, config=config)
    assert {p.name: p.read_bytes() for p in paths} == before


def test_refresh_keeps_master_and_syncs_a_changed_pilot_case(tmp_path, collection, config):
    build(tmp_path, config=config)
    source = tmp_path / config["collection"]["file"]
    collection[1]["query"] = "When would my reminder need to be today?"
    source.write_bytes(records_bytes(collection))
    before = source.read_bytes()
    build(tmp_path, source=source, config=config, refresh=True)
    assert source.read_bytes() == before
    assert load_jsonl(tmp_path / config["pilot"]["file"])[1]["query"] == collection[1]["query"]
    manifest = json.loads(source.with_suffix(".manifest.json").read_text())
    assert manifest["status"] == "changed_since_language_review"
    assert not manifest["language_review"]["applies_to_current_source"]


def test_refresh_refuses_to_discard_direct_pilot_edits(tmp_path, config):
    build(tmp_path, config=config)
    source = tmp_path / config["collection"]["file"]
    pilot = tmp_path / config["pilot"]["file"]
    rows = load_jsonl(pilot)
    rows[0]["query"] = "A direct pilot edit that must not disappear"
    pilot.write_bytes(records_bytes(rows))
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    with pytest.raises(ValueError, match="Pilot was edited directly"):
        build(tmp_path, source=source, config=config, refresh=True)
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before


def test_revision_preserves_identity_and_invalidates_changed_language_review(collection):
    original = copy.deepcopy(collection)
    chinese = next(r for r in collection if r["language"] == "zh")
    revision = revision_for(collection, chinese["id"], after="重阳节里说的登高是什么呀？")
    revised = apply_review(collection, revision)
    assert collection == original
    changed = next(r for r in revised if r["id"] == chinese["id"])
    for field in ("id", "domain", "language", "difficulty", "context", "ideal_response"):
        assert changed[field] == chinese[field]
    for field in ("family_id", "subset", "required_facts", "sources", "expected_behavior"):
        assert changed["evaluation_labels"][field] == chinese["evaluation_labels"][field]
    review = changed["evaluation_labels"]["review"]
    assert review["status"] == "needs_revision" and review["reviewer_ids"] == []
    assert review["native_zh_review_status"] == "pending" and review["native_zh_author_id"] is None


@pytest.mark.parametrize("mistake", ["stale", "duplicate_id", "duplicate_path", "unknown", "approval", "split", "unchanged"])
def test_invalid_revision_does_not_mutate_source(collection, mistake):
    original = copy.deepcopy(collection)
    revision = revision_for(collection)
    edit = revision["edits"][0]
    if mistake == "stale":
        edit["changes"][0]["before"] = "Stale wording"
    elif mistake == "duplicate_id":
        revision["edits"].append(copy.deepcopy(edit))
    elif mistake == "duplicate_path":
        edit["changes"].append(copy.deepcopy(edit["changes"][0]))
    elif mistake == "unknown":
        edit["id"] = "w01-fari-en-9999-base"
    elif mistake in {"approval", "split"}:
        path = "/evaluation_labels/review/status" if mistake == "approval" else "/evaluation_labels/subset"
        edit["changes"].append({"path": path, "before": "draft", "after": "approved"})
    else:
        edit["changes"][0]["after"] = edit["changes"][0]["before"]
    with pytest.raises(ValueError):
        apply_review(collection, revision)
    assert collection == original


def test_update_rejects_stale_base_and_existing_output(tmp_path, collection):
    base, patch, output = [tmp_path / name for name in ("base.jsonl", "revision.json", "preview.jsonl")]
    base.write_bytes(records_bytes(collection))
    revision = revision_for(collection)
    revision["base_dataset_sha256"] = "0" * 64
    patch.write_text(json.dumps(revision))
    with pytest.raises(ValueError, match="Base collection differs"):
        update(base, patch, output)
    assert not output.exists()
    revision["base_dataset_sha256"] = digest(base)
    patch.write_text(json.dumps(revision))
    update(base, patch, output)
    assert load_jsonl(output)[0]["query"] == "A revised wording for review"
    before = output.read_bytes()
    with pytest.raises(ValueError, match="Refusing to overwrite"):
        update(base, patch, output)
    assert output.read_bytes() == before


def test_partial_and_conflicting_targets_keep_their_behavior(collection):
    lookup = {int(r["id"].split("-")[-2]): r["evaluation_labels"] for r in collection}
    for number in (56, 61, 74, 90):
        assert lookup[number]["required_facts"] == []
    for number in (57, 91):
        assert lookup[number]["required_facts"][0]["context_support"] == "conflicting"
        assert lookup[number]["expected_behavior"] == "clarify"
    for number in (60, 89):
        assert [f["context_support"] for f in lookup[number]["required_facts"]] == ["supported", "unsupported"]
        assert lookup[number]["expected_behavior"] == "partial_answer_with_uncertainty"


def test_release_split_and_authorship_are_recorded(collection, config):
    report = validate_records(collection, "release")
    assert report["valid"] and report["warnings"] == []
    calibration = [r for r in collection if r["evaluation_labels"]["subset"] == "calibration"]
    held_out = [r for r in collection if r["evaluation_labels"]["subset"] == "held_out"]
    assert len(calibration) == 20 and len(held_out) == 80
    assert {r["evaluation_labels"]["family_id"] for r in calibration}.isdisjoint(
        r["evaluation_labels"]["family_id"] for r in held_out
    )
    assert [r["id"] for r in calibration] == config["split_policy"]["calibration_case_ids"]
    assert set(config["pilot_case_ids"]) <= {r["id"] for r in calibration}
    assert all(r["evaluation_labels"]["review"]["native_zh_author_id"] == "Huang"
               for r in collection if r["language"] == "zh")


def test_release_is_invalidated_by_unapproved_case(collection):
    collection[0]["evaluation_labels"]["review"]["status"] = "needs_revision"
    assert "release_review" in {e["code"] for e in validate_records(collection, "release")["errors"]}


def test_reviewed_wording_and_revised_behavior_remain_consistent(collection):
    lookup = {r["id"]: r for r in collection}
    case = lookup["w01-senpai-en-0008-base"]
    assert case["ideal_response"] == "Let's work it out. Four red notebooks cost eight credits, and three blue ones cost nine credits. Eight plus nine makes seventeen credits altogether."
    assert "explicit multiplication notation is optional" in case["evaluation_labels"]["behavior_criteria"][1]
    assert lookup["w01-fari-zh-0070-base"]["query"] == "今天book club聊哪本书，在哪儿meeting？"
