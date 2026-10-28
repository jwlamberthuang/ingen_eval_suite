# Week 3 extended evaluation results

Recorded run: `w03-qwen25-7b-mlx4bit-text-v1` · Dataset contract 2.0.0 ·
Prepared for submission, October 28, 2026.

The 200-case text baseline is complete and all scores replay exactly. New
held-out exact task success is 7/8 spatial, 4/4 temporal, 7/12 entity
recognition/classification, and 3/12 task planning. Interpretation requires three
qualifications: every raw claim proposal failed its output contract; the support
proxy accepts the deliberately flawed boundary candidates; and the separately
versioned context-recall correction below is a post-inspection diagnostic.

## Frozen experiment

The [protocol](W03_Evaluation_Protocol.md), [configuration](../../configs/week-03.json),
[run manifest](../../results/week-03/w03-qwen25-7b-mlx4bit-text-v1/run_manifest.json),
and [release manifest](../../data/W01_Evaluation_Dataset_v2.manifest.json) identify
the methods and inputs. All 100 new references were reviewed; native authorship or
substantial native reworking and review of all 35 new Chinese cases were confirmed.
The original 100 cases and the Week 2 experiment remain unchanged.

Generation uses `mlx-community/Qwen2.5-7B-Instruct-4bit`, revision
`c26a38f6a37d0a51b4e9a1eb3026530fa35d9fed`, with temperature 0, seed 17,
a 512-token output budget and a 4096-token input limit. The encoder is
`intfloat/multilingual-e5-base`, revision
`d128750597153bb5987e10b1c3493a34e5a4502a`, on CPU with a 512-token limit.
The recorded runtime is macOS/arm64 with MLX; package versions are in the manifest.
Models were loaded from cached pinned files with offline inference. The support
threshold transfers unchanged from Week 2 at 0.80; no new fitting or subgroup
threshold selection was performed. New calibration labels have only two negative
atoms, both English, and do not establish cross-language threshold validity.

The primary cohort is **80 new held-out cases: 44 RAG and 36 structured**.
Twenty new calibration cases and the historical 20 calibration/80 previously
evaluated legacy cases are separate populations. Changes in prompt transport,
claim inspection, and scenario mix preclude attributing differences from Week 2
to model improvement. Text proxies do not measure internal InGen models, robot
perception, physical execution, or audio quality.

## Execution and raw extraction coverage

All 200 response attempts returned nonempty answers and stopped normally. There
were no generation failures, token-budget terminations, or substantive answer
retries. The extractor also completed 155 attempts, but **0/155 proposals passed
the strict claims-object contract**: 153 were bare arrays and two were malformed
JSON. These remain `scorer_error` in the sealed raw artifact.

Every actual response/proposal pair was inspected. The separate
[claim review](../../results/week-03/w03-qwen25-7b-mlx4bit-text-v1/claim_review.json)
contains 155 corrections: 70 checked transport normalizations and 85 changes to
claim content, scope, duplication, omissions, modality, or procedural exclusions.
Two inspected responses are claim-free. Nothing rewrites generated answers,
corrects their false assertions, or changes the strict parser. The resulting
faithfulness values are **post-inspection assisted diagnostics**; they do not
establish fully automatic extraction reliability or independent human accuracy.
The public role identifier `technical-inspection` describes this inspection role,
not an independent human reviewer.

## New held-out structured results

| Task | Cases | Valid outputs | Exact task success | Core metrics: mean (defined cases) |
| --- | ---: | ---: | ---: | --- |
| Spatial | 8 | 8/8 | 7/8 = 0.8750 | Spatial accuracy 0.8750 (8) |
| Temporal | 4 | 4/4 | 4/4 = 1.0000 | Pair accuracy, consistency, coherence each 1.0000 (4) |
| SEOM | 12 | 12/12 | 7/12 = 0.5833 | Recall 0.8125 (12); class accuracy 0.7708 (12); precision 1.0000 (12) |
| HTD-IRL | 12 | 7/12 | 3/12 = 0.2500 | Coverage 0.8611 (6); precision 0.6905 (7) |

Means use defined values. Five held-out HTD format failures contribute zero to
task success and null core metrics. One valid no-goal case has undefined coverage
and precision zero because an extra task was predicted. No reference is
quarantined. Conditional coverage 0.8611 therefore cannot be read as end-to-end
planning success. The small temporal group supports case inspection, not a
population claim of solved temporal reasoning.

The [notebook](../../notebooks/week-03/W03_Extended_Evaluation_Suite.ipynb) reports
calibration separately: spatial 2/2 exact, temporal 0/1, SEOM 0/3, and HTD 1/3.
It includes language/tier tables, visualizations, and 10 STUM, 6 SEOM, and 6 HTD
recorded demonstrations selected by ID order without consulting outcomes.

The [structured failure inspection](../../results/week-03/w03-qwen25-7b-mlx4bit-text-v1/structured_failure_review.jsonl)
covers all 21 non-successful cases across both new cohorts. Examples:

- 0138 chooses `aligned` instead of reporting conflicting equally credible spatial records.
- 0106, a calibration case, has pair accuracy 1/3 but consistency 1. A coherent set of wrong relations is still wrong.
- 0150 lists only the tablet, missing three entities. In 0152 the toy rocket is recognized but misclassified as a device: recall 1, class accuracy 1/2.
- 0143, in calibration, invents an entity in an explicitly empty scene. Recall is undefined, precision and task success are zero.
- 0110 and five held-out plans contain malformed task objects/quoting. Raw outputs are retained without JSON repair.
- 0163 covers both requested goals but adds a kitchen-window notification, giving coverage 1 and precision 2/3.
- 0159 and 0165 are **frozen alias limitations**: “both tasks completed” and “cards are ready” express the intended notifications, but are absent from the accepted topic aliases. Scores remain 2/3 and 1/2 respectively. These are technical observations, not a replacement human-adjusted score.

## RAG metrics and their limits

Each cell is mean (defined/total). Relevance is raw cosine; lexical recall is a
separate diagnostic. Neither is an answer-correctness score. Context recall uses
the **reviewed 2.0.1 annotation amendment** for new cases; other metrics and
the legacy context-recall inventories remain unchanged.

| Cohort | Context recall | Inspected-claim faithfulness proxy | Semantic relevance | Lexical reference recall |
| --- | --- | --- | --- | --- |
| legacy_calibration | 0.8684 (19/20) | 0.9223 (19/20) | 0.8864 (20/20) | 0.5001 (20/20) |
| legacy_previously_evaluated | 0.9286 (77/80) | 0.9403 (80/80) | 0.8907 (80/80) | 0.5207 (80/80) |
| new_calibration | 0.8182 (11/11) | 0.9697 (11/11) | 0.8940 (11/11) | 0.5120 (11/11) |
| new_held_out | 0.7442 (43/44) | 0.9050 (43/44) | 0.8922 (44/44) | 0.4386 (44/44) |

### Versioned context recall correction

The frozen baseline reports 1.0000 for both new cohorts: 11/11 calibration and
44/44 held-out. Some inventories credit supported descriptions of missingness
instead of the requested answer. The [annotation amendment](../../data/annotations/W03_Context_Recall_v2.0.1.json)
audits all 55 new RAG inventories and changes 17, with before/after labels,
evidence links, reasons, and separate behavior observations. The original dataset,
review approvals, protocol, scores, and run remain frozen. The amendment is
**2.0.1, approved after intern review of all 17 corrections**, including five cases
with revised Chinese annotation wording. A separate content hash and reviewed-case
inventory bind this approval to the exact amendment; original dialogue/authorship
approvals remain source-specific. See the [Word review record](W03_Context_Recall_Review_v2.0.1.docx)
or its [Markdown copy](context_recall_correction.md).

Recall now counts supported requested targets divided by all requested targets;
unavailable and conflicting targets remain in the denominator. Unknown answer
slots have `canonical_value: null`; no room, signer, page, sender, price, or other
unobserved value is invented. In 0101, time is supported but room is unavailable,
giving 1/2. In 0125, the page is unavailable, giving 0/1. In 0115 and 0129, equal
authority conflicts leave the effective day/shape unresolved, each 0/1. Case
0186 has no identified referent for “she”: its inventory is empty and recall is
N/A, following the existing clarification-required convention. In 0172, removing
an unasked water-temperature absence leaves the supported washing policy at 1/1.
Known negative states and direct capability-boundary answers retain credit.

Four partial cases are all in calibration; eleven unresolved/conflicting targets
are in held-out. One held-out case becomes N/A and one keeps recall 1 with a
smaller denominator. Thus calibration is 9/11 = 0.8182; held-out is 32/43 = 0.7442
over 43 defined of 44 eligible cases. These are means of per-case ratios, not
pooled target recall or model accuracy. Correct abstention can accompany low
context recall because the metric concerns evidence sufficiency.

The [correction replay](../../results/week-03/context-recall-v2.0.1/context_recall.json)
and [manifest](../../results/week-03/context-recall-v2.0.1/manifest.json) bind the
baseline inputs, amendment, schema, and replay implementation. All 200 visible
inputs and every other per-case metric are identical. Saved responses and vectors
are reused with zero new generation attempts. This post-inspection correction is
a diagnostic comparison, not fresh untouched held-out evidence. Legacy inventories
were not reannotated, so cohort differences cannot establish a model improvement.

Faithfulness is also limited by claim granularity, pronoun interpretation, and
context-only support search. A response can repeat information supplied by the
user query, such as the upstairs glasses in 0014, without that information appearing
in the retrieved context searched by the metric. Conversely, high similarity can
accept a wrong number, negation, or entity assignment. High relevance can correctly
indicate an on-topic but incorrect answer.

## Fixed metric-boundary probes

These are **prewritten candidates, not generated model answers**. Two belong to
calibration and eight to held-out. Every candidate receives proxy 1.0 despite an
ideal supported-claim fraction of 0 or 1/2. Across 18 annotated atoms, all five
supported and all thirteen unsupported/contradicted claims pass the threshold.
The ten-case mean ideal fraction is 0.25; this is not a population estimate.

| Case | Cohort | Annotated ideal support | Frozen proxy | Relevance |
| --- | --- | ---: | ---: | ---: |
| 0103 | new_calibration | 0.0 | 1.0 | 0.8878 |
| 0168 | new_calibration | 0.5 | 1.0 | 0.8951 |
| 0169 | new_held_out | 0.5 | 1.0 | 0.8616 |
| 0170 | new_held_out | 0.0 | 1.0 | 0.9488 |
| 0171 | new_held_out | 0.5 | 1.0 | 0.9175 |
| 0172 | new_held_out | 0.0 | 1.0 | 0.9332 |
| 0173 | new_held_out | 0.0 | 1.0 | 0.8790 |
| 0174 | new_held_out | 0.5 | 1.0 | 0.8019 |
| 0175 | new_held_out | 0.0 | 1.0 | 0.9139 |
| 0176 | new_held_out | 0.5 | 1.0 | 0.8733 |

In 0103, the wrong seven-star claim matches the quoted instruction at cosine
0.8513; trusted arithmetic gives twenty. In 0170, permission to take the tablet
home matches the policy forbidding it at 0.8490. In 0171 the wrong key recipient
matches the contrasting recipient passage at 0.9444. These expose source-authority,
negation, and entity-binding gaps in retrieval similarity. No threshold was tuned
against the probes. Full matches and annotations are in the
[fixed-probe artifact](../../results/week-03/w03-qwen25-7b-mlx4bit-text-v1/analysis/fixed_probes.json).

## Actual response failure analysis

[Technical RAG inspection](../../results/week-03/w03-qwen25-7b-mlx4bit-text-v1/response_review.jsonl)
covers all 155 answers: 99 meet essential reference behavior, 41 are partial,
13 fail essential reference behavior, and 2 expose legacy input/reference identity
ambiguity. Partial judgments include explanation, role, and register issues and
must not be converted into an independent accuracy estimate. Categories overlap;
the [review metadata](../../results/week-03/w03-qwen25-7b-mlx4bit-text-v1/response_review_metadata.json)
defines judgments and limitations.

Actual new failures include four instead of three remaining seats (0169), reversal
of a library policy (0170), the swapped key recipient (0171), contradictory craft
ordering (0175), and no biscuits left instead of two (0180). Case 0173 correctly
withholds a current sprout but invents a previous-observation explanation for an
injected height. Capability abstentions often succeed, while some answers address
the user as the robot platform or adopt the user's first-person experiences.
Legacy 0036/0039 clarification is marked ambiguous because the visible input does
not explicitly link the current speaker to the named person presumed by the reference.

## Runtime and replay

Response durations: mean 8.17 s, median 7.04 s, nearest-rank p95 19.90 s, maximum
41.18 s. Extraction durations: mean 2.58 s, median 2.35 s, p95 4.93 s. These are
recorded local per-attempt durations, not robot latency; model setup and review
are separate. Both stages have one recorded attempt per eligible case.

Run from the repository root with the pinned environment:

```sh
.venv/bin/python scripts/evaluation/week3.py replay
.venv/bin/python scripts/evaluation/analyze_week3.py --replay
.venv/bin/python scripts/evaluation/correct_week3_context_recall.py --replay
.venv/bin/python scripts/evaluation/build_week3_notebook.py --execute
.venv/bin/python -m pytest -q
```

Replay uses saved embeddings and requires no model download or generation. The
[supplementary manifest](../../results/week-03/w03-qwen25-7b-mlx4bit-text-v1/analysis/manifest.json)
binds review artifacts, analysis source, tables, fixed probes, and their vectors.
See the [weekly validation record](../../deliverables/week-03/validation/tests.json).

## Follow-up decisions for review

1. Use the approved context-recall amendment alongside the frozen source. Any further target, conflict, or N/A changes require renewed review and a new sealed version.
2. Improve extraction contract reliability, then compare raw and inspected scoring coverage explicitly. Keep this completed baseline unchanged.
3. Evaluate support judgments with evidence authority, contradiction, numbers, and identity tests; add bilingual negative labels before new calibration claims.
4. Review HTD alias coverage and structured-output reliability before a new frozen experiment. Do not add aliases retrospectively to improve these held-out results.
5. Obtain independent response assessment before treating technical qualitative judgments as human accuracy evidence. Use the Week 4 report to distinguish model limitations from measurement limitations.

The 80 new held-out cases have now been evaluated and inspected. If future
prompts, aliases, or scorers are selected using these failures, new untouched
scenario families are needed for a fresh held-out claim. Reusing this collection
can support a labeled diagnostic comparison, rather than a new untouched test.
