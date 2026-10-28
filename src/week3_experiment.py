"""Versioned Week 3 experiments with release gates and offline artifact replay.

Importing this module never loads a model. Pure scoring accepts injected encoders
for mathematical tests; disk-backed experiment commands require a reviewed freeze.
"""

from collections import Counter, defaultdict
from contextlib import contextmanager
from copy import deepcopy
from datetime import date, datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import tempfile
import time

from scripts.datasets.v2 import manage_dataset as dataset
from .evaluator import aggregate_results, compute_metrics, select_threshold, support_scores
from .extended_evaluator import aggregate_extended_results, score_extended_case
from . import week3_inputs as inputs

PIPELINE_VERSION = "week3-pipeline-v1"
SOURCE_FILES = (
    "src/week3_inputs.py", "src/week3_experiment.py", "src/evaluator.py",
    "src/extended_evaluator.py", "src/model_inputs.py", "src/embeddings.py",
    "scripts/datasets/v2/manage_dataset.py", "scripts/evaluation/week3.py",
    "configs/dataset-v2.json", "schemas/w03_evaluation_case.schema.json",
    "schemas/w01_dialogue_case.schema.json", "requirements-evaluation.txt",
    "requirements-generation.txt", "requirements-validation.txt",
    "docs/week-03/W03_Evaluation_Protocol.md",
)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def content_hash(value):
    return digest(json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False).encode())


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def _path(root, name):
    if not isinstance(name, str) or Path(name).is_absolute() or ".." in Path(name).parts:
        raise ValueError("Use repository-relative paths without parent traversal")
    root = Path(root).resolve()
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Path escapes repository")
    return path


def validate_config(root, config):
    keys = {"pipeline_version", "run_name", "dataset", "dataset_manifest", "output",
            "generation", "embedding", "support"}
    if set(config) != keys or config["pipeline_version"] != PIPELINE_VERSION:
        raise ValueError("Unsupported experiment configuration")
    if not config["run_name"] or Path(config["run_name"]).name != config["run_name"]:
        raise ValueError("Invalid run name")
    output = _path(root, config["output"])
    if not output.is_relative_to(_path(root, "results/week-03")) or output == _path(root, "results/week-03"):
        raise ValueError("Experiment outputs must be under results/week-03")
    for key in ("dataset", "dataset_manifest"):
        _path(root, config[key])
    generation = config["generation"]
    if set(generation) != {"model_id", "revision", "runtime", "temperature", "max_new_tokens",
                            "seed", "input_limit_tokens", "case_timeout_seconds"}:
        raise ValueError("Unexpected generation settings")
    if generation["runtime"] != "mlx-lm" or generation["temperature"] != 0:
        raise ValueError("Version one requires greedy MLX generation")
    for key in ("max_new_tokens", "input_limit_tokens", "case_timeout_seconds"):
        if type(generation[key]) is not int or generation[key] <= 0:
            raise ValueError("Budgets must be positive integers")
    if type(generation["seed"]) is not int:
        raise ValueError("Seed must be an integer")
    embedding = config["embedding"]
    if set(embedding) != {"model_id", "revision", "device", "max_tokens", "batch_size"}:
        raise ValueError("Unexpected embedding settings")
    if embedding["device"] != "cpu" or any(type(embedding[k]) is not int or embedding[k] <= 0
                                           for k in ("max_tokens", "batch_size")):
        raise ValueError("Invalid embedding runtime or limits")
    for settings in (generation, embedding):
        revision = settings["revision"]
        if not isinstance(revision, str) or len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
            raise ValueError("Model revisions must be pinned commit hashes")
        if not isinstance(settings["model_id"], str) or not settings["model_id"]:
            raise ValueError("Model identifier is required")
    support = config["support"]
    if set(support) != {"mode", "calibration_artifact", "threshold_grid", "tie_break", "segmenter", "claim_extractor"}:
        raise ValueError("Unexpected support settings")
    if support["mode"] not in {"transfer_week2", "calibrate_new"}:
        raise ValueError("Unknown support calibration mode")
    if (support["threshold_grid"] != [0.5, 0.6, 0.7, 0.8, 0.9] or
        support["tie_break"] != "larger_threshold" or support["segmenter"] != "punctuation_sentences_v1" or
        support["claim_extractor"] != "w03-qwen-json-atomic-v1"):
        raise ValueError("Scoring policies differ from the version-one contract")
    _path(root, support["calibration_artifact"])
    return output


def load_collection(root, config, require_release=False):
    """Validate current data and manifests before any experiment side effect."""
    path = _path(root, config["dataset"])
    records, raw = dataset.read_records(path)
    collection = dataset.validate_records(records, "collection", raw)
    manifest = dataset.loads(_path(root, config["dataset_manifest"]).read_text())
    profile = manifest.get("validation", {}).get("profile")
    if profile not in {"collection", "release"}:
        raise ValueError("Collection manifest has the wrong validation profile")
    recorded = dataset.validate_records(records, profile, raw)
    if not collection["valid"] or not dataset.verify_manifest(manifest, path, raw, recorded):
        raise ValueError("Dataset validation or manifest integrity failed")
    release = dataset.validate_records(records, "release", raw)
    gates = list(release["errors"])
    if manifest["status"] != "release":
        gates.append("Refresh the collection manifest under the release profile after review")
    if "draft" in dataset.config()["schema_version"]:
        gates.append("Freeze a reviewed release schema version and matching construction configuration")
    info = {"collection_validation": collection, "release_validation": release,
            "ready": not gates, "release_gates": gates,
            "dataset_sha256": digest(raw),
            "dataset_manifest_sha256": digest(_path(root, config["dataset_manifest"]).read_bytes())}
    if require_release and gates:
        raise ValueError(f"Release freeze blocked by {len(gates)} review/manifest/schema gates")
    return records, raw, info


def preflight(root, config):
    """Read-only inspection is available while examples remain drafts."""
    validate_config(root, config)
    records, _, info = load_collection(root, config)
    plans = [{"id": r["id"], "messages": inputs.generation_messages(r)} for r in records]
    return {**info, "pipeline_version": PIPELINE_VERSION, "model_calls": 0,
            "input_count": len(plans), "input_plan_sha256": content_hash(plans),
            "new_calibration_labels": _label_counts(calibration_statements(records)),
            "type_counts": dict(sorted(Counter(inputs.evaluation_type(r) for r in records).items())),
            "cohort_counts": dict(sorted(Counter(inputs.cohort(r) for r in records).items()))}


def calibration_statements(records):
    """Reviewed reference facts and fixed probe atoms from new calibration only."""
    statements = []
    for record in records:
        if inputs.cohort(record) != "new_calibration" or inputs.evaluation_type(record) != "rag":
            continue
        common = {"case_id": record["id"], "language": record["language"]}
        for fact in record["reference"]["required_facts"]:
            statements.append({**common, "statement_id": "fact:" + fact["fact_id"], "claim": fact["text"],
                               "support_label": fact["context_support"], "supported": fact["context_support"] == "supported",
                               "label_source": "reference_fact"})
        for probe in record["reference"]["metric_probes"]:
            for index, claim in enumerate(probe["claims"]):
                statements.append({**common, "statement_id": f"probe:{probe['probe_id']}:{index}", "claim": claim["text"],
                                   "support_label": claim["support"], "supported": claim["support"] == "supported",
                                   "label_source": "fixed_calibration_probe"})
    return statements


def _label_counts(statements):
    def counts(rows):
        return {"positive": sum(r["supported"] for r in rows), "negative": sum(not r["supported"] for r in rows),
                "by_source": dict(sorted(Counter(r["label_source"] for r in rows).items()))}
    return {"all": counts(statements), "by_language": {language: counts([r for r in statements if r["language"] == language])
                                                     for language in sorted({r["language"] for r in statements})}}


def _identity(root, config, raw, info, plans):
    return {"pipeline_version": PIPELINE_VERSION, "adapter_version": inputs.ADAPTER_VERSION,
            "config": deepcopy(config), "dataset_sha256": digest(raw),
            "dataset_manifest_sha256": info["dataset_manifest_sha256"],
            "input_plan_sha256": content_hash(plans),
            "source_hashes": {name: digest(_path(root, name).read_bytes()) for name in SOURCE_FILES},
            "support_source_sha256": digest(_path(root, config["support"]["calibration_artifact"]).read_bytes())}


def _write_new(path, value):
    dataset.write_new(path, dataset.json_bytes(value))


def _replace(path, value):
    """Atomic manifest updates; immutable snapshots use exclusive creation."""
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".state-", delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(dataset.json_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _rows(path):
    if not path.exists():
        return {}
    records, _ = dataset.read_records(path) if path.stat().st_size else ([], b"")
    result = {}
    for row in records:
        if row["id"] in result:
            raise ValueError("Duplicate artifact case ID")
        result[row["id"]] = row
    return result


def _append(path, row):
    with path.open("ab") as stream:
        stream.write((json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n").encode())
        stream.flush()
        os.fsync(stream.fileno())


@contextmanager
def _lock(output):
    import fcntl
    with (output / ".run.lock").open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("Another process is using this run") from exc
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def freeze_run(root, config):
    output = validate_config(root, config)
    records, raw, info = load_collection(root, config, require_release=True)
    plans = [{"id": r["id"], "messages": inputs.generation_messages(r)} for r in records]
    identity = _identity(root, config, raw, info, plans)
    output.mkdir(parents=True, exist_ok=False)
    dataset.write_new(output / "dataset.jsonl", raw)
    _write_new(output / "config.json", config)
    _write_new(output / "validation.json", info)
    dataset.write_new(output / "inputs.jsonl", b"".join(
        (json.dumps(p, ensure_ascii=False) + "\n").encode() for p in plans))
    manifest = {"identity": identity, "fingerprint": content_hash(identity),
                "created_at": timestamp(), "status": "frozen", "stages": {}, "artifacts": {}}
    _seal(output, manifest, ["dataset.jsonl", "config.json", "validation.json", "inputs.jsonl"])
    return manifest


def _seal(output, manifest, names):
    manifest["artifacts"].update({name: digest((output / name).read_bytes()) for name in names})
    _replace(output / "run_manifest.json", manifest)


def _state(root, config):
    output = validate_config(root, config)
    records, raw, info = load_collection(root, config, require_release=True)
    manifest = dataset.loads((output / "run_manifest.json").read_text())
    plans = [{"id": r["id"], "messages": inputs.generation_messages(r)} for r in records]
    identity = _identity(root, config, raw, info, plans)
    if manifest["identity"] != identity or manifest["fingerprint"] != content_hash(identity):
        raise ValueError("Frozen run inputs changed; use a new experiment version")
    for name, expected in manifest["artifacts"].items():
        if Path(name).name != name or Path(name).is_absolute():
            raise ValueError("Invalid sealed artifact name")
        if digest((output / name).read_bytes()) != expected:
            raise ValueError("A sealed artifact changed: " + name)
    return output, records, manifest


def cached_checkpoint(settings):
    """Resolve the pinned inference files without requiring repository extras."""
    from huggingface_hub import snapshot_download
    return snapshot_download(settings["model_id"], revision=settings["revision"], local_files_only=True,
                             allow_patterns=["*.json", "*.safetensors", "*.model", "*.txt"])


class MLXBackend:
    """Load only the cached pinned checkpoint; no download or model installation."""

    def __init__(self, generation):
        import mlx.core as mx
        from mlx_lm import load, stream_generate
        from mlx_lm.sample_utils import make_sampler
        checkpoint = cached_checkpoint(generation)
        self.model, self.tokenizer = load(checkpoint)
        self.mx, self.stream_generate = mx, stream_generate
        self.sampler = make_sampler(temp=generation["temperature"])
        self.metadata = {"system": platform.system(), "architecture": platform.machine(),
                         **{name: importlib.metadata.version(name) for name in ("mlx", "mlx-lm", "transformers")}}

    def render(self, messages):
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        return prompt, len(self.tokenizer.encode(prompt))

    def generate(self, prompt, settings):
        self.mx.random.seed(settings["seed"])
        pieces, last, started = [], None, time.perf_counter()
        try:
            for piece in self.stream_generate(self.model, self.tokenizer, prompt=prompt,
                                              max_tokens=settings["max_new_tokens"], sampler=self.sampler):
                pieces.append(piece.text)
                last = piece
                if time.perf_counter() - started > settings["case_timeout_seconds"]:
                    raise TimeoutError("Cooperative generation budget exceeded")
            return {"response": "".join(pieces), "generation_tokens": last.generation_tokens if last else 0,
                    "finish_reason": last.finish_reason if last else "stop"}
        finally:
            self.mx.clear_cache()


def generate_stage(root, config, stage="responses", backend_factory=MLXBackend):
    if stage not in {"responses", "claims"}:
        raise ValueError("Unknown generation stage")
    output, records, manifest = _state(root, config)
    with _lock(output):
        # Reload after taking the lock so two callers cannot act on stale state.
        output, records, manifest = _state(root, config)
        if manifest["stages"].get(stage) == "complete":
            return {"stage": stage, "status": "already_complete", "new_attempts": 0}
        if manifest["stages"].get("calibration") != "complete":
            raise ValueError("Freeze support calibration before model generation")
        if stage == "claims" and manifest["stages"].get("responses") != "complete":
            raise ValueError("Complete response generation before claim extraction")
        responses = _rows(output / "responses.jsonl")
        selected = records if stage == "responses" else [r for r in records if inputs.evaluation_type(r) == "rag"]
        path, journal = output / f"{stage}.jsonl", output / f"{stage}_attempts.jsonl"
        finished, reserved = _rows(path), _rows(journal)
        expected_ids = {r["id"] for r in selected}
        if (set(finished) | set(reserved)) - expected_ids or set(finished) - set(reserved):
            raise ValueError("Artifact IDs or attempt reservations disagree")
        backend, new_attempts = None, 0
        for record in selected:
            identifier = record["id"]
            response = responses.get(identifier)
            skip = stage == "claims" and (response["status"] != "ok" or not response["response"].strip())
            messages = ([] if skip else inputs.generation_messages(record) if stage == "responses"
                        else inputs.claim_messages(record, response["response"]))
            input_hash = content_hash({"messages": messages, "generation": config["generation"]})
            if identifier in reserved and reserved[identifier]["input_sha256"] != input_hash:
                raise ValueError("Reserved attempt input changed")
            if identifier in finished:
                row = finished[identifier]
                body = {k: v for k, v in row.items() if k != "record_sha256"}
                if row.get("record_sha256") != content_hash(body):
                    raise ValueError("Existing attempt record changed")
                if row["input_sha256"] != input_hash or row["input_messages"] != messages or row["attempt"] != 1:
                    raise ValueError("Existing attempt input changed")
                continue
            row = {"id": identifier, "attempt": 1, "input_messages": messages,
                   "input_sha256": input_hash, "started_at": timestamp()}
            if identifier in reserved:
                row.update(status="generation_error", error_type="InterruptedAttempt")
            else:
                if not skip and backend is None:
                    # Unavailable checkpoints/runtime are stage setup failures,
                    # not failed model answers for every dataset case.
                    backend = backend_factory(config["generation"])
                    manifest.setdefault("runtime", {})[stage] = backend.metadata
                _append(journal, {"id": identifier, "input_sha256": input_hash, "reserved_at": timestamp()})
                if skip:
                    row.update(status="generation_error", error_type="ResponseUnavailable")
                else:
                    started = time.perf_counter()
                    try:
                        prompt, count = backend.render(messages)
                        row.update(rendered_prompt=prompt, rendered_prompt_sha256=digest(prompt.encode()), prompt_tokens=count)
                        if count > config["generation"]["input_limit_tokens"]:
                            raise ValueError("Input exceeds declared token budget")
                        new_attempts += 1
                        result = backend.generate(prompt, config["generation"])
                        if not isinstance(result.get("response"), str):
                            raise TypeError("Backend response must be text")
                        row.update({k: result[k] for k in ("response", "generation_tokens", "finish_reason") if k in result}, status="ok")
                        if stage == "claims":
                            try:
                                row["claims"] = inputs.parse_claims(row["response"])
                            except ValueError as exc:
                                row.update(status="scorer_error", claims=None, error_type=type(exc).__name__)
                    except Exception as exc:
                        row.update(status="generation_error", error_type=type(exc).__name__)
                    row["elapsed_seconds"] = time.perf_counter() - started
            if stage == "claims":
                row.setdefault("claims", None)
            row["finished_at"] = timestamp()
            row["record_sha256"] = content_hash(row)
            _append(path, row)
        manifest["stages"][stage] = "complete"
        manifest["status"] = stage + "_complete"
        _seal(output, manifest, [path.name, journal.name])
        return {"stage": stage, "status": "complete", "records": len(selected), "new_attempts": new_attempts}


def local_encoder(config, output):
    """Use a cached checkpoint and the retained encoder/cache representation."""
    import torch
    from sentence_transformers import SentenceTransformer
    from .embeddings import ReplayEncoder, SentenceEncoder
    torch.set_num_threads(4)
    settings = config["embedding"]
    checkpoint = cached_checkpoint(settings)
    model = SentenceTransformer(checkpoint, device=settings["device"], trust_remote_code=False, local_files_only=True)
    encoder = SentenceEncoder(**settings, model=model)
    if (output / "embeddings.json").exists():
        previous = ReplayEncoder(output)
        if (previous.model_id, previous.revision) != (encoder.model_id, encoder.revision):
            raise ValueError("Embedding cache model changed")
        encoder.cache.update(previous.cache)
    return encoder


def calibrate_stage(root, config, encoder_factory=local_encoder):
    output, records, manifest = _state(root, config)
    with _lock(output):
        output, records, manifest = _state(root, config)
        if manifest["stages"].get("calibration") == "complete":
            return dataset.loads((output / "calibration.json").read_text())
        if manifest["stages"].get("responses"):
            raise ValueError("Freeze calibration before generating model responses")
        settings = config["support"]
        if settings["mode"] == "transfer_week2":
            old = dataset.loads(_path(root, settings["calibration_artifact"]).read_text())
            if old["embedding"] != config["embedding"] or old["support_settings"]["segmenter"] != settings["segmenter"]:
                raise ValueError("Transferred threshold requires the same encoder and segmenter")
            result = {"mode": "transfer_week2", "threshold": old["threshold"],
                      "source_file": settings["calibration_artifact"],
                      "source_sha256": manifest["identity"]["support_source_sha256"],
                      "new_calibration_case_ids": [],
                      "limitations": ["Historical threshold transferred without new fitting; new-case validity is unestablished."]}
        else:
            statements = calibration_statements(records)
            if not any(s["supported"] for s in statements) or not any(not s["supported"] for s in statements):
                raise ValueError("Both supported and unsupported calibration classes are required")
            encoder, labeled = encoder_factory(config, output), []
            selected = [r for r in records if inputs.cohort(r) == "new_calibration" and inputs.evaluation_type(r) == "rag"]
            for record in selected:
                own = [s for s in statements if s["case_id"] == record["id"]]
                scores = support_scores([s["claim"] for s in own], record["context"], encoder)
                labeled.extend({**statement, **score} for statement, score in zip(own, scores))
            result = {**select_threshold(labeled, settings["threshold_grid"]), "mode": "calibrate_new",
                      "new_calibration_case_ids": [r["id"] for r in selected],
                      "label_counts": _label_counts(labeled),
                      "limitations": ["Reference/probe statements may differ from generated claims; negative labels are sparse and per-language validity is unestablished."]}
            _write_new(output / "calibration_claims.json", labeled)
            encoder.save(output)
        if not isinstance(result["threshold"], (int, float)) or not math.isfinite(result["threshold"]) or not 0 <= result["threshold"] <= 1:
            raise ValueError("Invalid support threshold")
        _write_new(output / "calibration.json", result)
        manifest["stages"]["calibration"] = "complete"
        names = ["calibration.json"] + (["calibration_claims.json", "embeddings.json", "embeddings.npz"]
                                       if settings["mode"] == "calibrate_new" else [])
        _seal(output, manifest, names)
        return result


def review_template(root, config):
    output, records, manifest = _state(root, config)
    with _lock(output):
        output, records, manifest = _state(root, config)
        if manifest["stages"].get("claims") != "complete":
            raise ValueError("Complete extraction before preparing claim review")
        review = {"status": "pending", "reviewer_ids": [], "reviewed_on": None,
                  "input_hashes": {name: digest((output / name).read_bytes()) for name in ("responses.jsonl", "claims.jsonl")},
                  "required_case_ids": [r["id"] for r in records if inputs.evaluation_type(r) == "rag"],
                  "reviewed_case_ids": [], "corrections": []}
        _write_new(output / "claim_review.json", review)
        return {"status": "pending", "required_cases": len(review["required_case_ids"])}


def _reviewed_claims(output, records):
    review = dataset.loads((output / "claim_review.json").read_text())
    rag_ids = {r["id"] for r in records if inputs.evaluation_type(r) == "rag"}
    fields = {"status", "reviewer_ids", "reviewed_on", "input_hashes", "required_case_ids", "reviewed_case_ids", "corrections"}
    if not isinstance(review, dict) or set(review) != fields:
        raise ValueError("Invalid claim review structure")
    for name in ("reviewer_ids", "required_case_ids", "reviewed_case_ids"):
        value = review[name]
        if (not isinstance(value, list) or any(not isinstance(s, str) or not s.strip() for s in value) or
            len(value) != len(set(value))):
            raise ValueError("Review identifiers must be unique string lists")
    if not isinstance(review["corrections"], list) or not isinstance(review["reviewed_on"], str):
        raise ValueError("Response/claim correspondence review is incomplete")
    if (review["status"] != "checked" or not review["reviewer_ids"] or
        any(not isinstance(s, str) or not s.strip() for s in review["reviewer_ids"]) or
        set(review["required_case_ids"]) != rag_ids or set(review["reviewed_case_ids"]) != rag_ids or
        len(review["reviewed_case_ids"]) != len(rag_ids)):
        raise ValueError("Response/claim correspondence review is incomplete")
    date.fromisoformat(review["reviewed_on"])
    expected = {name: digest((output / name).read_bytes()) for name in ("responses.jsonl", "claims.jsonl")}
    if review["input_hashes"] != expected:
        raise ValueError("Claim review inputs changed")
    proposals, responses = _rows(output / "claims.jsonl"), _rows(output / "responses.jsonl")
    if set(proposals) != rag_ids:
        raise ValueError("Claim proposals must cover RAG cases only and completely")
    claims = {i: row["claims"] if row["status"] == "ok" else None for i, row in proposals.items()}
    seen = set()
    for edit in review["corrections"]:
        if not isinstance(edit, dict) or set(edit) != {"id", "before", "after", "reason"}:
            raise ValueError("Invalid claim correction structure")
        identifier = edit["id"]
        if (identifier not in rag_ids or identifier in seen or edit["before"] != claims[identifier] or
            not isinstance(edit["reason"], str) or not edit["reason"].strip() or
            responses[identifier]["status"] != "ok" or not responses[identifier]["response"].strip()):
            raise ValueError("Stale, duplicate, unknown, or unexplained claim correction")
        claims[identifier] = inputs.parse_claims(json.dumps({"claims": edit["after"]}, ensure_ascii=False))
        seen.add(identifier)
    return claims


def score_records(records, responses, claims, encoder, threshold):
    """Pure mixed-task dispatch; fixture use does not establish model quality."""
    identifiers = [r["id"] for r in records]
    if len(set(identifiers)) != len(identifiers) or set(responses) - set(identifiers):
        raise ValueError("Duplicate records or unknown response IDs")
    rag = [r for r in records if inputs.evaluation_type(r) == "rag"]
    if set(claims) - {r["id"] for r in rag}:
        raise ValueError("Claims contain non-RAG or unknown IDs")
    for row in responses.values():
        if (not isinstance(row, dict) or row.get("status") not in {"ok", "generation_error"} or
            row["status"] == "ok" and not isinstance(row.get("response"), str)):
            raise ValueError("Malformed generation artifact")
    rag_outputs = {r["id"]: responses[r["id"]] for r in rag if r["id"] in responses}
    scored_rag = compute_metrics([inputs.rag_scoring_record(r) for r in rag], rag_outputs, encoder, claims, threshold)
    by_id = {row["id"]: row for row in scored_rag["per_example"]}
    rows, groups = [], defaultdict(list)
    for record in records:
        identifier, kind = record["id"], inputs.evaluation_type(record)
        if kind == "rag":
            row = by_id[identifier]
            output = responses.get(identifier)
            row.update(evaluation_type=kind, attempted=output is not None,
                       status=("missing_response" if output is None else "generation_error" if output["status"] != "ok"
                               else "empty_response" if not output["response"].strip() else "ok"))
        else:
            row = score_extended_case(record, responses.get(identifier))
        row["cohort"] = inputs.cohort(record)
        rows.append(row)
        groups[row["cohort"]].append(row)
    aggregate = {}
    for label, group in sorted(groups.items()):
        dialogue = [r for r in group if r["evaluation_type"] == "rag"]
        structured = [r for r in group if r["evaluation_type"] != "rag"]
        aggregate[label] = {"n_cases": len(group),
                            "rag": ({"coverage": {"n_total": len(dialogue), "n_attempted": sum(r["attempted"] for r in dialogue),
                                      "status_counts": dict(sorted(Counter(r["status"] for r in dialogue).items()))},
                                     "metrics": aggregate_results(dialogue)} if dialogue else None),
                            "structured": aggregate_extended_results(structured) if structured else None}
    return {"per_example": rows, "aggregate": {"by_cohort": aggregate},
            "interpretation": "Separate metric families and cohorts; no composite score or automated RAG correctness verdict."}


def score_stage(root, config, replay=False, encoder_factory=local_encoder):
    output, records, manifest = _state(root, config)
    with _lock(output):
        output, records, manifest = _state(root, config)
        if any(manifest["stages"].get(s) != "complete" for s in ("responses", "claims", "calibration")):
            raise ValueError("Complete calibration, responses, and claims before scoring")
        scored = manifest["stages"].get("scoring") == "complete"
        if replay and not scored:
            raise ValueError("No completed scores to replay")
        if scored and not replay:
            raise ValueError("Scores are frozen; use replay or a new experiment")
        responses = _rows(output / "responses.jsonl")
        if set(responses) != {r["id"] for r in records}:
            raise ValueError("Every case needs a recorded generation attempt")
        claims = _reviewed_claims(output, records)
        calibration = dataset.loads((output / "calibration.json").read_text())
        if replay:
            from .embeddings import ReplayEncoder
            encoder = ReplayEncoder(output)
        else:
            encoder = encoder_factory(config, output)
        result = score_records(records, responses, claims, encoder, calibration["threshold"])
        if replay:
            if result != dataset.loads((output / "scores.json").read_text()):
                raise ValueError("Replayed scores differ from frozen results")
            return {"status": "exact_replay", "cases": len(records)}
        encoder.save(output)
        _write_new(output / "scores.json", result)
        manifest["stages"]["scoring"] = "complete"
        manifest.update(status="complete", completed_at=timestamp())
        _seal(output, manifest, ["scores.json", "embeddings.json", "embeddings.npz", "claim_review.json"])
        return {"status": "complete", "cases": len(records)}
