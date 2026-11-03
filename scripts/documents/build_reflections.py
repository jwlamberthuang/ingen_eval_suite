"""Build the one-page retrospective from its editable Markdown source."""
import argparse
from datetime import datetime, timezone
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from set_bilingual_fonts import apply_bilingual_fonts

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'docs/reflections/retrospective.md'
TARGET = ROOT / 'docs/reflections/W04_Retrospective.docx'


def build(source=SOURCE, target=TARGET, overwrite=False):
    source, target = Path(source).resolve(), Path(target).resolve()
    if not source.is_relative_to(ROOT) or not target.is_relative_to(ROOT):
        raise ValueError('Reflection sources and outputs must stay in the repository')
    if target.exists() and not overwrite:
        raise FileExistsError('Inspect direct Word edits before using --overwrite')
    text = source.read_text()
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = section.bottom_margin = Inches(.8)
    section.left_margin = section.right_margin = Inches(.85)
    for name, size, bold in [('Normal', 12, False), ('Title', 22, True), ('Heading 1', 12, True)]:
        style = doc.styles[name]
        style.font.name, style.font.size = 'Times New Roman', Pt(size)
        style.font.bold, style.font.color.rgb = bold, RGBColor(0, 0, 0)
        fonts = style.element.get_or_add_rPr().get_or_add_rFonts()
        fonts.attrib.clear()
        fonts.set(qn('w:ascii'), 'Times New Roman')
        fonts.set(qn('w:hAnsi'), 'Times New Roman')
        fonts.set(qn('w:eastAsia'), 'Songti SC')
        style.paragraph_format.line_spacing = 1.02
        style.paragraph_format.space_after = Pt(6)
        style.paragraph_format.space_before = Pt(7 if name == 'Heading 1' else 0)
        props = style.element.get_or_add_pPr()
        for border in list(props.findall(qn('w:pBdr'))): props.remove(border)
    for block in text.strip().split('\n\n'):
        if block.startswith('# '):
            doc.add_paragraph(block[2:].strip(), style='Title')
        elif block.startswith('## '):
            doc.add_paragraph(block[3:].strip(), style='Heading 1')
        else:
            doc.add_paragraph(' '.join(block.splitlines()))
    doc.core_properties.title = 'AI evaluation retrospective'
    doc.core_properties.author = ''
    doc.core_properties.last_modified_by = ''
    doc.core_properties.created = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)
    doc.core_properties.modified = doc.core_properties.created
    doc.core_properties.comments = ''
    # Direct run fonts prevent office theme fonts overriding the requested face.
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            run.font.name = 'Times New Roman'
            fonts = run._element.get_or_add_rPr().get_or_add_rFonts()
            fonts.attrib.clear()
            for slot in ['ascii', 'hAnsi', 'cs']:
                fonts.set(qn('w:' + slot), 'Times New Roman')
            fonts.set(qn('w:eastAsia'), 'Songti SC')
    target.parent.mkdir(parents=True, exist_ok=True)
    doc.save(target)
    apply_bilingual_fonts(target)
    print(target.relative_to(ROOT))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--output', type=Path, default=TARGET)
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    build(args.source, args.output, args.overwrite)
