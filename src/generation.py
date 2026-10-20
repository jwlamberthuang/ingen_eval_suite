"""Local MLX generation and separately recorded claim extraction, with resume guards."""

from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import time

from .model_inputs import SYSTEM_PROMPT, CLAIM_PROMPT, generation_messages, claim_messages, parse_claims


def canonical_hash(value):
    """Content identity independent of JSON whitespace."""
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def read_jsonl(path):
    """Load a complete append-only artifact, rejecting duplicate case identities."""
    if not path.exists():
        return {}
    result = {}
    for line in path.read_text().splitlines():
        value = json.loads(line)
        if value["id"] in result:
            raise ValueError("Duplicate artifact case ID")
        result[value["id"]] = value
    return result


def append_jsonl(path, value):
    """Flush a complete record before proceeding to the next case."""
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, allow_nan=False)+'\n')
        handle.flush()


def generate_run(root, config):
    """Generate each response and atomic-claim proposal once, with no answer retries.

    MLX runs only when invoked, so importing the suite needs no Apple GPU runtime.
    All full inputs and attempts are retained. Failed outputs remain errors.
    """
    import mlx.core as mx
    from mlx_lm import load, stream_generate
    from mlx_lm.sample_utils import make_sampler
    from huggingface_hub import snapshot_download

    root = Path(root)
    dataset_path = root/config["dataset"]
    dataset_hash = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    records = [json.loads(line) for line in dataset_path.read_text().splitlines() if line.strip()]
    output = root/config["output"]
    output.mkdir(parents=True, exist_ok=True)
    generation = config["generation"]
    source_hashes = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in [root/"src/generation.py", root/"src/model_inputs.py"]}
    identity = {"dataset_sha256": dataset_hash, "generation": generation,
                "system_prompt": SYSTEM_PROMPT, "claim_prompt": CLAIM_PROMPT,
                "source_hashes": source_hashes}
    fingerprint = canonical_hash(identity)
    manifest_path = output/"run_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if manifest["generation_fingerprint"] != fingerprint:
            raise ValueError("Existing generation inputs changed; use a new run output directory")
    else:
        manifest = {"run_name": config["run_name"], "generation_fingerprint": fingerprint,
                    **identity, "dataset_file": config["dataset"], "context_mode": "fixed",
                    "generation_runtime": {"system": platform.system(), "architecture": platform.machine(),
                                           "mlx_lm": importlib.metadata.version("mlx-lm"),
                                           "mlx": importlib.metadata.version("mlx"),
                                           "transformers": importlib.metadata.version("transformers")},
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "status": "running", "retry_policy": "No substantive answer retries; one recorded local attempt per stage."}
        manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
    responses = read_jsonl(output/"responses.jsonl")
    claims = read_jsonl(output/"claims.jsonl")
    checkpoint = snapshot_download(generation["model_id"], revision=generation["revision"],
                                   local_files_only=True,
                                   allow_patterns=["*.json", "*.safetensors", "*.model", "*.txt"])
    model, tokenizer = load(checkpoint)
    sampler = make_sampler(temp=generation["temperature"])

    def infer(messages):
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        input_tokens = tokenizer.encode(prompt)
        if len(input_tokens) > generation["input_limit_tokens"]:
            raise ValueError("Generation input exceeds the declared token limit")
        started = time.perf_counter()
        mx.random.seed(generation["seed"])
        pieces, last = [], None
        for piece in stream_generate(model, tokenizer, prompt=prompt,
                                     max_tokens=generation["max_new_tokens"], sampler=sampler):
            pieces.append(piece.text)
            last = piece
            if time.perf_counter()-started > generation["case_timeout_seconds"]:
                raise TimeoutError("Local inference exceeded its time budget")
        return {"response": ''.join(pieces), "elapsed_seconds": time.perf_counter()-started,
                "prompt_tokens": len(input_tokens), "generation_tokens": last.generation_tokens if last else 0,
                "finish_reason": last.finish_reason if last else "stop",
                "peak_memory_gb": last.peak_memory if last else None,
                "rendered_prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()}

    started_run = time.perf_counter()
    for index, record in enumerate(records, 1):
        identifier = record["id"]
        if identifier not in responses:
            messages = generation_messages(record)
            result = {"id": identifier, "input_messages": messages, "attempt": 1,
                      "input_sha256": canonical_hash({"messages": messages, "generation": generation}),
                      "started_at": datetime.now(timezone.utc).isoformat()}
            try:
                result.update(infer(messages), status="ok")
            except Exception as exc:
                result.update(status="generation_error", error_type=type(exc).__name__)
            result["finished_at"] = datetime.now(timezone.utc).isoformat()
            append_jsonl(output/"responses.jsonl", result)
            responses[identifier] = result
        response = responses[identifier]
        if identifier not in claims:
            extracted = {"id": identifier, "attempt": 1, "extractor": "qwen-json-atomic-v1"}
            if response["status"] == "ok" and response["response"].strip():
                messages = claim_messages(record, response["response"])
                extracted["input_messages"] = messages
                try:
                    raw = infer(messages)
                    extracted.update(raw)
                    extracted["claims"] = parse_claims(raw["response"])
                    extracted["status"] = "ok"
                except Exception as exc:
                    extracted.update(status="scorer_error", claims=None, error_type=type(exc).__name__)
            else:
                extracted.update(status="generation_error", claims=None)
            append_jsonl(output/"claims.jsonl", extracted)
            claims[identifier] = extracted
        print(f"{index}/{len(records)} {identifier}: response={response['status']} claims={claims[identifier]['status']}", flush=True)
        mx.clear_cache()
    manifest.update(status="generation_complete", completed_at=datetime.now(timezone.utc).isoformat(),
                    response_count=len(responses), claim_record_count=len(claims),
                    invocation_elapsed_seconds=time.perf_counter()-started_run,
                    generation_errors=sum(r["status"] != "ok" for r in responses.values()),
                    claim_extraction_errors=sum(c["status"] != "ok" for c in claims.values()))
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
