# Week 3 Evaluation Protocol

Version 1.0 | October 27 2026 | Frozen evaluation methodology

This protocol defines how ingen_eval_suite measures grounded dialogue, spatial
and temporal reasoning, entity recognition, and alignment with requested tasks.
Use the metric definitions together with their coverage and error counts. A high
score establishes only the stated property under the supplied annotations.

The structured metrics and experiment pipeline are implemented and tested. Dataset
release 2.0.0 contains 200 cases. Content/reference review of all 100 additions and
native authorship or substantive native reworking and review of all 35 new Chinese
cases were confirmed on October 27 2026. This protocol is frozen before generation.
Execution status, model outputs, analysis, and the notebook are recorded separately
through the [Week 3 review package](../../deliverables/week-03/README.md).

## Scope and cohorts

The suite contains 155 RAG cases, 10 spatial cases, 5 temporal cases, 15 entity
cases, and 15 task-alignment cases. STUM, SEOM, and HTD-IRL are the assigned task
labels. Text scene reasoning does not establish visual perception, reward
learning, physical execution, or performance of unavailable internal systems.
AMDC and CRL-MRS retain future-work scope.

Preserve the original 100 records and the Week 2 experiment. The 100 additions
have 20 calibration families and 80 held-out families, with 65 English and 35
Chinese cases. The previously inspected original cohort is historical regression
evidence; it is not newly untouched held-out evidence. Annotation review before
freezing is separate from using model errors to tune a scorer or prompt.

## Evidence and information boundaries

New evidence and visible event descriptions use an explicit name, `user`,
`用户`, or a specific object or event. Personal pronouns remain appropriate in
queries and expected dialogue answers. Evidence must not depend on whether the
reader is the robot or user. A lexical validator checks common personal pronouns;
human review checks actual meaning. Frozen legacy wording is exempt.

Generation receives only platform, requested language, query, numbered evidence,
allowlisted history, learner information, current-user identity, and task inputs.
Hidden references, aliases, constraints, goals, review notes, split labels, and
probes must never enter the generation prompt. Use only the generic class/action
menu and requested relation or event descriptions from `task_input`.

<!-- pagebreak -->

## Context recall and lexical recall

**Context recall definition.** Let F be the canonical required facts and S the
facts annotated `context_support="supported"` in the supplied context.
`context_recall = |S| / |F|`. Unsupported and conflicting facts remain in F and
receive no support credit. With no required facts the score is null with status
`not_applicable`. Positive support with empty context is invalid.

**Range and interpretation.** The defined range is [0, 1]. Zero means no required
fact is supported; one means all are supported. Increasing supported facts while
holding F fixed cannot lower recall. This is an evidence-sufficiency measure,
independent of the generated response. It cannot establish answer correctness,
retriever ranking quality, or whether a model used the evidence.

**Failure example.** If the required facts are a meeting time and a room, but
only the time is supplied, recall is 1/2 even when the ideal answer correctly
asks for the room. Removing the room from F would falsely turn missing evidence
into perfect recall. A wrong model answer can still accompany recall of one.

**Calibration and languages.** No numeric threshold is fitted. Reviewers check
the canonical facts, support labels, conflict policy, passage links, and arithmetic
derivations. Equivalent EN/ZH facts follow the same counting rule; fact granularity
must be reviewed because splitting one proposition changes the denominator.
Native Chinese review is required for new Chinese references.

**Lexical reference recall definition.** Let T be the unique tokens of the ideal
response and C the unique tokens of all evidence. `lexical_recall = |T ∩ C| / |T|`.
An empty T is `not_applicable`. Defined values lie in [0, 1]. With fixed T,
adding matching evidence tokens cannot reduce recall.

**Limits and calibration.** Lexical recall is a supplementary diagnostic with no
acceptance threshold. The reference answer and the evidence can express the same
fact with different words, time formats, calculations, or a clarification. Adding
irrelevant text containing the answer words can raise recall without supplying
the fact. Therefore it must not replace context recall or become a pass criterion.

English uses the retained lowercase NFC regular-expression tokenizer. Chinese
and Chinese sentences with English content words use the retained jieba tokenizer.
Unique-token recall does not correct for segmentation, synonyms, or length, so
EN/ZH means should not be interpreted as a language ranking. Implementations are
in [the retained RAG module](../../src/evaluator.py).

<!-- pagebreak -->

## Faithfulness proxy

**Definition.** Extract atomic factual claims from the unmodified model response.
For each claim c, split evidence into punctuation-based segments and compute
`s(c) = max cosine(E_query(c), E_passage(segment))`. Mark c supported by the proxy
when `s(c) >= tau`. The score is passing claims divided by extracted claims.
With no evidence each nonempty claim fails support. With no factual claims the
ratio is null with status `not_applicable`; it is not perfect faithfulness.

**Range and monotonicity.** Defined scores lie in [0, 1]. With a fixed claim list,
encoder, threshold, and evidence segmentation, increasing a claim similarity
through the threshold cannot lower the score. Adding a passing claim may raise
the mean; adding a failing claim lowers it. Changes to extraction change the
denominator, so scores are not monotonic in response length or answer quality.

**Approximation gap.** Embedding similarity measures retrieval association, not
logical entailment. A segment can mention the correct topic while omitting the
claimed number, room, person, or prerequisite. Maximum single-segment retrieval
can accept one side of an unresolved conflict. The metric does not establish
numerical correctness, causal validity, instruction compliance, or completeness.

**Recorded counterexamples.** The Week 2 calibration accepted an unsupported room
claim at cosine 0.8653 and a time claim under unresolved conflict at 0.9267.
The selected threshold was 0.80. Raising the threshold to 0.90 rejected 23 of 27
supported calibration facts. These observations motivate separate failure review;
they do not justify retuning against the original held-out cases. See the
[recorded results and calibration](../week-02/W02_RAG_Evaluation_Results.md).

**Claim review.** Retain raw extraction output, parsing failures, and separately
identified inspected corrections. Check that each extracted claim corresponds
to the response, preserves names, numbers, negation and conditions, and does not
silently repair the answer. Missing or invalid extraction is `scorer_error`.
Raw Week 2 extraction needed 99 inspected corrections across 100 responses;
that dependence must remain visible in any comparison.

**Language handling.** The retained multilingual E5 base encoder uses `query: `
for claims and `passage: ` for evidence. Inspect claim correspondence separately
in EN and ZH, including mixed Chinese sentences and English content words.
Embedding proximity does not authorize translation or infer missing user identity.
The evidence convention and explicit current-user metadata reduce referent
ambiguity without resolving unsupported claims automatically.

<!-- pagebreak -->

## Semantic relevance and calibration

**Semantic relevance definition.** Compute raw cosine between query and response
embeddings, using `query: ` for both. The defined range is [-1, 1]; it is not
rescaled to a probability. An empty response has null value and `empty_response`
status. Invalid, zero-norm, non-finite, or incompatible vectors are errors.

Higher cosine means stronger association in the selected embedding space under
fixed preprocessing. It does not guarantee greater factuality, empathy, usefulness,
or task compliance. Repeating the question or giving a fluent wrong answer about
the same subject can score highly. A necessary clarification can be less similar
than an unsupported direct answer. No universal pass threshold is defined.

Use the same retained encoder, normalization, token limits, and prefixes for EN
and ZH. Report language groups with their counts and content mix. The same encoder
does not establish equal calibration or measurement invariance across languages.
Reject over-limit inputs rather than silently truncating evidence.

## Calibration decisions before generation

For a historical comparability run, retain the recorded Week 2 support threshold
0.80, encoder revision, segmenter, and scoring code. Describe this as a transferred
threshold whose validity on new cases is unestablished. Report the new calibration
probe results without selecting a different threshold from held-out predictions.

For a revised support experiment, declare a new configuration before held-out
generation. Review positive and negative atomic support statements only from the
new calibration families. Choose tau from [0.50, 0.60, 0.70, 0.80, 0.90] by maximum
balanced accuracy `(TPR + TNR) / 2`, breaking ties toward the larger threshold.
Both classes are required; with one class missing, stop calibration. Record every
candidate, support counts, confusion matrices, and selection inputs.

The optional new fit uses annotated reference facts and fixed probe claims from
new calibration families only. Current labels contain 17 positives and 2 negatives;
both negatives are English probe claims. Chinese labels are all positive. Report
these counts and label sources; no language-specific threshold is justified.

The old calibration used 27 positives and 3 negatives and achieved balanced
accuracy 2/3. It supplies no reliable subgroup threshold. Do not invent a language
threshold or a model acceptance target from these sparse observations. Report
per-language diagnostics only where both label classes are represented.

Structured scores use exact declared matching rules rather than fitted numeric
thresholds. Calibration checks reference truth, aliases, units, empty-set intent,
action slots, event ordering, parser behavior, and hand-worked examples. Global
rule changes use calibration fixtures and require a new version. A score of one
is computational task success under the reference, not a deployment standard.

<!-- pagebreak -->

## Spatial accuracy and temporal coherence

**Spatial accuracy.** On the requested horizontal or vertical axis, merge aligned
objects and derive strict-order reachability in the scene-fixed 2D frame. The
reference answer must agree with the derived relation. A relevant inconsistent
component gives `conflict`; a consistent disconnected pair gives `unknown`.
An unrelated inconsistent component does not determine the requested answer.
`spatial_accuracy = 1` for the exact derived relation and 0 otherwise.

The range is {0, 1}. Replacing a wrong relation with the reference increases the
score. The metric does not grade an explanation, distance, viewpoint changes,
or physical perception. Always predicting `unknown` can look good in a skewed
collection; report resolved-relation and abstention/conflict counts. Calibrate
reference graphs and coordinate conventions, not a learned cutoff.

For example, A left of B and B left of C entails A left of C. With no connecting
path, a left/right guess is wrong even when plausible. Scene evidence must be
reviewed against its symbolic graph; internal graph consistency alone cannot
prove that the graph faithfully represents the text.

**Temporal pair accuracy.** For Q requested event pairs, a pair is correct only
when its predicted label set equals the single derived answer.
`A = correct_requested_pairs / Q`, with Q > 0. Missing pairs receive no credit;
identical duplicates collapse and contradictory labels are incorrect.

**Temporal consistency.** Let C = 1 if predictions contain no contradictory
labels or strict-order cycle after simultaneous-event merging, and 0 otherwise.
Only known pair IDs supply graph edges. `temporal_coherence = A * C`.
Pair accuracy and coherence lie in [0, 1]; consistency lies in {0, 1}.

With fixed consistent predictions, correcting a pair raises or preserves A.
Creating a cycle can set coherence to zero even while pair accuracy increases.
Consistency alone can be one for an empty or entirely wrong acyclic answer.
Extra pair IDs may leave A and C unchanged but prevent strict task success.
For gold A before B, an empty relations list has A = 0, C = 1, coherence = 0.

Reference precedence, equality, conflict and unknown cases need hand checks.
Canonical relation labels and event IDs are language-independent. English and
Chinese scene wording, actor names, scope, and temporal expressions still require
language review. Visible event descriptions must identify actors explicitly.
See [the structured metric API](extended_metrics.md) and
[verified fixtures](../../tests/test_extended.py).

<!-- pagebreak -->

## Entity recall and classification

Let G be the number of annotated scene entities, R the number of recognized gold
identities, K the number recognized with exactly the correct class, and P the
number of distinct predicted identities. Define `entity_recall = R / G`,
`classification_accuracy = K / G`, and diagnostic `entity_precision = R / P`.
Omissions count as classification failures; accuracy is not conditional on recall.

The nine classes are person, robot, animal, furniture, mobility_aid, container,
device, document, and other. Match mentions through explicit reference aliases
after NFC, case folding, and whitespace normalization. Do not infer translation,
stemming, punctuation equivalence, or an unseen name. A hidden entity ID is not
automatically an accepted mention. Ambiguous aliases invalidate the reference.

Exact duplicate assertions and aliases for one identity do not multiply recall.
Conflicting classes for one identity receive no classification credit. Unknown
mentions are distinct extra identities, reduce precision, and prevent strict
success. These declared counts are entity-level; they are not object detection
accuracy, segmentation quality, or mention-level coreference evaluation.

**Ranges and monotonicity.** Defined ratios lie in [0, 1]. With fixed gold, adding
a new correctly identified entity cannot reduce recall. Giving its sole correct
class increases or preserves classification accuracy. Adding a conflicting class
can lower accuracy. An invented entity leaves recall and classification unchanged
while lowering precision. Removing false positives can improve precision without
recovering an omitted entity. Read all three measures together.

**Hand-worked failure.** Gold contains Nora as person and a chair as furniture.
Predicting both correctly plus an unsupported cat gives recall 1, classification
accuracy 1, precision 2/3, and strict success 0. Predicting only Nora gives recall
1/2, classification accuracy 1/2, and precision 1. Neither recall nor precision
alone captures both omissions and hallucinated objects.

**Empty cases.** An intentionally empty scene requires `entities=[]` and
`empty_inventory_expected=true`. Both sets empty yield null ratios and strict
success 1. Empty prediction with nonempty gold yields recall, classification,
and precision 0 under the documented empty-output convention. An empty reference
without the explicit marker is quarantined.

**Calibration and languages.** No fitted threshold is used. Review class choices,
entity boundaries, accepted EN/ZH names and mixed-language mentions, and alias
collisions on calibration fixtures. Canonical labels remain English in either
language. A valid unlisted synonym can receive zero credit; flag that approximation
for separate annotation review rather than repairing a scored prediction.

<!-- pagebreak -->

## Goal coverage and goal precision

Represent gold goals as independent IDs with accepted action templates and any
predecessor goals. The generic action catalog is `deliver_item(item, recipient)`,
`notify(recipient, topic)`, `move_item(item, destination)`,
`open_window(location)`, and `close_door(location)`. Arguments are strings.
These symbols do not establish that a product can execute the actions.

Normalize argument values using NFC, case folding, whitespace, and explicit
field-specific aliases. Action and slot names retain canonical spelling. Every
required argument must match a template; additional qualifiers or slots do not
match. Do not infer quantities, unit conversions, translations, or user identity
from a hidden reference. Identity needed for a first-person request must be visible.

Deduplicate equivalent predicted tasks, preserving the first original position.
Find a maximum one-to-one assignment of those tasks to gold goals, requiring
each matched predecessor to occur earlier. The implemented exact dynamic program
avoids a greedy choice that consumes another goal's only matching task.

Let M be matched goals, G gold goals, and P distinct predicted tasks.
`goal_coverage = M / G`; `goal_precision = M / P`. Defined ratios lie in [0, 1].
With gold and prediction count fixed, a larger valid M raises both. Adding a
matched task can raise coverage and precision; adding an unmatched task lowers
precision. Reordering or duplicating a task is not guaranteed to preserve M,
because dependencies and the first-occurrence rule matter.

**Hand-worked failure.** Gold requests water delivery and caregiver notification
with no required order. Predicting water delivery and an unrequested window
opening yields M = 1, G = 2, P = 2: both ratios are 1/2. Predicting both requested
tasks plus window opening gives coverage 1, precision 2/3, and strict success 0.
Reversing a required delivery-before-notification order leaves at most one match.

**Limits.** Matching measures conformity to a finite annotated plan. It does not
recover preferences or rewards, establish safety, measure execution, or reward
a useful alternative absent from the accepted templates. Goal granularity and
overlapping templates affect denominators. Exact matching has exponential state
growth in G; the current small goal sets do not establish scalability to long plans.

No-task gold requires an explicit empty marker. Both lists empty yield null
ratios and strict success 1. Empty predictions against nonempty gold give both
ratios 0. Calibrate dependencies, aliases, slot meaning, and independent goals
through hand checks. EN/ZH matching uses declared aliases, not automatic bilingual
equivalence; a door name must not become a window's location alias.

<!-- pagebreak -->

## Output validity and reporting

Structured predictions must be one JSON object with the task's exact keys and
types. Surrounding whitespace and one JSON fence are accepted and logged.
Prose wrappers, extra keys, duplicate JSON keys, bare arrays, and NaN/Infinity
are rejected. Unknown relation or class strings are scorable wrong content,
not automatically repaired. Preserve raw predictions and normalization logs.

Invalid references are quarantined with no model verdict. Missing, empty,
malformed, and generation-failed structured outputs have null core metrics and
strict task success 0. Scorer errors leave success unknown. Valid both-empty
entity/goal cases can succeed while ratio metrics remain undefined. Keep parsing,
generation, annotation, applicability, and computation statuses separate.

**Strict task success.** Spatial requires the exact relation. Temporal requires
every requested pair correct, consistency one, and no extra IDs. Entities require
all gold identities with exactly correct classes and no extras. Goals require
all goals matched in allowed order and no unmatched tasks. This is a separate
binary endpoint; it does not average the component ratios. RAG has no equivalent
automated correctness verdict; response review remains separate.

**Denominators.** For structured cases, report total, eligible, quarantined,
attempted, eligible attempted, and parsed counts. `parse_coverage = parsed /
eligible`, including missing outputs in the eligible denominator. For success,
report defined count, failures, unknowns, and mean over defined verdicts. Every
core metric reports its own defined count, statuses, mean, and population standard
deviation. Nulls are never silently replaced by zero or dropped without counts.

For example, one correct parsed spatial answer and one missing answer give
conditional spatial mean 1, parse coverage 1/2, and strict success mean 1/2.
This prevents an apparently perfect conditional mean from hiding missing output.
Both coverage and success lie in [0, 1]; coverage alone measures format availability,
and success alone remains limited by reference validity.

Report task type first, then domain, language, tier, cohort, and edge tags.
Overlapping tags are descriptive slices, not independent samples. Keep calibration,
new held-out, and legacy results separate. Report support counts with every
language comparison; the temporal sample is only five cases. Do not combine unlike
metric scales into a single overall quality score or imply statistical significance
from this small public collection.

RAG uses the retained status conventions, with evidence metrics computable even
when generation fails. Any unified Week 3 report needs a tested RAG adapter and
must preserve both the old RAG statuses and structured coverage denominators.

<!-- pagebreak -->

## Experiment procedure and review gates

1. Complete content/reference review and record native Chinese authorship and
   review for new Chinese examples. Reconcile Word edits into JSONL; verify
   evidence, visible identity, fact links, symbolic constraints, aliases, and goals.
2. Refresh both dataset manifests and validation reports. Require release
   validation and all tests to pass. Require a release-profile manifest and a
   reviewed release schema version. Freeze dataset, schema, prompts, parser,
   matching policy, encoder, calibration decision, and code hashes before evaluation.
3. Verify the implemented adapters and legacy/new RAG dispatch with the
   [pipeline checks](experiment_pipeline.md). Confirm that hidden fields cannot
   enter prompts. Validate token budgets and
   preserve complete rendered inputs. The existing Week 2 adapter is not a
   substitute for the new structured and current-user interfaces.
4. Register a separate Week 3 configuration and output directory. A proposed
   comparability baseline retains the pinned Qwen2.5 7B four-bit MLX model and
   multilingual E5 base configuration. Record actual revisions, packages, hardware,
   greedy settings, seed, token budgets, timeouts, and attempt policy.
5. Check calibration fixtures and claim correspondence. Freeze any revised
   thresholds or prompt/extraction rules before new held-out generation. Preserve
   every raw attempt and distinguish generation time from extraction/scoring time.
6. Generate once per declared case and score separately from generation. Inspect
   factual failures, empty or malformed outputs, unknown/conflict answers, aliases,
   duplicate/extra entities, slot errors, missing prerequisites, and task order.
   Keep any corrected annotations in a separately versioned review artifact.
7. Execute the notebook with 5–10 demonstrations per extended capability, selected
   under a recorded rule after scoring is frozen. Show aggregate results and
   failures, including denominators. Write the 300–500-word reflection from the
   observed analysis, then audit the weekly review package.

Dataset truth fixes before the freeze do not tune predictions that do not yet
exist. After held-out inspection, any prompt, alias-policy, extraction, threshold,
or annotation change requires a new experiment version; disclose exposure and
   do not present the revised cases as untouched evidence. Deterministic symbolic
scoring can replay exactly. A seed alone does not guarantee byte-identical local
model generation across hardware and runtime versions.

## Implementation and audit sources

- [Dataset specification](dataset_v2_specification.md), [review workflow](dataset_v2_workflow.md), and [construction configuration](../../configs/dataset-v2.json).
- [RAG methodology](../week-02/metric_methodology.md), [recorded calibration](../../results/week-02/baseline/calibration.json), and [baseline configuration](../../configs/week-02.json).
- [Structured implementation](../../src/extended_evaluator.py), [metric tests](../../tests/test_extended.py), and [dataset tests](../../tests/test_dataset_v2_collection.py).
- [Validation evidence](../../deliverables/week-03/README.md#validation-evidence). Validation confirms declared computational checks; it does not certify semantic truth or actual authorship.
