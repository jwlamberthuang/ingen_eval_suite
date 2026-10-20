"""Calibration restricted to declared families, scoring, and exact artifact replay."""

from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from .embeddings import SentenceEncoder, ReplayEncoder
from .evaluator import compute_metrics, evidence_segments, support_scores, select_threshold
from .generation import read_jsonl, canonical_hash


def write_json(path, value):
    """Write portable UTF-8 JSON without NaN values."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def _encoder(config, output):
    """Create the pinned encoder and reuse vectors only from the same revision."""
    import torch
    torch.set_num_threads(4)
    settings = config["embedding"]
    encoder = SentenceEncoder(**{key: value for key, value in settings.items() if key != "max_tokens"},
                              max_tokens=settings["max_tokens"])
    if (output/"embeddings.json").exists():
        previous = ReplayEncoder(output)
        if (previous.model_id, previous.revision) != (encoder.model_id, encoder.revision):
            raise ValueError("Embedding artifact revision differs from the requested scorer")
        encoder.cache.update(previous.cache)
    return encoder


def dataset_records(root, config):
    """Load source records only after data/schema/construction integrity checks."""
    import sys
    sys.path.insert(0, str(root/"scripts/datasets"))
    from validate_dataset import load_jsonl, validate_records, manifest_errors
    path = root/config["dataset"]
    records = load_jsonl(path)
    report = validate_records(records, "release")
    report["errors"].extend(manifest_errors(path, json.loads((root/config["dataset_manifest"]).read_text())))
    if report["errors"]:
        raise ValueError("Dataset validation or manifest integrity failed")
    return records


def calibrate_run(root, config):
    """Freeze tau on existing reviewed calibration facts before held-out scoring."""
    root, output = Path(root), Path(root)/config["output"]
    output.mkdir(parents=True, exist_ok=True)
    records = dataset_records(root, config)
    encoder = _encoder(config, output)
    labeled = []
    for record in records:
        if record["evaluation_labels"]["subset"] != "calibration":
            continue
        facts = record["evaluation_labels"]["required_facts"]
        for fact, scored in zip(facts, support_scores([f["text"] for f in facts], record["context"], encoder)):
            labeled.append({"case_id": record["id"], "fact_id": fact["fact_id"],
                            "language": record["language"], "claim": fact["text"],
                            "supported": fact["context_support"] == "supported",
                            "support_label": fact["context_support"],
                            "label_source": "reviewed_calibration_reference_fact", **scored})
    selected = select_threshold(labeled, config["support"]["threshold_grid"])
    result = {**selected, "dataset_sha256": hashlib.sha256((root/config["dataset"]).read_bytes()).hexdigest(),
              "embedding": config["embedding"], "support_settings": config["support"],
              "calibration_case_ids": [r["id"] for r in records if r["evaluation_labels"]["subset"] == "calibration"],
              "calibration_scope": "Reference-fact support only; no held-out data or generated responses used.",
              "limitations": ["Calibration reference statements may differ from model-generated claims.",
                              "Existing single-reviewer support annotations are reused; no new independent human agreement study."]}
    if (output/"calibration.json").exists():
        previous = json.loads((output/"calibration.json").read_text())
        if previous != result:
            raise ValueError("Calibration is frozen; changed results require a separately named run")
    write_json(output/"calibration.json", result)
    (output/"calibration_claims.jsonl").write_text(''.join(json.dumps(row, ensure_ascii=False)+'\n' for row in labeled))
    encoder.save(output)
    print(json.dumps({key: result[key] for key in ["threshold", "balanced_accuracy", "positive_count", "negative_count", "tp", "tn", "fp", "fn"]}, indent=2))


def _claims_for_scoring(output, records):
    """Apply inspected response-claim corrections without rewriting raw proposals."""
    review = json.loads((output/"claim_review.json").read_text())
    if review["status"] != "checked" or set(review["reviewed_case_ids"]) != {r["id"] for r in records}:
        raise ValueError("Response/claim correspondence review is incomplete")
    for filename, expected in review["input_hashes"].items():
        if hashlib.sha256((output/filename).read_bytes()).hexdigest() != expected:
            raise ValueError("Response or claim artifacts changed since inspection")
    proposals = read_jsonl(output/"claims.jsonl")
    claims = {identifier: row["claims"] if row["status"] == "ok" else None for identifier, row in proposals.items()}
    corrections = read_jsonl(output/"claim_corrections.jsonl")
    for identifier, correction in corrections.items():
        if correction["before"] != claims[identifier] or not correction["reason"]:
            raise ValueError("Stale or unexplained claim correction")
        claims[identifier] = correction["after"]
    return claims


def score_run(root, config, replay=False):
    """Score frozen outputs, or reproduce the same scores using saved embeddings."""
    root, output = Path(root), Path(root)/config["output"]
    records = dataset_records(root, config)
    calibration = json.loads((output/"calibration.json").read_text())
    if calibration["dataset_sha256"] != hashlib.sha256((root/config["dataset"]).read_bytes()).hexdigest():
        raise ValueError("Dataset changed since calibration")
    if calibration["embedding"] != config["embedding"] or calibration["support_settings"] != config["support"]:
        raise ValueError("Scorer settings changed since calibration")
    responses = read_jsonl(output/"responses.jsonl")
    if set(responses) != {r["id"] for r in records}:
        raise ValueError("Generation attempts must cover the complete dataset")
    encoder = ReplayEncoder(output) if replay else _encoder(config, output)
    claims = _claims_for_scoring(output, records)
    if not replay:
        query_inputs, passage_inputs = [], []
        for record in records:
            result = responses[record["id"]]
            if result["status"] == "ok" and result["response"].strip():
                query_inputs.extend([record["query"], result["response"], *(claims.get(record["id"]) or [])])
                passage_inputs.extend(evidence_segments(record["context"]))
        encoder.encode(list(dict.fromkeys(query_inputs)), prefix="query: ")
        encoder.encode(list(dict.fromkeys(passage_inputs)), prefix="passage: ")
    results = compute_metrics(records, responses, encoder, claims, calibration["threshold"])
    if replay:
        original = json.loads((output/"scores.json").read_text())
        if results != original:
            raise ValueError("Replayed scores differ from saved results")
        print('Exact score replay passed for all cases and aggregates.')
        return results
    write_json(output/"scores.json", results)
    encoder.save(output)
    manifest_path = output/"run_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["scoring"] = {"embedding": config["embedding"], "support": calibration,
                           "source_hashes": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                                             for p in [root/"src/evaluator.py", root/"src/embeddings.py", root/"src/experiment.py"]},
                           "population_std_ddof": 0, "case_count": len(records),
                           "primary_subset": "held_out", "status": "complete"}
    manifest["artifacts"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in sorted(output.iterdir()) if p.is_file() and p.name != "run_manifest.json"}
    write_json(manifest_path, manifest)
    print(json.dumps(results["aggregate"]["overall"], indent=2))
    return results
