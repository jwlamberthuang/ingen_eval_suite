"""Build the formal report from its reviewed Markdown and numeric evidence.

Uses the same Word font and table helpers as the other suite deliverables.
PDF export/rendering is a separate document-conversion step. No model runs,
scoring changes or dataset mutation are performed by this builder.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

from build_docx import add_table, inline, normalize_fonts, set_font
from set_bilingual_fonts import apply_bilingual_fonts

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'docs/reports/technical_report.md'
TARGET = ROOT / 'docs/reports/technical_report.docx'


def source_contract(text):
    required = ['Abstract', 'Introduction', 'Methodology', 'Results', 'Error analysis', 'Discussion', 'Conclusion']
    headings = re.findall(r'^## (.+)$', text, re.MULTILINE)
    if not all(h in headings for h in required):
        raise ValueError('Report is missing a required section')
    abstract = text.split('## Abstract\n', 1)[1].split('\n## Introduction', 1)[0]
    if not 150 <= len(abstract.split()) <= 200:
        raise ValueError('Abstract must contain 150–200 words')
    if text.count('<!-- pagebreak -->') != 6:
        raise ValueError('Report source must define seven pages')
    discussion = text.split('## Discussion', 1)[1].split('## Conclusion', 1)[0]
    if len(re.findall(r'^\d\. ', discussion, re.MULTILINE)) != 3:
        raise ValueError('Discussion must contain three recommendations')
    evidence = json.loads((ROOT / 'docs/reports/evidence/summary.json').read_text())
    # Subgroup and overall rows must show exactly the retained mean/SD/counts.
    for row in evidence['tables']:
        if (row['experiment'], row['annotation'], row['cohort'], row['evaluation_type']) != (
                'extended_baseline', 'context_recall_v2.0.1', 'new_held_out', 'rag'):
            continue
        if row['dimension'] == 'overall' or row['metric'] not in {'context_recall', 'faithfulness_proxy', 'semantic_relevance'}:
            continue
        token = f"{row['mean']:.4f} ± {row['population_sd']:.4f}; {row['n_defined']}/{row['n_eligible']}"
        if token not in text:
            raise ValueError('Report subgroup table differs from retained evidence')
    return {'abstract_words': len(abstract.split()), 'required_sections': required,
            'source_sha256': hashlib.sha256(text.encode()).hexdigest(),
            'evidence_sha256': hashlib.sha256((ROOT / 'docs/reports/evidence/summary.json').read_bytes()).hexdigest()}


def portable_inline(paragraph, text):
    """Keep public HTTPS links; cite repository artifacts without file URLs.

    This prevents PDF export from resolving relative links to workstation paths.
    The report's reference table provides repository-relative artifact locators.
    """
    def link(match):
        label, target = match.groups()
        if urlsplit(target).scheme == 'https':
            return match.group(0)
        if urlsplit(target).scheme:
            raise ValueError('Report accepts public HTTPS hyperlinks only')
        return label
    inline(paragraph, re.sub(r'\[([^\]]+)\]\(([^\s)]+)\)', link, text))


def build(source=SOURCE, output=TARGET, overwrite=False):
    text = Path(source).read_text()
    contract = source_contract(text)
    if Path(output).exists() and not overwrite:
        raise FileExistsError('Report exists; inspect edits before using --overwrite')
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin, section.bottom_margin = Inches(.67), Inches(.67)
    section.left_margin, section.right_margin = Inches(.8), Inches(.8)
    section.footer_distance = Inches(.28)
    styles = doc.styles
    for name, size, bold in [('Normal',12,False),('Title',22,True),('Subtitle',10.5,False),
                              ('Heading 1',14,True),('Heading 2',12,True),('Caption',10.5,False)]:
        set_font(styles[name],size,bold)
        style=styles[name]
        style.paragraph_format.line_spacing=1.04
        style.paragraph_format.space_after=Pt(6)
        style.paragraph_format.space_before=Pt(8 if name.startswith('Heading') else 0)
        if name.startswith('Heading') or name in {'Title','Caption'}:
            style.paragraph_format.keep_with_next=True
        props=style._element.get_or_add_pPr()
        for border in list(props.findall(qn('w:pBdr'))):props.remove(border)
    styles['Title'].paragraph_format.space_after=Pt(8)
    styles['Subtitle'].paragraph_format.space_after=Pt(10)
    styles['Caption'].paragraph_format.space_after=Pt(4)
    styles['Normal'].paragraph_format.widow_control=True
    footer=section.footer.paragraphs[0]
    footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    footer.add_run('Page ').font.size=Pt(9.5)
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
    footer.add_run(' of ').font.size=Pt(9.5)
    total=OxmlElement('w:fldSimple');total.set(qn('w:instr'),'NUMPAGES');footer._p.append(total)
    doc.core_properties.title='Technical evaluation of bilingual dialogue and structured reasoning'
    doc.core_properties.subject='Reproducible bilingual dialogue and structured reasoning evaluation'
    doc.core_properties.author=''
    doc.core_properties.last_modified_by=''
    doc.core_properties.version='1.0'
    doc.core_properties.created=datetime(2026,11,2,12,0,tzinfo=timezone.utc)
    doc.core_properties.modified=datetime(2026,11,2,12,0,tzinfo=timezone.utc)
    doc.core_properties.comments='source-sha256:'+contract['source_sha256']+'; evidence-sha256:'+contract['evidence_sha256']
    paragraph=[];lines=text.splitlines();index=0;table_number=0;pending_page=False
    def flush():
        if paragraph:
            p=doc.add_paragraph()
            portable_inline(p,' '.join(paragraph));paragraph.clear()
    while index<len(lines):
        line=lines[index]
        if not line.strip():flush();index+=1;continue
        if line=='<!-- pagebreak -->':
            flush();pending_page=True;index+=1;continue
        if line.startswith(('# ', '## ', '### ')):
            flush()
            prefix, label = line.split(' ', 1)
            style = {'#':'Title', '##':'Heading 1', '###':'Heading 2'}[prefix]
            p=doc.add_paragraph(style=style)
            if pending_page:
                p.paragraph_format.page_break_before=True
                pending_page=False
            portable_inline(p,label);index+=1;continue
        if line.startswith('ingen_eval_suite |'):
            flush();p=doc.add_paragraph(style='Subtitle');portable_inline(p,line);index+=1;continue
        if line.startswith('Table '):
            flush();p=doc.add_paragraph(style='Caption');portable_inline(p,line);index+=1;continue
        if line.startswith('| '):
            flush();raw=[]
            while index<len(lines) and lines[index].startswith('| '):
                raw.append([c.strip() for c in lines[index].strip().strip('|').split('|')]);index+=1
            headers,rows=raw[0],raw[2:];table_number+=1
            widths={1:[2.42,.77,.92,1.29,.65,.85],2:[.85,.95,1.70,3.40],
                    3:[1.25,1.88,1.88,1.89],4:[4.30,1.30,1.30],5:[2.48,4.42]}[table_number]
            if table_number==2:
                rows=[[r[0],r[1],r[2].replace("; ","\n"),r[3]] for r in rows]
            if table_number==3:
                rows=[[r[0],*[v.replace('; ','\n') for v in r[1:]]] for r in rows]
            add_table(doc,{'headers':headers,'rows':rows,'widths':widths,'font_size':10.5,
                           'center_columns':list(range(1,len(headers))) if table_number!=5 else [],'keep_together':True})
            continue
        # Keep each numbered recommendation as one flowing paragraph.
        if re.match(r'^\d\. ',line):flush()
        paragraph.append(line.strip());index+=1
    flush()
    if table_number!=5:raise ValueError('Expected five scientific tables')
    normalize_fonts(doc)
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    doc.save(output);apply_bilingual_fonts(output)
    print(json.dumps({'word':str(Path(output).relative_to(ROOT)),**contract},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=SOURCE)
    parser.add_argument('--output',type=Path,default=TARGET)
    parser.add_argument('--overwrite',action='store_true')
    args=parser.parse_args()
    build(args.source,args.output,args.overwrite)
