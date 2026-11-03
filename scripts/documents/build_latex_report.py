"""Typeset the reviewed report as a self-contained AMS article.

The emitted .tex embeds its bibliography and tables. Build it with XeLaTeX twice;
all auxiliary outputs belong in an ignored build directory. Dataset contents,
recorded computations, the Word report, and the Markdown text remain unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'docs/reports/technical_report.md'
TARGET = ROOT / 'docs/reports/technical_report.tex'
CITES = {'1':'suite','2':'qwen','3':'e5','4':'ragas','5':'mlx'}
LABELS = {1:'rag',2:'structured',3:'subgroups',4:'failures',5:'artifacts'}
TABLE_LEADS = {
    1:r'\autoref{tab:rag} reports the new held-out RAG measurements.',
    2:r'\autoref{tab:structured} summarizes structured-task success and metric coverage.',
    3:r'\autoref{tab:subgroups} gives the domain, difficulty and language breakdowns.',
    5:r'\autoref{tab:artifacts} indexes the retained evidence and reproducibility artifacts.',
}

PREAMBLE = r'''% !TeX program = xelatex
% Self-contained AMS article: bibliography, mathematical definitions and tables.
% Compile twice to resolve the contents, citations and cross-references.
\documentclass{amsart}
\usepackage{amssymb}
\usepackage[letterpaper,margin=1in,heightrounded]{geometry}
\usepackage{fontspec}
% Keep the class's standard Computer Modern-style text and mathematics.
% fontspec is needed only for the Chinese quotation font.
\IfFontExistsTF{Songti SC}{\newfontfamily\songti{Songti SC}}
  {\newfontfamily\songti{FandolSong-Regular.otf}}
\newcommand{\zh}[1]{{\songti\XeTeXlinebreaklocale "zh"\relax #1}}
\usepackage{booktabs,tabularx,array}
\usepackage[dvipsnames]{xcolor}
\usepackage{url}
\usepackage[unicode,bookmarksnumbered=true,colorlinks=true,
  linkcolor=blue,citecolor=blue,urlcolor=blue]{hyperref}
\hypersetup{pdftitle={Technical evaluation of bilingual dialogue and structured reasoning},
  pdfauthor={},pdfsubject={Bilingual dialogue and structured reasoning evaluation}}
\newtheorem{thm}{Theorem}[section]
\theoremstyle{definition}
\newtheorem{defn}{Definition}[section]
\newtheorem{exmp}{Example}[section]
\newtheorem{rem}{Remark}[section]
% Independent environment names preserve correct autoref labels while sharing
% the sequence of statements and equations, as in an AMS REU article.
\makeatletter
\let\c@defn\c@thm
\let\c@exmp\c@thm
\let\c@rem\c@thm
\let\c@equation\c@thm
\numberwithin{equation}{section}
\makeatother
\newcommand{\defnautorefname}{Definition}
\newcommand{\exmpautorefname}{Example}
\newcommand{\remautorefname}{Remark}
\let\fullref\autoref
\newcommand{\scorecell}[3]{\shortstack{$#1\pm#2$\\[-1pt]{\scriptsize #3}}}
\newcommand{\NAAA}{\textnormal{N/A}}
\setlength{\emergencystretch}{1.5em}
\title[Bilingual dialogue and structured reasoning evaluation]
  {Technical evaluation of bilingual dialogue and structured reasoning}
\date{2 November 2026}
\begin{document}
\raggedbottom
'''

FORMAL = r'''\subsection{Formal metric specifications}
\begin{defn}[Reference context recall]\label{def:recall}
Let $F$ be the required-fact inventory, let $C$ denote the supplied context,
and let $S(f,C)\in\{0,1\}$ indicate reviewed support for $f$. For $F\ne\varnothing$,
\begin{equation}\label{eq:recall}
  \mathrm{CR}(F,C)=\frac{1}{|F|}\sum_{f\in F}S(f,C).
\end{equation}
An empty $F$ is \NAAA. The approved annotation revision changes 17 inventories
after inspection without changing model inputs or other metrics; it is a
post-inspection diagnostic, not fresh held-out evidence.
\end{defn}
\begin{defn}[Faithfulness proxy]\label{def:faithfulness}
Let $A$ be the inspected atomic claims and $C_{\rm seg}$ the segmented evidence.
Let $E_q$ and $E_p$ use the E5 query and passage prefixes. For nonempty $A$ and
$C_{\rm seg}$, define
\begin{equation}\label{eq:faithfulness}
 \widehat{\mathrm{Faith}}(A,C)=\frac{1}{|A|}\sum_{a\in A}
 \mathbf{1}\!\left\{\max_{c\in C_{\rm seg}}
 \cos\bigl(E_q(a),E_p(c)\bigr)\geq0.80\right\}.
\end{equation}
Empty evidence gives zero claim credit. Appropriate claim-free responses are
\NAAA. This approximation to factual support~\cite{ragas} does not prove entailment.
\end{defn}
\begin{defn}[Semantic relevance]\label{def:relevance}
For query $q$ and response $r$ with valid nonzero embeddings,
\begin{equation}\label{eq:relevance}
 \mathrm{SR}(q,r)=
 \frac{\langle E_q(q),E_q(r)\rangle}
 {\|E_q(q)\|_2\,\|E_q(r)\|_2}\in[-1,1].
\end{equation}
Invalid vectors and over-limit inputs are scorer errors. Lexical reference
recall is supplementary and wording-sensitive.
\end{defn}
Spatial accuracy indicates an exact relation match. Temporal pair accuracy is
correct/requested pairs; coherence multiplies it by binary consistency against
contradictions or cycles. Entity recall and class accuracy divide correct
identities and correctly classified identities by the gold count; precision
divides matches by predictions. Goal coverage is $M/G$ and precision $M/P$ for
maximum one-to-one matches $M$, gold goals $G$ and predictions $P$, with
precedence constraints and frozen aliases.

Means and population standard deviations use defined values ($\mathrm{ddof}=0$).
\NAAA\ and errors retain counts. Malformed structured outputs have null core
metrics and task success zero; valid empty inventories follow explicit denominator
rules. Exact success and parse coverage accompany conditional means. No composite
score combines capabilities. Saved-vector replay verifies recorded computations
independently of fresh inference.
'''

BIBLIOGRAPHY = r'''\begin{thebibliography}{9}
\bibitem{suite} \emph{ingen\_eval\_suite}.
\href{https://github.com/jwlamberthuang/ingen_eval_suite}{Public evaluation repository}.
The repository-relative paths in \autoref{tab:artifacts} identify the retained evidence.
\bibitem{qwen} Qwen team, \href{https://huggingface.co/Qwen/Qwen2.5-7B-Instruct}
{Qwen2.5 7B Instruct model card}; MLX Community,
\href{https://huggingface.co/mlx-community/Qwen2.5-7B-Instruct-4bit}{four-bit conversion}.
The study evaluates the pinned conversion, not all parent-model configurations.
\bibitem{e5} intfloat, \href{https://huggingface.co/intfloat/multilingual-e5-base}
{Multilingual E5 base model card}. Embedding prefixes, pooling, token limits and interpretation.
\bibitem{ragas} Ragas, \href{https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_recall/}
{context recall} and \href{https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/}
{faithfulness}. Claim-support definitions provide methodological context; the
suite's cosine proxy is a distinct implementation.
\bibitem{mlx} MLX team, \href{https://github.com/ml-explore/mlx-lm}{MLX LM}.
Runtime for the recorded quantized inference.
\end{thebibliography}
'''


def escape(text):
    mapping = {'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$',
               '#':r'\#','_':r'\_','{':r'\{','}':r'\}',
               '~':r'\textasciitilde{}','^':r'\textasciicircum{}',
               '±':r'\(\pm\)','≥':r'\(\geq\)'}
    return ''.join(mapping.get(c,c) for c in text)


def inline(text):
    pattern = r'(\*\*.*?\*\*|`[^`]+`|\[[^\]]+\]\([^\s)]+\)|\[[1-5](?:,\s*[1-5])*\]|[\u3400-\u9fff][\u3400-\u9fff，。！？、：；]*)'
    result=[]
    for token in re.split(pattern,text):
        if not token:continue
        if token.startswith('**'):
            result.append(r'\textbf{'+inline(token[2:-2])+'}')
        elif token.startswith('`'):
            code=token[1:-1]
            if re.fullmatch(r'[0-9a-f]{40,64}',code):
                result.append(r'\allowbreak'.join(r'\mbox{'+code[i:i+8]+'}' for i in range(0,len(code),8)))
            else:
                result.append(r'\ '.join(r'\nolinkurl{'+part+'}' for part in code.split()))
        elif re.fullmatch(r'\[[1-5](?:,\s*[1-5])*\]',token):
            result.append(r'\cite{'+','.join(CITES[x.strip()] for x in token[1:-1].split(','))+'}')
        elif token.startswith('[') and re.fullmatch(r'\[([^\]]+)\]\(([^\s)]+)\)',token):
            label,target=re.fullmatch(r'\[([^\]]+)\]\(([^\s)]+)\)',token).groups()
            result.append(r'\href{'+target+'}{'+escape(label)+'}' if target.startswith('https://') else escape(label))
        elif re.match(r'^[\u3400-\u9fff]',token):
            result.append(r'\zh{'+token+'}')
        else:
            result.append(escape(token))
    value=''.join(result)
    value=re.sub(r'\bTable ([1-5])\b',lambda m:r'\autoref{tab:'+LABELS[int(m[1])]+'}',value)
    return value


def table(rows,number,caption):
    header,data=rows[0],rows[2:]
    specs={1:r'@{}>{\raggedright\arraybackslash}Xrrccc@{}',2:r'@{}p{.12\linewidth}c>{\raggedright\arraybackslash}p{.20\linewidth}X@{}',
           3:r'@{}p{.18\linewidth}*{3}{>{\centering\arraybackslash}X}@{}',
           4:r'@{}Xcc@{}',5:r'@{}>{\raggedright\arraybackslash}p{.33\linewidth}X@{}'}
    out=([TABLE_LEADS[number],''] if number in TABLE_LEADS else [])+[
         r'\begin{table}[htbp]',r'\centering\small',
         r'\renewcommand{\arraystretch}{1.28}' if number==3 else '',
         r'\caption{'+inline(caption)+'}',
         r'\label{tab:'+LABELS[number]+'}',r'\begin{tabularx}{\linewidth}{'+specs[number]+'}',r'\toprule']
    if number==1:header=['Measurement','Mean','SD',r'Defined / eligible','N/A','Errors']
    if number==2:header=['Task','Valid / eligible','Exact success: n/N; mean $\\pm$ SD','Core mean $\\pm$ population SD (defined count)']
    # Header labels use math for pm, while prose labels stay in text mode.
    h=[]
    for s in header:
        if number==2:s=s.replace('$\\pm$','±')
        h.append(r'\textbf{'+inline(s)+'}')
    out += [' & '.join(h)+r' \\',r'\midrule']
    for row in data:
        cells=[]
        for col,value in enumerate(row):
            if number==3 and col>0:
                match=re.fullmatch(r'([0-9.]+) ± ([0-9.]+); (\d+/\d+)',value)
                if not match:raise ValueError('Invalid subgroup cell')
                cells.append(r'\scorecell{'+match[1]+'}{'+match[2]+'}{'+match[3]+'}')
            elif number==2 and col==2:
                count,metric=value.split('; ')
                cells.append(r'\shortstack{'+escape(count)+r'\\'+inline(metric)+'}')
            else:cells.append(inline(value))
        out.append(' & '.join(cells)+r' \\')
    out += [r'\bottomrule',r'\end{tabularx}',r'\end{table}']
    return '\n'.join(out)


def build(source=SOURCE,target=TARGET,overwrite=False):
    source,target=Path(source).resolve(),Path(target).resolve()
    if not source.is_relative_to(ROOT) or not target.is_relative_to(ROOT):
        raise ValueError('Report sources and outputs must stay within the repository')
    text=Path(source).read_text()
    abstract=text.split('## Abstract\n',1)[1].split('\n## Introduction',1)[0].strip()
    if not 150<=len(abstract.split())<=200:raise ValueError('Abstract length differs from the report contract')
    if Path(target).exists() and not overwrite:raise FileExistsError('Inspect direct edits before using --overwrite')
    body=text.split('## Introduction\n',1)[1]
    body='## Introduction\n'+body
    # The bibliography is embedded and generated from the same reviewed references.
    ref_start=body.index('[1] ingen_eval_suite.')
    ref_end=body.index('### Artifact and source identities',ref_start)
    body=body[:ref_start]+body[ref_end:]
    body=body.replace('### Public methodological references\n\n','')
    formal_start=body.index('### Formal metric specifications')
    formal_end=body.index('<!-- pagebreak -->',formal_start)
    body=body[:formal_start]+'LATEX_FORMAL_BLOCK\n\n'+body[formal_end:]
    lines=body.splitlines();out=[PREAMBLE,r'\begin{abstract}',inline(' '.join(abstract.split())),
          r'\end{abstract}',r'\maketitle',r'\tableofcontents','']
    paragraph=[];index=0;number=0;caption=''
    def flush():
        if paragraph:out.append(inline(' '.join(paragraph))+'\n');paragraph.clear()
    while index<len(lines):
        line=lines[index].strip()
        if not line:flush();index+=1;continue
        if line=='<!-- pagebreak -->':flush();index+=1;continue
        if line=='LATEX_FORMAL_BLOCK':flush();out.append(FORMAL);index+=1;continue
        if line.startswith('## '):
            flush();heading=line[3:]
            if heading=='References and reproducibility':
                out.append(r'\section{Reproducibility}\label{sec:reproducibility}')
            else:
                out.append(r'\section{'+escape(heading)+'}'+r'\label{sec:'+heading.lower().replace(' ','-')+'}')
            index+=1;continue
        if line.startswith('### '):
            flush();out.append(r'\subsection{'+escape(line[4:])+'}')
            index+=1;continue
        if line.startswith('Table '):
            flush();caption=re.sub(r'^Table \d+\. ','',line);index+=1;continue
        if line.startswith('| '):
            flush();rows=[]
            while index<len(lines) and lines[index].strip().startswith('| '):
                rows.append([c.strip() for c in lines[index].strip().strip('|').split('|')]);index+=1
            number+=1;out.append(table(rows,number,caption));continue
        if re.match(r'^\d\. ',line):
            flush();out.append(r'\begin{enumerate}')
            while index<len(lines) and re.match(r'^\d\. ',lines[index].strip()):
                item=[re.sub(r'^\d\. ','',lines[index].strip())];index+=1
                while index<len(lines) and lines[index].strip() and not re.match(r'^\d\. ',lines[index].strip()):
                    item.append(lines[index].strip());index+=1
                out.append(r'\item '+inline(' '.join(item)))
            out.append(r'\end{enumerate}');continue
        if line.startswith('The Chinese case '):
            flush();value=[line];index+=1
            while index<len(lines) and lines[index].strip() and lines[index].strip()!='<!-- pagebreak -->':
                value.append(lines[index].strip());index+=1
            out.append(r'\begin{exmp}[Entity binding in a Chinese response]\label{ex:identity}'+'\n'+inline(' '.join(value))+'\n'+r'\end{exmp}')
            continue
        paragraph.append(line);index+=1
    flush();out += [BIBLIOGRAPHY,r'\end{document}','']
    if number!=5:raise ValueError('Expected five scientific tables')
    value='\n'.join(out)
    value=value.replace('The generation revision is ', 'Generator revision: ')
    value=value.replace('; the embedding revision is ', '; embedding revision: ')
    Path(target).write_text(value)
    print(json.dumps({'source':str(Path(source).relative_to(ROOT)),'latex':str(Path(target).relative_to(ROOT)),
          'source_sha256':hashlib.sha256(text.encode()).hexdigest(),'abstract_words':len(abstract.split()),'tables':number},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=SOURCE)
    parser.add_argument('--output',type=Path,default=TARGET)
    parser.add_argument('--overwrite',action='store_true')
    args=parser.parse_args();build(args.source,args.output,args.overwrite)
