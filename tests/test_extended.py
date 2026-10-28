"""Synthetic mathematical/transport fixtures, not released dataset cases.

Expected fractions and graph outcomes are reasoned independently in comments.
No language authorship, model result, or release approval is implied by a fixture.
"""

import copy
import json
import math

import pytest

from src.extended_evaluator import (
    InvalidReference, PredictionFormatError, aggregate_extended_results,
    compute_extended_metrics, entity_scores, goal_scores, parse_prediction,
    score_extended_case, spatial_accuracy, temporal_scores,
)


def spatial(axis="horizontal", answer="left_of"):
    low, high = ("left_of", "right_of") if axis == "horizontal" else ("below", "above")
    return ({"constraints": [{"subject": "a", "reference": "b", "relation": low, "axis": axis},
                             {"subject": "b", "reference": "c", "relation": low, "axis": axis}],
             "answer": answer},
            {"subject": "a", "reference": "c", "axis": axis,
             "coordinate_frame": "scene_fixed_2d"})


def temporal():
    return ({"constraints": [{"event_a": "a", "event_b": "b", "relation": "before"},
                             {"event_a": "b", "event_b": "c", "relation": "before"}],
             "answers": {"ab": "before", "ac": "before", "bc": "before"}},
            {"events": ["a", "b", "c"],
             "pairs": [{"pair_id": "ab", "event_a": "a", "event_b": "b"},
                       {"pair_id": "ac", "event_a": "a", "event_b": "c"},
                       {"pair_id": "bc", "event_a": "b", "event_b": "c"}]})


def temporal_output(labels):
    return {"relations": [{"pair_id": key, "relation": value}
                          for key, value in zip(("ab", "ac", "bc"), labels)]}


def entities():
    return {"entities": [{"entity_id": "e1", "aliases": ["Nora"], "class": "person"},
                         {"entity_id": "e2", "aliases": ["blue chair", "chair"], "class": "furniture"},
                         {"entity_id": "e3", "aliases": ["walker"], "class": "mobility_aid"}]}


def entity_output(count=3):
    return {"entities": [{"mention": name, "class": label}
                         for name, label in [("Nora", "person"), ("chair", "furniture"),
                                             ("walker", "mobility_aid")][:count]]}


def task(action, **arguments):
    return {"action": action, "arguments": arguments}


def goals(ordered=False):
    return {"goals": [{"goal_id": "water", "templates": [task("deliver_item", item="water", recipient="current_user")]},
                      {"goal_id": "notify", "templates": [task("notify", recipient="caregiver")],
                       "after": ["water"] if ordered else []}]}


def goal_output():
    return {"tasks": [task("deliver_item", item="water", recipient="current_user"),
                      task("notify", recipient="caregiver")]}


def case(identifier="example", kind="stum_spatial"):
    reference, inputs = spatial()
    if kind == "stum_temporal":
        reference, inputs = temporal()
    elif kind == "seom_entities":
        reference, inputs = entities(), {}
    elif kind == "htd_task_alignment":
        reference, inputs = goals(), {}
    return {"id": identifier, "evaluation_type": kind, "reference": reference,
            "task_input": inputs, "domain": "fari-en", "language": "en", "difficulty": "medium",
            "annotations": {"subset": "calibration", "edge_case_tags": []}}


@pytest.mark.parametrize("relation,expected", [("left_of", 1), ("right_of", 0), ("mystery", 0)])
def test_spatial_hand_calculations(relation, expected):
    # a<b<c entails a<c; opposite and unknown-vocabulary guesses are incorrect.
    reference, inputs = spatial()
    assert spatial_accuracy({"relation": relation}, reference, inputs).value == expected


def test_spatial_unknown_is_evidence_sensitive():
    reference, inputs = spatial(answer="unknown")
    reference["constraints"].pop()
    assert spatial_accuracy({"relation": "unknown"}, reference, inputs).value == 1
    assert spatial_accuracy({"relation": "left_of"}, reference, inputs).value == 0


def test_spatial_conflict_in_either_queried_component():
    reference, inputs = spatial(answer="conflict")
    reference["constraints"] = [{"subject": "c", "reference": "d", "relation": relation,
                                 "axis": "horizontal"} for relation in ["left_of", "right_of"]]
    assert spatial_accuracy({"relation": "conflict"}, reference, inputs).value == 1


def test_spatial_unrelated_conflict_does_not_destroy_answer():
    reference, inputs = spatial()
    reference["constraints"] += [{"subject": "x", "reference": "y", "relation": relation,
                                  "axis": "horizontal"} for relation in ["left_of", "right_of"]]
    assert spatial_accuracy({"relation": "left_of"}, reference, inputs).value == 1


def test_spatial_equality_substitution_and_self_relation():
    reference, inputs = spatial()
    reference["constraints"][0]["relation"] = "aligned"
    assert spatial_accuracy({"relation": "left_of"}, reference, inputs).value == 1
    inputs["reference"] = "b"
    reference["answer"] = "aligned"
    assert spatial_accuracy({"relation": "aligned"}, reference, inputs).value == 1


def test_spatial_strict_edge_inside_equality_class_is_conflict():
    reference, inputs = spatial(answer="conflict")
    reference["constraints"].append({"subject": "a", "reference": "c", "relation": "aligned", "axis": "horizontal"})
    assert spatial_accuracy({"relation": "conflict"}, reference, inputs).value == 1


def test_spatial_vertical_orientation_and_no_cross_axis_inference():
    reference, inputs = spatial(axis="vertical", answer="below")
    assert spatial_accuracy({"relation": "below"}, reference, inputs).value == 1
    inputs["axis"] = "horizontal"
    reference["answer"] = "unknown"
    assert spatial_accuracy({"relation": "unknown"}, reference, inputs).value == 1


@pytest.mark.parametrize("change", ["wrong_answer", "bad_frame", "wrong_axis_relation"])
def test_invalid_spatial_reference_is_rejected(change):
    reference, inputs = spatial()
    if change == "wrong_answer": reference["answer"] = "right_of"
    elif change == "bad_frame": inputs["coordinate_frame"] = "observer_rotated"
    else: reference["constraints"][0]["relation"] = "above"
    with pytest.raises(InvalidReference):
        spatial_accuracy({"relation": "left_of"}, reference, inputs)


@pytest.mark.parametrize("labels,accuracy,consistency,coherence", [
    (("before", "before", "before"), 1, 1, 1),
    (("before", "before", "simultaneous"), 2/3, 1, 2/3),
    (("before", "after", "before"), 2/3, 0, 0),
])
def test_temporal_hand_calculations(labels, accuracy, consistency, coherence):
    # Last prediction creates a<b<c<a; middle prediction identifies b=c without a cycle.
    reference, inputs = temporal()
    scores = temporal_scores(temporal_output(labels), reference, inputs)
    assert scores["temporal_pair_accuracy"].value == pytest.approx(accuracy)
    assert scores["temporal_consistency"].value == consistency
    assert scores["temporal_coherence"].value == pytest.approx(coherence)


def test_temporal_missing_pair_has_no_credit():
    reference, inputs = temporal()
    assert temporal_scores(temporal_output(["before"]), reference, inputs)["temporal_coherence"].value == pytest.approx(1/3)


def test_temporal_identical_duplicates_collapse_but_conflicting_labels_fail():
    reference, inputs = temporal()
    prediction = temporal_output(["before"]*3)
    prediction["relations"].append(copy.deepcopy(prediction["relations"][0]))
    assert temporal_scores(prediction, reference, inputs)["temporal_coherence"].value == 1
    prediction["relations"].append({"pair_id": "ab", "relation": "unknown"})
    scores = temporal_scores(prediction, reference, inputs)
    assert scores["temporal_pair_accuracy"].value == pytest.approx(2/3)
    assert scores["temporal_consistency"].value == 0


def test_temporal_extra_pair_prevents_strict_success():
    prediction = temporal_output(["before"]*3)
    prediction["relations"].append({"pair_id": "extra", "relation": "before"})
    row = score_extended_case(case(kind="stum_temporal"), json.dumps(prediction))
    assert row["metrics"]["temporal_coherence"]["value"] == 1
    assert row["task_success"]["value"] == 0


def test_temporal_unknown_and_conflict_gold_are_derived():
    reference, inputs = temporal()
    reference["constraints"] = [{"event_a": "b", "event_b": "c", "relation": "before"},
                                {"event_a": "c", "event_b": "b", "relation": "before"}]
    reference["answers"] = {"ab": "conflict", "ac": "conflict", "bc": "conflict"}
    scores = temporal_scores(temporal_output(["conflict"]*3), reference, inputs)
    assert scores["temporal_coherence"].value == 1
    reference["constraints"] = []
    reference["answers"] = dict.fromkeys(reference["answers"], "unknown")
    assert temporal_scores(temporal_output(["unknown"]*3), reference, inputs)["temporal_coherence"].value == 1


def test_temporal_simultaneous_equivalence_can_expose_a_cycle():
    reference, inputs = temporal()
    prediction = temporal_output(["before", "simultaneous", "before"])
    # a<b<c and a=c is impossible after equality merging.
    assert temporal_scores(prediction, reference, inputs)["temporal_consistency"].value == 0


@pytest.mark.parametrize("change", ["wrong_answer", "unknown_event", "duplicate_pair", "no_pairs"])
def test_invalid_temporal_reference_is_rejected(change):
    reference, inputs = temporal()
    if change == "wrong_answer": reference["answers"]["ab"] = "after"
    elif change == "unknown_event": reference["constraints"][0]["event_a"] = "missing"
    elif change == "duplicate_pair": inputs["pairs"].append(copy.deepcopy(inputs["pairs"][0]))
    else: inputs["pairs"] = []
    with pytest.raises(InvalidReference): temporal_scores(temporal_output(["before"]*3), reference, inputs)


@pytest.mark.parametrize("count,expected", [(3, 1), (2, 2/3), (0, 0)])
def test_entity_hand_calculations(count, expected):
    # Three gold entities; correctly recognizing/classifying 3,2,0 gives 1,2/3,0.
    scores = entity_scores(entity_output(count), entities())
    assert scores["entity_recall"].value == pytest.approx(expected)
    assert scores["classification_accuracy"].value == pytest.approx(expected)
    if count == 0:
        assert scores["entity_precision"].value == 0


def test_extra_entity_lowers_precision_even_with_full_recall():
    prediction = entity_output()
    prediction["entities"].append({"mention": "invented plant", "class": "other"})
    row = score_extended_case(case(kind="seom_entities"), json.dumps(prediction))
    assert row["metrics"]["entity_recall"]["value"] == 1
    assert row["metrics"]["entity_precision"]["value"] == 0.75
    assert row["task_success"]["value"] == 0


def test_conflicting_classes_do_not_receive_classification_credit():
    prediction = entity_output(1)
    prediction["entities"].append({"mention": "Nora", "class": "robot"})
    scores = entity_scores(prediction, entities())
    assert scores["entity_recall"].value == pytest.approx(1/3)
    assert scores["classification_accuracy"].value == 0


def test_alias_normalization_deduplication_and_unknown_class():
    prediction = {"entities": [{"mention": " BLUE   CHAIR ", "class": "furniture"},
                                {"mention": "chair", "class": "furniture"}]}
    assert entity_scores(prediction, entities())["entity_precision"].value == 1
    prediction["entities"][0]["class"] = "mystery"
    assert entity_scores(prediction, entities())["classification_accuracy"].value == 0


def test_unicode_nfc_and_symbolic_chinese_aliases_use_explicit_matching():
    # Synthetic symbol aliases test Unicode; they are not natural-language dataset cases.
    reference = {"entities": [{"entity_id": "e", "aliases": ["Café", "甲"], "class": "person"}]}
    for mention in ["CAFE\u0301", "甲"]:
        assert entity_scores({"entities": [{"mention": mention, "class": "person"}]}, reference)["entity_recall"].value == 1


def test_hidden_entity_ids_and_punctuation_are_not_implicit_aliases():
    for mention in ["e1", "Nora!"]:
        assert entity_scores({"entities": [{"mention": mention, "class": "person"}]}, entities())["entity_recall"].value == 0


def test_ambiguous_entity_alias_is_quarantined():
    reference = entities()
    reference["entities"][1]["aliases"].append("nora")
    with pytest.raises(InvalidReference): entity_scores(entity_output(), reference)


def test_valid_empty_entity_inventory_and_unrequested_entity():
    reference = {"entities": [], "empty_inventory_expected": True}
    empty_case = case(kind="seom_entities")
    empty_case["reference"] = reference
    row = score_extended_case(empty_case, '{"entities":[]}')
    assert row["task_success"]["value"] == 1
    assert all(metric["status"] == "not_applicable" for metric in row["metrics"].values())
    assert entity_scores(entity_output(1), reference)["entity_precision"].value == 0


@pytest.mark.parametrize("prediction,coverage,precision", [
    (goal_output(), 1, 1),
    ({"tasks": [task("deliver_item", item="water", recipient="current_user"), task("open_window", location="room")]}, .5, .5),
    ({"tasks": []}, 0, 0),
])
def test_goal_hand_calculations(prediction, coverage, precision):
    # Two goals; respectively two matched tasks, one match plus one extra, and none.
    scores = goal_scores(prediction, goals())
    assert scores["goal_coverage"].value == coverage
    assert scores["goal_precision"].value == precision


def test_goal_matching_respects_order_and_reports_raw_task_indices():
    prediction = goal_output()
    prediction["tasks"].insert(1, copy.deepcopy(prediction["tasks"][0]))
    scores = goal_scores(prediction, goals(ordered=True))
    assert scores["goal_coverage"].value == 1
    assert scores["goal_precision"].details["matching"] == [
        {"goal_id": "water", "task_index": 0}, {"goal_id": "notify", "task_index": 2}]
    prediction["tasks"].reverse()
    assert goal_scores(prediction, goals(ordered=True))["goal_coverage"].value == .5


def test_dependent_goal_cannot_match_without_predecessor():
    assert goal_scores({"tasks": [task("notify", recipient="caregiver")]}, goals(ordered=True))["goal_coverage"].value == 0


def test_maximum_goal_matching_is_not_greedy():
    # The first task must match g2, leaving the second for g1: maximum is 2.
    a, b = task("select", item="a"), task("select", item="b")
    reference = {"goals": [{"goal_id": "g1", "templates": [a, b]},
                            {"goal_id": "g2", "templates": [a]}]}
    assert goal_scores({"tasks": [a, b]}, reference)["goal_coverage"].value == 1


@pytest.mark.parametrize("arguments", [
    {"item": "water"},
    {"item": "water", "recipient": "someone_else"},
    {"item": "water", "recipient": "current_user", "temperature": "hot"},
])
def test_goal_missing_wrong_or_invented_arguments_do_not_match(arguments):
    assert goal_scores({"tasks": [task("deliver_item", **arguments)]}, goals())["goal_coverage"].value == 0


def test_goal_aliases_are_explicit():
    reference = goals()
    reference["argument_aliases"] = {"recipient": {"caregiver": ["care giver"]}}
    assert goal_scores({"tasks": [task("notify", recipient="CARE  GIVER")]}, reference)["goal_coverage"].value == .5
    assert goal_scores({"tasks": [task("notify", recipient="helper")]}, reference)["goal_coverage"].value == 0


def test_goal_quantities_require_an_explicit_reviewed_unit_equivalence():
    reference = {"goals": [{"goal_id": "g", "templates": [task("deliver_item", quantity="1000 ml")]}]}
    prediction = {"tasks": [task("deliver_item", quantity="1 l")]}
    assert goal_scores(prediction, reference)["goal_coverage"].value == 0
    reference["argument_aliases"] = {"quantity": {"1000 ml": ["1 l"]}}
    assert goal_scores(prediction, reference)["goal_coverage"].value == 1
    assert goal_scores({"tasks": [task("deliver_item", quantity="100 ml")]}, reference)["goal_coverage"].value == 0


@pytest.mark.parametrize("change", ["cycle", "unknown_dependency", "duplicate_goal", "ambiguous_alias"])
def test_invalid_goal_reference_is_rejected(change):
    reference = goals(ordered=True)
    if change == "cycle": reference["goals"][0]["after"] = ["notify"]
    elif change == "unknown_dependency": reference["goals"][1]["after"] = ["missing"]
    elif change == "duplicate_goal": reference["goals"].append(copy.deepcopy(reference["goals"][0]))
    else: reference["argument_aliases"] = {"item": {"water": ["same"], "juice": ["SAME"]}}
    with pytest.raises(InvalidReference): goal_scores(goal_output(), reference)


def test_duplicate_template_sets_are_invalid_even_with_different_goal_ids():
    reference = goals()
    duplicate = copy.deepcopy(reference["goals"][0])
    duplicate["goal_id"] = "redundant"
    reference["goals"].append(duplicate)
    with pytest.raises(InvalidReference): goal_scores(goal_output(), reference)


def test_valid_no_task_scenario_and_missing_empty_reference_marker():
    reference = {"goals": [], "empty_inventory_expected": True}
    assert all(score.status == "not_applicable" for score in goal_scores({"tasks": []}, reference).values())
    empty_case = case(kind="htd_task_alignment")
    empty_case["reference"] = reference
    assert score_extended_case(empty_case, '{"tasks":[]}')["task_success"]["value"] == 1
    unexpected = {"tasks": [task("notify", recipient="caregiver")]}
    assert goal_scores(unexpected, reference)["goal_precision"].value == 0
    assert score_extended_case(empty_case, json.dumps(unexpected))["task_success"]["value"] == 0
    reference.pop("empty_inventory_expected")
    with pytest.raises(InvalidReference): goal_scores({"tasks": []}, reference)


def test_parser_logs_only_permitted_transport_normalizations():
    parsed = parse_prediction(' \n```json\n{"relation":"left_of"}\n```\n', "stum_spatial")
    assert parsed.value == {"relation": "left_of"}
    assert parsed.normalizations == ("surrounding_whitespace", "single_json_fence")


def test_parser_keeps_normalization_audit_for_a_failed_response():
    row = score_extended_case(case(), ' ```json\n["left_of"]\n``` ')
    assert row["status"] == "format_error"
    assert row["normalizations"] == ["surrounding_whitespace", "single_json_fence"]
    assert row["task_success"]["value"] == 0


@pytest.mark.parametrize("text", [
    '["left_of"]', '{"relation":"left_of","extra":true}', '{"relation":1}',
    '{"relation":"left_of","relation":"right_of"}', '{"relation":NaN}',
    'Answer: {"relation":"left_of"}', '{"relation":"left_of"} trailing',
])
def test_malformed_prediction_is_not_repaired(text):
    with pytest.raises(PredictionFormatError): parse_prediction(text, "stum_spatial")


@pytest.mark.parametrize("kind,text", [
    ("stum_temporal", '{"relations":[{"pair_id":"a"}]}'),
    ("seom_entities", '{"entities":[{"mention":"a","class":true}]}'),
    ("htd_task_alignment", '{"tasks":[{"action":"a","arguments":{"quantity":2}}]}'),
    ("htd_task_alignment", '{"tasks":[{"action":"a","arguments":{},"goal_id":"hidden"}]}'),
])
def test_nested_output_contracts_are_strict(kind, text):
    with pytest.raises(PredictionFormatError): parse_prediction(text, kind)


@pytest.mark.parametrize("output,status,attempted", [
    (None, "missing_response", False), (" ", "empty_response", True),
    ("broken JSON", "format_error", True),
    ({"status": "generation_error", "error_type": "TimeoutError"}, "generation_error", True),
])
def test_unusable_outputs_have_null_metrics_and_zero_task_success(output, status, attempted):
    row = score_extended_case(case(), output)
    assert row["status"] == status and row["attempted"] == attempted
    assert row["task_success"]["value"] == 0
    assert row["metrics"]["spatial_accuracy"]["value"] is None


def test_invalid_reference_is_quarantined_before_output_parsing():
    record = case()
    record["reference"]["answer"] = "wrong"
    row = score_extended_case(record, "broken JSON")
    assert row["status"] == "invalid_reference" and row["task_success"]["value"] is None


def test_scorer_errors_remain_unknown_and_parse_coverage_is_preserved(monkeypatch):
    import src.extended_evaluator as module
    def fail(*args): raise RuntimeError("fixture failure")
    monkeypatch.setattr(module, "_score", fail)
    row = score_extended_case(case(), '{"relation":"left_of"}')
    assert row["status"] == "scorer_error" and row["task_success"]["value"] is None
    assert aggregate_extended_results([row])["overall"]["parse_coverage"] == 1


def test_batch_aggregates_match_hand_calculated_statistics_and_expose_coverage():
    records = [case(str(i)) for i in range(3)]
    records[2]["domain"], records[2]["difficulty"] = "senpai-en", "hard"
    outputs = {"0": '{"relation":"left_of"}', "1": '{"relation":"right_of"}', "2": '{"relation":"left_of"}'}
    result = compute_extended_metrics(records, outputs)["aggregate"]
    stats = result["overall"]["metrics"]["spatial_accuracy"]
    assert stats["mean"] == pytest.approx(2/3)
    assert stats["std_population"] == pytest.approx(math.sqrt(2)/3)
    assert result["by_domain"]["fari-en"]["metrics"]["spatial_accuracy"]["std_population"] == .5
    assert result["by_difficulty"]["hard"]["task_success"]["mean"] == 1
    assert result["overall"]["parse_coverage"] == 1
    outputs["1"] = "broken"
    outputs.pop("2")
    summary = compute_extended_metrics(records, outputs)["aggregate"]["overall"]
    assert summary["metrics"]["spatial_accuracy"]["mean"] == 1
    assert summary["metrics"]["spatial_accuracy"]["n_scored"] == 1
    assert summary["task_success"]["mean"] == pytest.approx(1/3)
    assert summary["n_attempted"] == 2 and summary["parse_coverage"] == pytest.approx(1/3)


def test_batch_keeps_cohorts_and_overlapping_tags_explicit():
    records = [case("a"), case("b")]
    records[0]["annotations"].update(subset="held_out", edge_case_tags=["adversarial", "mixed_language"])
    records[1]["annotations"].update(subset="calibration", edge_case_tags=["adversarial"])
    result = compute_extended_metrics(records, {"a": '{"relation":"left_of"}'})["aggregate"]
    assert result["by_cohort"]["held_out"]["task_success"]["mean"] == 1
    assert result["by_cohort"]["calibration"]["task_success"]["mean"] == 0
    assert result["by_edge_tag"]["adversarial"]["n_total"] == 2


def test_batch_empty_and_quarantined_groups_have_no_fabricated_means():
    assert compute_extended_metrics([], {})["aggregate"]["overall"]["parse_coverage"] is None
    record = case()
    record["reference"] = {}
    summary = compute_extended_metrics([record], {})["aggregate"]["overall"]
    assert summary["n_quarantined"] == 1 and summary["n_eligible"] == 0
    assert summary["task_success"]["mean"] is None


def test_batch_rejects_duplicate_ids_unknown_outputs_and_rag_routing():
    with pytest.raises(ValueError): compute_extended_metrics([case(), case()], {})
    with pytest.raises(ValueError): compute_extended_metrics([case()], {"unknown": "answer"})
    record = case()
    record["evaluation_type"] = "rag"
    with pytest.raises(ValueError): compute_extended_metrics([record], {})


def test_scoring_does_not_mutate_reviewed_inputs():
    record, prediction = case(kind="htd_task_alignment"), goal_output()
    before_record, before_prediction = copy.deepcopy(record), copy.deepcopy(prediction)
    score_extended_case(record, json.dumps(prediction))
    assert record == before_record and prediction == before_prediction


def test_all_extended_types_are_dispatched_and_json_serializable():
    kinds = ["stum_spatial", "stum_temporal", "seom_entities", "htd_task_alignment"]
    records = [case(kind, kind) for kind in kinds]
    predictions = [{"relation": "left_of"}, temporal_output(["before"]*3), entity_output(), goal_output()]
    result = compute_extended_metrics(records, {kind: json.dumps(p) for kind, p in zip(kinds, predictions)})
    assert all(row["task_success"]["value"] == 1 for row in result["per_example"])
    json.dumps(result, allow_nan=False)
