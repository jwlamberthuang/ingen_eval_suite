# ingen_eval_suite

A bilingual dialogue evaluation suite for Fari eldercare and Senpai educational
scenarios. `inGen_AI_Evaluation` is the sole Git repository root. Local internship
writeups and reference documents live in the parent `inGen` directory.

The current **Draft 0.6.0** contains **100 base cases in 99 families**, including
65 English and 35 Chinese cases. Jingwei Huang reviewed all English and Chinese
cases and supplied 11 wording edits across 10 cases. Those edits are preserved
verbatim. The **Pilot 0.3.0** contains the original twelve pilot cases, derived
from the current collection so their wording and annotations stay synchronized.

| Domain | Easy | Medium | Hard | Total |
| --- | ---: | ---: | ---: | ---: |
| Fari English | 16 | 16 | 8 | 40 |
| Fari Chinese | 8 | 8 | 4 | 20 |
| Senpai English | 10 | 10 | 5 | 25 |
| Senpai Chinese | 6 | 6 | 3 | 15 |
| Total | 40 | 40 | 20 | 100 |

Language review is recorded for every case. Final annotation and release approval
remain separate; original author identities and native Chinese author attestations
have not been added. Twelve pilot cases remain in calibration and 88 cases remain
unassigned. The proposed final split is 20 calibration and 80 held out, with
related language cases and context variants kept in the same family and subset.
No model generations or evaluation metric scores have been produced.

## Active files

| Path | Purpose |
| --- | --- |
| `data/W01_Evaluation_Dataset_Draft_v0.6.jsonl` | Authoritative editable 100-case collection |
| `data/W01_Evaluation_Dataset_Draft_v0.6.manifest.json` | Collection version, hashes, counts, and review scope |
| `data/W01_Evaluation_Dataset_Pilot_v0.3.jsonl` | Matching twelve-case pilot derived from the collection |
| `data/W01_Evaluation_Dataset_Pilot_v0.3.manifest.json` | Pilot version, hashes, and source collection hash |
| `dataset_config.json` | Active versions, fixed pilot IDs, and language-review record |
| `schemas/w01_dialogue_case.schema.json` | Record contract 1.1.0 |
| `scripts/datasets/build_dataset.py` | Validate and derive the pilot and manifests |
| `scripts/datasets/update_dataset.py` | Apply guarded content edits to a separate review preview |
| `scripts/datasets/validate_dataset.py` | Schema, annotation, family, count, and release checks |
| `scripts/datasets/dataset_io.py` | Shared serialization and manifest support |
| `tests/test_dataset_validation.py` | Known acceptance and rejection cases for the contract |
| `tests/test_dataset_workflow.py` | Edit preservation, pilot synchronization, and review safeguards |
| `scripts/documents/build_docx.py` | Build local Word deliverables from document source JSON |
| `scripts/documents/set_bilingual_fonts.py` | Times New Roman for English and Songti SC for Chinese |
| `requirements-validation.txt` | Pinned dataset-validation and test dependencies |
| `requirements-documents.txt` | Optional dependencies for Word document tooling |
| `.gitignore` | Excludes environments, caches, archives, reports, and scratch work |

Older datasets, batch-specific builders, revision payloads, and validation reports
are removed from the active tree. Published history remains available in Git;
additional local snapshots are archived under ignored `.local/archive/`.
Generated reports and preview builds also belong under `.local/`.

## Local deliverables

The parent `inGen` directory holds the following writeups; they are local internship
artifacts and are not included in this public repository.

| Deliverable | State |
| --- | --- |
| `W01_InGen_AI_Evaluation_Framework.docx` | Evaluation framework draft |
| `W01_Dataset_Specification.docx` | Dataset specification draft |
| `WEEK_01_DELIVERABLES.md` | Requirements and completion checklist |
| `WEEK_01_MODEL_LANDSCAPE_GUIDE.md` | Product/model audit and source discrepancies |
| `W01_RADNOVA_PIPELINE_REVIEW.md` | Prior-pipeline design notes |
| `W01_Dataset_Spoken_Style_Addendum_2026-10-13.md` | Dialogue modality and wording decisions |
| `weekly/Wk-01-Log.md` | Still to write: 300–500-word methodological reflection |

The required final dataset submission is `W01_Evaluation_Dataset_v1.jsonl`.
Draft 0.6 is the working collection; the final release name should be assigned
after annotation acceptance and split planning. Word build sources, historical
review packs, and detailed contributor records are kept locally under the
parent directory's hidden `.local/` folder. Original reference PDFs and other
internship reference documents remain local.

## Validation and reproducibility

Run commands from this repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-validation.txt
.venv/bin/python scripts/datasets/validate_dataset.py data/W01_Evaluation_Dataset_Draft_v0.6.jsonl --profile collection --manifest data/W01_Evaluation_Dataset_Draft_v0.6.manifest.json --report .local/reports/collection.json
.venv/bin/python scripts/datasets/validate_dataset.py data/W01_Evaluation_Dataset_Pilot_v0.3.jsonl --profile pilot --manifest data/W01_Evaluation_Dataset_Pilot_v0.3.manifest.json --report .local/reports/pilot.json
.venv/bin/python -m pytest -q
```

`collection` checks the exact 100-base-case allocation above. `pilot` checks one
case per domain/tier cell and calibration membership. Both check source and
evidence references, Unicode normalization, family separation, and context-variant
invariants. `release` additionally requires approved annotations and assigned
subsets; it must reject this working draft. Structural validation does not
establish factual truth, actual authorship, language suitability, or model quality.
These tests validate datasets and tooling; they are not implemented metric tests.

To reproduce the two datasets and their manifests in a fresh ignored directory:

```sh
.venv/bin/python scripts/datasets/build_dataset.py --output-dir .local/reproduced
```

The collection JSONL is the source of truth. Builders copy its exact bytes and
select the pilot from it; they never reconstruct reviewed dialogue from an old
Python draft. A preview build refuses to overwrite existing files.

After intentionally editing the master, synchronize the derived pilot and refresh
both hash manifests:

```sh
.venv/bin/python scripts/datasets/build_dataset.py --refresh
```

This leaves the master untouched. It refuses to discard a pilot edited directly
since its last manifest. Merge any such pilot edits into the master first. A
changed source hash is flagged as changed since the recorded language review;
building does not grant renewed review or approval.

For guarded updates, prepare a local JSON revision with `base_dataset_sha256`
and `edits`, each containing a case `id` and `changes` with `path`, `before`, and
`after`. For example, a query change uses `path: "/query"`. Apply it to a preview:

```sh
.venv/bin/python scripts/datasets/update_dataset.py --revision .local/review_edits.json --output .local/reviewed_collection.jsonl
```

The updater rejects a stale base hash, stale field values, duplicate edits,
unknown IDs, and identity/split/approval changes. Changed cases are marked as
needing renewed review. Inspect the preview and supporting annotations before
promoting it to the master and refreshing derived files. Keep version and review
metadata in `dataset_config.json` accurate when freezing a reviewed revision.

## Evaluation scope

Inputs and outputs are text intended for spoken dialogue. Fari answers should be
short, respectful, and clear. Senpai queries use simple child wording; answers
explain essential evidence or calculations for the stated learner. Equivalent
spoken and numeric forms express the same facts. Chinese mixed-language cases
blend English content words into Chinese sentence structure. Audio quality,
pronunciation, prosody, transcription, and audio latency require a later audio
stage and are not measured here.

Examples use original fictional scenarios and attributed public paraphrases.
Public source citations remain in the records. Local internship documents,
previous-client examples, credentials, and private authoring notes are excluded
from the public project. Every future metric implementation needs a test against
a manually verified example before use.
