# ingen_eval_suite

A bilingual dialogue evaluation project for Fari eldercare and Senpai educational
scenarios. This checkout, `inGen_AI_Evaluation`, is the Git repository root.
Local internship writeups, Word review packs, specification addenda, and private
reference notes live outside this repository.

The current **Draft 0.4.0** working collection contains **32 base cases in 31
families**. It combines the twelve-case pilot with twenty new review drafts.
All cases remain unapproved; the twelve pilot cases are in calibration and the
new twenty are unassigned pending review and split planning. Thirteen Chinese
examples still require complete native language and annotation review. Thirteen
wording edits across seven Chinese cases were adopted from human review, and
nineteen English cases were checked and adapted to the same dialogue style.

The new batch contains 8 Fari English, 4 Fari Chinese, 5 Senpai English, and
3 Senpai Chinese cases, with 8 Easy, 8 Medium, and 4 Hard cases. It expands
preference recall, accessible routes, event planning, contextual vocabulary,
arithmetic, rule application, uncertainty, and adversarial evidence handling.
This is a working draft toward the final 100-case target. No model generations
or evaluation metric scores have been produced.

Current files:

- `data/W01_Evaluation_Dataset_Draft_v0.4.jsonl`: the revised 32-case working collection.
- `data/batches/W01_Review_Batch_02_v0.2.jsonl`: the revised twenty-case batch.
- `data/revisions/W01_Draft_v0.4.review_edits.json`: guarded wording and annotation changes.
- `data/W01_Evaluation_Dataset_Draft_v0.3.jsonl`: the frozen collection before this review.
- `data/batches/W01_Review_Batch_02_v0.1.jsonl`: the frozen first wording of the new batch.
- `data/W01_Evaluation_Dataset_Pilot_v0.2.1.jsonl`: revised twelve-case pilot,
  retaining the five Chinese query edits and six English language edits.
- `data/W01_Evaluation_Dataset_Pilot_v0.1.1.jsonl`: initial pilot wording.
- `schemas/w01_dialogue_case.schema.json`: schema 1.1.0.
- `data/validation/`: structural reports; each dataset also has a hash manifest.

Public author identities may be omitted without changing the draft or review
state. Known public-source citations are retained. Schema 1.1.0 allows null
author identities for original scenarios and case review metadata; it does not
relax native Chinese approval requirements. Pilot versions 0.1.1 and 0.2.1 are
publication revisions with the same task wording and evidence as their earlier
versions and new schema/file hashes. Detailed contributor records are maintained
locally. A query edit alone does not approve an entire example.

The evaluation currently uses **text inputs and outputs intended for spoken
dialogue**. Fari answers use short, respectful sentences. Senpai queries use
simple child wording, and answers provide friendly explanations suited to the
stated learner. Essential calculations, times, and evidence should be clear
when read aloud. Equivalent spoken and numeric forms express the same required
facts; formatting alone should not count as an error. Existing correctness,
grounding, behavior, and learner-suitability criteria still apply.

The two selected mixed-language queries use Chinese sentence structure with
English content words embedded in it. This is the pattern chosen for these
examples, rather than a claim about every bilingual speaker. The cozy preference
has explicit supporting evidence and is not inferred merely from quietness.
Fari's eldercare audience remains unchanged; mixed cases assume users familiar
with the borrowed words. Audio quality, pronunciation, prosody, transcription,
and audio end-to-end latency will require a separate audio evaluation stage.
No audio performance is measured by this text collection.

Run from this repository root after creating a Python virtual environment:

```sh
.venv/bin/python -m pip install -r requirements-validation.txt
.venv/bin/python scripts/datasets/validate_dataset.py data/W01_Evaluation_Dataset_Draft_v0.4.jsonl --profile draft --manifest data/W01_Evaluation_Dataset_Draft_v0.4.manifest.json --report data/validation/W01_Draft_v0.4_validation.json
.venv/bin/python -m pytest -q
```

The validator checks schema conformance, evidence and source references, context
coverage, family separation, and variant invariants. `--profile pilot` checks the
twelve-case pilot layout. `--profile release` adds final domain counts, human
approval, and edge coverage requirements and must reject the current drafts.
Structural validation cannot establish factual truth, actual authorship,
language suitability, or successful model behavior. Metric implementations
require separate tests against manually verified examples before use.

The builders refuse to overwrite existing data or review work. To reproduce the
current batch and working collection in a fresh directory:

```sh
.venv/bin/python scripts/datasets/revise_collection.py --output-dir /tmp/ingen-draft-reproduced
```

`scripts/datasets/build_pilot.py` preserves the initial pilot task wording.
`scripts/datasets/revise_pilot.py` applies recorded query edits only when the
frozen base hash and original queries match. The revision payload is
`data/revisions/W01_Pilot_v0.2.1.query_edits.json`. After review edits, create a new
version, revalidate, and freeze a new manifest rather than changing an existing
hash. Related language cases and later context variants stay in one family and
must never cross dataset subsets.

`scripts/datasets/revise_collection.py` replays the current review from the
frozen Draft 0.3.0 hash. Each changed field must match its recorded prior value.
The script rejects duplicate or stale edits and cannot change case identities,
split assignments, difficulty tiers, or native review approval. Earlier drafts
remain reproducible with `scripts/datasets/build_review_batch.py`.

The public examples use original fictional scenarios and attributed public
paraphrases. Local internship PDFs, previous internship client examples,
credentials, and private authoring reference notes are excluded.
