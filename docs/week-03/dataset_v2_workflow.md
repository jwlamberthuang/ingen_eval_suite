# Dataset v2 collection and review

The [200-case release collection](../../data/W01_Evaluation_Dataset_v2.jsonl) contains
the original 100 cases unchanged, the revised twelve-case pilot, and 88 further
additions. Pilot edits were incorporated on October 27, 2026. The shorter
door-code query and the raw quoted injection are preserved exactly.

Review the [88-case Word packet](W03_Dataset_Additions_Review_v0.1.docx), covering
new-case numbers 13–100, or its [Markdown counterpart](additions_review.md).
The [pilot Word packet](W03_Dataset_Pilot_Review_v0.1.docx) and
[matching Markdown](pilot_review.md) reflect the imported edits. Word uses Times
New Roman and Songti SC. Structured JSON is a scoring reference, not a spoken
robot reply, model generation, or record of a physically executed action.

## Collection coverage

| Evaluation type | Preserved v1 | Revised pilot | Further additions | Total |
| --- | ---: | ---: | ---: | ---: |
| RAG | 100 | 4 | 51 | 155 |
| Spatial | 0 | 2 | 8 | 10 |
| Temporal | 0 | 1 | 4 | 5 |
| Entities and classes | 0 | 2 | 13 | 15 |
| Task alignment | 0 | 3 | 12 | 15 |
| Total | 100 | 12 | 88 | 200 |

The 100 new cases have 65 English/35 Chinese, 40 Fari EN/20 Fari ZH/25 Senpai
EN/15 Senpai ZH, and 20 Easy/40 Medium/40 Hard cases. The full collection has
130 English/70 Chinese and 60 Easy/80 Medium/60 Hard cases. The 88 further
additions contain 57 English/31 Chinese and 18 Easy/34 Medium/36 Hard cases.

All twelve pilot families remain in calibration. Eight additional calibration
families bring the new cohort to 20 calibration and 80 held-out cases. The
[configuration](../../configs/dataset-v2.json) records the exact IDs and manual
selection method; no random seed is implied. The original 20/80 split is preserved
as historical metadata, and its previously evaluated cases are not fresh held-out
evidence. Human review of new held-out annotations is allowed before freezing;
keep these cases out of scorer tuning and model selection.

All 100 new content/reference reviews are approved. Native authorship or substantive
native reworking and review of all 35 new Chinese cases were separately confirmed
on October 27, 2026. Approval hashes bind the released content; independent reviewer
agreement has not been measured. Construction notes preserve drafting context and
may describe earlier pending review: current `annotations.review` fields establish
the release status. Actual model results are separate experiment artifacts.

## Explicit evidence referents

New evidence and visible event descriptions name the user, a named person, or
the specific object or event. Use `user` or `用户` when no name is supplied.
Personal and possessive pronouns remain natural in user queries and expected
dialogue answers, but evidence must stand independently of the speaker. For
example, `User finished the puzzle before the bell rang` identifies the actor;
`You finished the puzzle` leaves the actor dependent on who is reading it.
Ambiguous-reference queries retain their intended challenge while the evidence
states the separate facts with explicit names.

The validator rejects common English and Chinese personal pronouns in new
`context` passages and temporal `event_descriptions`. This lexical check cannot
prove that every name or noun phrase has one meaning; human review remains
necessary. The original 100 records are frozen historical data and are exempt.
The latest evidence and temporal-event wording edits are incorporated into both
the JSONL master and the review copies.

## Contract and validation

- [Release schema](../../schemas/w03_evaluation_case.schema.json)
- [Maintenance commands](../../scripts/datasets/v2/manage_dataset.py)
- [Collection manifest](../../data/W01_Evaluation_Dataset_v2.manifest.json)
- [Pilot manifest](../../data/W03_Evaluation_Dataset_Pilot_v0.1.manifest.json)
- [Collection validation](../../deliverables/week-03/validation/collection.json)
- [Pilot validation](../../deliverables/week-03/validation/pilot.json)
- [Dataset tests](../../tests/test_dataset_v2.py)
- [Full collection tests](../../tests/test_dataset_v2_collection.py)

Schema version is `2.0.0`. New records separate visible `query`, `context`,
optional `input_metadata`, and `task_input` from hidden references, annotations,
and construction notes. All new RAG records use the pilot's common answer
contract. The [implemented adapters](experiment_pipeline.md) enforce the
visibility boundary through recursive allowlists and task-specific dispatch.

The legacy schema resolves offline through a registry using the tracked schema.
Legacy acceptance also checks original IDs, content, order, and exact line bytes.
Collection validation additionally checks the revised pilot prefix and recorded
new split memberships. Omitting a type cannot make a new record legacy-compatible.

Evidence indices are zero-based: index 0 is the first passage, shown as p001 in
review documents. Structured references include derivations and evidence links;
RAG retains fact/passage/source and behavior annotations. The ten adversarial
cases contain fixed candidate-response probes with atomic supported, unsupported,
and contradicted labels. Their ideal support fractions are hand-worked annotation
targets, separate from actual scorer results or model generations. No embedding
cosines are invented. Empty inventories and no-task cases are explicitly marked.

The entity ontology has nine classes. The generic planning action catalog is:

| Action | Required string arguments |
| --- | --- |
| `deliver_item` | `item`, `recipient` |
| `notify` | `recipient`, `topic` |
| `move_item` | `item`, `destination` |
| `open_window` | `location` |
| `close_door` | `location` |

These are benchmark symbols and do not establish product tool availability.
Aliases are explicit, field-specific annotation choices, not automatic translation
or semantic matching. Location aliases should name places rather than convert a
door into a window. Identity links required by first-person requests are visible.

| Profile | Purpose |
| --- | --- |
| `draft` | Validate typed records, symbolic references, evidence links, IDs, families, and review metadata consistency within allocation limits. |
| `pilot` | Require the configured twelve cases/order, all calibration, and every task type. |
| `collection` | Require the complete 200-case shape, exact targets, original/pilot prefixes, and recorded new split IDs; report pending reviews as warnings. |
| `release` | Collection checks plus approved content hashes, reviewers/dates, and confirmed native Chinese authorship/review. |

Release and pilot validation pass with zero errors and warnings. The full
release-profile report has `release_ready=true`; the reviewed twelve-case pilot
is a subset, not a standalone 200-case release. Structural and symbolic checks
cannot establish natural-language truth, semantic family independence, or actual
authorship. The schema, protocol, source, and dataset were frozen before generation.

Run from the repository root:

```sh
.venv/bin/python scripts/datasets/v2/manage_dataset.py validate data/W01_Evaluation_Dataset_v2.jsonl --profile release --manifest data/W01_Evaluation_Dataset_v2.manifest.json
.venv/bin/python scripts/datasets/v2/manage_dataset.py validate data/W03_Evaluation_Dataset_Pilot_v0.1.jsonl --profile pilot --manifest data/W03_Evaluation_Dataset_Pilot_v0.1.manifest.json
.venv/bin/python -m pytest -q
.venv/bin/python scripts/datasets/v2/manage_dataset.py build --output-dir build/week3-reproduced
```

The full JSONL is authoritative. A fresh build copies it byte for byte, selects
the pilot's original lines, and reproduces both manifests. Existing output
directories are refused. The older `assemble` command remains available for
joining a new-record-only file to the frozen legacy collection in a fresh preview.

## Incorporate the next review

### Context recall annotation amendment

The [approved 2.0.1 amendment](../../data/annotations/W03_Context_Recall_v2.0.1.json)
changes only the hidden context-recall inventory for 17 of the 55 audited new
RAG cases. The 200-case JSONL and original approval hashes remain the frozen
source. Combine that source with the amendment in memory for corrected recall
scoring; the combined view is not a separately approved full dataset export. The amendment
has its own [schema](../../schemas/w03_context_recall_amendment.schema.json),
[Word review sheet](W03_Context_Recall_Review_v2.0.1.docx),
[Markdown explanation](context_recall_correction.md), and
[replay manifest](../../results/week-03/context-recall-v2.0.1/manifest.json).

Unavailable answer slots have null canonical values and no supporting passage
links. Equal-authority conflicts link both passages without choosing a value.
Missingness observations remain separate from the recall denominator. Intern
review approved all 17 corrections, including revised Chinese annotation wording.
The amendment records a content hash and the complete reviewed-case inventory;
original source/authorship approval remains separate. To incorporate further edits, preserve the reviewed Word
file, reconcile the amendment against its exact `before` labels, rerun its tests,
and seal a new replay version. A source wording change requires a new dataset and
experiment version instead of this annotation-only path.

```sh
.venv/bin/python scripts/evaluation/correct_week3_context_recall.py --replay
.venv/bin/python -m pytest -q tests/test_week3_context_recall.py
```

### Future source changes

The released v2 collection has been used in the frozen Week 3 experiment. Future
content changes need a new version and matching experiment configuration; retain
this release and its run snapshots. Examples inspected during failure analysis
cannot become untouched held-out evidence again after tuning against them.

Edit the Word copy or the authoritative JSONL. Reconcile queries, evidence,
expected answers, aliases, facts, constraints, and goals together. Preserve the
reviewed Word file before rebuilding; the builder does not automatically import
Word text as verified ground truth. Pilot changes must also be synchronized to
the corresponding source lines in the collection.

The guarded update accepts a JSON payload containing `base_sha256` and an `edits`
list. Each edit has `id`, a list-valued `path`, `before`, and `after`. Paths may be
`["query"]` or `["reference", "ideal_response"]`. The base hash and exact old
value prevent stale edits. Legacy, identity, split, and review-attestation changes
are refused. Untouched lines remain byte for byte, and affected review records
reset to draft; Chinese edits also reset native authorship/review to pending.

```sh
.venv/bin/python scripts/datasets/v2/manage_dataset.py update data/W01_Evaluation_Dataset_v2.jsonl --edits build/review-edits.json --output build/revised-collection.jsonl
.venv/bin/python scripts/datasets/v2/manage_dataset.py manifest data/W01_Evaluation_Dataset_v2.jsonl --profile release --output build/revised-collection.manifest.json
.venv/bin/python scripts/documents/build_week3_pilot.py --source data/W01_Evaluation_Dataset_v2.jsonl --mode additions --output-dir build/additions-review
```

After accepting revised master/pilot data, refresh both manifests together under
fresh filenames, validate, and replace the former manifests. Each binds current
data, schemas, configuration, validator, and metric source; the two manifests
also bind the other JSONL source. No manifest hashes another manifest. Never
restore approval merely by regenerating files. Approved review hashes use
canonical sorted JSON with only `annotations.review` excluded, as implemented by
`content_hash`. Render and visually inspect regenerated Word copies before use.
