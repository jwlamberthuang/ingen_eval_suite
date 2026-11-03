# Release and final deliverables

The repository is organized as one evaluation suite. Existing baseline reports,
reviewed datasets, metric implementations, and experiment records are available
from the [documentation index](README.md). The six-page LaTeX technical report is available in [PDF](technical_report.pdf), [LaTeX](reports/technical_report.tex), [Word](reports/technical_report.docx), and [Markdown](reports/technical_report.md).

## Technical report

- [x] Consolidate recorded evidence without new inference or threshold fitting.
- [x] Provide means, population SDs, defined/eligible/N/A/error counts and subgroup tables.
- [x] Quantify inspected failure categories and distinguish probes, extraction and model behavior.
- [x] Prepare a seven-section [Markdown report](reports/technical_report.md) with a 150–200-word abstract and three recommendations.
- [x] Review the scientific claims, examples, subgroup interpretation, and recommendations (findings accepted 2 November 2026).
- [x] Produce and visually verify the seven-page Word companion; [Word validation](../validation/technical_report.json) records the checks.
- [x] Revise the LaTeX source with AMS typography and continuous page flow; [source validation](../validation/technical_report_latex.json) records compilation and the six-page layout check.
- [x] Export and visually verify all six pages of the revised LaTeX PDF, including numeric, font and metadata checks.
- [x] Provide the PDF at `docs/technical_report.pdf` and link its editable source; commit/push remain separate approval steps.

## Presentation and reflections

- [x] Prepare exactly ten capstone slides with findings as titles and the repository URL on the final slide; retain [editable PowerPoint](presentation/capstone.pptx) and [PDF](presentation/W04_Capstone_Deck.pdf).
- [x] Draft and visually verify the [one-page retrospective](reflections/W04_Retrospective.docx), incorporating the intern's actual learning and career notes.
- [x] Complete intern review of the retrospective and presentation wording (review reported 3 November 2026); release approval remains separate.
- [x] Complete the separate 300–500-word [final methodological log](reflections/phase_04.md).
- [x] Prepare a timed 30-minute presentation and 15-minute repository demonstration sequence.
- [ ] Rehearse the readout and demo against the reviewed release candidate.

## Repository release

- [x] Replace week-based navigation with project documentation, data, methods and experiment entry points.
- [x] Preserve historical source/config identities through a self-contained verified migration.
- [x] Install the full pinned requirements into a new isolated environment and audit the public candidate checkout; see the [candidate audit](../validation/release_candidate.json).
- [x] Pass current and historical tests, four dataset validations, exact rebuild/replay checks, and both notebooks in that environment.
- [x] Record the layout migration test, dataset-validation, replay and notebook checks in [validation](../validation/layout_validation.json).
- [x] Verify the prepared report/deck consistency, public references, metadata and fonts; repeat after any substantive revisions.
- [x] Prepare [release notes](release_notes.md) and audit the public candidate files.
- [ ] Obtain approval immediately before committing and pushing the prepared release.
- [ ] Publish `ingen_eval_v1.0` and the GitHub release with the report/deck PDFs.
- [ ] Verify a fresh clone of the actual published tag.

Final mentor review, meeting arrangements, and the signed evaluation rubric are
external completion steps. No scores, signatures, appointment, or approval are
assumed. Original calendar dates are not used as current deadlines.
