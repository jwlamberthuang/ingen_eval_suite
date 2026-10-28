"""Build the annotation amendment review copies without overwriting Word edits."""

import argparse
import json
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from set_bilingual_fonts import apply_bilingual_fonts

ROOT = Path(__file__).resolve().parents[2]
STEM = 'W03_Context_Recall_Review_v2.0.1'


def read(path):
    return json.loads((ROOT / path).read_text())


def format_score(metric):
    if metric['value'] is None:
        return 'N/A (no unique answer target)'
    details = metric['details']
    return f"{metric['value']:g} ({details['supported_facts']}/{details['required_facts']} targets supported)"


def build(output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    word = output_dir / (STEM + '.docx')
    markdown = output_dir / 'context_recall_correction.md'
    if word.exists() or markdown.exists():
        raise FileExistsError('Use a fresh directory to preserve reviewer edits')
    patch = read('data/annotations/W03_Context_Recall_v2.0.1.json')
    result = read('results/week-03/context-recall-v2.0.1/context_recall.json')
    scores = {r['id']: r for r in result['per_case']}
    records = {r['id']: r for r in [json.loads(l) for l in
               (ROOT / 'data/W01_Evaluation_Dataset_v2.jsonl').read_text().splitlines()]}
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = section.bottom_margin = Inches(.65)
    section.left_margin = section.right_margin = Inches(.75)
    for name, size in [('Normal', 10.5), ('Title', 23), ('Heading 1', 14), ('Heading 2', 11)]:
        style = doc.styles[name]
        style.font.name, style.font.size = 'Times New Roman', Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.line_spacing = 1.0
        style.paragraph_format.space_after = Pt(4)
        style.paragraph_format.space_before = Pt(4 if name == 'Heading 2' else 0)
        fonts = style.element.get_or_add_rPr().get_or_add_rFonts()
        for slot in ('ascii', 'hAnsi', 'cs'):
            fonts.set(qn('w:' + slot), 'Times New Roman')
        fonts.set(qn('w:eastAsia'), 'Songti SC')
    for border in list(doc.styles.element.iter(qn('w:pBdr'))):
        border.getparent().remove(border)
    doc.core_properties.author = doc.core_properties.last_modified_by = ''
    doc.core_properties.title = 'Week 3 context recall annotation review'
    doc.core_properties.subject = 'Provisional annotation amendment 2.0.1'
    doc.core_properties.identifier = 'w03-context-recall-2.0.1-approved'
    md = []

    def paragraph(text, style=None, heading_level=None):
        p = doc.add_paragraph(text, style)
        if heading_level:
            md.extend(['#' * heading_level + ' ' + text, ''])
        else:
            md.extend([text, ''])
        return p

    paragraph('Week 3 context recall annotation review', 'Title', 1)
    paragraph('Annotation amendment 2 0 1 approved', 'Subtitle')
    paragraph('This record contains the 17 reviewed and approved annotation changes. All 55 new RAG inventories were inspected. The correction measures whether the supplied evidence establishes each requested answer target. Supported descriptions of missing information no longer substitute for unavailable answers.')
    paragraph('Review status', 'Heading 2', 2)
    paragraph(f"Intern annotation review approved all 17 corrections on {patch['approval']['reviewed_on']}, including the five cases with revised Chinese annotation wording. The approval binds the exact amendment content. Original dialogue and authorship approvals remain specific to the frozen source. Annotation review does not establish independent human assessment of model responses.")
    paragraph('Scoring rules', 'Heading 2', 2)
    paragraph('Recall is supported requested targets divided by all requested targets. Unsupported and conflicting targets stay in the denominator. Unresolved targets have canonical_value=null; their text names a slot without inventing its value. An unidentified referent with no unique target uses an empty inventory and N/A. Known negative states and established capability limits remain supported when they answer the query.')
    paragraph('What the correction changes', 'Heading 2', 2)
    paragraph('The 200-case release and completed experiment remain frozen. This amendment changes only the context-recall scoring view. Queries, evidence, expected answers, raw model outputs, claim inspection, all other metrics, and the 0.80 threshold remain unchanged. Saved responses and vectors are replayed without generation. These cases have already been inspected; this is a diagnostic correction, not a fresh held-out experiment.')
    paragraph('Corrected cohort results', 'Heading 2', 2)
    for row in result['context_recall_by_cohort']:
        paragraph(f"{row['cohort']}: {row['mean']:.4f}; {row['n_scored']}/{row['n_total']} defined; {row['n_not_applicable']} N/A.")
    paragraph('Future annotation changes', 'Heading 2', 2)
    paragraph('Preserve this approved record before revising target granularity, support status, evidence links, or N/A decisions. Requested answer values remain unresolved unless authoritative evidence supplies them. Changed annotation content requires renewed review and a new sealed version; do not overwrite the frozen baseline.')
    md.extend(['[Annotation amendment](../../data/annotations/W03_Context_Recall_v2.0.1.json) · '
               '[Schema](../../schemas/w03_context_recall_amendment.schema.json) · '
               '[Replay results](../../results/week-03/context-recall-v2.0.1/context_recall.json) · '
               '[Replay manifest](../../results/week-03/context-recall-v2.0.1/manifest.json)', ''])
    for index, edit in enumerate(patch['edits']):
        if index % 2 == 0:
            doc.add_page_break()
        else:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(4)
        r, score = records[edit['id']], scores[edit['id']]
        paragraph('Case ' + edit['id'].split('-')[-2], 'Heading 1', 2)
        paragraph(f"{edit['id']} | {r['language'].upper()} | {score['cohort']} | Approved")
        for heading, body in [
            ('User query', r['query']),
            ('Evidence', '\n'.join(f'p{i+1:03d}  {t}' for i, t in enumerate(r['context']))),
            ('Expected answer retained', r['reference']['ideal_response']),
            ('Before correction', '\n'.join(f"{f['fact_id']}  {f['text']} [{f['context_support']}]" for f in edit['before'])),
            ('Approved answer targets', '\n'.join(f"{f['fact_id']}  {f['text']} [{f['context_support']}; evidence: {', '.join(f['evidence_passage_ids']) or 'none'}]" for f in edit['after']) or 'Empty inventory because the referent is unresolved'),
            ('Reason for change', edit['rationale']),
            ('Recall change', format_score(score['baseline']) + ' to ' + format_score(score['corrected'])),
        ]:
            p = doc.add_paragraph()
            p.add_run(heading + '  ').bold = True
            p.add_run(body)
            md.extend(['### ' + heading, '', body, ''])
    for p in doc.paragraphs:
        for run in p.runs:
            run.font.name = 'Times New Roman'
            run.font.color.rgb = RGBColor(0, 0, 0)
    footer = section.footer.paragraphs[0]
    footer.alignment = 2
    footer.add_run('Week 3 annotation review   ')
    field = OxmlElement('w:fldSimple'); field.set(qn('w:instr'), 'PAGE'); footer._p.append(field)
    doc.save(word)
    apply_bilingual_fonts(word)
    markdown.write_text('\n'.join(md))
    print(word.relative_to(ROOT) if word.is_relative_to(ROOT) else word.name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'docs/week-03')
    build(parser.parse_args().output_dir)
