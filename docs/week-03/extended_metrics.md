# Extended metric implementation

Implementation version 0.1 | October 26, 2026

[extended_evaluator.py](../../src/extended_evaluator.py) implements the reviewed
[scoring specification](dataset_v2_specification.md) for four structured task
types. The functions use symbolic references and standard Python; no embeddings,
model weights, external API, or generation call is involved. The existing RAG
module and recorded experiment remain unchanged.

This is a metric implementation with synthetic test fixtures. It is not a
released v2 dataset, a full corpus validator, or measured model performance.
Reference checks establish computational consistency of the supplied annotations;
review must still establish that they accurately represent the natural-language
evidence and are suitable for public evaluation.

## Public API

| Function | Input | Result |
| --- | --- | --- |
| `parse_prediction(text, evaluation_type)` | Raw model response text and a supported type. | `ParsedPrediction(value, normalizations)`; raises `PredictionFormatError` on invalid structure. |
| `spatial_accuracy(prediction, reference, task_input)` | Parsed spatial answer, symbolic reference, visible query parameters. | One `MetricResult`. |
| `temporal_scores(prediction, reference, task_input)` | Parsed pair answers, event constraints, requested pairs. | Pair accuracy, consistency, and coherence results. |
| `entity_scores(prediction, reference)` | Parsed entities/classes and reviewed entity aliases. | Recall, joint classification accuracy, and precision results. |
| `goal_scores(prediction, reference)` | Parsed proposed tasks and explicit goal templates. | Goal coverage and precision results. |
| `score_extended_case(record, output)` | A structured case and raw response text or a generation record. | Scores, task success, parsing state, normalization log, and statuses. |
| `compute_extended_metrics(records, responses)` | Structured cases and outputs keyed by case ID. | Per-example results and grouped population summaries. |

Direct metric functions validate structure and symbolic reference consistency.
They raise `InvalidReference` for invalid annotations. Batch scoring quarantines
those cases instead of assigning a model failure. RAG must use its existing
evaluator separately; unsupported task types, duplicate case IDs, and unknown
response IDs are rejected.

## Strict prediction parsing

The parser accepts the four response objects in the specification. It permits
surrounding whitespace and one enclosing JSON Markdown fence, recording each
normalization. It rejects prose wrappers, bare arrays, extra keys, wrong types,
duplicate JSON object keys, and nonstandard NaN/Infinity constants. It does not
repair predictions or use the reference to rewrite their content.

String values outside the answer vocabulary remain scorable content errors.
For example, an unrecognized spatial relation is incorrect; an unrecognized entity
class earns no classification credit. Task argument values are strings under
this interface, including quantities. Any accepted unit equivalence must be an
explicit reference alias rather than an inferred conversion.

## Spatial reference interface

`task_input` requires `subject`, `reference`, `axis`, and
`coordinate_frame="scene_fixed_2d"`. The axis is `horizontal` or `vertical`.
The reference has a `constraints` array and an `answer`:

```json
{
  "constraints": [
    {"subject": "a", "relation": "left_of", "reference": "b", "axis": "horizontal"},
    {"subject": "b", "relation": "left_of", "reference": "c", "axis": "horizontal"}
  ],
  "answer": "left_of"
}
```

The graph merges aligned objects before deriving strict-order reachability.
Only the requested axis contributes. Any inconsistent component containing a
queried object gives `conflict`; unrelated inconsistent components do not affect
the answer. Consistent disconnected objects give `unknown`. A reference answer
that disagrees with this derivation is quarantined.

Minimal computational example, run from the project root:

```python
from src.extended_evaluator import spatial_accuracy

reference = {
    "constraints": [
        {"subject": "a", "relation": "left_of", "reference": "b", "axis": "horizontal"},
        {"subject": "b", "relation": "left_of", "reference": "c", "axis": "horizontal"},
    ],
    "answer": "left_of",
}
task_input = {"subject": "a", "reference": "c", "axis": "horizontal",
              "coordinate_frame": "scene_fixed_2d"}
assert spatial_accuracy({"relation": "left_of"}, reference, task_input).value == 1
```

## Temporal reference interface

`task_input.events` lists visible unique event IDs. `task_input.pairs` contains
objects with `pair_id`, `event_a`, and `event_b`. The reference contains
`constraints`, each with `event_a`, `event_b`, and `relation`, and an `answers`
object mapping every requested pair ID to its reviewed relation.

Reference constraints use `before`, `after`, or `simultaneous`. Derived answers
also permit `unknown` and `conflict`. Reference answers must match the graph
derivation. At least one requested pair is required.

The scorer separately returns `temporal_pair_accuracy`, `temporal_consistency`,
and their product `temporal_coherence`. Identical duplicate pair answers collapse.
Contradictory labels and cycles, including those exposed by simultaneous-event
merging, fail consistency. Missing pairs receive no correctness credit. Extra
pair IDs prevent strict task success and remain visible in details; their event
relations cannot be inferred from an unknown question ID.

## Entity reference interface

The reference has `entities`, each containing `entity_id`, `aliases`, and `class`.
Every entity needs an explicit accepted scene-grounded alias. Hidden entity IDs
are not automatically accepted mentions. Reference classes must belong to the
nine-class ontology declared in the specification and exported as `ENTITY_CLASSES`.

Alias matching applies only NFC, case folding, whitespace normalization, and
the supplied alias map. It preserves punctuation and numbers. An alias mapping
to multiple gold identities is invalid. Alias variants of one entity and exact
duplicate assertions do not inflate counts.

Classification accuracy divides correctly classified gold entities by all gold
entities, including omissions. Conflicting classes for one recognized identity
receive no classification credit. Extra entities reduce precision and prevent
strict task success even if recall and classification accuracy remain perfect.

An intentionally empty reference requires both `entities=[]` and
`empty_inventory_expected=true`. Empty references without that marker are
quarantined. Empty output against nonempty gold scores zero; both inventories
empty produce undefined ratio metrics and strict task success of one.

## Goal reference interface

The reference contains `goals`, each with a `goal_id`, nonempty `templates`, and
an optional `after` array of predecessor goal IDs. Templates have exactly the
same `action` and string-valued `arguments` structure as predicted tasks.
Predecessors must exist and form an acyclic graph. Identical normalized template
sets under different goal IDs are rejected as redundant annotations.

Optional `argument_aliases` map argument names to canonical-value/alias groups:

```json
{"recipient": {"caregiver": ["care giver"]}}
```

This object is the value of `reference.argument_aliases`. Canonical values and
aliases undergo the declared text normalization; ambiguous mappings are rejected.
Actions and argument names retain their canonical spelling. Missing arguments,
invented qualifiers, and unstated tasks do not match a goal template. The drafting action menu is fixed in the
[v2 construction configuration](../../configs/dataset-v2.json); full corpus review
and the release freeze remain pending.

The scorer deduplicates equivalent tasks while preserving their first original
position. An exact dynamic program finds a maximum one-to-one matching satisfying
the goal dependencies. It does not greedily consume an action that another goal
needs. This is intended for small finite goal sets; state growth is exponential
in the number of goals, so large unconstrained plans need a separate scalability
assessment. Matching details reference original prediction indices.

Goal coverage divides matched goals by all gold goals; goal precision divides
matches by distinct predicted tasks. A valid empty task list against nonempty
gold has both values zero. An intentional no-task reference uses `goals=[]` and
`empty_inventory_expected=true`; ratio metrics are undefined for two empty sets,
with strict task success of one. Partial overlap between different goals' accepted
templates is handled by one-to-one matching; review must still establish that
the underlying goals are independent and nonredundant.

## Case scoring and summaries

A case supplies `id`, `evaluation_type`, `domain`, `language`, `difficulty`,
`reference`, and `task_input`. Its `annotations` can supply `subset` and
`edge_case_tags`. These are computational fixtures/interfaces; full dataset
schema, review, source, and family validation are supplied by the separate
[v2 dataset tooling](dataset_v2_workflow.md).

An output is raw response text or `{"status":"ok","response":"..."}`.
A recorded generation failure uses `status="generation_error"`. An invalid
generation artifact is a scorer/input-contract error, rather than an invented
model failure. Omitting a case's output differs from a recorded failed attempt.

Missing, empty, malformed, and generation-failed outputs have null core metrics
and end-to-end task success zero. A computation failure leaves success unknown.
Invalid references are quarantined, with no model verdict. Parsing state remains
independent of scoring state, so a later scorer error does not erase successful
parsing coverage. No result requires altering the original prediction.

Summaries provide `n_total`, `n_eligible`, `n_quarantined`, `n_attempted`,
`n_eligible_attempted`, `n_parsed`, `parse_coverage`, case status counts, task-success
statistics, and metric statistics. Attempts count supplied outputs/generation
records, including those attached to quarantined cases. Parse coverage uses
eligible cases as the denominator and includes missing outputs in that denominator.
Every metric reports its own defined count and status counts, mean, and population
standard deviation. Known end-to-end failures contribute zero to task success;
undefined core metrics are not converted to zeros. A conditional metric mean must
always be read alongside coverage and task-success counts.

Groups are by type, domain, language, difficulty, cohort, and edge tag. Edge-tag
groups can overlap. The separate binary task-success result does not average the
different core metrics into a composite.

## Verification and remaining work

[test_extended.py](../../tests/test_extended.py) verifies the specification's
hand-worked outcomes, strict parsing, reference contradictions, aliases, missing
and duplicate outputs, exact goal matching, precedence, error statuses, cohort
separation, population statistics, and input immutability. The fixtures do not
constitute reviewed dataset examples or evidence of model quality.

Run from the repository root:

```sh
.venv/bin/python -m pytest -q tests/test_extended.py
.venv/bin/python -m pytest -q
```

The [v2 schema and pilot](dataset_v2_workflow.md) form the approved 200-case release.
The [adapters and experiment pipeline](experiment_pipeline.md) have been exercised
on the recorded baseline. The [results](W03_Extended_Evaluation_Results.md) separate
actual model errors from strict-output failures and frozen alias limitations.
The [formal protocol](W03_Evaluation_Protocol.md), executed notebook, reflection,
and validation are linked from the [Week 3 index](../../deliverables/week-03/README.md).
The recorded Week 2 experiment remains frozen.
