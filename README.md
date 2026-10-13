# ingen_eval_suite

A bilingual evaluation suite for grounded Fari companion dialogue and Senpai
educational dialogue. Week 1 provides a reproducible evaluation design, a
versioned annotation contract, and 100 reviewed English/Chinese cases. Model
execution and measured RAG scores are the next implementation stage.

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

Jingwei Huang reviewed every English and Chinese case and confirmed native
authorship of all 35 Chinese cases. The reviewed dialogue is preserved verbatim;
annotation checks and review limitations are documented in
[dataset documentation](data/dataset_documentation.md).

| Check | Current state |
| --- | --- |
| Release schema, counts, and annotation relationships | Valid |
| Native Chinese authorship and language review | Recorded for all 35 Chinese cases |
| Pilot synchronization and exact dataset rebuild | Verified |
| Model generations and metric scores | Not yet produced |
| Audio evaluation | Outside the current text experiment |

The selected generation baseline is Qwen2.5-7B-Instruct, with multilingual-e5-base
for the planned embedding metrics. These are public task proxies. No result in
this repository establishes performance of an unavailable InGen model or a
physical robot.

## Setup and reproduce dataset checks

Run from the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/datasets/validate_dataset.py data/W01_Evaluation_Dataset_v1.jsonl --profile release --manifest data/W01_Evaluation_Dataset_v1.manifest.json
.venv/bin/python scripts/datasets/validate_dataset.py data/W01_Evaluation_Dataset_Pilot_v0.4.jsonl --profile pilot --manifest data/W01_Evaluation_Dataset_Pilot_v0.4.manifest.json
.venv/bin/python -m pytest -q
```

These tests validate data and maintenance tooling. They are distinct from the
planned metric tests, which must use manually verified expected outcomes before
model scores are reported. The `release` profile requires approved annotations,
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
| [requirements.txt](requirements.txt) | Complete Week 1 setup |
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

## Next implementation stage

Implement the three core RAG metrics, validate their English/Chinese paths with
at least 20 manually verified metric tests, and add the reusable evaluator and
demonstration notebook. Calibrate support proxies on the designated subset,
freeze model/scorer configuration, then evaluate the held-out cases and report
subgroup scores, errors, applicability, and failure examples. Optional retrieval
experiments need a frozen public corpus and relevance labels.
