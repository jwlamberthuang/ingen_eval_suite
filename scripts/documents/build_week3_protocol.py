"""Build the Week 3 Word protocol from its canonical Markdown source.

Use the document runtime and a fresh output directory. The small Markdown subset
is deliberately limited to headings, paragraphs, and lists; layout breaks are
explicit so Word and Markdown retain the same substantive content.
"""

import argparse
import json
from pathlib import Path
import re
import tempfile

from build_docx import build

ROOT = Path(__file__).resolve().parents[2]


def blocks_from_markdown(text):
    blocks, paragraph, items = [], [], []
    ordered = False

    def flush():
        if paragraph:
            blocks.append({"type": "paragraph", "text": " ".join(paragraph)})
            paragraph.clear()
        if items:
            blocks.append({"type": "list", "ordered": ordered, "items": items.copy()})
            items.clear()

    for line in text.splitlines():
        if not line.strip():
            flush()
        elif line == "<!-- pagebreak -->":
            flush()
            blocks.append({"type": "page_break"})
        elif line.startswith("# "):
            flush()
            blocks.append({"type": "title", "text": line[2:]})
        elif line.startswith("## "):
            flush()
            blocks.append({"type": "heading", "level": 1, "text": line[3:]})
        elif line.startswith("- ") or re.match(r"^\d+\. ", line):
            flush_paragraph = bool(paragraph)
            if flush_paragraph:
                flush()
            next_ordered = not line.startswith("- ")
            if items and next_ordered != ordered:
                flush()
            ordered = next_ordered
            items.append(re.sub(r"^(?:- |\d+\. )", "", line))
        elif items:
            items[-1] += " " + line.strip()
        else:
            paragraph.append(line.strip())
    flush()
    return blocks


def build_protocol(source, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "W03_Evaluation_Protocol.docx"
    if output.exists():
        raise FileExistsError("Protocol exists; use a fresh output directory")
    text = source.read_text(encoding="utf-8")
    version = re.search(r"^Version ([0-9.]+)", text, flags=re.MULTILINE)
    data = {"title": "Week 3 Evaluation Protocol", "version": version.group(1) if version else "0.1",
            "subject": "Metric definitions and reproducible evaluation procedure",
            "blocks": blocks_from_markdown(text)}
    with tempfile.TemporaryDirectory(prefix="week3-protocol-") as temporary:
        spec = Path(temporary) / "protocol.json"
        spec.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        build(spec, output)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path,
                        default=ROOT / "docs/week-03/W03_Evaluation_Protocol.md")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    build_protocol(args.source, args.output_dir)
