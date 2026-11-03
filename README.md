# ingen_eval_suite

A reproducible English/Chinese evaluation suite for grounded companion and
educational dialogue, spatial/temporal reasoning, entity recognition, and
explicit-goal planning. It includes reviewed datasets, tested metrics, controlled
model inputs, recorded public-model baselines, and offline score replay.

The experiments use Qwen2.5-7B-Instruct and multilingual-e5-base as public task
proxies. They do not establish performance of internal InGen models or physical
robots. Results retain malformed outputs, inspected claim corrections, and known
limits of embedding-based support judgments.

## Start here

| Goal | Entry point |
| --- | --- |
| Read the technical evaluation report | [PDF](docs/technical_report.pdf) · [LaTeX](docs/reports/technical_report.tex) · [Word](docs/reports/technical_report.docx) · [Markdown](docs/reports/technical_report.md) |
| Review the capstone presentation | [PDF](docs/presentation/W04_Capstone_Deck.pdf) · [Editable PowerPoint](docs/presentation/capstone.pptx) · [Slide guide](docs/presentation/README.md) |
| Read the retrospective and methodological logs | [Reflections](docs/reflections/README.md) |
| Review methods and public sources | [Documentation index](docs/README.md) |
| Inspect the 100- and 200-case datasets | [Dataset guide](data/README.md) |
| Explore recorded model behavior | [Executed notebooks](notebooks/README.md) |
| Inspect results, reviews, and manifests | [Experiment results](results/README.md) |
| Install, test, and replay | [Reproduction guide](docs/reproducibility.md) |
| Prepare a new experiment | [Experiment workflow](docs/methodology/experiment_pipeline.md) |
| Review release readiness | [Release notes](docs/release_notes.md) · [Release checklist](docs/release_checklist.md) |

## Current findings

The primary extended experiment evaluates **80 new held-out cases**, comprising
44 RAG and 36 structured tasks. Twenty new calibration cases and 100 previously
evaluated cases remain separate. This is one model baseline, not a model ranking.

| New held-out measurement | Result | Interpretation |
| --- | ---: | --- |
| Context recall, approved annotation v2.0.1 | 0.7442; 43/44 defined | Post-inspection annotation-only diagnostic |
| Inspected-claim faithfulness proxy | 0.9050; 43/44 defined | Assisted scoring; high similarity can accept false claims |
| Semantic relevance | 0.8922; 44/44 defined | Query–response similarity, not correctness |
| Spatial exact task success | 7/8 | 8/8 valid outputs |
| Temporal exact task success | 4/4 | Small descriptive sample |
| Entity exact task success | 7/12 | 12/12 valid outputs |
| Goal-planning exact task success | 3/12 | 7/12 valid outputs; retain format failures |

All 155 raw claim proposals fail the strict object contract. Separate inspected
corrections support the assisted diagnostic; they do not repair model answers.
All ten deliberately flawed fixed probes receive proxy faithfulness 1.0. These
probes are distinct from generated responses. Read the
[extended results](docs/reports/extended_baseline.md) and
[evidence tables](docs/reports/evidence_tables.md) for denominators, dispersion,
subgroups, technical inspection, and limitations.

## Quick start

Use Python 3.12 from the repository root:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python scripts/evaluation/replay.py all
.venv/bin/python scripts/reporting/build_report_evidence.py --check
```

Saved-vector replay does not download models and does not require Apple GPU
inference. Fresh generation uses the recorded Apple Silicon/MLX runtime; details
and platform boundaries are in the [reproduction guide](docs/reproducibility.md).

## Repository structure

```text
configs/          Dataset policies and experiment configurations
schemas/          Versioned dialogue, extended-task, and amendment contracts
data/             Reviewed collections, pilots, annotations, and manifests
src/              Core metrics, adapters, generation, scoring, and replay
scripts/          Dataset maintenance, experiment, document, and report tools
tests/            Manually verified metric cases and pipeline/artifact checks
notebooks/        Executed RAG and extended-evaluation demonstrations
results/          Named immutable baseline and annotation-diagnostic results
docs/             Methods, specifications, reports, reviews, and reflections
validation/       Recorded validation evidence
reproducibility/  Verified layout map and deduplicated historical source snapshot
```

The public layout is organized by purpose. Case IDs, schema identifiers, original
run names, and some internal module names retain historical phase prefixes to
preserve their identity. The [layout migration](reproducibility/README.md) maps
original paths to canonical files and preserves exact historical sources. No
recorded experiment identity, score, label, or model-visible input was resealed.

The six-page LaTeX technical report uses an AMS article layout, with a standalone
LaTeX source and compiled PDF, a Word companion, reviewed Markdown and validated
evidence tables. The intern has reviewed the ten-slide capstone presentation and
one-page retrospective; a separate final methodological log is also available.
Pre-commit installation and verification are recorded in the
[candidate audit](validation/release_candidate.json). Publication of the reviewed
commit and release tag, followed by a tagged-clone check and rehearsal, remain on the
[release checklist](docs/release_checklist.md).
