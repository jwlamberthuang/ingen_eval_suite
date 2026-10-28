"""Deterministic structured metrics for spatial, temporal, entity, and goal tasks.

Reference checks operate on reviewed symbolic annotations, not natural-language
truth. The module performs no inference, downloads, release approval, or I/O.
"""

from collections import Counter, defaultdict, deque
from dataclasses import dataclass
import json
import re
import statistics
import unicodedata

from .evaluator import MetricResult


EVALUATION_TYPES = ("stum_spatial", "stum_temporal", "seom_entities", "htd_task_alignment")
ENTITY_CLASSES = ("person", "robot", "animal", "furniture", "mobility_aid",
                  "container", "device", "document", "other")
METRICS = {
    "stum_spatial": ("spatial_accuracy",),
    "stum_temporal": ("temporal_pair_accuracy", "temporal_consistency", "temporal_coherence"),
    "seom_entities": ("entity_recall", "classification_accuracy", "entity_precision"),
    "htd_task_alignment": ("goal_coverage", "goal_precision"),
}


class InvalidReference(ValueError):
    """Quarantine an invalid symbolic reference instead of grading the model."""


class PredictionFormatError(ValueError):
    """The response does not have the required JSON structure."""

    def __init__(self, message, normalizations=()):
        super().__init__(message)
        self.normalizations = tuple(normalizations)


@dataclass(frozen=True)
class ParsedPrediction:
    """Parsed content and the explicitly permitted transport normalizations."""
    value: dict
    normalizations: tuple[str, ...]


def normalize_text(value):
    """NFC, case folding, and whitespace only; retain numbers and punctuation."""
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


def _string(value, error=InvalidReference):
    if not isinstance(value, str) or not value.strip():
        raise error("Expected a nonempty string")
    return value


def _object(value, keys, error=InvalidReference):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise error("Object has missing or unexpected fields")


def _list(value, error=InvalidReference):
    if not isinstance(value, list):
        raise error("Expected an array")
    return value


def _check_prediction(value, evaluation_type):
    if evaluation_type not in EVALUATION_TYPES:
        raise ValueError("Unsupported extended evaluation type")
    key = {"stum_spatial": "relation", "stum_temporal": "relations",
           "seom_entities": "entities", "htd_task_alignment": "tasks"}[evaluation_type]
    _object(value, [key], PredictionFormatError)
    if key == "relation":
        _string(value[key], PredictionFormatError)
        return
    for item in _list(value[key], PredictionFormatError):
        fields = {"relations": ("pair_id", "relation"),
                  "entities": ("mention", "class"),
                  "tasks": ("action", "arguments")}[key]
        _object(item, fields, PredictionFormatError)
        for field in fields:
            if field == "arguments":
                if not isinstance(item[field], dict):
                    raise PredictionFormatError("Task arguments must be an object")
                for name, argument in item[field].items():
                    _string(name, PredictionFormatError)
                    _string(argument, PredictionFormatError)
            else:
                _string(item[field], PredictionFormatError)


def parse_prediction(text, evaluation_type):
    """Strict JSON; permit whitespace and one JSON fence, with an audit trail.

    Duplicate object keys and nonstandard NaN/Infinity values are rejected before
    they can silently overwrite content or become invalid numeric values.
    """
    if not isinstance(text, str):
        raise PredictionFormatError("Response must be text")
    normalizations = []
    stripped = text.strip()
    if stripped != text:
        normalizations.append("surrounding_whitespace")
    wrapper = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.DOTALL)
    if wrapper:
        stripped = wrapper.group(1)
        normalizations.append("single_json_fence")

    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise PredictionFormatError("Duplicate JSON object key")
            result[key] = value
        return result

    def nonstandard_constant(_):
        raise PredictionFormatError("Nonstandard JSON constant")

    try:
        value = json.loads(stripped, object_pairs_hook=object_pairs,
                           parse_constant=nonstandard_constant)
    except (ValueError, TypeError, RecursionError) as exc:
        raise PredictionFormatError("Response is not strict JSON", normalizations) from exc
    try:
        _check_prediction(value, evaluation_type)
    except PredictionFormatError as exc:
        exc.normalizations = tuple(normalizations)
        raise
    return ParsedPrediction(value, tuple(normalizations))


class _Order:
    """Equality classes plus a strict directed order; cycles mark components."""

    def __init__(self, nodes, equalities, inequalities):
        self.parent = {node: node for node in sorted(nodes)}

        def find(node):
            while self.parent[node] != node:
                self.parent[node] = self.parent[self.parent[node]]
                node = self.parent[node]
            return node

        self.find = find
        for left, right in equalities:
            left, right = find(left), find(right)
            if left != right:
                self.parent[max(left, right)] = min(left, right)
        self.graph = {find(node): set() for node in nodes}
        undirected = {node: set() for node in self.graph}
        for left, right in inequalities:
            left, right = find(left), find(right)
            self.graph[left].add(right)
            undirected[left].add(right)
            undirected[right].add(left)
        self.inconsistent = set()
        unseen = set(self.graph)
        while unseen:
            start = min(unseen)
            component, pending = set(), [start]
            while pending:
                node = pending.pop()
                if node not in component:
                    component.add(node)
                    pending.extend(undirected[node] - component)
            unseen -= component
            indegree = {node: 0 for node in component}
            for node in component:
                for target in self.graph[node]:
                    indegree[target] += 1
            ready = deque(sorted(n for n, count in indegree.items() if count == 0))
            visited = 0
            while ready:
                node = ready.popleft()
                visited += 1
                for target in sorted(self.graph[node]):
                    indegree[target] -= 1
                    if indegree[target] == 0:
                        ready.append(target)
            if visited != len(component):
                self.inconsistent.update(component)

    def precedes(self, left, right):
        pending, seen = [left], set()
        while pending:
            node = pending.pop()
            if node == right:
                return True
            if node not in seen:
                seen.add(node)
                pending.extend(self.graph[node] - seen)
        return False

    def relation(self, left, right, forward, reverse, equal):
        left, right = self.find(left), self.find(right)
        if left in self.inconsistent or right in self.inconsistent:
            return "conflict"
        if left == right:
            return equal
        if self.precedes(left, right):
            return forward
        if self.precedes(right, left):
            return reverse
        return "unknown"


def _spatial_reference(reference, task_input):
    subject, target = _string(task_input["subject"]), _string(task_input["reference"])
    axis = task_input["axis"]
    if axis not in ("horizontal", "vertical") or task_input["coordinate_frame"] != "scene_fixed_2d":
        raise InvalidReference("Unsupported axis or coordinate frame")
    nodes, equalities, inequalities = {subject, target}, [], []
    for item in _list(reference["constraints"]):
        left, right = _string(item["subject"]), _string(item["reference"])
        item_axis, relation = item["axis"], item["relation"]
        allowed = {"horizontal": ("left_of", "right_of", "aligned"),
                   "vertical": ("below", "above", "aligned")}
        if item_axis not in allowed or relation not in allowed[item_axis]:
            raise InvalidReference("Invalid spatial constraint")
        if item_axis != axis:
            continue
        nodes.update((left, right))
        if relation == "aligned":
            equalities.append((left, right))
        elif relation in ("left_of", "below"):
            inequalities.append((left, right))
        else:
            inequalities.append((right, left))
    order = _Order(nodes, equalities, inequalities)
    forward, reverse = ("left_of", "right_of") if axis == "horizontal" else ("below", "above")
    answer = order.relation(subject, target, forward, reverse, "aligned")
    if reference["answer"] != answer:
        raise InvalidReference("Spatial answer disagrees with symbolic constraints")
    return {"answer": answer, "axis": axis}


def _temporal_reference(reference, task_input):
    events = [_string(event) for event in _list(task_input["events"])]
    if not events or len(set(events)) != len(events):
        raise InvalidReference("Events must be nonempty and unique")
    pairs = {}
    for item in _list(task_input["pairs"]):
        identifier = _string(item["pair_id"])
        left, right = item["event_a"], item["event_b"]
        if identifier in pairs or left not in events or right not in events:
            raise InvalidReference("Invalid or duplicate temporal question")
        pairs[identifier] = (left, right)
    if not pairs:
        raise InvalidReference("At least one temporal question is required")
    equalities, inequalities = [], []
    for item in _list(reference["constraints"]):
        left, right, relation = item["event_a"], item["event_b"], item["relation"]
        if left not in events or right not in events:
            raise InvalidReference("Constraint names an unknown event")
        if relation == "simultaneous":
            equalities.append((left, right))
        elif relation == "before":
            inequalities.append((left, right))
        elif relation == "after":
            inequalities.append((right, left))
        else:
            raise InvalidReference("Invalid temporal constraint")
    order = _Order(set(events), equalities, inequalities)
    answers = {key: order.relation(a, b, "before", "after", "simultaneous")
               for key, (a, b) in pairs.items()}
    if reference["answers"] != answers:
        raise InvalidReference("Temporal answers disagree with symbolic constraints")
    return {"events": events, "pairs": pairs, "answers": answers}


def _empty_reference(reference, items):
    marker = reference.get("empty_inventory_expected", False)
    if not isinstance(marker, bool) or marker != (not items):
        raise InvalidReference("Empty inventory requires an explicit true marker")


def _entity_reference(reference, task_input):
    entities, aliases = {}, {}
    for item in _list(reference["entities"]):
        identifier, label = _string(item["entity_id"]), item["class"]
        if identifier in entities or label not in ENTITY_CLASSES:
            raise InvalidReference("Duplicate entity or unknown reference class")
        names = _list(item["aliases"])
        if not names:
            raise InvalidReference("Every entity needs an explicit visible alias")
        for name in names:
            alias = normalize_text(_string(name))
            if alias in aliases and aliases[alias] != identifier:
                raise InvalidReference("Alias resolves to multiple entities")
            aliases[alias] = identifier
        entities[identifier] = label
    _empty_reference(reference, entities)
    return {"entities": entities, "aliases": aliases}


def _argument_aliases(reference):
    result = {}
    source = reference.get("argument_aliases", {})
    if not isinstance(source, dict):
        raise InvalidReference("Argument aliases must be an object")
    for field, groups in source.items():
        _string(field)
        if not isinstance(groups, dict):
            raise InvalidReference("Alias groups must be objects")
        result[field] = {}
        for canonical, aliases in groups.items():
            canonical = normalize_text(_string(canonical))
            for alias in [canonical, *_list(aliases)]:
                alias = normalize_text(_string(alias))
                previous = result[field].get(alias, canonical)
                if previous != canonical:
                    raise InvalidReference("Argument alias has ambiguous meaning")
                result[field][alias] = canonical
    return result


def _task_key(task, aliases, error=InvalidReference):
    _object(task, ("action", "arguments"), error)
    action = _string(task["action"], error)
    if not isinstance(task["arguments"], dict):
        raise error("Task arguments must be an object")
    arguments = []
    for name, value in task["arguments"].items():
        _string(name, error)
        value = normalize_text(_string(value, error))
        arguments.append((name, aliases.get(name, {}).get(value, value)))
    return action, tuple(sorted(arguments))


def _goal_reference(reference, task_input):
    aliases = _argument_aliases(reference)
    goals, templates, dependencies = [], [], []
    for item in _list(reference["goals"]):
        identifier = _string(item["goal_id"])
        if identifier in goals:
            raise InvalidReference("Duplicate goal ID")
        accepted = {_task_key(task, aliases) for task in _list(item["templates"])}
        if not accepted or accepted in templates:
            raise InvalidReference("Empty or duplicate goal template set")
        after = [_string(value) for value in _list(item.get("after", []))]
        if len(set(after)) != len(after) or identifier in after:
            raise InvalidReference("Invalid goal dependencies")
        goals.append(identifier)
        templates.append(accepted)
        dependencies.append(after)
    _empty_reference(reference, goals)
    if any(parent not in goals for parents in dependencies for parent in parents):
        raise InvalidReference("Goal dependency does not resolve")
    order = _Order(set(goals), [], [(parent, goal) for goal, parents in zip(goals, dependencies)
                                  for parent in parents])
    if order.inconsistent:
        raise InvalidReference("Goal precedence contains a cycle")
    masks = [sum(1 << goals.index(parent) for parent in parents) for parents in dependencies]
    return {"goals": goals, "templates": templates, "dependencies": masks, "aliases": aliases}


def _prepare(evaluation_type, reference, task_input):
    builders = {"stum_spatial": _spatial_reference, "stum_temporal": _temporal_reference,
                "seom_entities": _entity_reference, "htd_task_alignment": _goal_reference}
    try:
        if not isinstance(reference, dict) or not isinstance(task_input, dict):
            raise InvalidReference("Reference and task input must be objects")
        return builders[evaluation_type](reference, task_input)
    except (KeyError, TypeError, AttributeError) as exc:
        raise InvalidReference("Missing or malformed reference fields") from exc


def _fraction(numerator, denominator, details):
    return (MetricResult(numerator / denominator, details=details) if denominator
            else MetricResult(None, "not_applicable", details))


def _precision(matched, predicted, gold, details):
    if predicted:
        return MetricResult(matched / predicted, details=details)
    if gold:
        return MetricResult(0.0, details={**details, "empty_output_convention": True})
    return MetricResult(None, "not_applicable", details)


def _spatial_scores(prediction, prepared):
    correct = float(prediction["relation"] == prepared["answer"])
    metric = MetricResult(correct, details={"expected": prepared["answer"],
                          "predicted": prediction["relation"], "axis": prepared["axis"],
                          "answer_group": "abstention_or_conflict" if prepared["answer"] in
                          ("unknown", "conflict") else "resolved_relation"})
    return {"spatial_accuracy": metric}, correct


def _temporal_scores(prediction, prepared):
    labels = defaultdict(set)
    for answer in prediction["relations"]:
        labels[answer["pair_id"]].add(answer["relation"])
    correct = sum(labels[key] == {answer} for key, answer in prepared["answers"].items())
    extra = sorted(set(labels) - set(prepared["pairs"]))
    contradictory = any(len(values) > 1 for values in labels.values())
    equalities, inequalities = [], []
    for key, pair in prepared["pairs"].items():
        for relation in labels[key]:
            left, right = pair
            if relation == "before":
                inequalities.append((left, right))
            elif relation == "after":
                inequalities.append((right, left))
            elif relation == "simultaneous":
                equalities.append((left, right))
    order = _Order(set(prepared["events"]), equalities, inequalities)
    consistent = float(not contradictory and not order.inconsistent)
    accuracy = correct / len(prepared["pairs"])
    details = {"correct_pairs": correct, "requested_pairs": len(prepared["pairs"]),
               "extra_pair_ids": extra, "contradictory_pair_answers": contradictory}
    scores = {"temporal_pair_accuracy": MetricResult(accuracy, details=details),
              "temporal_consistency": MetricResult(consistent, details=details),
              "temporal_coherence": MetricResult(accuracy * consistent, details=details)}
    return scores, float(accuracy == consistent == 1 and not extra)


def _entity_scores(prediction, prepared):
    predicted = defaultdict(set)
    for item in prediction["entities"]:
        mention = normalize_text(item["mention"])
        identity = (("known", prepared["aliases"][mention]) if mention in prepared["aliases"]
                    else ("unknown", mention))
        predicted[identity].add(item["class"])
    gold = len(prepared["entities"])
    recognized = sum(kind == "known" for kind, _ in predicted)
    classified = sum(predicted.get(("known", identity), set()) == {label}
                     for identity, label in prepared["entities"].items())
    details = {"gold_entities": gold, "predicted_entities": len(predicted),
               "recognized_entities": recognized, "correctly_classified_entities": classified}
    scores = {"entity_recall": _fraction(recognized, gold, details),
              "classification_accuracy": _fraction(classified, gold, details),
              "entity_precision": _precision(recognized, len(predicted), gold, details)}
    return scores, float(classified == recognized == gold == len(predicted))


def _goal_scores(prediction, prepared):
    # Preserve the first occurrence after explicitly permitted argument matching.
    first_positions = {}
    for position, task in enumerate(prediction["tasks"]):
        key = _task_key(task, prepared["aliases"], PredictionFormatError)
        first_positions.setdefault(key, position)
    tasks = list(first_positions)
    # Exact maximum matching with precedence. States retain one witness per
    # matched-goal subset; at a fixed task index no other past state is needed.
    states = {0: ()}
    for task in tasks:
        position = first_positions[task]
        following = dict(states)
        for mask, witness in states.items():
            for goal, templates in enumerate(prepared["templates"]):
                bit, required = 1 << goal, prepared["dependencies"][goal]
                if not mask & bit and mask & required == required and task in templates:
                    new_mask = mask | bit
                    candidate = witness + ((goal, position),)
                    if new_mask not in following or candidate < following[new_mask]:
                        following[new_mask] = candidate
        states = following
    mask = min(states, key=lambda value: (-value.bit_count(), states[value]))
    matched, gold = mask.bit_count(), len(prepared["goals"])
    details = {"gold_goals": gold, "predicted_tasks": len(tasks), "matched_goals": matched,
               "matching": [{"goal_id": prepared["goals"][goal], "task_index": position}
                            for goal, position in states[mask]]}
    scores = {"goal_coverage": _fraction(matched, gold, details),
              "goal_precision": _precision(matched, len(tasks), gold, details)}
    return scores, float(matched == gold == len(tasks))


def _score(evaluation_type, prediction, prepared):
    return {"stum_spatial": _spatial_scores, "stum_temporal": _temporal_scores,
            "seom_entities": _entity_scores, "htd_task_alignment": _goal_scores}[evaluation_type](prediction, prepared)


def _direct(evaluation_type, prediction, reference, task_input):
    prepared = _prepare(evaluation_type, reference, task_input)
    _check_prediction(prediction, evaluation_type)
    return _score(evaluation_type, prediction, prepared)[0]


def spatial_accuracy(prediction, reference, task_input):
    """Binary spatial accuracy after checking the symbolic gold derivation."""
    return _direct("stum_spatial", prediction, reference, task_input)["spatial_accuracy"]


def temporal_scores(prediction, reference, task_input):
    """Pair accuracy, graph consistency, and their coherence product."""
    return _direct("stum_temporal", prediction, reference, task_input)


def entity_scores(prediction, reference):
    """Entity recall, joint classification accuracy, and entity precision."""
    return _direct("seom_entities", prediction, reference, {})


def goal_scores(prediction, reference):
    """Maximum one-to-one explicit-goal coverage and task precision."""
    return _direct("htd_task_alignment", prediction, reference, {})


def score_extended_case(record, output=None):
    """Score raw response text or a generation record; quarantine invalid gold.

    A generation record has status='ok' plus response text, or a distinct
    generation-error status. Output absence differs from a recorded failed attempt.
    """
    evaluation_type = record["evaluation_type"]
    if evaluation_type not in EVALUATION_TYPES:
        raise ValueError("Use the RAG evaluator separately; unsupported extended type")
    annotations = record.get("annotations", {})
    row = {"id": record["id"], "evaluation_type": evaluation_type,
           "domain": record["domain"], "language": record["language"],
           "difficulty": record["difficulty"], "cohort": annotations.get("subset", "unassigned"),
           "edge_case_tags": annotations.get("edge_case_tags", []), "attempted": output is not None,
           "status": "ok", "parsed": False, "normalizations": [],
           "metrics": {}, "task_success": None}

    def failure(status, success, reason):
        row.update(status=status, metrics={name: MetricResult(None, status, {"reason": reason}).to_dict()
                                          for name in METRICS[evaluation_type]},
                   task_success=MetricResult(success, status, {"reason": reason}).to_dict())
        return row

    try:
        prepared = _prepare(evaluation_type, record.get("reference"), record.get("task_input", {}))
    except InvalidReference as exc:
        return failure("invalid_reference", None, str(exc))
    if output is None:
        return failure("missing_response", 0.0, "No generation record supplied")
    if isinstance(output, dict):
        if output.get("status") == "generation_error":
            return failure("generation_error", 0.0, "Recorded generation failure")
        if output.get("status") != "ok" or not isinstance(output.get("response"), str):
            return failure("scorer_error", None, "Invalid generation artifact contract")
        output = output["response"]
    if not isinstance(output, str):
        return failure("scorer_error", None, "Output must be response text or a generation record")
    if not output.strip():
        return failure("empty_response", 0.0, "Response contains no content")
    try:
        parsed = parse_prediction(output, evaluation_type)
    except PredictionFormatError as exc:
        row["normalizations"] = list(exc.normalizations)
        return failure("format_error", 0.0, str(exc))
    row["normalizations"] = list(parsed.normalizations)
    row["parsed"] = True
    try:
        metrics, success = _score(evaluation_type, parsed.value, prepared)
    except Exception as exc:
        return failure("scorer_error", None, type(exc).__name__)
    row["metrics"] = {name: result.to_dict() for name, result in metrics.items()}
    row["task_success"] = MetricResult(success).to_dict()
    return row


def _statistics(results):
    values = [result["value"] for result in results if result["value"] is not None]
    return {"n_total": len(results), "n_scored": len(values),
            "status_counts": dict(sorted(Counter(result["status"] for result in results).items())),
            "mean": statistics.mean(values) if values else None,
            "std_population": statistics.pstdev(values) if values else None}


def _summary(rows):
    eligible = [row for row in rows if row["status"] != "invalid_reference"]
    names = sorted({name for row in rows for name in row["metrics"]})
    return {"n_total": len(rows), "n_eligible": len(eligible),
            "n_quarantined": len(rows) - len(eligible),
            "n_attempted": sum(row["attempted"] for row in rows),
            "n_eligible_attempted": sum(row["attempted"] for row in eligible),
            "n_parsed": sum(row["parsed"] for row in eligible),
            "parse_coverage": sum(row["parsed"] for row in eligible) / len(eligible) if eligible else None,
            "case_status_counts": dict(sorted(Counter(row["status"] for row in rows).items())),
            "task_success": _statistics([row["task_success"] for row in rows]),
            "metrics": {name: _statistics([row["metrics"][name] for row in rows if name in row["metrics"]])
                        for name in names}}


def aggregate_extended_results(rows):
    """Population summaries with explicit coverage, missing values, and cohorts."""
    result = {"overall": _summary(rows)}
    for field, label in [("evaluation_type", "by_type"), ("domain", "by_domain"),
                         ("language", "by_language"), ("difficulty", "by_difficulty"),
                         ("cohort", "by_cohort")]:
        groups = defaultdict(list)
        for row in rows:
            groups[row[field]].append(row)
        result[label] = {key: _summary(values) for key, values in sorted(groups.items())}
    tags = defaultdict(list)
    for row in rows:
        for tag in set(row["edge_case_tags"]):
            tags[tag].append(row)
    result["by_edge_tag"] = {key: _summary(values) for key, values in sorted(tags.items())}
    return result


def compute_extended_metrics(records, responses):
    """Batch the four structured task types; never route RAG through this scorer."""
    records = list(records)
    identifiers = [record["id"] for record in records]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Duplicate case IDs")
    if set(responses) - set(identifiers):
        raise ValueError("Response contains an unknown case ID")
    rows = [score_extended_case(record, responses.get(record["id"])) for record in records]
    return {"per_example": rows, "aggregate": aggregate_extended_results(rows)}
