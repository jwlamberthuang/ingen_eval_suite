# Editable document sources

[Framework](evaluation_framework.json), [dialogue specification](dialogue_specification.json),
and [RAG results](rag_baseline.json) are the tracked sources for their Word copies.

```sh
.venv/bin/python scripts/documents/build_docx.py docs/sources/evaluation_framework.json docs/methodology/evaluation_framework.docx
.venv/bin/python scripts/documents/build_docx.py docs/sources/dialogue_specification.json docs/datasets/dialogue_specification.docx
.venv/bin/python scripts/documents/build_week2_report.py
```

The [protocol builder](../../scripts/documents/build_week3_protocol.py),
[pilot/additions builder](../../scripts/documents/build_week3_pilot.py), and
[amendment builder](../../scripts/documents/build_week3_context_review.py) use
tracked specifications and datasets. Review build options before use; never
replace reviewed content with a regeneration without inspecting the difference.
Word formatting requires Times New Roman for Latin text and Songti SC for Chinese.

## Consolidated technical report

The [reviewed Markdown](../reports/technical_report.md) supplies the findings and
all five tables for the [Word companion](../reports/technical_report.docx) and
[standalone LaTeX article](../reports/technical_report.tex). The current six-page [PDF](../technical_report.pdf) is compiled from LaTeX. Tables retain the saved
[evidence](../reports/evidence/summary.json); LaTeX expands the metric definitions
into numbered equations without changing the scoring rules or results.

```sh
.venv/bin/python scripts/documents/build_technical_report.py
.venv/bin/python scripts/documents/build_latex_report.py
mkdir -p build/latex
xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error -output-directory=build/latex docs/reports/technical_report.tex
xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error -output-directory=build/latex docs/reports/technical_report.tex
```

Both builders refuse an existing output unless `--overwrite` is supplied. Inspect
and reconcile direct Word or LaTeX edits before regenerating from Markdown. The
LaTeX file embeds its tables and bibliography and can also be compiled directly,
without Python or additional project files. Use XeLaTeX with the AMS, fontspec,
geometry, booktabs, tabularx, xcolor and hyperref packages.

The current LaTeX source uses the standard AMS article type size and
Computer Modern-style typography: Latin Modern for Unicode prose and Computer
Modern/AMS for mathematics. Sections flow continuously, with ordinary table
floats, a full contents list and conventional one-inch margins. Chinese quotations
use Songti SC where available and Fandol Song otherwise. The Word companion
retains Times New Roman and Songti SC.

The current source and exported PDF pass compilation, numeric/text checks and
visual review of all six pages. The PDF embeds Latin Modern, Computer Modern/AMS
and Songti SC fonts. The [LaTeX validation](../../validation/technical_report_latex.json)
records source/output hashes and inspection results. After future edits, compile
twice, inspect every page, replace `docs/technical_report.pdf` with the verified
output and refresh validation. Font fallback can alter pagination; retain a
readable 5–7-page report with complete Chinese text and embedded fonts.

The AMS article has a linked contents list, numbered definitions/equations,
scientific tables, cross-references and an embedded bibliography. Public HTTPS
references remain clickable; repository paths are printed as source locators.
