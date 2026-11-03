# Validation evidence

[Recorded RAG checks](recorded/rag/tests.json) and
[recorded extended checks](recorded/extended/tests.json) document their respective
submission versions. Paths and test counts in these immutable records describe
those versions. The [migration](../reproducibility/README.md) resolves original
artifact locations without rewriting the records.

The current layout verification is recorded in
[layout_validation.json](layout_validation.json). Re-run the commands in the
[reproduction guide](../docs/reproducibility.md) when preparing a new release;
an earlier passing record does not establish that later edits pass.

The final pre-commit [release-candidate audit](release_candidate.json) records
fresh dependency installation, candidate checks, dataset rebuilds, replay,
notebook execution and public-file boundaries. It supersedes the older layout
audit's pending report/presentation items. It distinguishes candidate verification
from the tagged-clone check that can only follow publication.

## Technical report

[Word validation](technical_report.json) covers the seven-page companion and
reviewed Markdown source. [LaTeX validation](technical_report_latex.json) covers
the current six-page source and exported PDF: compilation, preserved scientific
content, numeric parity, Chinese text, embedded fonts, public links, metadata and
visual inspection of all six pages. Markdown findings and the Word companion
remain unchanged.
