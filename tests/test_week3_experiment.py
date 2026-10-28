"""Release gates and full pipeline tests use synthetic backends, never model runs."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts.datasets.v2 import manage_dataset as v2
from src import week3_experiment as pipeline
from src import week3_inputs as adapter


@pytest.fixture
def cases():
    records = v2.read_records(v2.ROOT / v2.config()["collection"])[0]
    return deepcopy([records[0], *records[100:112]])


class FixtureEncoder:
    """Orthogonal evidence/unsupported claim vectors give hand-computed scores."""
    model_id = "intfloat/multilingual-e5-base"
    revision = "d128750597153bb5987e10b1c3493a34e5a4502a"

    def __init__(self):
        self.cache = {}

    def encode(self, texts, prefix="query: "):
        values = [[0.0, 1.0] if text == "unsupported assertion" else [1.0, 0.0] for text in texts]
        self.cache.update(zip([prefix + t for t in texts], values))
        return values

    def save(self, output):
        import numpy as np
        keys = sorted(self.cache)
        (output / "embeddings.json").write_text(json.dumps({"model_id": self.model_id, "revision": self.revision,
                                                           "max_tokens": 512, "inputs": keys}))
        np.savez_compressed(output / "embeddings.npz", vectors=np.asarray([self.cache[k] for k in keys]))


class FixtureBackend:
    metadata = {"kind": "synthetic_test_fixture"}

    def __init__(self, responses, oversized=False):
        self.responses, self.calls, self.oversized = iter(responses), 0, oversized

    def render(self, messages):
        return json.dumps(messages, ensure_ascii=False), 10000 if self.oversized else 25

    def generate(self, prompt, settings):
        self.calls += 1
        value = next(self.responses)
        if isinstance(value, BaseException):
            raise value
        return {"response": value, "generation_tokens": 5, "finish_reason": "stop"}


@pytest.fixture
def sandbox(tmp_path, monkeypatch, cases):
    """A release-qualified fixture loader does not approve the real collection."""
    config = json.loads((v2.ROOT / "configs/week-03.json").read_text())
    for name in pipeline.SOURCE_FILES:
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((v2.ROOT / name).read_bytes())
    historical = config["support"]["calibration_artifact"]
    target = tmp_path / historical
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((v2.ROOT / historical).read_bytes())
    raw = v2.records_bytes(cases)
    def load(root, cfg, require_release=False):
        return deepcopy(cases), raw, {"ready": True, "release_gates": [], "dataset_manifest_sha256": "fixture-manifest"}
    monkeypatch.setattr(pipeline, "load_collection", load)
    return tmp_path, config, cases


def freeze(sandbox):
    root, config, cases = sandbox
    pipeline.freeze_run(root, config)
    pipeline.calibrate_stage(root, config)
    return root, config, cases, root / config["output"]


def generate_fixture(sandbox):
    root, config, cases, output = freeze(sandbox)
    texts = [r.get("ideal_response", r.get("reference", {}).get("ideal_response", ""))
             if adapter.evaluation_type(r) == "rag" else json.dumps(v2.expected_prediction(r), ensure_ascii=False) for r in cases]
    backend = FixtureBackend(texts)
    pipeline.generate_stage(root, config, backend_factory=lambda cfg: backend)
    rag = [r for r in cases if adapter.evaluation_type(r) == "rag"]
    extractor = FixtureBackend(['{"claims":["supported assertion"]}'] * len(rag))
    pipeline.generate_stage(root, config, "claims", backend_factory=lambda cfg: extractor)
    return root, config, cases, output, backend, extractor


def approve_fixture_review(root, config, output):
    pipeline.review_template(root, config)
    review = json.loads((output / "claim_review.json").read_text())
    review.update(status="checked", reviewer_ids=["synthetic-fixture-reviewer"], reviewed_on="2026-10-27",
                  reviewed_case_ids=review["required_case_ids"])
    (output / "claim_review.json").write_text(json.dumps(review))


def test_real_preflight_is_read_only_and_cannot_freeze_unreviewed_data(tmp_path):
    config = json.loads((v2.ROOT / "configs/week-03.json").read_text())
    result = pipeline.preflight(v2.ROOT, config)
    assert result["input_count"] == 200 and result["model_calls"] == 0 and result["ready"]
    assert result["type_counts"]["rag"] == 155
    assert result["cohort_counts"] == {"legacy_calibration": 20, "legacy_previously_evaluated": 80,
                                       "new_calibration": 20, "new_held_out": 80}
    # Keep the refusal test on a truly unapproved fixture after canonical release.
    records, _ = v2.read_records(v2.ROOT / config["dataset"])
    records[112]["annotations"]["review"].update(status="draft", reviewer_ids=[], reviewed_on=None, content_sha256=None)
    raw = v2.records_bytes(records)
    path = tmp_path / config["dataset"]
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)
    report = v2.validate_records(records, "collection", raw)
    manifest = v2.make_manifest(path, raw, report)
    (tmp_path / config["dataset_manifest"]).write_bytes(v2.json_bytes(manifest))
    output = tmp_path / config["output"]
    with pytest.raises(ValueError, match="Release freeze blocked"):
        pipeline.freeze_run(tmp_path, config)
    assert not output.exists()


def test_cached_checkpoint_requires_only_pinned_inference_files(monkeypatch):
    calls = []
    def cached(model, **kwargs):
        calls.append((model, kwargs))
        return "cached-checkpoint"
    monkeypatch.setattr("huggingface_hub.snapshot_download", cached)
    assert pipeline.cached_checkpoint({"model_id": "public/model", "revision": "a" * 40}) == "cached-checkpoint"
    assert calls == [("public/model", {"revision": "a" * 40, "local_files_only": True,
                                      "allow_patterns": ["*.json", "*.safetensors", "*.model", "*.txt"]})]


@pytest.mark.parametrize("field,value", [("output", "results/week-02/overwrite"), ("dataset", "../outside.jsonl"),
                                         ("output", "results/week-03/../other"), ("pipeline_version", "unknown")])
def test_config_refuses_scope_escape_and_unknown_version(sandbox, field, value):
    root, config, _ = sandbox
    config[field] = value
    with pytest.raises(ValueError):
        pipeline.validate_config(root, config)


def test_freeze_never_overwrites_and_source_changes_break_resume(sandbox):
    root, config, _, output = freeze(sandbox)
    preview = pipeline.preflight(root, config)
    manifest = json.loads((output / "run_manifest.json").read_text())
    assert preview["input_plan_sha256"] == manifest["identity"]["input_plan_sha256"]
    with pytest.raises(FileExistsError):
        pipeline.freeze_run(root, config)
    (root / "src/week3_inputs.py").write_text("changed")
    with pytest.raises(ValueError, match="inputs changed"):
        pipeline.generate_stage(root, config)
    assert not (output / "responses.jsonl").exists()


def test_generation_cannot_precede_calibration(sandbox):
    root, config, _ = sandbox
    pipeline.freeze_run(root, config)
    with pytest.raises(ValueError, match="calibration"):
        pipeline.generate_stage(root, config)


def test_setup_failure_does_not_become_dataset_wide_model_failures(sandbox):
    root, config, _, output = freeze(sandbox)
    def absent(cfg):
        raise FileNotFoundError("Fixture checkpoint absent")
    with pytest.raises(FileNotFoundError):
        pipeline.generate_stage(root, config, backend_factory=absent)
    assert not (output / "responses_attempts.jsonl").exists()


def test_generation_and_extraction_cover_correct_tasks_and_never_retry(sandbox):
    root, config, cases, output, backend, extractor = generate_fixture(sandbox)
    assert backend.calls == len(cases)
    assert extractor.calls == sum(adapter.evaluation_type(r) == "rag" for r in cases)
    def no_backend(cfg):
        pytest.fail("Completed stage must not load a backend")
    assert pipeline.generate_stage(root, config, backend_factory=no_backend)["new_attempts"] == 0
    rows = pipeline._rows(output / "responses.jsonl")
    assert all(row["rendered_prompt_sha256"] == pipeline.digest(row["rendered_prompt"].encode()) for row in rows.values())
    assert all(row["attempt"] == 1 for row in rows.values())


def test_interrupted_reserved_attempt_is_recorded_without_answer_retry(sandbox):
    root, config, cases, output = freeze(sandbox)
    first = cases[0]
    messages = adapter.generation_messages(first)
    reserved_hash = pipeline.content_hash({"messages": messages, "generation": config["generation"]})
    pipeline._append(output / "responses_attempts.jsonl", {"id": first["id"], "input_sha256": reserved_hash})
    backend = FixtureBackend(["fixture"] * (len(cases) - 1))
    pipeline.generate_stage(root, config, backend_factory=lambda cfg: backend)
    result = pipeline._rows(output / "responses.jsonl")[first["id"]]
    assert result["status"] == "generation_error" and result["error_type"] == "InterruptedAttempt"
    assert backend.calls == len(cases) - 1


def test_token_overflow_preserves_full_input_and_never_calls_inference(sandbox):
    root, config, cases, output = freeze(sandbox)
    backend = FixtureBackend([], oversized=True)
    pipeline.generate_stage(root, config, backend_factory=lambda cfg: backend)
    assert backend.calls == 0
    assert all(r["status"] == "generation_error" and r["rendered_prompt"]
               for r in pipeline._rows(output / "responses.jsonl").values())


def test_failed_generation_and_malformed_extraction_preserve_raw_output(sandbox):
    root, config, cases, output = freeze(sandbox)
    backend = FixtureBackend([TimeoutError(), *(["factual response"] * (len(cases) - 1))])
    pipeline.generate_stage(root, config, backend_factory=lambda cfg: backend)
    count = sum(adapter.evaluation_type(r) == "rag" for r in cases) - 1
    extractor = FixtureBackend(["[]"] * count)
    pipeline.generate_stage(root, config, "claims", backend_factory=lambda cfg: extractor)
    proposals = pipeline._rows(output / "claims.jsonl")
    assert proposals[cases[0]["id"]]["status"] == "generation_error"
    assert all(p["response"] == "[]" and p["claims"] is None and p["status"] == "scorer_error"
               for i, p in proposals.items() if i != cases[0]["id"])


def test_scoring_requires_complete_claim_review_and_replay_is_exact(sandbox):
    root, config, cases, output, _, _ = generate_fixture(sandbox)
    pipeline.review_template(root, config)
    with pytest.raises(ValueError, match="review is incomplete"):
        pipeline.score_stage(root, config, encoder_factory=lambda c, o: FixtureEncoder())
    review = json.loads((output / "claim_review.json").read_text())
    review.update(status="checked", reviewer_ids=["fixture-reviewer"], reviewed_on="2026-10-27",
                  reviewed_case_ids=review["required_case_ids"])
    (output / "claim_review.json").write_text(json.dumps(review))
    assert pipeline.score_stage(root, config, encoder_factory=lambda c, o: FixtureEncoder())["cases"] == len(cases)
    assert pipeline.score_stage(root, config, replay=True) == {"status": "exact_replay", "cases": len(cases)}
    with pytest.raises(ValueError, match="Scores are frozen"):
        pipeline.score_stage(root, config)
    scores = json.loads((output / "scores.json").read_text())
    assert "legacy_calibration" in scores["aggregate"]["by_cohort"]
    assert "new_calibration" in scores["aggregate"]["by_cohort"]
    assert "overall" not in scores["aggregate"]
    (output / "responses.jsonl").write_text("tampered\n")
    with pytest.raises(ValueError, match="sealed artifact"):
        pipeline.score_stage(root, config, replay=True)


@pytest.mark.parametrize("mutation", ["hash", "case", "before", "reason", "duplicate"])
def test_stale_or_unexplained_claim_corrections_are_rejected(sandbox, mutation):
    root, config, cases, output, _, _ = generate_fixture(sandbox)
    approve_fixture_review(root, config, output)
    p = output / "claim_review.json"
    review = json.loads(p.read_text())
    correction = {"id": cases[0]["id"], "before": ["supported assertion"], "after": ["corrected assertion"], "reason": "Fixture correspondence check"}
    review["corrections"] = [correction]
    if mutation == "hash":
        review["input_hashes"]["responses.jsonl"] = "stale"
    elif mutation == "case":
        correction["id"] = "unknown"
    elif mutation == "before":
        correction["before"] = []
    elif mutation == "reason":
        correction["reason"] = ""
    else:
        review["corrections"].append(deepcopy(correction))
    p.write_text(json.dumps(review))
    with pytest.raises(ValueError):
        pipeline._reviewed_claims(output, cases)


def test_review_correction_changes_only_scoring_claims(sandbox):
    root, config, cases, output, _, _ = generate_fixture(sandbox)
    approve_fixture_review(root, config, output)
    before = {name: (output / name).read_bytes() for name in ("responses.jsonl", "claims.jsonl")}
    p = output / "claim_review.json"
    review = json.loads(p.read_text())
    review["corrections"] = [{"id": cases[0]["id"], "before": ["supported assertion"],
                              "after": ["unsupported assertion"], "reason": "Preserve actual response assertion"}]
    p.write_text(json.dumps(review))
    assert pipeline._reviewed_claims(output, cases)[cases[0]["id"]] == ["unsupported assertion"]
    assert all((output / name).read_bytes() == raw for name, raw in before.items())


def test_new_calibration_never_uses_legacy_or_held_out_cases(sandbox):
    root, config, cases = sandbox
    config["support"]["mode"] = "calibrate_new"
    pipeline.freeze_run(root, config)
    result = pipeline.calibrate_stage(root, config, encoder_factory=lambda c, o: FixtureEncoder())
    assert result["positive_count"] > 0 and result["negative_count"] > 0
    assert result["new_calibration_case_ids"] == [r["id"] for r in cases
        if adapter.cohort(r) == "new_calibration" and adapter.evaluation_type(r) == "rag"]
    assert not any(i.startswith("w01-") for i in result["new_calibration_case_ids"])


def test_calibration_inventory_discloses_sparse_negatives_and_one_class_fails(sandbox, monkeypatch):
    root, config, cases = sandbox
    labels = pipeline.calibration_statements(cases)
    assert any(s["label_source"] == "fixed_calibration_probe" and not s["supported"] for s in labels)
    assert all(s["case_id"].startswith("w03-") for s in labels)
    config["support"]["mode"] = "calibrate_new"
    pipeline.freeze_run(root, config)
    monkeypatch.setattr(pipeline, "calibration_statements", lambda rs: [s for s in labels if s["supported"]])
    def no_encoder(c, o):
        pytest.fail("One-class calibration must stop before embedding inference")
    with pytest.raises(ValueError, match="Both supported"):
        pipeline.calibrate_stage(root, config, encoder_factory=no_encoder)
    assert not (root / config["output"] / "calibration.json").exists()


def test_pure_mixed_scoring_keeps_nulls_and_population_denominators(cases):
    spatial = [r for r in cases if adapter.evaluation_type(r) == "stum_spatial"]
    responses = {spatial[0]["id"]: {"status": "ok", "response": json.dumps(v2.expected_prediction(spatial[0]))}}
    result = pipeline.score_records(spatial, responses, {}, FixtureEncoder(), 0.8)
    summary = result["aggregate"]["by_cohort"]["new_calibration"]["structured"]["overall"]
    assert summary["n_total"] == 2 and summary["parse_coverage"] == 0.5
    assert summary["metrics"]["spatial_accuracy"]["mean"] == 1 and summary["task_success"]["mean"] == 0.5


def test_pure_scoring_rejects_unknown_outputs_and_structured_claims(cases):
    with pytest.raises(ValueError):
        pipeline.score_records(cases, {"unknown": {"status": "ok", "response": "x"}}, {}, FixtureEncoder(), 0.8)
    structured = next(r for r in cases if adapter.evaluation_type(r) != "rag")
    with pytest.raises(ValueError):
        pipeline.score_records(cases, {}, {structured["id"]: []}, FixtureEncoder(), 0.8)


def test_duplicate_or_partial_jsonl_is_never_silently_resumed(tmp_path):
    p = tmp_path / "attempts.jsonl"
    p.write_text('{"id":"x"}\n{"id":"x"}\n')
    with pytest.raises(ValueError):
        pipeline._rows(p)
    p.write_text('{"id":"x"}')
    with pytest.raises(ValueError):
        pipeline._rows(p)


def test_all_200_cases_dispatch_without_treating_fixtures_as_model_results():
    cases = v2.read_records(v2.ROOT / v2.config()["collection"])[0]
    responses, claims = {}, {}
    for record in cases:
        identifier = record["id"]
        if adapter.evaluation_type(record) == "rag":
            responses[identifier] = {"status": "ok", "response": adapter.rag_scoring_record(record)["ideal_response"]}
            claims[identifier] = []  # Explicitly claim-free fixtures; not extracted model assertions.
        else:
            responses[identifier] = {"status": "ok", "response": json.dumps(v2.expected_prediction(record), ensure_ascii=False)}
    before = deepcopy(cases)
    result = pipeline.score_records(cases, responses, claims, FixtureEncoder(), 0.8)
    assert len(result["per_example"]) == 200 and cases == before
    assert {c: g["n_cases"] for c, g in result["aggregate"]["by_cohort"].items()} == {
        "legacy_calibration": 20, "legacy_previously_evaluated": 80, "new_calibration": 20, "new_held_out": 80}
    assert all(row["metrics"]["faithfulness_proxy"]["status"] == "not_applicable"
               for row in result["per_example"] if row["evaluation_type"] == "rag")
    assert all(row["task_success"]["value"] == 1 for row in result["per_example"] if row["evaluation_type"] != "rag")


def test_manifest_drift_blocks_preflight_before_model_setup(monkeypatch):
    config = json.loads((v2.ROOT / "configs/week-03.json").read_text())
    monkeypatch.setattr(v2, "verify_manifest", lambda *args: False)
    with pytest.raises(ValueError, match="manifest integrity"):
        pipeline.preflight(v2.ROOT, config)


def test_reserved_input_drift_is_not_silently_retried(sandbox):
    root, config, cases, output = freeze(sandbox)
    pipeline._append(output / "responses_attempts.jsonl", {"id": cases[0]["id"], "input_sha256": "stale"})
    with pytest.raises(ValueError, match="Reserved attempt input changed"):
        pipeline.generate_stage(root, config)


def test_transferred_threshold_cannot_change_encoder(sandbox):
    root, config, _ = sandbox
    config["embedding"]["revision"] = "0" * 40
    pipeline.freeze_run(root, config)
    with pytest.raises(ValueError, match="same encoder"):
        pipeline.calibrate_stage(root, config)


def test_changed_generation_configuration_cannot_resume_frozen_run(sandbox):
    root, config, _, _ = freeze(sandbox)
    config["generation"]["seed"] += 1
    with pytest.raises(ValueError, match="inputs changed"):
        pipeline.generate_stage(root, config)


def test_partial_completed_attempt_cannot_be_edited_before_resume(sandbox):
    root, config, cases, output = freeze(sandbox)
    backend = FixtureBackend(["first answer", KeyboardInterrupt()])
    with pytest.raises(KeyboardInterrupt):
        pipeline.generate_stage(root, config, backend_factory=lambda c: backend)
    p = output / "responses.jsonl"
    row = pipeline._rows(p)[cases[0]["id"]]
    row["response"] = "edited after the interrupted invocation"
    p.write_text(json.dumps(row) + "\n")
    with pytest.raises(ValueError, match="attempt record changed"):
        pipeline.generate_stage(root, config)


def test_claim_review_rejects_mistyped_identifiers(sandbox):
    root, config, _, output, _, _ = generate_fixture(sandbox)
    approve_fixture_review(root, config, output)
    p = output / "claim_review.json"
    valid = json.loads(p.read_text())
    for key, value in [("reviewer_ids", "someone"), ("reviewer_ids", ["same", "same"]),
                       ("corrections", {"id": "malformed"})]:
        review = deepcopy(valid)
        review[key] = value
        p.write_text(json.dumps(review))
        with pytest.raises(ValueError):
            pipeline._reviewed_claims(output, sandbox[2])
