"""Portable analysis of the frozen Week 3 run; no tuning or answer generation."""

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import statistics

from .evaluator import faithfulness, semantic_relevance
from .week3_inputs import cohort, evaluation_type


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def demonstration_ids(records):
    """Fixed ID-order selection, independent of predictions or their scores."""
    def first(kind, language, n):
        return [r['id'] for r in sorted(records, key=lambda r: r['id'])
                if evaluation_type(r) == kind and r['language'] == language][:n]
    return {
        'STUM': first('stum_spatial', 'en', 3) + first('stum_spatial', 'zh', 2)
                + [r['id'] for r in sorted(records, key=lambda r: r['id'])
                   if evaluation_type(r) == 'stum_temporal'],
        'SEOM': first('seom_entities', 'en', 3) + first('seom_entities', 'zh', 3),
        'HTD-IRL': first('htd_task_alignment', 'en', 3) + first('htd_task_alignment', 'zh', 3),
    }


def result_tables(scores):
    """Keep cohorts, metric applicability, nulls, and output failures explicit."""
    rag, structured = [], []
    for label, group in scores['aggregate']['by_cohort'].items():
        if group['rag']:
            for metric, summary in group['rag']['metrics']['overall'].items():
                rag.append({'cohort': label, 'metric': metric, **summary})
        if group['structured']:
            for kind, summary in group['structured']['by_type'].items():
                structured.append({
                    'cohort': label, 'type': kind, 'n_total': summary['n_total'],
                    'n_eligible': summary['n_eligible'], 'n_parsed': summary['n_parsed'],
                    'parse_coverage': summary['parse_coverage'],
                    'task_success': summary['task_success'],
                    'metrics': summary['metrics'], 'status_counts': summary['case_status_counts'],
                })
    return {'rag': rag, 'structured': structured}


def stage_summary(rows):
    """Per-attempt durations, with the number of timed attempts retained."""
    durations = [r['elapsed_seconds'] for r in rows if 'elapsed_seconds' in r]
    ordered = sorted(durations)
    return {'n_attempts': len(rows), 'status_counts': dict(sorted(Counter(r['status'] for r in rows).items())),
            'finish_reasons': dict(sorted(Counter(r.get('finish_reason', 'unavailable') for r in rows).items())),
            'n_timed': len(durations),
            'mean_seconds': statistics.mean(durations) if durations else None,
            'median_seconds': statistics.median(durations) if durations else None,
            'p95_nearest_rank_seconds': ordered[max(0, math.ceil(.95 * len(ordered))-1)] if ordered else None,
            'max_seconds': max(durations) if durations else None,
            'total_generation_tokens': sum(r.get('generation_tokens', 0) for r in rows)}


def score_probes(records, encoder, threshold):
    """Score prewritten boundary candidates separately from generated answers."""
    rows = []
    for record in records:
        for probe in record.get('reference', {}).get('metric_probes', []):
            claims = [c['text'] for c in probe['claims']]
            actual = faithfulness(claims, record['context'], encoder, threshold).to_dict()
            ideal = sum(c['support'] == 'supported' for c in probe['claims']) / len(claims)
            if ideal != probe['ideal_property_score']:
                raise ValueError('Probe annotation fraction is inconsistent')
            rows.append({'id': record['id'], 'probe_id': probe['probe_id'],
                         'cohort': cohort(record), 'language': record['language'],
                         'candidate_response': probe['candidate_response'],
                         'source': 'fixed_dataset_candidate_not_model_generation',
                         'ideal_faithfulness': ideal,
                         'faithfulness_proxy': actual,
                         'semantic_relevance': semantic_relevance(record['query'], probe['candidate_response'], encoder).to_dict(),
                         'claim_annotations': probe['claims']})
    return {'threshold': threshold, 'purpose': 'Diagnostic only; no post-hoc fitting.', 'per_probe': rows}


def inspect_run(root, config):
    """Load complete frozen results and verify supplementary review coverage."""
    output = Path(root) / config['output']
    records = read_jsonl(output / 'dataset.jsonl')
    responses = read_jsonl(output / 'responses.jsonl')
    claims = read_jsonl(output / 'claims.jsonl')
    scores = json.loads((output / 'scores.json').read_text())
    reviews = read_jsonl(output / 'response_review.jsonl')
    structured_review = read_jsonl(output / 'structured_failure_review.jsonl')
    rag_ids = {r['id'] for r in records if evaluation_type(r) == 'rag'}
    if len(reviews) != len(rag_ids) or {r['id'] for r in reviews} != rag_ids:
        raise ValueError('Technical RAG inspection must cover every RAG response exactly once')
    for r in reviews:
        if r['review_type'] != 'technical_inspection' or r['independent_human_assessment'] is not False:
            raise ValueError('Do not misrepresent technical inspection as independent human assessment')
    review_metadata = json.loads((output / 'response_review_metadata.json').read_text())
    failed_structured = {r['id'] for r in scores['per_example']
                         if r['evaluation_type'] != 'rag' and r['task_success']['value'] != 1}
    if len(structured_review) != len(failed_structured) or {r['id'] for r in structured_review} != failed_structured:
        raise ValueError('Technical structured inspection must cover every non-successful case exactly once')
    if any(r['score_adjusted'] is not False or r['independent_human_assessment'] is not False for r in structured_review):
        raise ValueError('Technical inspection cannot replace frozen scores or independent assessment')
    for name in ['responses.jsonl', 'dataset.jsonl', 'response_review.jsonl', 'structured_failure_review.jsonl']:
        if review_metadata['input_hashes'][name] != sha256(output / name):
            raise ValueError('Technical response inspection inputs changed')
    return {'records': records, 'responses': responses, 'claims': claims, 'scores': scores,
            'reviews': reviews, 'structured_review': structured_review, 'tables': result_tables(scores),
            'timing': {'responses': stage_summary(responses), 'claim_extraction': stage_summary(claims)},
            'demonstration_ids': demonstration_ids(records)}
