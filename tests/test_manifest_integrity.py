"""Regression coverage for metadata edits that previously left stale manifests."""

import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts/datasets"))
from validate_dataset import manifest_errors


def test_current_release_and_pilot_manifests_match_all_inputs():
    for name in ["W01_Evaluation_Dataset_v1", "W01_Evaluation_Dataset_Pilot_v0.4"]:
        path = ROOT/"data"/(name+".jsonl")
        assert manifest_errors(path, json.loads(path.with_suffix(".manifest.json").read_text())) == []


def test_stale_schema_hash_is_detected():
    path = ROOT/"data/W01_Evaluation_Dataset_v1.jsonl"
    manifest = json.loads(path.with_suffix(".manifest.json").read_text())
    manifest["schema_sha256"] = "0"*64
    assert "manifest_schema_hash" in {e["code"] for e in manifest_errors(path, manifest)}


def test_stale_construction_input_hash_is_detected():
    path = ROOT/"data/W01_Evaluation_Dataset_v1.jsonl"
    manifest = json.loads(path.with_suffix(".manifest.json").read_text())
    manifest["construction_inputs"][0]["sha256"] = "0"*64
    assert "manifest_input_hash" in {e["code"] for e in manifest_errors(path, manifest)}


def test_incorrect_review_snapshot_is_detected():
    path = ROOT/"data/W01_Evaluation_Dataset_v1.jsonl"
    manifest = json.loads(path.with_suffix(".manifest.json").read_text())
    manifest["language_review"]["dataset_sha256"] = "0"*64
    assert "manifest_review_hash" in {e["code"] for e in manifest_errors(path, manifest)}
