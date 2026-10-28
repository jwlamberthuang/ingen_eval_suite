"""Guard analysis denominators and the separation of diagnostic candidates."""

from copy import deepcopy
from pathlib import Path
import json

import pytest

from src.week3_analysis import demonstration_ids, result_tables, score_probes, stage_summary

ROOT = Path(__file__).resolve().parents[1]


def test_demonstrations_are_bilingual_and_independent_of_record_order():
    rows = [json.loads(l) for l in (ROOT / 'data/W01_Evaluation_Dataset_v2.jsonl').read_text().splitlines()]
    selected = demonstration_ids(rows)
    assert selected == demonstration_ids(list(reversed(rows)))
    assert {k: len(v) for k, v in selected.items()} == {'STUM': 10, 'SEOM': 6, 'HTD-IRL': 6}
    by_id = {r['id']: r for r in rows}
    for identifiers in selected.values():
        assert len(set(identifiers)) == len(identifiers)
        assert {by_id[i]['language'] for i in identifiers} == {'en', 'zh'}
    assert sum(by_id[i]['evaluation_type'] == 'stum_temporal' for i in selected['STUM']) == 5


def test_boundary_diagnostic_does_not_replace_annotation_with_proxy():
    class AlwaysSimilar:
        model_id = 'synthetic-identical-vectors'
        def encode(self, texts, prefix='query: '):
            return [[1., 0.] for _ in texts]
    records = [{'id': 'fixture', 'evaluation_type': 'rag', 'language': 'en',
                'annotations': {'subset': 'held_out'}, 'query': 'How many?', 'context': ['Three remain.'],
                'reference': {'metric_probes': [{'probe_id': 'fixed-wrong',
                    'candidate_response': 'Four remain.', 'claims': [{'text': 'Four remain.', 'support': 'contradicted'}],
                    'ideal_property_score': 0.0}]}}]
    probe = score_probes(records, AlwaysSimilar(), .8)['per_probe'][0]
    assert probe['ideal_faithfulness'] == 0
    assert probe['faithfulness_proxy']['value'] == 1
    assert probe['source'] == 'fixed_dataset_candidate_not_model_generation'
    assert probe['cohort'] == 'new_held_out'
    changed = deepcopy(records)
    changed[0]['reference']['metric_probes'][0]['ideal_property_score'] = .5
    with pytest.raises(ValueError, match='annotation fraction'):
        score_probes(changed, AlwaysSimilar(), .8)


def test_timing_retains_untimed_errors_and_nearest_rank_percentile():
    rows = [{'status': 'ok', 'elapsed_seconds': i, 'finish_reason': 'stop', 'generation_tokens': 2}
            for i in range(1, 21)] + [{'status': 'generation_error'}]
    summary = stage_summary(rows)
    assert summary['n_attempts'] == 21 and summary['n_timed'] == 20
    assert summary['status_counts'] == {'generation_error': 1, 'ok': 20}
    assert summary['mean_seconds'] == 10.5 and summary['p95_nearest_rank_seconds'] == 19
    assert summary['total_generation_tokens'] == 40
    assert stage_summary([])['mean_seconds'] is None


def test_tables_preserve_undefined_success_and_parse_denominators():
    original = {'aggregate': {'by_cohort': {'new_held_out': {
        'rag': None, 'structured': {'by_type': {'seom_entities': {
            'n_total': 3, 'n_eligible': 2, 'n_parsed': 1, 'parse_coverage': .5,
            'task_success': {'n_total': 3, 'n_scored': 2, 'mean': .5},
            'metrics': {'entity_recall': {'n_total': 3, 'n_scored': 0, 'mean': None}},
            'case_status_counts': {'ok': 1, 'parse_error': 1, 'invalid_reference': 1},
        }}}}}}}
    row = result_tables(original)['structured'][0]
    assert row['n_total'] == 3 and row['n_eligible'] == 2 and row['n_parsed'] == 1
    assert row['task_success']['mean'] == .5
    assert row['metrics']['entity_recall']['mean'] is None
