"""Build editable Week 3 pilot or additions review packets from JSONL.

Use the document dependencies. Existing review files are never overwritten;
choose a fresh output directory when checking a rebuild.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from set_bilingual_fonts import apply_bilingual_fonts

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.datasets.v2.manage_dataset import expected_prediction, read_records  # noqa: E402

NAMES = {"rag": "Grounded dialogue", "stum_spatial": "Spatial reasoning",
         "stum_temporal": "Event ordering", "seom_entities": "Entities and classes",
         "htd_task_alignment": "Requested tasks"}
STEM = "W03_Dataset_Pilot_Review_v0.1"


def sections(record):
    """One shared content model for Word and Markdown; no duplicate seed data."""
    kind, ref, task = record["evaluation_type"], record["reference"], record["task_input"]
    result = [("User query", record["query"])]
    if record.get("input_metadata"):
        result.append(("Visible user information", json.dumps(record["input_metadata"], ensure_ascii=False)))
    result.append(("Evidence", "\n".join(f"p{i+1:03d}  {text}" for i, text in enumerate(record["context"]))))
    if kind == "stum_spatial":
        visible = f"Subject: {task['subject']}. Reference: {task['reference']}. Axis: {task['axis']}. Frame: {task['coordinate_frame']}."
    elif kind == "stum_temporal":
        events = "; ".join(f"{k} = {v}" for k, v in task["event_descriptions"].items())
        pairs = "; ".join(f"{p['pair_id']}: {p['event_a']} relative to {p['event_b']}" for p in task["pairs"])
        visible = events + "\n" + pairs
    elif kind == "seom_entities":
        visible = "Use the nine entity classes on the opening page. Include only explicitly present entities."
    elif kind == "htd_task_alignment":
        visible = "Use the action catalog on the opening page. Return requested tasks with complete string-valued arguments, in an allowed order."
    else:
        visible = "Give a natural spoken answer grounded in the supplied evidence. State uncertainty or capability limits where needed."
    result.append(("Task instructions", visible))
    if kind == "rag":
        result.append(("Expected answer", ref["ideal_response"]))
        explanation = "\n".join(ref["behavior_criteria"] + [f["text"] for f in ref["required_facts"]])
    else:
        # One line per entity/pair/task keeps structured answers readable in Word.
        prediction = expected_prediction(record)
        key, value = next(iter(prediction.items()))
        if isinstance(value, list):
            rendered = '{"' + key + '": [\n' + ",\n".join(
                "  " + json.dumps(item, ensure_ascii=False) for item in value) + "\n]}"
        else:
            rendered = json.dumps(prediction, ensure_ascii=False)
        result.append(("Expected structured answer", rendered))
        explanation = ref["derivation"]["explanation"]
    result.append(("Answer explanation", explanation))
    if kind == "seom_entities":
        result.append(("Accepted mentions for review", "\n".join(
            f"{e['class']}: " + " / ".join(e["aliases"]) for e in ref["entities"])))
    elif kind == "htd_task_alignment":
        result.append(("Accepted argument wording for review", "\n".join(
            f"{field}  {canonical}: " + " / ".join(aliases)
            for field, groups in ref["argument_aliases"].items() for canonical, aliases in groups.items())))
    if kind == "rag" and ref["metric_probes"]:
        probe = ref["metric_probes"][0]
        result.append(("Fixed metric probe", f"Deliberately wrong candidate: {probe['candidate_response']}\n"
                       f"Ideal factual support: {probe['ideal_property_score']:g}. {probe['rationale']}"))
    return result


def set_font(run):
    run.font.name = "Times New Roman"
    run.font.color.rgb = RGBColor(0, 0, 0)
    fonts = run._element.get_or_add_rPr().get_or_add_rFonts()
    for slot in ("ascii", "hAnsi", "cs"):
        fonts.set(qn("w:" + slot), "Times New Roman")
    fonts.set(qn("w:eastAsia"), "Songti SC")


def paragraph(doc, text, style=None):
    p = doc.add_paragraph(style=style)
    for index, line in enumerate(text.split("\n")):
        if index:
            p.add_run().add_break()
        set_font(p.add_run(line))
    return p


def build(source, output_dir, mode="pilot"):
    records, raw = read_records(source)
    cfg = json.loads((ROOT / "configs/dataset-v2.json").read_text())
    if mode == "additions":
        records = [r for r in records if "evaluation_type" in r and r["id"] not in cfg["pilot_case_ids"]]
    # Run the v2 pilot validator before authoring. Keep this presentation builder
    # usable with document-only runtimes as well as the full project environment.
    expected_count = 12 if mode == "pilot" else 88
    if len(records) != expected_count or any("evaluation_type" not in r for r in records):
        raise ValueError("Unexpected review case count or missing task type")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = STEM if mode == "pilot" else "W03_Dataset_Additions_Review_v0.1"
    word, markdown = output_dir / f"{stem}.docx", output_dir / f"{mode if mode == 'pilot' else 'additions'}_review.md"
    if word.exists() or markdown.exists():
        raise FileExistsError("Review files already exist; use a fresh output directory to preserve edits")
    doc = Document()
    for border in list(doc.styles.element.iter(qn("w:pBdr"))):
        border.getparent().remove(border)
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = section.bottom_margin = Inches(0.65)
    section.left_margin = section.right_margin = Inches(0.75)
    compact = mode == "additions"
    for name, size in (("Normal", 10.5 if compact else 11), ("Title", 23),
                       ("Heading 1", 13 if compact else 17), ("Heading 2", 11)):
        style = doc.styles[name]
        style.font.name, style.font.size = "Times New Roman", Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.space_after = Pt(3 if compact else 5)
        style.paragraph_format.space_before = Pt(7 if name == "Heading 2" else 0)
        style.paragraph_format.line_spacing = 1.0 if compact else 1.05
    doc.core_properties.author = ""
    doc.core_properties.last_modified_by = ""
    title = "Week 3 dataset pilot review" if mode == "pilot" else "Week 3 dataset additions review"
    doc.core_properties.title = title
    doc.core_properties.subject = "Evaluation cases and reviewed reference annotations"
    doc.core_properties.identifier = ("pilot" if mode == "pilot" else "collection") + "-sha256:" + hashlib.sha256(raw).hexdigest()
    paragraph(doc, title, "Title")
    paragraph(doc, f"{len(records)} cases for wording and reference review", "Subtitle")
    paragraph(doc, "Please review queries, evidence, expected answers, and accepted wording. Edit directly or add comments. Evidence and event labels must use explicit names or user rather than personal pronouns. Keep dialogue natural and check that answers follow from the evidence.")
    languages = Counter(r["language"] for r in records)
    subsets = Counter(r["annotations"]["subset"] for r in records)
    approved = sum(r["annotations"]["review"]["status"] == "approved" for r in records)
    native = sum(r["language"] == "zh" and r["annotations"]["review"]["native_zh_authorship_status"] == "confirmed"
                 and r["annotations"]["review"]["native_zh_review_status"] == "approved" for r in records)
    review_status = (f"{languages['en']} English and {languages['zh']} Chinese cases; "
                     f"{subsets['calibration']} calibration and {subsets['held_out']} held-out. "
                     f"Approved content references: {approved}/{len(records)}. "
                     f"Chinese native authorship and review confirmed: {native}/{languages['zh']}.")
    paragraph(doc, review_status)
    paragraph(doc, "The structured JSON answers are scoring references. They do not represent spoken robot replies or actions that have been executed. The fixed wrong-answer probe is separate from model generation.")
    paragraph(doc, "Review coverage", "Heading 2")
    counts = Counter(r["evaluation_type"] for r in records)
    tiers = Counter(r["difficulty"] for r in records)
    labels = {"rag": "grounded dialogue", "stum_spatial": "spatial", "stum_temporal": "event ordering",
              "seom_entities": "entity", "htd_task_alignment": "task planning"}
    coverage = "; ".join(f"{counts[k]} {labels[k]} {'case' if counts[k] == 1 else 'cases'}" for k in NAMES)
    coverage += f". Difficulty: {tiers['easy']} Easy, {tiers['medium']} Medium, {tiers['hard']} Hard."
    paragraph(doc, coverage)
    paragraph(doc, "Entity classes", "Heading 2")
    paragraph(doc, "person, robot, animal, furniture, mobility_aid, container, device, document, other")
    paragraph(doc, "Action catalog", "Heading 2")
    for action, arguments in json.loads((ROOT / "configs/dataset-v2.json").read_text())["action_catalog"].items():
        paragraph(doc, f"{action}({', '.join(arguments)})")
    paragraph(doc, "How edits are incorporated", "Heading 2")
    paragraph(doc, "After review, wording and reference changes are reconciled into the JSONL and validated together. Changing a query or expected answer may also require updating constraints, evidence links, aliases, or task dependencies. Validation alone does not approve an example.")
    if compact:
        paragraph(doc, "Held out cases", "Heading 2")
        paragraph(doc, "Review ground-truth annotations before freezing the collection. Keep these held-out cases separate from parser tuning, global alias-rule changes, and model selection. No new model predictions are supplied in this packet.")
    md = ["# " + title, "", review_status, "", "Review wording, evidence, expected answers, accepted aliases, and dependencies. Evidence and event labels use explicit names or user rather than personal pronouns. Structured answers are reference fixtures, not model responses or executed actions.", "", coverage, "", "### Entity classes", "", ", ".join(cfg["entity_classes"]), "", "### Action catalog", ""]
    md += [f"- `{action}({', '.join(args)})`" for action, args in cfg["action_catalog"].items()]
    md += [""]
    for index, record in enumerate(records, 1):
        if not compact or index % 2 == 1:
            doc.add_page_break()
        start = len(doc.paragraphs)
        display_index = int(record["id"].split("-")[-2]) - 100
        title = f"Case {display_index:02d} {NAMES[record['evaluation_type']]}"
        paragraph(doc, title, "Heading 1")
        review_label = "Approved" if record["annotations"]["review"]["status"] == "approved" else "Review pending"
        metadata = f"{record['domain']} | {record['difficulty'].title()} | {record['annotations']['subset']} | {review_label}"
        paragraph(doc, (record["id"] + " | " if compact else "") + metadata)
        if not compact:
            paragraph(doc, record["id"])
        md += [f"## {title}", "", f"`{record['id']}`", "", metadata, ""]
        for heading, content in sections(record):
            md += [f"### {heading}", "", content, ""]
            if compact:
                if heading == "Task instructions" and record["evaluation_type"] in {"rag", "seom_entities", "htd_task_alignment"}:
                    continue
                if heading == "Answer explanation" and record["evaluation_type"] == "rag":
                    content = record["annotations"]["tier_rationale"]
                if heading == "Expected structured answer":
                    content = json.dumps(expected_prediction(record), ensure_ascii=False)
                content = content.replace("\n", "; ")
                p = paragraph(doc, "")
                run = p.add_run(heading + ": "); run.bold = True; set_font(run)
                set_font(p.add_run(content))
            else:
                paragraph(doc, heading, "Heading 2")
                paragraph(doc, content)
        paragraph(doc, "Review notes" + (": " if compact else ""), None if compact else "Heading 2")
        if not compact:
            paragraph(doc, " ")
        if compact:
            block = doc.paragraphs[start:]
            for p in block:
                p.paragraph_format.keep_together = True
                p.paragraph_format.keep_with_next = p is not block[-1]
            block[-1].paragraph_format.space_after = Pt(16)
        md += ["### Review notes", "", "", ""]
    for p in doc.paragraphs:
        for run in p.runs:
            set_font(run)
    # Meaningful page numbers help locate edits in a thirteen-page review packet.
    footer = section.footer.paragraphs[0]
    footer.alignment = 2
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)
    doc.save(word)
    apply_bilingual_fonts(word)
    markdown.write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
    return word, markdown


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "data/W03_Evaluation_Dataset_Pilot_v0.1.jsonl")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs/week-03")
    parser.add_argument("--mode", choices=("pilot", "additions"), default="pilot")
    args = parser.parse_args()
    for path in build(args.source, args.output_dir, args.mode):
        print(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path.name)
