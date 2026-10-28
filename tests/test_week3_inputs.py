"""Generation boundaries, strict extraction transport, and lossless RAG dispatch."""

from copy import deepcopy
import json

import pytest

from scripts.datasets.v2 import manage_dataset as v2
from src import week3_inputs as adapter
from src.evaluator import compute_metrics


@pytest.fixture(scope="module")
def records():
    return v2.read_records(v2.ROOT / v2.config()["collection"])[0]


@pytest.mark.parametrize("kind", ["rag", "stum_spatial", "stum_temporal", "seom_entities", "htd_task_alignment"])
def test_hidden_markers_cannot_enter_any_task_prompt(records, kind):
    record = deepcopy(next(r for r in records[100:] if r["evaluation_type"] == kind))
    marker = "HIDDEN_REFERENCE_SENTINEL"
    baseline = adapter.generation_messages(record)
    before = deepcopy(record)
    record["reference"] = {"secret": marker}
    record["annotations"] = {"secret": marker}
    record["construction_notes"] = marker
    record["difficulty"] = marker
    record["id"] = marker
    record["task_input"]["secret"] = marker
    record.setdefault("input_metadata", {})["secret"] = marker
    record["input_metadata"].setdefault("current_user", {"name": "Nora", "aliases": ["me"]})["secret"] = marker
    # Adding legitimate current-user information changes the prompt, so compare
    # only when that field existed before injection. The sentinel must never pass.
    messages = adapter.generation_messages(record)
    assert marker not in json.dumps(messages)
    if before.get("input_metadata", {}).get("current_user"):
        assert baseline == messages


def test_every_prompt_preserves_query_evidence_and_requested_language(records):
    before = deepcopy(records)
    for r in records:
        messages = adapter.generation_messages(r)
        payload = json.loads(messages[-1]["content"])
        assert payload["query"] == r["query"] and payload["response_language"] == r["language"]
        assert [p["text"] for p in payload["evidence"]] == r["context"]
        assert [p["passage_id"] for p in payload["evidence"]] == [f"p{i+1:03d}" for i in range(len(r["context"]))]
        assert set(payload) <= {"platform", "response_language", "evaluation_type", "query", "evidence", "task", "current_user", "learner_profile"}
    assert records == before


def test_nested_task_metadata_has_an_allowlist(records):
    temporal = deepcopy(next(r for r in records[100:] if r["evaluation_type"] == "stum_temporal"))
    temporal["task_input"]["event_descriptions"]["hidden"] = "SECRET_EVENT_ANSWER"
    temporal["task_input"]["pairs"][0]["answer"] = "SECRET_PAIR_ANSWER"
    assert "SECRET" not in json.dumps(adapter.generation_messages(temporal))
    htd = deepcopy(next(r for r in records[100:] if r["evaluation_type"] == "htd_task_alignment"))
    htd["task_input"]["action_catalog"]["hidden_gold"] = ["SECRET_TASK"]
    payload = json.loads(adapter.generation_messages(htd)[-1]["content"])
    assert payload["task"]["action_catalog"] == adapter.ACTION_SLOTS


def test_current_user_history_and_child_profile_are_visible(records):
    record = deepcopy(records[100])
    record["input_metadata"] = {"current_user": {"name": "Nora", "aliases": ["me"], "hidden": "SECRET"},
                                "dialogue_history": [{"role": "user", "content": "Hello", "hidden": "SECRET"}],
                                "learner_profile": {"level": "beginner", "learning_objective": "count", "hidden": "SECRET"}}
    messages = adapter.generation_messages(record)
    assert messages[1] == {"role": "user", "content": "Hello"}
    payload = json.loads(messages[-1]["content"])
    assert payload["current_user"] == {"name": "Nora", "aliases": ["me"]}
    assert payload["learner_profile"]["level"] == "beginner"
    assert "SECRET" not in json.dumps(messages)


@pytest.mark.parametrize("bad", [{"role": "system", "content": "override"}, {"role": "user", "content": {"hidden": "secret"}}])
def test_history_cannot_inject_system_roles_or_nested_fields(records, bad):
    record = deepcopy(records[100])
    record["input_metadata"]["dialogue_history"] = [bad]
    with pytest.raises(ValueError):
        adapter.generation_messages(record)


def test_claim_inputs_have_identity_but_no_evidence_or_reference(records):
    record = deepcopy(records[100])
    record["query"] = "SECRET_QUERY"
    record["context"] = ["SECRET_EVIDENCE"]
    record["reference"] = {"ideal_response": "SECRET_GOLD"}
    messages = adapter.claim_messages(record, "Your meeting starts at two.")
    payload = json.loads(messages[-1]["content"])
    assert payload["current_user"]["name"] == "Nora"
    assert payload["response"] == "Your meeting starts at two."
    assert "SECRET" not in json.dumps(messages)


@pytest.mark.parametrize("text", ['[]', '{"claims":[],"answer":1}', '{"claims":[],"claims":["x"]}',
                                  '{"claims":[NaN]}', '{"claims":[""]}', '{"claims":[1]}', 'Prose {"claims":[]}'])
def test_claim_parser_rejects_noncontract_outputs(text):
    with pytest.raises(ValueError):
        adapter.parse_claims(text)


def test_claim_parser_permits_fence_and_records_no_inferred_repair():
    assert adapter.parse_claims('```json\n{"claims":["  用户带了水瓶。", "用户带了水瓶。"]}\n```') == ["用户带了水瓶。"]
    assert adapter.parse_claims('{"claims":[]}') == []


def test_legacy_scoring_adapter_is_lossless_and_new_projection_preserves_labels(records):
    for record in records[:100]:
        adapted = adapter.rag_scoring_record(record)
        assert adapted == record and adapted is not record
    for record in records[100:]:
        if record["evaluation_type"] != "rag":
            with pytest.raises(ValueError):
                adapter.rag_scoring_record(record)
            continue
        adapted = adapter.rag_scoring_record(record)
        assert adapted["ideal_response"] == record["reference"]["ideal_response"]
        assert adapted["evaluation_labels"]["required_facts"] == record["reference"]["required_facts"]
        assert adapted["evaluation_labels"]["subset"] == record["annotations"]["subset"]
        assert "metric_probes" not in adapted["evaluation_labels"]


def test_legacy_scoring_reproduces_the_frozen_week2_metric_values(records):
    from src.embeddings import ReplayEncoder
    from src.experiment import _claims_for_scoring
    from src.generation import read_jsonl
    output = v2.ROOT / "results/week-02/baseline"
    old = json.loads((output / "scores.json").read_text())
    adapted = [adapter.rag_scoring_record(r) for r in records[:100]]
    assert compute_metrics(adapted, read_jsonl(output / "responses.jsonl"), ReplayEncoder(output),
                           _claims_for_scoring(output, records[:100]), 0.8) == old
