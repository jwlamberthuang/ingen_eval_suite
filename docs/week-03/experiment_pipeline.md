# Week 3 experiment pipeline

The adapters and staged experiment pipeline operate on the approved 200-case
release. Unit tests use synthetic backends and hand-worked fixtures; actual
inference artifacts are recorded separately. The
[weekly review index](../../deliverables/week-03/README.md) records the current
execution and deliverable status. The dataset, schema, protocol, input plans,
source, and configuration are frozen before generation.

## Annotation correction replay

The original run below remains frozen. The separate
[context-recall amendment](../../data/annotations/W03_Context_Recall_v2.0.1.json)
is applied only to an in-memory scoring view by
[`week3_context_recall`](../../src/week3_context_recall.py). Version 2.0.1 is
approved after intern review of all 17 corrections. A content hash and complete
reviewed-case inventory bind that approval. Original source/authorship approval
remains separate; annotation review does not establish independent response assessment.

The replay verifies baseline hashes and exact baseline scores, rejects stale or
out-of-scope edits, proves every generation input unchanged, and reuses recorded
responses, inspected claims, and saved vectors. It asserts every per-case metric
except amended context recall is identical. No generation or threshold fitting
occurs. Missing answer slots carry null canonical values; conflicts and N/A stay
explicit. The output contains only recall results, comparisons, and its manifest.
The notebook displays amended recall alongside the original baseline; the
original analysis command continues to replay the original results.

```sh
.venv/bin/python scripts/evaluation/correct_week3_context_recall.py --replay
```

Building a new amendment output uses the same command without `--replay` and
refuses to overwrite an existing output directory. Source changes or reviewer
edits require a fresh sealed version, preserving the reviewed copy and completed
experiment. See the [review sheet](context_recall_correction.md) for all 17 edits.

## Inputs and scoring

[week3_inputs.py](../../src/week3_inputs.py) builds generation messages from
allowlisted fields. Every payload contains platform, response language, task type,
the original query, and numbered evidence. Supplied history permits only user and
assistant roles. Current-user names and aliases and learner level/objective are
copied explicitly. References, hidden constraints, gold aliases, goals, probes,
IDs, difficulty, split membership, and review notes never enter generation.

Spatial inputs include the named objects, requested axis, and coordinate frame.
Temporal inputs include visible event IDs/descriptions and requested pairs, with
no hidden relation edges. Entity inputs use the fixed nine-class vocabulary.
Task planning uses the generic five-action catalog. These vocabularies are task
instructions and do not expose the case-specific reference inventory or goals.

The RAG scoring adapter copies legacy records without alteration and projects
new RAG references into the retained metric interface. Structured records cannot
enter the RAG scorer. The mixed dispatcher preserves metric nulls and error
statuses. It reports four separate populations: legacy calibration, previously
evaluated legacy cases, new calibration, and new held-out. Each population has
separate RAG and structured summaries. There is no composite metric or automated
RAG correctness verdict.

Claim extraction receives the actual RAG response, permitted conversation, and
current-user identity. It receives no evidence or reference answer that could
silently correct an assertion. Structured predictions do not undergo extraction.
The strict claims parser accepts one object containing a string array, optionally
inside one JSON fence; duplicate keys, NaN/Infinity, bare arrays, extra fields,
and empty claim strings are rejected. Exact duplicate claims and surrounding
claim whitespace are normalized; raw text is retained.

## Run commands

Run from the repository root with the pinned dependencies installed. The default
[configuration](../../configs/week-03.json) names a separate Week 3 output folder
and reuses the recorded model/encoder revisions. The backend loads cached model
files only. It never downloads or installs a checkpoint.

```sh
.venv/bin/python scripts/evaluation/week3.py preflight
.venv/bin/python scripts/evaluation/week3.py freeze
.venv/bin/python scripts/evaluation/week3.py calibrate
.venv/bin/python scripts/evaluation/week3.py generate
.venv/bin/python scripts/evaluation/week3.py extract
.venv/bin/python scripts/evaluation/week3.py review-template
```

`preflight` is read-only, builds all 200 input plans, reports task/cohort counts,
and lists readiness gates. It does not tokenize using a model or call inference.
`freeze` requires valid release reviews, a refreshed release-profile collection
manifest, and a reviewed schema version without the draft label. It reserves a
fresh output directory and saves immutable dataset, input, configuration, and
validation snapshots. Existing outputs are never overwritten. It does not grant
review or native-authorship approval.

Each following stage verifies the configuration, dataset, manifest, prompts,
adapter/scorer source, schema/configuration, requirements, and protocol hashes.
Changed inputs require a separately named experiment. `calibrate` must finish
before generation. `generate` records one response attempt per case. `extract`
records claim proposals for the 155 RAG cases, with explicit skipped/failure
records when a response is unavailable. Missing checkpoints stop stage setup
before creating a model attempt.

## Calibration choice

The default `support.mode="transfer_week2"` transfers threshold 0.80 from the
recorded calibration artifact and requires the same embedding and segmenter.
This preserves a historical comparison; it does not establish validity on new
cases. The prompt and extraction transport are separately versioned and therefore
generation should not be described as identical to Week 2.

A new configuration can select `support.mode="calibrate_new"` before freezing.
That option fits only annotated reference facts and fixed probe claims in the
new calibration families. It records label sources, language/class counts, all
threshold candidates and confusion matrices. The 16 reference facts are all
positive; three probe claims add one positive and two negatives. Thus there are
17 positives and 2 negatives, with both negatives in English. No language-specific
threshold is fitted. A one-class inventory stops before embedding inference.
The grid and balanced-accuracy/larger-threshold tie rule follow the
[formal protocol](W03_Evaluation_Protocol.md).

Fixed calibration probes remain labeled scorer challenges. They never enter
generation inputs and are never presented as generated responses. Their labels
do not prescribe embedding cosine values. The optional fit is weakly supported
by two negatives and must be reported with that limitation.

## Inspect claim correspondence

`review-template` creates `claim_review.json` inside the run directory with status
`pending`. Inspect every RAG response against its raw extraction proposal. Preserve
numbers, names, conditions, negation, and completed-action assertions. Do not
rewrite a response to agree with a reference.

In the review file, record actual `reviewer_ids`, the ISO review date, and all
required RAG IDs in `reviewed_case_ids`. A correction has `id`, `before`, `after`,
and a nonempty `reason`; `before` must equal the parsed proposal (or null after
extraction failure), and `after` must be an array of nonempty claim strings.
Unknown/duplicate IDs, stale input hashes, unexplained changes, and corrections
for unavailable responses are rejected. Set status to `checked` only after the
correspondence review is complete. An unresolved invalid proposal can remain
null and produce a faithfulness scorer error rather than an invented score.

Then run:

```sh
.venv/bin/python scripts/evaluation/week3.py score
.venv/bin/python scripts/evaluation/week3.py replay
```

Scoring requires complete generation/extraction attempts, frozen calibration,
and the inspected claim review. It preserves raw responses and proposals, saves
separate scores and portable embedding vectors, and seals artifact hashes.
Replay requires no model or embedding inference and compares all scores and
aggregates exactly. A completed scoring stage cannot be overwritten.

## Resume behavior and artifact contract

Before an attempt, a flushed reservation is written to the stage journal. A
completed attempt is appended once to `responses.jsonl` or `claims.jsonl`.
On resume, finished attempts are skipped. A reservation without a finished row
becomes `InterruptedAttempt` and receives no substantive retry. A changed reserved
input, edited completed row, duplicate case ID, or truncated JSONL is rejected.
Completed rows carry content hashes even before the stage is sealed. A process lock prevents
concurrent writers. Model setup errors remain stage errors; they are not recorded
as a failed answer for every case.

Rows preserve messages, full rendered prompts and hashes where rendering
succeeded, token counts, raw text, timing, and error categories. Inputs exceeding
the declared token budget fail without silent truncation. Timeout checks occur
between streamed tokens and are cooperative; they cannot preempt a blocked first
token or backend call. Failed stream attempts retain their inputs and error type;
an incomplete generated text is not treated as a completed response.

The run manifest records the pinned identity, actual runtime package versions,
stage completion, and hashes of sealed artifacts. Changed sealed outputs stop
resume/replay. Hashes detect drift; they are not independent signatures. If a
process crashes while committing a scoring bundle, an integrity mismatch stops
reuse and requires a new run rather than automatic repair. Metrics are replayable;
generation is not promised byte-identical across machines or runtime versions.

The recorded [results and limitations](W03_Extended_Evaluation_Results.md) document
the completed run. Every raw extraction proposal failed its strict object
contract (153 bare arrays and two malformed JSON outputs). All 155 were inspected
and corrected separately; these failures remain visible in the raw artifacts.
Post-inspection faithfulness is an assisted diagnostic, not fully automatic
extraction performance or independent human accuracy. Source, references, parser,
matching, and threshold remain frozen.

Supplementary analysis and the notebook can be replayed without model inference:

```sh
.venv/bin/python scripts/evaluation/analyze_week3.py --replay
.venv/bin/python scripts/evaluation/build_week3_notebook.py --execute
```

The [weekly review index](../../deliverables/week-03/README.md) links the executed
notebook, reflection, and technical response/claim inspection artifacts.
See [pipeline tests](../../tests/test_week3_experiment.py),
[adapter tests](../../tests/test_week3_inputs.py), and
[pipeline verification](../../deliverables/week-03/validation/pipeline.json).
