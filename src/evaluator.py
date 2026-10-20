"""Core RAG metrics with explicit applicability, errors, and bilingual diagnostics.

Context recall uses reviewed reference-fact support annotations. Faithfulness is
an embedding retrieval proxy, not a logical entailment certificate. Embedding
providers are injected, so deterministic mathematical tests need no model download.
"""

from collections import defaultdict
from dataclasses import asdict, dataclass, field
import math
import re
import statistics
import unicodedata


@dataclass
class MetricResult:
    """One value, its applicability/error status, and auditable evidence."""
    value: float | None
    status: str = "ok"
    details: dict = field(default_factory=dict)

    def to_dict(self):
        """Serialize without replacing missing values by numerical zeros."""
        return asdict(self)


def cosine(left, right):
    """Raw cosine in [-1,1]; reject malformed or zero-norm embeddings."""
    left, right = list(left), list(right)
    if not left or len(left) != len(right) or not all(math.isfinite(float(v)) for v in left + right):
        raise ValueError("Invalid embedding dimensions or non-finite values")
    norm = math.sqrt(sum(float(v)**2 for v in left) * sum(float(v)**2 for v in right))
    if norm == 0:
        raise ValueError("Zero-norm embedding")
    return max(-1.0, min(1.0, sum(float(a)*float(b) for a, b in zip(left, right))/norm))


def context_recall(record):
    """Fraction of canonical required facts supported by reviewed supplied context.

    Reference facts are held stable when evidence is removed. This prevents an
    ideal clarification from becoming a misleading perfect recall denominator.
    Annotation validation and frozen input hashes are prerequisites.
    """
    facts = record["evaluation_labels"]["required_facts"]
    if not facts:
        return MetricResult(None, "not_applicable", {"required_facts": 0})
    supported = sum(f["context_support"] == "supported" for f in facts)
    if not record["context"] and supported:
        raise ValueError("Positive fact support cannot accompany empty context")
    return MetricResult(supported/len(facts), details={"supported_facts": supported,
                        "required_facts": len(facts), "support_source": "reviewed_reference_annotations"})


def tokenize(text, language):
    """NFC word tokens; jieba for Chinese/mixed Chinese and regex for English."""
    text = unicodedata.normalize("NFC", text).lower()
    if language == "zh":
        import jieba
        import logging
        jieba.setLogLevel(logging.ERROR)
        tokens = jieba.lcut(text)
    elif language == "en":
        tokens = re.findall(r"[a-z]+(?:'[a-z]+)?|\d+(?:[.:]\d+)*", text)
    else:
        raise ValueError("Language must be en or zh")
    return [t.strip() for t in tokens if any(c.isalnum() for c in t)]


def lexical_recall(reference, contexts, language):
    """Separate unique-token recall diagnostic; it does not establish fact support."""
    required = set(tokenize(reference, language))
    available = set(tokenize("\n".join(contexts), language))
    if not required:
        return MetricResult(None, "not_applicable")
    return MetricResult(len(required & available)/len(required), details={
        "reference_tokens": len(required), "matched_tokens": len(required & available),
        "tokenizer": "jieba" if language == "zh" else "english_regex_v1"})


def evidence_segments(contexts):
    """Punctuation-based evidence units, with full text and stable ordering."""
    result = []
    for passage in contexts:
        for segment in re.split(r"(?<=[.!?])\s+|[\n]+|(?<=[。！？；;])", passage):
            if segment.strip():
                result.append(segment.strip())
    return result


def support_scores(claims, contexts, encoder):
    """Maximum asymmetric claim-to-evidence cosine and its best evidence segment."""
    segments = evidence_segments(contexts)
    if not segments:
        return [{"claim": claim, "score": None, "evidence_segment": None} for claim in claims]
    claim_vectors = encoder.encode(claims, prefix="query: ")
    evidence_vectors = encoder.encode(segments, prefix="passage: ")
    results = []
    for claim, vector in zip(claims, claim_vectors):
        similarities = [cosine(vector, evidence) for evidence in evidence_vectors]
        index = max(range(len(similarities)), key=similarities.__getitem__)
        results.append({"claim": claim, "score": similarities[index],
                        "evidence_segment": segments[index], "segment_index": index})
    return results


def faithfulness(claims, contexts, encoder, threshold):
    """Fraction of extracted claims passing the calibrated retrieval threshold."""
    if not 0 <= threshold <= 1:
        raise ValueError("Support threshold must be in [0,1]")
    if claims is None:
        return MetricResult(None, "scorer_error", {"reason": "missing_or_invalid_claim_extraction"})
    if not claims:
        return MetricResult(None, "not_applicable", {"claims": 0})
    judgments = support_scores(claims, contexts, encoder)
    for judgment in judgments:
        judgment["supported_proxy"] = judgment["score"] is not None and judgment["score"] >= threshold
    count = sum(j["supported_proxy"] for j in judgments)
    return MetricResult(count/len(judgments), details={"threshold": threshold,
                        "supported_claims_proxy": count, "claim_count": len(judgments),
                        "judgments": judgments, "definition": "embedding_retrieval_proxy_v1"})


def semantic_relevance(query, response, encoder):
    """Raw cosine between symmetric multilingual query/response embeddings."""
    if not response.strip():
        return MetricResult(None, "empty_response")
    left, right = encoder.encode([query, response], prefix="query: ")
    return MetricResult(cosine(left, right), details={"model_id": encoder.model_id,
                        "prefix": "query: ", "range": [-1, 1]})


def select_threshold(labeled_scores, grid):
    """Maximize calibration balanced accuracy, resolving ties toward larger tau."""
    positives = sum(bool(p["supported"]) for p in labeled_scores)
    negatives = len(labeled_scores)-positives
    if not positives or not negatives:
        raise ValueError("Both supported and unsupported calibration classes are required")
    candidates = []
    for threshold in grid:
        tp = sum(p["supported"] and p["score"] is not None and p["score"] >= threshold for p in labeled_scores)
        tn = sum(not p["supported"] and (p["score"] is None or p["score"] < threshold) for p in labeled_scores)
        candidates.append({"threshold": threshold, "balanced_accuracy": (tp/positives+tn/negatives)/2,
                           "tp": tp, "tn": tn, "fp": negatives-tn, "fn": positives-tp})
    chosen = max(candidates, key=lambda c: (c["balanced_accuracy"], c["threshold"]))
    return {**chosen, "positive_count": positives, "negative_count": negatives, "candidates": candidates}


def _summary(rows):
    """Summarize each metric over scored values with separate missing/error counts."""
    names = sorted({key for row in rows for key in row["metrics"]})
    result = {}
    for name in names:
        metrics = [row["metrics"][name] for row in rows]
        values = [m["value"] for m in metrics if m["status"] == "ok" and m["value"] is not None]
        result[name] = {"n_total": len(metrics), "n_scored": len(values),
                        "n_not_applicable": sum(m["status"] == "not_applicable" for m in metrics),
                        "n_errors": sum(m["status"].endswith("error") for m in metrics),
                        "n_empty_response": sum(m["status"] == "empty_response" for m in metrics),
                        "mean": statistics.mean(values) if values else None,
                        "std_population": statistics.pstdev(values) if values else None}
    return result


def aggregate_results(rows):
    """Population mean/std over defined values with explicit status denominators."""
    result = {"overall": _summary(rows)}
    for field, label in [("domain", "by_domain"), ("difficulty", "by_difficulty"),
                         ("language", "by_language"), ("subset", "by_subset")]:
        groups = defaultdict(list)
        for row in rows:
            groups[row[field]].append(row)
        result[label] = {key: _summary(value) for key, value in sorted(groups.items())}
    tags = defaultdict(list)
    for row in rows:
        for tag in row["edge_case_tags"]:
            tags[tag].append(row)
    result["by_edge_tag"] = {tag: _summary(value) for tag, value in sorted(tags.items())}
    return result


def compute_metrics(records, responses, encoder, claims_by_id, threshold):
    """Return per-example scores and domain/tier/language/subset aggregates.

    Responses are keyed by case ID; successful entries contain status='ok' and
    response text. Missing outputs are errors. Reference annotations are never
    inferred from the generated response. Claim extraction failures are retained.
    """
    if len({r["id"] for r in records}) != len(records):
        raise ValueError("Duplicate case IDs")
    rows = []
    def safe(call):
        try:
            return call().to_dict()
        except Exception as exc:
            return MetricResult(None, "scorer_error", {"error_type": type(exc).__name__}).to_dict()
    for record in records:
        labels = record["evaluation_labels"]
        output = responses.get(record["id"], {"status": "generation_error"})
        if isinstance(output, str):
            output = {"status": "ok", "response": output}
        metrics = {"context_recall": safe(lambda: context_recall(record)),
                   "lexical_reference_recall": safe(lambda: lexical_recall(record["ideal_response"], record["context"], record["language"]))}
        if output["status"] != "ok":
            for name in ("faithfulness_proxy", "semantic_relevance"):
                metrics[name] = MetricResult(None, "generation_error").to_dict()
        else:
            response = output["response"]
            metrics["semantic_relevance"] = safe(lambda: semantic_relevance(record["query"], response, encoder))
            metrics["faithfulness_proxy"] = (safe(lambda: faithfulness(claims_by_id.get(record["id"]), record["context"], encoder, threshold))
                                              if response.strip() else MetricResult(None, "empty_response").to_dict())
        rows.append({"id": record["id"], "domain": record["domain"], "difficulty": record["difficulty"],
                     "language": record["language"], "subset": labels["subset"],
                     "edge_case_tags": labels["edge_case_tags"], "metrics": metrics})
    return {"per_example": rows, "aggregate": aggregate_results(rows)}
