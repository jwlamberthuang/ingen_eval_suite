"""Keep published deliverables self-contained and preserve required Word fonts."""

import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit
from zipfile import ZipFile
import xml.etree.ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[1]
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
PRIVATE_PATH = re.compile(r"file://(?=[A-Za-z/])|/(?:Users|home|private|tmp)/|(?<![A-Za-z0-9_])[A-Za-z]:\\", re.I)
DOCUMENTS = ("W01_InGen_AI_Evaluation_Framework", "W01_Dataset_Specification")


def check_reference(path, target):
    parsed = urlsplit(target)
    if parsed.scheme:
        assert parsed.scheme == "https" and parsed.netloc, (path, target)
        return
    resolved = (path.parent / unquote(parsed.path)).resolve()
    assert resolved.is_relative_to(ROOT), (path, target)
    assert resolved.is_file() or (not parsed.path and parsed.fragment), (path, target)


def published_text_files():
    roots = [ROOT / name for name in ("data", "docs", "schemas", "scripts", "tests", "weekly",
                                     "src", "configs", "deliverables", "notebooks", "results")]
    paths = [p for p in ROOT.iterdir() if p.is_file()]
    paths += [p for directory in roots for p in directory.rglob("*") if p.is_file()]
    return [p for p in paths if p.suffix in {".md", ".json", ".jsonl", ".py", ".txt", ".ipynb"}
            and "__pycache__" not in p.parts]


def test_public_text_has_no_workstation_file_references():
    for path in published_text_files():
        assert not any(PRIVATE_PATH.search(value) for value in published_strings(path)), path


def published_strings(path):
    """Inspect decoded structured text, so escaped line breaks are not drive paths."""
    text = path.read_text(encoding="utf-8")
    if path.suffix not in {".json", ".jsonl", ".ipynb"}:
        return [text]
    objects = [json.loads(line) for line in text.splitlines() if line.strip()] if path.suffix == ".jsonl" else [json.loads(text)]
    def strings(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, list):
            for item in value:
                yield from strings(item)
        elif isinstance(value, dict):
            for key, item in value.items():
                yield key
                yield from strings(item)
    return [s for value in objects for s in strings(value)]


def test_structured_privacy_scan_handles_escaped_line_breaks_and_real_paths(tmp_path):
    path = tmp_path / "example.ipynb"
    path.write_text(json.dumps({"source": ["Results:\nNext line"]}))
    assert not any(PRIVATE_PATH.search(value) for value in published_strings(path))
    absolute = "/" + "Users" + "/" + "example"
    path.write_text(json.dumps({"source": [absolute]}))
    assert any(PRIVATE_PATH.search(value) for value in published_strings(path))
    drive = "C" + ":" + chr(92) + "example"
    path.write_text(json.dumps({"source": [drive]}))
    assert any(PRIVATE_PATH.search(value) for value in published_strings(path))


def test_markdown_links_resolve_within_suite_or_to_public_https():
    for path in published_text_files():
        if path.suffix == ".md":
            for target in re.findall(r"\]\(([^\s)]+)\)", path.read_text()):
                check_reference(path, target)


@pytest.mark.parametrize("stem", DOCUMENTS)
def test_word_deliverables_have_public_links_and_requested_fonts(stem):
    path = ROOT / "docs" / f"{stem}.docx"
    with ZipFile(path) as zipped:
        for name in zipped.namelist():
            if name.endswith((".xml", ".rels")):
                text = zipped.read(name).decode("utf-8")
                assert not PRIVATE_PATH.search(text), (path, name)
                if name.endswith(".rels"):
                    for relationship in ET.fromstring(text):
                        if relationship.get("TargetMode") == "External":
                            check_reference(path, relationship.get("Target"))
        document = ET.fromstring(zipped.read("word/document.xml"))
        chinese_runs = 0
        for run in document.iter(W + "r"):
            text = "".join(t.text or "" for t in run.iter(W + "t"))
            if not text.strip():
                continue
            fonts = run.find(W + "rPr/" + W + "rFonts")
            assert fonts is not None
            if any('\u3400' <= char <= '\u9fff' for char in text):
                chinese_runs += 1
                assert fonts.get(W + "eastAsia") == "Songti SC", text
            elif any(char.isascii() and char.isalpha() for char in text):
                assert fonts.get(W + "ascii") == "Times New Roman", text
        for run in document.iter(M + "r"):
            fonts = run.find(W + "rPr/" + W + "rFonts")
            assert fonts is not None and fonts.get(W + "ascii") == "Times New Roman"
        if stem.endswith("Framework"):
            assert len(list(document.iter(M + "oMath"))) == 4
        else:
            assert chinese_runs > 0


def test_required_week1_artifacts_and_log_length():
    for stem in DOCUMENTS:
        assert (ROOT / "docs" / f"{stem}.docx").is_file()
        assert (ROOT / "docs/sources" / f"{stem}.json").is_file()
    assert (ROOT / "data/W01_Evaluation_Dataset_v1.jsonl").is_file()
    words = (ROOT / "weekly/Wk-01-Log.md").read_text().split("\n", 2)[-1].split()
    assert 300 <= len(words) <= 500


def test_specification_schema_and_config_versions_match():
    config = json.loads((ROOT / "dataset_config.json").read_text())
    schema = json.loads((ROOT / "schemas/w01_dialogue_case.schema.json").read_text())
    source = json.loads((ROOT / "docs/sources/W01_Dataset_Specification.json").read_text())
    assert config["collection"]["version"] == source["version"] == "1.0.0"
    assert schema["$defs"]["labels"]["properties"]["schema_version"]["const"] == "1.1.0"
    label_table = next(b for b in source["blocks"] if b.get("caption", "").startswith("Table 5"))
    assert label_table["rows"][0] == ["schema_version", "String fixed to 1.1.0."]
