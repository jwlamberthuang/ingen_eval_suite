# ingen_eval_suite

A bilingual evaluation suite for grounded Fari companion dialogue and Senpai
educational dialogue. Week 1 provides a reproducible evaluation design, a
versioned annotation contract, and 100 reviewed English/Chinese cases. Week 2
adds implemented metrics, an executed notebook, a measured local baseline, and
failure analysis with replayable artifacts.

## Review by week

| Week | Review package |
| --- | --- |
| 1 | [Framework, specification, dataset, pilot, and reflection](deliverables/week-01/README.md) |
| 2 | [Metrics, executed notebook, results report, validation, and failure analysis](deliverables/week-02/README.md) |

Each weekly entry page links the canonical artifacts for review. Shared software,
datasets, and schemas remain in their documented project locations.

All 102 checks pass. The [verification summary](deliverables/week-02/validation/tests.json)
records dataset validation, metric tests, exact score replay, notebook execution,
and the Word document review.

## Week 1 deliverables

| Deliverable | Artifact |
| --- | --- |
| Evaluation framework | [Word](docs/W01_InGen_AI_Evaluation_Framework.docx) · [Markdown](docs/evaluation_framework.md) |
| Dataset specification | [Word](docs/W01_Dataset_Specification.docx) · [Markdown](docs/dataset_specification.md) |
| 100-case dataset v1 | [JSONL](data/W01_Evaluation_Dataset_v1.jsonl) · [Manifest](data/W01_Evaluation_Dataset_v1.manifest.json) |
| Methodological reflection | [Week 1 log](weekly/Wk-01-Log.md) |

The framework audits GRPO, STUM, SEOM, HTD-IRL, AMDC, and CRL-MRS. It defines
context recall, faithfulness, semantic relevance, answer coverage, domain rubrics,
model input boundaries, calibration, replay, and reporting. The primary dialogue
scope is GRPO task evaluation; later hands-on extensions cover STUM, SEOM, and
HTD-IRL. AMDC and CRL-MRS remain future work. Public product terminology and suite
capability names are documented separately in the
[source register](docs/public_sources.md).

## Dataset and current results

| Domain | Easy | Medium | Hard | Total |
| --- | ---: | ---: | ---: | ---: |
| Fari English | 16 | 16 | 8 | 40 |
| Fari Chinese | 8 | 8 | 4 | 20 |
| Senpai English | 10 | 10 | 5 | 25 |
| Senpai Chinese | 6 | 6 | 3 | 15 |
| Total | 40 | 40 | 20 | 100 |

Dataset v1 has 99 scenario families, 48 edge-tagged cases, 20 calibration cases,
and 80 held-out cases. The [twelve-case pilot](data/W01_Evaluation_Dataset_Pilot_v0.4.jsonl)
is derived from the collection and remains in calibration. Its
[manifest](data/W01_Evaluation_Dataset_Pilot_v0.4.manifest.json) identifies the
source collection hash. Related examples stay in the same subset.

I reviewed every English and Chinese case and confirmed native
authorship of all 35 Chinese cases. The reviewed dialogue is preserved verbatim;
annotation checks and review limitations are documented in
[dataset documentation](data/dataset_documentation.md).

| Check | Current state |
| --- | --- |
| Release schema, counts, and annotation relationships | Valid |
| Native Chinese authorship and language review | Recorded for all 35 Chinese cases |
| Pilot synchronization and exact dataset rebuild | Verified |
| Model generations and metric scores | 100 recorded responses; frozen scores and inspected failures in Week 2 |
| Audio evaluation | Outside the current text experiment |

The recorded local generation baseline is the four-bit MLX conversion of
Qwen2.5-7B-Instruct, with multilingual-e5-base for embedding metrics. These are
public task proxies. No result in
this repository establishes performance of an unavailable InGen model or a
physical robot.

## Setup and reproduce dataset checks

Use Python 3.12 and run from the repository root:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/datasets/validate_dataset.py data/W01_Evaluation_Dataset_v1.jsonl --profile release --manifest data/W01_Evaluation_Dataset_v1.manifest.json
.venv/bin/python scripts/datasets/validate_dataset.py data/W01_Evaluation_Dataset_Pilot_v0.4.jsonl --profile pilot --manifest data/W01_Evaluation_Dataset_Pilot_v0.4.manifest.json
.venv/bin/python -m pytest -q
```

The suite tests data, maintenance tooling, core metric computations, input
boundaries, experiment hashes, the executed notebook, and exact score replay.
The metric/input module contains 41 tests, including at least three hand-computed
examples per core metric. The `release` profile requires approved annotations,
assigned subsets, and native Chinese author/review records. Validation cannot
establish truth or actual authorship by itself.

Reproduce both JSONL files and manifests in a fresh output directory:

```sh
.venv/bin/python scripts/datasets/build_dataset.py --output-dir build/reproduced
```

The authoritative JSONL is copied byte for byte. The pilot is selected from it
using [dataset_config.json](dataset_config.json). Existing output files are never
overwritten by a preview build.

After intentional master edits, refresh the derived pilot and manifests with:

```sh
.venv/bin/python scripts/datasets/build_dataset.py --refresh
```

Refresh preserves the master and refuses to discard direct pilot edits. A changed
source hash invalidates the recorded release/review match; building grants no
renewed approval. Version and review metadata must be updated only after the
revised content is accepted.

## Maintained tooling

| File | Purpose |
| --- | --- |
| [Schema](schemas/w01_dialogue_case.schema.json) | Record contract 1.1.0 |
| [build_dataset.py](scripts/datasets/build_dataset.py) | Validate master and derive pilot/manifests |
| [update_dataset.py](scripts/datasets/update_dataset.py) | Guarded content edits to a separate preview |
| [validate_dataset.py](scripts/datasets/validate_dataset.py) | Structure, evidence, family, coverage, release, and hash checks |
| [dataset_io.py](scripts/datasets/dataset_io.py) | Serialization and manifest support |
| [Validation tests](tests/test_dataset_validation.py) | Known contract acceptance/rejection cases |
| [Workflow tests](tests/test_dataset_workflow.py) | Edit protection, synchronization, rebuild, and release safeguards |
| [Publication tests](tests/test_public_artifacts.py) | Public document links and publication boundary |
| [build_docx.py](scripts/documents/build_docx.py) | Word deliverables from tracked document sources |
| [set_bilingual_fonts.py](scripts/documents/set_bilingual_fonts.py) | Times New Roman for English; Songti SC for Chinese |
| [requirements.txt](requirements.txt) | Complete Week 1 and Week 2 setup |
| [requirements-validation.txt](requirements-validation.txt) | Pinned validation/test packages |
| [requirements-documents.txt](requirements-documents.txt) | Pinned Word tooling packages |
| [.gitignore](.gitignore) | Environments, caches, reports, and scratch outputs |

The updater accepts a JSON object with `base_dataset_sha256` and an `edits` array.
Each edit names a case `id` and `changes` containing `path`, `before`, and `after`.
For example, a query edit uses `/query`. It rejects stale hashes/values, duplicate
edits, unknown cases, and attempts to change identity, split, or approval. Changed
cases require renewed review, including renewed Chinese author confirmation when
Chinese content changes. Promote an inspected preview only as a reviewed revision.

Editable Word sources are tracked alongside the methods:

- [Framework source](docs/sources/W01_InGen_AI_Evaluation_Framework.json)
- [Specification source](docs/sources/W01_Dataset_Specification.json)

To regenerate the Word deliverables:

```sh
.venv/bin/python scripts/documents/build_docx.py docs/sources/W01_InGen_AI_Evaluation_Framework.json docs/W01_InGen_AI_Evaluation_Framework.docx
.venv/bin/python scripts/documents/build_docx.py docs/sources/W01_Dataset_Specification.json docs/W01_Dataset_Specification.docx
```

## Week 2 results and reproduce scores

The complete fixed-context run produced 100 responses without generation errors.
Primary evaluation uses eighty held-out cases, after freezing support calibration
on the designated twenty cases.

| Core measurement | Held out mean | Population SD | Defined cases |
| --- | ---: | ---: | ---: |
| Context recall | 0.9286 | 0.2379 | 77 |
| Faithfulness proxy | 0.9602 | 0.1224 | 80 |
| Semantic relevance | 0.8852 | 0.0380 | 80 |

The support proxy has only 66.7 percent balanced calibration accuracy and gives
perfect scores to several incorrect responses. Raw claim extraction required
99 inspected corrections, recorded separately from unmodified model responses.
Read the [results report](docs/week-02/W02_RAG_Evaluation_Results.md) and
[methodology](docs/week-02/metric_methodology.md) before interpreting the means.
Technical inspection flags nine failures and one dataset-identity review across
all 100 cases; this is not an independent human accuracy estimate.

Recompute every saved score and aggregate without downloading models:

```sh
.venv/bin/python scripts/evaluation/score_week2.py replay
.venv/bin/python scripts/evaluation/execute_week2_notebook.py
```

The notebook reads full recorded responses, inspected claims, calibration,
embedding vectors, and scores under [the run manifest](results/week-02/baseline/run_manifest.json).
It checks exact reproduction and shows distributions, language/tier tables,
lexical recall, calibration errors, and classified response failures.

## Fresh model execution

The recorded generation runtime requires Apple Silicon and MLX LM. Scoring,
tests, and saved-vector replay are independent of Apple GPU inference. Pinned
generation packages use platform markers in requirements-generation.txt.

```sh
.venv/bin/python scripts/evaluation/prepare_models.py
.venv/bin/python scripts/evaluation/generate_week2.py
.venv/bin/python scripts/evaluation/score_week2.py calibrate
```

Existing generation artifacts are protected by input fingerprints. To create a
fresh experiment, copy the tracked configuration to a new config with a distinct
run_name and output directory, then pass --config to the generation and scoring
commands. Freeze calibration before inspecting held-out outputs. Inspect every
response/claim correspondence and record matching input hashes before scoring:

```sh
.venv/bin/python scripts/evaluation/score_week2.py score
```

Claim-review and correction formats are exemplified in the recorded run folder.
Substantive wrong answers are never retried to improve scores. Fresh inference
records its own runtime, model revision, prompts, and attempts; exact generation
equality across different hardware is not assumed.

## Next review

The technical Week 2 package is assembled; the
[midpoint sheet](docs/week-02/midpoint_review.md) awaits mentor scoring, sign-off,
and confirmation of later scope. Next refinements are extraction reliability,
negative calibration contrasts, source authority, and explicit resident identity.
Later extensions cover STUM, SEOM, and HTD-IRL. Any scorer revision is a separately
recorded experiment and must preserve the held-out boundary.
