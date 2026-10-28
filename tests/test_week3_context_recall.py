"""Hand-worked answer-slot examples and guarded annotation replay checks."""

from copy import deepcopy

import pytest
from jsonschema import ValidationError

from src.evaluator import context_recall
from src.week3_analysis import read_jsonl
from src.week3_context_recall import AMENDMENT, ROOT, annotation_digest, apply_amendment, load, rescore, run
from src.week3_inputs import generation_messages, rag_scoring_record
from src import week3_context_recall as correction

BASE = read_jsonl(ROOT / 'data/W01_Evaluation_Dataset_v2.jsonl')
PATCH = load(ROOT / AMENDMENT)


@pytest.mark.parametrize('number, expected', [
    (101, .5), (113, .5), (114, 0), (115, 0), (116, 0), (119, 0),
    (120, 0), (121, .5), (122, 0), (125, 0), (126, 0), (128, 0),
    (129, 0), (168, .5), (172, 1), (186, None), (191, 0),
])
def test_manually_verified_requested_answer_coverage(number, expected):
    # Four partial two-part questions are 1/2; eleven unresolved single targets
    # are 0/1; washing policy is 1/1; unidentified speaker has no unique target.
    revised = apply_amendment(BASE, PATCH)
    case = next(r for r in revised if int(r['id'].split('-')[-2]) == number)
    actual = context_recall(rag_scoring_record(case))
    assert actual.value == expected
    if expected is None:
        assert actual.status == 'not_applicable'


def test_amendment_preserves_inputs_and_all_fields_except_fact_inventory():
    before = deepcopy(BASE)
    revised = apply_amendment(BASE, PATCH)
    assert BASE == before
    assert [generation_messages(r) for r in revised] == [generation_messages(r) for r in BASE]
    for old, new in zip(BASE, revised):
        restored = deepcopy(new)
        if restored.get('evaluation_type') == 'rag':
            restored['reference']['required_facts'] = old['reference']['required_facts']
        assert restored == old


@pytest.mark.parametrize('mutation, error', [
    ('duplicate_edit', ValueError), ('stale_before', ValueError),
    ('unknown_case', ValueError), ('missing_audit', ValueError),
    ('unknown_passage', ValueError), ('unsupported_link', ValueError),
    ('conflict_one_link', ValueError), ('invented_value', ValidationError),
    ('missing_approval', ValidationError), ('unallowed_field', ValidationError),
    ('stale_approval', ValueError), ('incomplete_approval', ValueError),
])
def test_invalid_or_misleading_corrections_rejected(mutation, error):
    patch = deepcopy(PATCH)
    edit = patch['edits'][0]
    if mutation == 'duplicate_edit':
        patch['edits'].append(deepcopy(edit))
    elif mutation == 'stale_before':
        edit['before'][0]['text'] = 'Changed base'
    elif mutation == 'unknown_case':
        edit['id'] = BASE[0]['id']
    elif mutation == 'missing_audit':
        patch['audited_case_ids'].pop()
    elif mutation == 'unknown_passage':
        edit['after'][0]['evidence_passage_ids'] = ['p999']
    elif mutation == 'unsupported_link':
        edit['after'][1]['evidence_passage_ids'] = ['p001']
    elif mutation == 'conflict_one_link':
        conflict = next(e for e in patch['edits'] if any(f['context_support'] == 'conflicting' for f in e['after']))
        conflict['after'][0]['evidence_passage_ids'] = ['p001']
    elif mutation == 'invented_value':
        edit['unresolved_answer_slots'][0]['canonical_value'] = 'Room 201'
    elif mutation == 'missing_approval':
        del patch['approval']
    elif mutation == 'unallowed_field':
        edit['query'] = 'Changed prompt'
    elif mutation == 'stale_approval':
        edit['after'][0]['verification_notes'] = 'Changed after review'
    elif mutation == 'incomplete_approval':
        patch['approval']['reviewed_case_ids'].pop()
    if mutation not in {'missing_approval', 'stale_approval', 'incomplete_approval'}:
        patch['approval']['annotation_content_sha256'] = annotation_digest(patch)
    with pytest.raises(error):
        apply_amendment(BASE, patch)


def test_known_negative_states_and_capability_boundaries_remain_supported():
    revised = apply_amendment(BASE, PATCH)
    for number in (102, 109, 124, 184, 194, 199):
        case = next(r for r in revised if int(r['id'].split('-')[-2]) == number)
        assert context_recall(rag_scoring_record(case)).value == 1


def test_real_replay_changes_only_context_metric_and_keeps_denominators():
    artifact, scores = rescore(ROOT)
    assert len(scores['per_example']) == 200
    assert artifact['checks']['amended_cases'] == 17
    assert artifact['checks']['other_per_case_metrics_unchanged']
    summaries = {r['cohort']: r for r in artifact['context_recall_by_cohort']}
    assert summaries['new_calibration']['n_scored'] == 11
    assert summaries['new_calibration']['mean'] == pytest.approx(9 / 11)
    assert summaries['new_held_out']['n_total'] == 44
    assert summaries['new_held_out']['n_scored'] == 43
    assert summaries['new_held_out']['n_not_applicable'] == 1
    assert summaries['new_held_out']['mean'] == pytest.approx(32 / 43)


def test_saved_amendment_has_exact_replay_and_content_bound_approval():
    result = run(ROOT, replay=True)
    assert result['status'] == 'exact_replay'
    assert result['new_generation_attempts'] == 0
    assert result['review_status'] == 'approved'
    assert PATCH['approval']['annotation_content_sha256'] == annotation_digest(PATCH)


@pytest.mark.parametrize('problem', ['omitted_base_hash', 'changed_base_hash'])
def test_unbound_or_stale_baseline_rejected_before_rescoring(monkeypatch, problem):
    patch = deepcopy(PATCH)
    name = 'data/W01_Evaluation_Dataset_v2.jsonl'
    if problem == 'omitted_base_hash':
        del patch['base_hashes'][name]
    else:
        patch['base_hashes'][name] = '0' * 64
    original = correction.load
    monkeypatch.setattr(correction, 'load', lambda p: patch if p == ROOT / AMENDMENT else original(p))
    with pytest.raises(ValueError, match='baseline input set|Amendment base changed'):
        correction.rescore(ROOT)
