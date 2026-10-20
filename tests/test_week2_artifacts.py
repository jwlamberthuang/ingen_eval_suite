"""Validate frozen measurements, input boundaries, and the delivered artifacts."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
from src.experiment import score_run
from src.generation import read_jsonl

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/"results/week-02/baseline"


def test_experiment_replays_exactly_without_model_download():
    config = json.loads((ROOT/"configs/week-02.json").read_text())
    assert score_run(ROOT, config, replay=True) == json.loads((OUT/"scores.json").read_text())


def test_artifacts_and_implementation_match_recorded_hashes():
    manifest = json.loads((OUT/"run_manifest.json").read_text())
    assert manifest["status"] == "complete"
    for name, expected in manifest["artifacts"].items():
        assert hashlib.sha256((OUT/name).read_bytes()).hexdigest() == expected, name
    for group in [manifest["source_hashes"], manifest["scoring"]["source_hashes"]]:
        for name, expected in group.items():
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, name


def test_all_generation_inputs_use_only_permitted_fields():
    records = read_jsonl(ROOT/"data/W01_Evaluation_Dataset_v1.jsonl")
    responses = read_jsonl(OUT/"responses.jsonl")
    assert len(responses) == 100 and set(responses) == set(records)
    for identifier, row in responses.items():
        assert row["status"] == "ok" and row["attempt"] == 1
        payload = json.loads(row["input_messages"][-1]["content"])
        assert set(payload) <= {"platform", "evidence", "query", "learner_profile"}
        assert payload["query"] == records[identifier]["query"]
        assert [p["text"] for p in payload["evidence"]] == records[identifier]["context"]


def test_claim_inspection_covers_all_cases_and_current_inputs():
    review = json.loads((OUT/"claim_review.json").read_text())
    assert review["status"] == "checked"
    assert set(review["reviewed_case_ids"]) == set(read_jsonl(OUT/"responses.jsonl"))
    for name, expected in review["input_hashes"].items():
        assert hashlib.sha256((OUT/name).read_bytes()).hexdigest() == expected
    assert set(read_jsonl(OUT/"response_review.jsonl")) == set(review["reviewed_case_ids"])


def test_calibration_uses_only_designated_cases():
    records = read_jsonl(ROOT/"data/W01_Evaluation_Dataset_v1.jsonl")
    calibration = json.loads((OUT/"calibration.json").read_text())
    assert len(calibration["calibration_case_ids"]) == 20
    assert all(records[i]["evaluation_labels"]["subset"] == "calibration" for i in calibration["calibration_case_ids"])
    assert calibration["positive_count"] == 27 and calibration["negative_count"] == 3
    assert calibration["threshold"] == 0.8


def test_notebook_executed_every_code_cell_without_errors():
    notebook = json.loads((ROOT/"notebooks/week-02/W02_RAG_Evaluation_Pipeline.ipynb").read_text())
    code = [c for c in notebook["cells"] if c["cell_type"] == "code"]
    assert code and all(c["execution_count"] is not None for c in code)
    assert all(o["output_type"] != "error" for c in code for o in c["outputs"])


def test_word_results_use_requested_latin_and_chinese_fonts():
    w = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with ZipFile(ROOT/"docs/week-02/W02_RAG_Evaluation_Results.docx") as zipped:
        root = ET.fromstring(zipped.read("word/document.xml"))
        chinese = 0
        for run in root.iter(w+"r"):
            text = ''.join(t.text or '' for t in run.iter(w+"t"))
            if not text.strip():
                continue
            fonts = run.find(w+"rPr/"+w+"rFonts")
            assert fonts is not None
            if any('\u3400' <= c <= '\u9fff' for c in text):
                chinese += 1
                assert fonts.get(w+"eastAsia") == "Songti SC"
            elif any(c.isascii() and c.isalpha() for c in text):
                assert fonts.get(w+"ascii") == "Times New Roman"
        assert chinese > 0


def test_weekly_log_length_and_week_indexes():
    words = (ROOT/"weekly/Wk-02-Log.md").read_text().split('\n',2)[-1].split()
    assert 300 <= len(words) <= 500
    for week in ["week-01", "week-02"]:
        assert (ROOT/"deliverables"/week/"README.md").is_file()
