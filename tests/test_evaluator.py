"""Hand-computed expectations; no downloads or model inference in unit tests."""

import copy
import math

import pytest

from src.evaluator import (
    aggregate_results, context_recall, cosine, faithfulness, lexical_recall,
    semantic_relevance, select_threshold, compute_metrics,
)
from src.model_inputs import generation_messages, parse_claims


class Vectors:
    model_id = "intfloat/multilingual-e5-base"

    def __init__(self, vectors):
        self.vectors, self.calls = vectors, []

    def encode(self, texts, prefix="query: "):
        self.calls.append((prefix, texts))
        return [self.vectors[t] for t in texts]


def record(supports=("supported", "unsupported"), language="en"):
    return {"id": "example", "query": "question", "context": ["evidence"],
            "ideal_response": "reference", "language": language,
            "domain": "fari-" + language, "difficulty": "hard",
            "evaluation_labels": {"required_facts": [{"context_support": s} for s in supports],
                                  "subset": "calibration", "edge_case_tags": []}}


@pytest.mark.parametrize("supports,expected", [
    (("supported", "supported"), 1.0),
    (("supported", "unsupported"), 0.5),
    (("contradicted", "conflicting"), 0.0),
])
def test_context_recall_hand_calculations(supports, expected):
    # Two required facts: respectively 2, 1, and 0 supported, denominator 2.
    assert context_recall(record(supports)).value == expected


def test_no_reference_facts_is_not_applicable():
    assert context_recall(record(())).status == "not_applicable"


def test_no_context_has_zero_recall_for_known_targets():
    case = record(("unsupported",))
    case["context"] = []
    assert context_recall(case).value == 0


def test_inconsistent_positive_support_without_context_is_rejected():
    case = record(("supported",))
    case["context"] = []
    with pytest.raises(ValueError):
        context_recall(case)


@pytest.mark.parametrize("claims,expected", [
    (["a", "b"], 1.0), (["a", "c"], 0.5), (["c", "d"], 0.0),
])
def test_faithfulness_hand_calculations(claims, expected):
    # Evidence=(1,0); a,b have cosine 1, c has 0, d has -1.
    encoder = Vectors({"evidence": [1, 0], "a": [1, 0], "b": [2, 0],
                       "c": [0, 1], "d": [-1, 0]})
    assert faithfulness(claims, ["evidence"], encoder, 0.7).value == expected


def test_claim_free_clarification_is_not_perfect_faithfulness():
    assert faithfulness([], [], Vectors({}), 0.7).status == "not_applicable"


def test_missing_claims_is_a_scorer_error():
    assert faithfulness(None, [], Vectors({}), 0.7).status == "scorer_error"


def test_claims_with_empty_context_have_zero_faithfulness():
    assert faithfulness(["a"], [], Vectors({}), 0.7).value == 0


@pytest.mark.parametrize("left,right,expected", [
    ([1, 0], [0, 1], 0), ([1, 0], [-1, 0], -1), ([3, 4], [4, 3], 24 / 25),
])
def test_relevance_hand_calculations(left, right, expected):
    # Orthogonal=0; antiparallel=-1; dot=24 and norm product=25.
    assert semantic_relevance("q", "y", Vectors({"q": left, "y": right})).value == pytest.approx(expected)


def test_relevance_uses_query_prefix_for_both_inputs():
    encoder = Vectors({"问题": [1, 0], "回答": [1, 0]})
    assert semantic_relevance("问题", "回答", encoder).value == 1
    assert encoder.calls == [("query: ", ["问题", "回答"])]
    assert encoder.model_id == "intfloat/multilingual-e5-base"


def test_faithfulness_uses_asymmetric_prefixes():
    encoder = Vectors({"a": [1, 0], "evidence": [1, 0]})
    faithfulness(["a"], ["evidence"], encoder, 0.7)
    assert encoder.calls == [("query: ", ["a"]), ("passage: ", ["evidence"])]


@pytest.mark.parametrize("left,right", [([0, 0], [1, 0]), ([1], [1, 0]), ([float('nan')], [1])])
def test_invalid_embeddings_are_rejected(left, right):
    with pytest.raises(ValueError):
        cosine(left, right)


def test_empty_response_has_no_relevance_score():
    assert semantic_relevance("q", " ", Vectors({})).status == "empty_response"


def test_chinese_lexical_path_invokes_jieba(monkeypatch):
    import jieba
    calls = []
    def cut(text):
        calls.append(text)
        return list(text)
    monkeypatch.setattr(jieba, "lcut", cut)
    # Reference has two characters, evidence contains one: intersection 1/2.
    assert lexical_recall("甲乙", ["甲"], "zh").value == 0.5
    assert calls == ["甲乙", "甲"]


@pytest.mark.parametrize("reference,contexts,expected", [
    ("red blue", ["red blue green"], 1),
    ("red blue", ["red green"], 0.5),
    ("red blue", [], 0),
])
def test_lexical_diagnostic_hand_calculations(reference, contexts, expected):
    assert lexical_recall(reference, contexts, "en").value == expected


def test_mixed_chinese_query_english_answer_can_be_scored():
    encoder = Vectors({"几点video call": [1, 0], "At seven": [1, 0]})
    assert semantic_relevance("几点video call", "At seven", encoder).value == 1


def test_aggregate_mean_and_population_std_match_manual_values():
    rows = [{"domain": d, "difficulty": t, "language": "en", "subset": "held_out",
             "edge_case_tags": [], "metrics": {"context_recall": {"value": v, "status": "ok"}}}
            for d, t, v in [("fari-en", "easy", 0), ("fari-en", "hard", 1), ("senpai-en", "hard", 1)]]
    summary = aggregate_results(rows)
    assert summary["overall"]["context_recall"]["mean"] == pytest.approx(2/3)
    assert summary["overall"]["context_recall"]["std_population"] == pytest.approx(math.sqrt(2)/3)
    assert summary["by_domain"]["fari-en"]["context_recall"]["mean"] == 0.5
    assert summary["by_domain"]["fari-en"]["context_recall"]["std_population"] == 0.5
    assert summary["by_difficulty"]["hard"]["context_recall"]["mean"] == 1


def test_errors_and_not_applicable_are_counted_separately():
    rows = [{"domain": "fari-en", "difficulty": "easy", "language": "en", "subset": "held_out",
             "edge_case_tags": [], "metrics": {"context_recall": {"value": v, "status": s}}}
            for v, s in [(1, "ok"), (None, "not_applicable"), (None, "scorer_error")]]
    stats = aggregate_results(rows)["overall"]["context_recall"]
    assert stats["mean"] == 1 and stats["n_total"] == 3
    assert stats["n_scored"] == stats["n_not_applicable"] == stats["n_errors"] == 1


def test_threshold_selection_requires_both_classes():
    with pytest.raises(ValueError):
        select_threshold([{"score": 0.8, "supported": True}], [0.5, 0.9])


def test_threshold_ties_prefer_larger_value():
    result = select_threshold([{"score": 0.95, "supported": True}, {"score": 0.1, "supported": False}], [0.5, 0.9])
    assert result["threshold"] == 0.9 and result["balanced_accuracy"] == 1


def test_aggregate_pipeline_preserves_generation_error():
    case = record()
    result = compute_metrics([case], {"example": {"status": "generation_error"}}, Vectors({}), {}, 0.7)
    row = result["per_example"][0]
    assert row["metrics"]["semantic_relevance"]["status"] == "generation_error"
    assert row["metrics"]["context_recall"]["value"] == 0.5


def test_model_prompt_withholds_hidden_reference_and_labels():
    case = record()
    case["construction_notes"] = "SECRET_NOTES"
    case["evaluation_labels"]["required_facts"][0]["text"] = "SECRET_FACT"
    messages = generation_messages(case)
    visible = str(messages)
    for forbidden in ["SECRET_NOTES", "SECRET_FACT", "reference", "calibration", "required_facts"]:
        assert forbidden not in visible
    assert "question" in visible and "evidence" in visible


def test_claim_parser_preserves_quantities_and_negation():
    assert parse_claims('{"claims":["It is not at 4:00 PM.","费用是17元。"]}') == ["It is not at 4:00 PM.", "费用是17元。"]


@pytest.mark.parametrize("text", ["not json", '{"claims":[4]}', '{"claims":[],"extra":true}'])
def test_malformed_claim_output_is_rejected(text):
    with pytest.raises(ValueError):
        parse_claims(text)


def test_claim_duplicates_collapse_without_rewriting():
    assert parse_claims('{"claims":["At 3:50.","At 3:50."]}') == ["At 3:50."]


def test_single_json_fence_wrapper_is_normalized_without_changing_claims():
    assert parse_claims('```json\n{"claims":["At 3:50."]}\n```') == ["At 3:50."]


def test_real_embedding_adapter_uses_multilingual_model_and_full_chinese_prefixes():
    from src.embeddings import SentenceEncoder
    class Tokenizer:
        def encode(self, text, **kwargs):
            return list(text)
    class Model:
        tokenizer = Tokenizer()
        def encode(self, texts, **kwargs):
            assert texts == ["query: 问题", "query: 回答"]
            assert kwargs["normalize_embeddings"] is True
            return [[1, 0], [1, 0]]
    encoder = SentenceEncoder(model=Model())
    assert encoder.model_id == "intfloat/multilingual-e5-base"
    assert semantic_relevance("问题", "回答", encoder).value == 1


def test_embedding_overflow_is_rejected_without_truncation():
    from src.embeddings import SentenceEncoder
    class Tokenizer:
        def encode(self, text, **kwargs):
            return [1]*513
    class Model:
        tokenizer = Tokenizer()
        def encode(self, *args, **kwargs):
            raise AssertionError("Overflow must be rejected before model encoding")
    with pytest.raises(ValueError, match="token limit"):
        SentenceEncoder(model=Model()).encode(["long input"])


def test_embedding_artifacts_replay_exactly(tmp_path):
    import numpy as np
    from src.embeddings import SentenceEncoder, ReplayEncoder
    encoder = SentenceEncoder(model=object(), revision="test-revision")
    encoder.cache = {"query: a": np.array([3., 4.]), "query: b": np.array([4., 3.])}
    encoder.save(tmp_path)
    replay = ReplayEncoder(tmp_path)
    assert semantic_relevance("a", "b", replay).value == pytest.approx(24/25)
