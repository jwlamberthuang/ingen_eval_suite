# ingen_eval_v1.0 release notes

Status: release candidate. Commit, push, tag creation and GitHub release
publication are pending approval.

## Included in this release

- A reviewed 200-case English/Chinese collection, preserving the original
  100-case dialogue dataset and both pilots. The additions have a separate
  20-case calibration and 80-case held-out partition.
- Implemented RAG metrics and text-task evaluations for the assigned STUM,
  SEOM and HTD-IRL capabilities, with explicit output contracts, undefined-value
  handling, and manually verified metric examples.
- A recorded Qwen2.5-7B-Instruct baseline with multilingual-e5-base embeddings,
  retained raw responses, separate claim inspections, fixed scorer probes, and
  an approved context-recall annotation diagnostic.
- A topic-oriented repository with verified historical source restoration and
  exact offline replay. Relocation preserves original experiment identities.
- A six-page [technical report PDF](technical_report.pdf), with
  [LaTeX](reports/technical_report.tex), [Word](reports/technical_report.docx),
  [Markdown](reports/technical_report.md), and reproducible evidence tables.
- A ten-slide [capstone PDF](presentation/W04_Capstone_Deck.pdf) and
  [editable PowerPoint](presentation/capstone.pptx), a one-page
  [retrospective](reflections/W04_Retrospective.docx), and the
  [final methodological log](reflections/phase_04.md).

## Release verification

The [candidate audit](../validation/release_candidate.json) records the exact
scope and results. Verification uses a newly created Python 3.12.14 environment
with the full pinned requirements on macOS arm64. It covers the current 357-test
suite, the preserved 336-test historical suite, all four dataset/pilot
validations, exact dataset rebuilds, saved-score replay, evidence freshness, and
execution of all 11 RAG and 12 extended-notebook code cells.

Both notebook commands now bind the kernel to the invoking interpreter and
capture figures inline. This prevents a global default Python installation from
silently supplying a different dependency environment. The change preserves
the recorded model inputs, raw outputs, labels, thresholds and scores.

The public-file audit checks repository references, document metadata and nested
packages, including the historical source archive. Office lock files, build
outputs, caches and environments are excluded. PDF and PowerPoint files are
explicitly binary in Git attributes.

## Interpretation and compatibility

The suite evaluates public-model text proxies. It does not establish performance
of internal InGen models, physical robots or audio systems. It provides one
baseline rather than a model ranking.

Faithfulness remains an embedding-based support approximation using inspected
claims. All ten flawed fixed probes receive 1.0, so high scores cannot establish
factual support. Planning results retain malformed outputs in exact task
success, alongside conditional core metrics. The recall amendment is a
post-inspection annotation diagnostic rather than a new independent experiment.

Saved-artifact replay requires no model downloads or fresh inference. New MLX
generation uses the documented macOS/arm64 runtime and model caches. This audit
does not establish installation on other operating systems or identical fresh
generations across hardware.

## Publication gate

The pre-commit audit tests the candidate files with fresh dependencies. The
published tag cannot be cloned until publication. After approval, publish the
reviewed commit and `ingen_eval_v1.0`, then verify a new clone of that tag and
attach the report and deck PDFs to the GitHub release. The
[release checklist](release_checklist.md) keeps these publication steps separate
from rehearsal, the final mentor readout and the signed rubric.
