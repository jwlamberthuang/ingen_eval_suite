# Dataset v2 and extended scoring specification

Specification 0.1 | October 26, 2026 | Scoring contract reviewed for implementation

This reviewed specification defines dataset v2, model-visible inputs, structured
outputs, and scoring rules. The released collection contains 200 cases: the
100 existing dialogue cases and 100 additions. The new evaluation areas are
STUM spatial/temporal reasoning, SEOM entity recognition/classification, and
HTD-IRL task alignment. These are text-based capability tasks using separately
identified public model baselines.

**Status:** the scoring contract has been reviewed for implementation. The
[metric module and API](extended_metrics.md) implement the structured scoring
rules. The [schema and pilot workflow](dataset_v2_workflow.md) supplies the
2.0.0 release schema and approved 200-case collection, including the revised pilot
and 88 further additions. The [recorded results](W03_Extended_Evaluation_Results.md)
identify extraction, matching, and annotation limitations requiring review.
Illustrations within this specification remain hypothetical design examples;
they do not establish native-language authorship. Allocation targets guide
the full construction stage.

## 1. Scope and evaluation types

| `evaluation_type` | Task | Primary measurements |
| --- | --- | --- |
| `rag` | Answer a grounded Fari/Senpai dialogue query from supplied evidence. | Existing context recall, faithfulness proxy, and semantic relevance. |
| `stum_spatial` | Determine a requested spatial relation in a described scene. | Spatial accuracy. |
| `stum_temporal` | Determine relations between specified events. | Temporal coherence; pair accuracy and consistency reported alongside it. |
| `seom_entities` | Identify explicitly described scene entities and classify them. | Entity recall and classification accuracy; entity precision as a diagnostic. |
| `htd_task_alignment` | Propose goal-level tasks fulfilling a human request. | Goal coverage and goal precision. |

The structured tasks assess reasoning from text and compliance with a declared
answer format. They do not measure image perception, physical execution, learned
reward recovery, or performance of an unavailable internal endpoint. AMDC and
CRL-MRS remain outside the hands-on expansion.

The notebook will demonstrate 5–10 cases per extended capability selected from
the collection. Selection occurs after scoring is frozen; presentation examples
must not become an additional tuning set.

## 2. Proposed allocation: exactly 100 additions

Allocation groups are disjoint accounting buckets. Evaluation types and edge
tags describe the task and may overlap those buckets. Count unique case IDs.

| Allocation group | New cases | EN | ZH | Calibration target | Fresh held-out target |
| --- | ---: | ---: | ---: | ---: | ---: |
| Hard RAG: hallucination and out-of-domain probes | 20 | 13 | 7 | 4 | 16 |
| STUM: 10 spatial and 5 temporal | 15 | 10 | 5 | 3 | 12 |
| SEOM: entity recognition and classification | 15 | 10 | 5 | 3 | 12 |
| HTD-IRL: task alignment | 15 | 10 | 5 | 3 | 12 |
| Adversarial RAG metric-boundary probes | 10 | 6 | 4 | 2 | 8 |
| Additional targeted RAG dialogue | 25 | 16 | 9 | 5 | 20 |
| **Total additions** | **100** | **65** | **35** | **20** | **80** |

This gives 155 RAG cases, 10 spatial cases, 5 temporal cases, 15 entity cases,
and 15 task-alignment cases across v2. The additional 25 cases close the gap
between the specified addition groups and the 200-case collection target.
They target arithmetic, prerequisites, entity/identity relations, source authority,
clarification, and other documented dialogue weaknesses. The 20 Hard cases must
include both hallucination and out-of-domain probes, regardless of their observed
frequency in the earlier run.

Proposed new domain totals retain the established mix: 40 Fari EN, 20 Fari ZH,
25 Senpai EN, and 15 Senpai ZH. Full v2 totals would be 80/40/50/30 respectively,
or 130 EN and 70 ZH. Proposed new difficulty targets are 20 Easy, 40 Medium,
and 40 Hard; full totals would be 60/80/60. These are design targets, not external
quotas. Apply the existing tier criteria honestly and rebalance construction
rather than relabeling a case to fit a target.

The ten adversarial records retain correct ideal dialogue answers and separately
store hidden `metric_probes`: a candidate response, its atomic claims/support
labels, the targeted property, a hand-justified ideal-property score, and a
rationale. These are fixed scorer challenges, not recorded model generations.
For example, an unsupported detail can require a low factual-support score while
remaining highly relevant. Do not prescribe an invented embedding cosine or
require every metric to be low. Report probe results separately from generation.

## 3. Versioning, record shape, and information boundaries

Keep the v1 dataset, pilot, schema, configuration, manifests, and Week 2 results
unchanged. The proposed output is `data/W01_Evaluation_Dataset_v2.jsonl` with its
own schema, manifest, construction configuration, and review snapshot. The current
pilot is also retained separately. All 100 new references and 35 new Chinese
native authorship/reworking and review attestations are recorded for release 2.0.0.

### Legacy records

Copy the original 100 JSONL records unchanged, preserving their original line
bytes, IDs, annotations, and order. A v2 reader validates these against the frozen
v1 schema and treats them as `rag`. Their original lack of an `evaluation_type`
field is an explicit compatibility rule, not permission to omit it on new cases.
The new schema must distinguish the legacy branch from the new-record branch.
The original validator must never be silently repurposed for structured records.
The legacy branch is restricted to the original 100 IDs and verified source
lines; omitting a type cannot turn a new record into an accepted legacy case.

### New records

Use the following common contract, with a typed reference for each task:

| Field | Meaning | Visible to generation? |
| --- | --- | --- |
| `id` | Stable unique ID, proposed prefix `w03-`; never reuse an old ID. | No. |
| `schema_version` | `2.0.0` for the released additions; the earlier drafting contract used `2.0.0-draft.1`. | No. |
| `evaluation_type` | One value from Section 1; selects the task adapter. | Yes, as a task instruction. |
| `domain`, `language`, `difficulty` | Existing platform/language domains; `en`/`zh`; established tiers. | Platform and requested language only; no difficulty label. |
| `query`, `context` | Natural user query and ordered evidence passages. | Yes. |
| `input_metadata` | Optional visible history, learner profile, or explicit current-user identity. | Yes, through an allowlist. |
| `task_input` | Asked relation/pairs, generic class/action vocabulary, answer-format instructions. | Yes. |
| `reference` | Typed correct answer, supporting facts/relations, accepted aliases, or goal templates. | No. |
| `annotations` | Family, allocation group, subset, tags, tier rationale, provenance, review state. | No. |
| `construction_notes` | Design rationale and intended failure probe. | No. |

New RAG references preserve the existing ideal-response, required-fact, evidence,
behavior, and rubric semantics. A tested adapter can supply the existing metric
functions with their expected inputs; a RAG scorer must not receive spatial,
entity, or task-alignment records by accident. Legacy/new dispatch and lossless
legacy copying are implementation acceptance checks.

New evidence and visible event descriptions use explicit names, `user`/`用户`,
or specific object and event names. Personal pronouns belong in natural user
queries and expected dialogue answers; evidence must not depend on speaker
identity to resolve an actor. The frozen legacy cohort retains its original
wording. See the [evidence convention and checks](dataset_v2_workflow.md#explicit-evidence-referents).

New structured references additionally contain evidence indices and a reviewed
derivation for each answer or goal. Scene/event names must be unambiguous. A
reference with contradictory annotations, overlapping alias identities, or an
answer not established by visible inputs is quarantined until corrected.

Input histories must contain only supplied conversation. Public/original source
eligibility and actual review status remain required. Explicit identity links
belong in visible metadata when an answer depends on them; a hidden reference
cannot establish who the current user is.

## 4. STUM: begin with spatial reasoning

### Spatial task and output

The initial scope is a scene-fixed two-dimensional frame with a requested
horizontal or vertical axis. The query names the subject and reference object.
`task_input` repeats those names, the axis, the frame, and the response contract.
The relation vocabulary is `left_of`, `right_of`, `above`, `below`, `aligned`,
`unknown`, and `conflict`. `aligned` means equality on the requested axis.
No observer rotation, distance, physical geometry, or cross-axis inference is implied.

Hypothetical context: the cup is left of the plate; the plate is left of the bowl.
Query: where is the cup relative to the bowl on the horizontal axis?

```json
{"relation": "left_of"}
```

Hidden annotations encode the stated constraints and the derivation. Strict
relations are transitive on the same axis; equality permits substitution. With
a consistent relevant constraint component, return the uniquely entailed relation,
or `unknown` if no unique relation is established. Return `conflict` if a
constraint component containing either queried object on the requested axis is
inconsistent. An unrelated contradiction elsewhere must not change the target
answer. Spatial cycles and strict inequalities within an equality class are
inconsistent.

**Spatial accuracy** is 1 when the predicted relation equals the reviewed target,
otherwise 0. This includes correct `unknown` and `conflict` judgments. Report
resolved-relation and abstention/conflict subsets separately so a high score
does not conceal weak relation reasoning. A syntactically valid unknown symbol
or a relation for the wrong axis is an incorrect answer.

### Temporal task and output

Events are instants with visible stable identifiers. Scene descriptions establish
`before`, `after`, and `simultaneous` constraints. `task_input` lists one or more
requested pairs, each with a `pair_id`, `event_a`, and `event_b`. Answers are
relative to `event_a` versus `event_b`; `unknown` and `conflict` follow the same
evidence policy as spatial tasks.

```json
{"relations": [{"pair_id": "q1", "relation": "before"}, {"pair_id": "q2", "relation": "after"}]}
```

**Temporal pair accuracy** is correct requested pairs divided by all requested
pairs. A missing pair receives no credit. Duplicate identical pair answers collapse;
conflicting answers to one pair receive no credit and fail consistency. Unexpected
pair IDs are reported as extra assertions and prevent strict task success.

**Temporal consistency** is 1 if the asserted strict-order graph is acyclic after
merging simultaneous events, and no pair has contradictory labels; otherwise 0.
`unknown`/`conflict` answers add no ordering edge. **Temporal coherence** is pair
accuracy multiplied by consistency. This measures correct, mutually consistent
answers to the specified pairs; it does not assess unrestricted narrative coherence.
Both components must be reported alongside the product.

## 5. SEOM: entities and classes

Identify entities explicitly mentioned as present in the scene. Do not infer
unmentioned objects from typical room contents. The visible generic ontology is
proposed as `person`, `robot`, `animal`, `furniture`, `mobility_aid`, `container`,
`device`, `document`, and `other`; construction must make the correct class
unambiguous. The ontology is a benchmark choice and requires review.
Individually counted entities must have distinguishable visible descriptions;
an unresolved plural group cannot supply several hidden individual identities.

```json
{"entities": [{"mention": "Nora", "class": "person"}, {"mention": "blue chair", "class": "furniture"}]}
```

The hidden reference assigns canonical entity IDs, accepted scene-grounded aliases,
one class per entity, and supporting evidence. The model receives scene text and
the generic ontology, not the answer inventory or hidden entity IDs. Mention
matching uses Unicode NFC, case folding, whitespace normalization, and explicitly
reviewed aliases. Do not remove negation/numbers, invent translations, or apply
embedding similarity as an unreviewed alias fallback.

Let G be the gold entities, P the distinct predicted entity identities, and R the
gold identities recognized through accepted mentions:

- **Entity recall:** |R| / |G|.
- **Classification accuracy:** gold entities with exactly the correct predicted
  class divided by |G|. Missing entities count as incorrect, so this is a joint
  recognition-and-classification accuracy. A matched-entities-only diagnostic
  may be added but must have a different name and denominator.
- **Entity precision, diagnostic:** recognized identities divided by |P|.

Exact duplicate assertions collapse. Aliases resolving to one gold identity do
not create extra credit. Unknown mentions count as extra entities. Conflicting
classes for one identity retain recognition credit but receive no classification
credit. Unknown class strings are incorrect classifications. Extra entities
reduce precision and prevent strict task success; recall alone cannot penalize them.

## 6. HTD-IRL: explicit goals and proposed tasks

Use a structured rubric for finite, explicit human goals. The model proposes
ordered goal-level tasks using a visible generic action vocabulary and argument
schema. The drafting vocabulary is `deliver_item(item, recipient)`,
`notify(recipient, topic)`, `move_item(item, destination)`, `open_window(location)`,
and `close_door(location)`, fixed in the [construction configuration](../../configs/dataset-v2.json). Detailed
grasp/motion planning, implied household preferences, and latent-goal inference
are outside this first contract.

For a hypothetical request to bring water and notify the caregiver:

```json
{"tasks": [{"action": "deliver_item", "arguments": {"item": "water", "recipient": "current_user"}}, {"action": "open_window", "arguments": {"location": "living_room"}}]}
```

The second action is an illustrative prediction error, not an accepted reference.
Gold goals are atomic, nonredundant task specifications with mandatory arguments,
accepted equivalent templates, constraints, evidence, and any explicit precedence.
One goal-level task can match at most one goal. The output contains actions and
arguments, not self-declared gold goal IDs or assertions that it is aligned.

An action matches only if its action and all required arguments satisfy one
reviewed template; invented qualifiers or omitted essential slots do not match.
Allowed normalization is explicit, including approved argument aliases and unit
equivalences. Do not infer user identity or add unstated prerequisite tasks.

Deduplicate identical action/argument assertions, preserving the first position.
Find the largest one-to-one matching between proposed tasks and gold goals that
satisfies the recorded precedence constraints. A dependent goal can match only
when its required predecessor is matched earlier. Let its size be M:

- **Goal coverage:** M / number of gold goals.
- **Goal precision:** M / number of distinct proposed tasks.

The illustration has coverage 1/2 and precision 1/2. An unrequested task remains
in the precision denominator even if it sounds helpful. A redundant extra goal
in the reference is an annotation problem to fix before scoring. These metrics
measure explicit goal/task matching under a reviewed rubric, not an internal
reward function or successful execution.

## 7. Parsing, empty sets, errors, and reporting

Structured answers must be one JSON object with the specified keys and types.
Allow surrounding whitespace and one enclosing JSON Markdown fence; log that
normalization. Reject prose outside the object, extra top-level keys, missing
required fields, and wrong types. Do not convert a bare array or repair an answer
silently. String values outside the declared vocabulary are content errors that
can be scored as incorrect. RAG continues to use natural dialogue text.

Every case has an **end-to-end task-success** result separate from its metric
values. It is 1 only for valid output satisfying the full answer contract: the
correct spatial relation; all temporal answers correct with consistency and no
extra pairs; exact entity/class inventory; or complete goal coverage with no
extra tasks and satisfied constraints. For RAG, use a separately inspected
behavior verdict, never infer success from a high embedding score.

| Situation | Metric handling | Task-success handling |
| --- | --- | --- |
| Valid wrong answer | Compute the defined values, including zero. | 0. |
| Valid empty entity/task list with nonempty gold | Recall/coverage/classification are 0; precision is 0 by declared empty-output convention. | 0. |
| Empty gold inventory | Recall/coverage/classification denominators are undefined: null, `not_applicable`. Nonempty predicted inventory has precision 0; both empty gives null precision. | 1 only for the valid expected empty output. |
| Missing, empty-text, or malformed model output | Null with distinct missing/format status; never silently omit its attempt. | 0, including recorded generation failure. |
| Scorer failure | Null with `scorer_error`; computation must be investigated. | Unknown if it cannot be established; never fabricate a verdict. |
| Invalid or unresolved reference annotation | Quarantine before model evaluation. | No model verdict assigned. |

A temporal record must ask at least one pair; a spatial record must have one
reviewed target. Task-specific empty references require an explicitly reviewed
empty-inventory/no-task scenario rather than missing annotations.

Report attempted cases, parse coverage, all status counts, strict task-success
counts, and per-metric defined denominators. Metric means and population SD use
defined values only and must be presented alongside coverage and task success.
Do not promote a conditional mean after excluding format failures as overall
pipeline accuracy. Report per type, domain, language, difficulty, cohort, and
relevant edge tags; do not average unrelated metric scales into a composite.

## 8. Calibration, families, language, and review

The original 20 calibration cases remain legacy calibration. The original 80
held-out cases are now a previously evaluated legacy cohort. Preserve their
historical split labels and frozen results, but do not present repeated use as
fresh held-out evidence after refinement against known failures.

The new 20/80 split is a proposal. Allocate whole scenario families before model
evaluation. Translations, paraphrases, context variants, and repairs of an old
scenario remain in its family; they cannot create fresh held-out cases or pad
the 100 genuinely new scenario records. Corrections to old identity examples
belong in separately versioned variants, not silent edits to the copied records.
If exact quota targets conflict with family integrity, preserve the family and
review the allocation before freezing. Record the selection algorithm, seed,
actual counts, and IDs in the future v2 construction configuration.

Only calibration cases and declared development fixtures can inform global
normalization, automatic alias-matching rules, parser changes, support thresholds,
or model selection. Case-specific reference aliases may be authored and reviewed
for every cohort before freezing, as ground-truth annotation. Do not expand a
held-out alias list after seeing its predictions without a new version and
disclosure. Freeze the scoring choices before fresh held-out generations.
Deterministic structured
metrics introduce no similarity threshold; acceptance thresholds remain unset
until supported by a reviewed criterion. Do not inherit 0.80 into the new metrics.

For new RAG support calibration, deliberately include unsupported entities,
quantities, negation, conflicts, and joint-evidence probes. Record supported and
unsupported counts and confusion matrices; sparse negatives must remain an
explicit limitation. A revised faithfulness method is a new scorer/run, not a
retroactive replacement for the Week 2 score file.

EN and ZH use the same structured keys and canonical class/action/relation symbols.
Narrative queries, evidence, and RAG answers remain natural in their language.
Chinese aliases and wording require native authorship/review. Mixed queries
retain Chinese syntax with occasional English content words. Structured symbol
scoring does not establish natural spoken response quality; review any prose
explanation or register separately.

New records start in `draft`. Record actual author/reviewer identities, review
dates, native-language status, and the reviewed content hash. New Chinese cases
need native authorship and review; approval of the original 35 does not transfer.
Do not mark machine-created drafts as natively authored by the reviewer. Freeze
release approval only after content, derivations, language, family, source,
schema, and collection checks pass. No independent annotation agreement is assumed.

## 9. Hand-worked design checks for later implementation

These are illustrative expectations, not constructed dataset records or empirical
model results. They should become verified metric fixtures before metric use.

| Check | Expected result |
| --- | --- |
| Cup left of plate; plate left of bowl; predict cup left of bowl. | Spatial accuracy 1. |
| Only cup left of plate is known; bowl relation unconstrained; predict `unknown`. | Spatial accuracy 1; a guessed `left_of` scores 0. |
| Cup left of plate and plate left of cup; answer `conflict` for that component. | Spatial accuracy 1. |
| Gold order a<b<c. For (a,b), (a,c), (b,c), predict before, before, simultaneous. | Pair accuracy 2/3; consistency 1; temporal coherence 2/3. |
| Same gold, but predict a<b, b<c, and c<a. | Pair accuracy 2/3; consistency 0; temporal coherence 0. |
| Three gold entities; predict two with correct classes plus one invented entity. | Recall 2/3; classification accuracy 2/3; entity precision 2/3; task success 0. |
| Gold tasks: water delivery and caregiver notification; predict water delivery and opening a window. | Goal coverage 1/2; goal precision 1/2; task success 0. |
| Repeat an identical correct entity or task assertion. | No additional credit or denominator inflation. |
| Return malformed JSON. | Format status; core values null; task success 0. |

## 10. Implementation decisions and next stage

The reviewed specification establishes these implementation choices:

1. The 100-case allocation, including 55 new RAG cases, language/domain targets,
   difficulty targets, and the proposed 20/80 fresh split.
2. Strict structured outputs, the limited spatial/action/class vocabularies,
   and the explicit treatment of missing or conflicting evidence.
3. Temporal coherence as pair correctness gated by consistency; classification
   accuracy including missed entities; explicit-goal matching and precedence.
4. Lossless legacy compatibility and separate new-record validation, rather than
   modifying the accepted v1 schema or reclassifying old results as fresh.

The structured parser, metrics, reference checks, and hand-worked tests are
implemented in the [extended metric module](../../src/extended_evaluator.py).
Versioned [schema/validation tooling and a review pilot](dataset_v2_workflow.md)
are supplied. The 200-case collection is approved and released under schema 2.0.0.
The frozen [formal protocol](W03_Evaluation_Protocol.md) covers per-metric range,
monotonicity, calibration, language, and approximation gaps. The
[model-run analysis](W03_Extended_Evaluation_Results.md) identifies a gap between
some new required-fact annotations and the canonical requested-fact interpretation
of context recall. The separately versioned
[approved 2.0.1 annotation amendment](../../data/annotations/W03_Context_Recall_v2.0.1.json)
addresses this gap for 17 of the 55 audited new RAG cases. All 17 corrections,
including revised Chinese annotation wording, passed intern review; the approval
binds their exact content. Missing answer targets remain unresolved instead of acquiring
invented values. The [correction review sheet](context_recall_correction.md)
records every change. The source collection, approvals, and completed experiment
remain frozen; the combined scoring view is not a new approved dataset release.

## Related suite documents

- [Original dataset specification](../dataset_specification.md)
- [Frozen v1 schema](../../schemas/w01_dialogue_case.schema.json)
- [Dataset documentation](../../data/dataset_documentation.md)
- [Week 2 metric methodology](../week-02/metric_methodology.md)
- [Week 2 findings and limitations](../week-02/W02_RAG_Evaluation_Results.md)
