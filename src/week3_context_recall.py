"""Versioned annotation-only replay of the frozen Week 3 experiment.

Unresolved answer slots describe the requested information without inventing a
hidden value. The amendment changes only the context-recall scoring view; it is
not a newly approved dataset, a new generation, or a fresh held-out experiment.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from .embeddings import ReplayEncoder
from .week3_analysis import read_jsonl, result_tables, sha256
from .week3_experiment import _reviewed_claims, score_records, score_stage
from .week3_inputs import generation_messages

ROOT = Path(__file__).resolve().parents[1]
AMENDMENT = 'data/annotations/W03_Context_Recall_v2.0.1.json'
SCHEMA = 'schemas/w03_context_recall_amendment.schema.json'
OUTPUT = 'results/week-03/context-recall-v2.0.1'
SOURCES = ['src/week3_context_recall.py', 'scripts/evaluation/correct_week3_context_recall.py']


def load(path):
    from scripts.datasets.v2.manage_dataset import loads
    return loads(Path(path).read_text())


def annotation_digest(amendment):
    """Bind approval to the exact annotation content, excluding approval fields."""
    content = {k: v for k, v in amendment.items() if k not in {'approval', 'review_status'}}
    return hashlib.sha256(json.dumps(content, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def apply_amendment(records, amendment, schema=None):
    """Validate scope and stale references, then return a private scoring view."""
    Draft202012Validator(schema or load(ROOT / SCHEMA), format_checker=FormatChecker()).validate(amendment)
    approval = amendment['approval']
    if approval['annotation_content_sha256'] != annotation_digest(amendment):
        raise ValueError('Annotation content changed after approval')
    edited_ids = [e['id'] for e in amendment['edits']]
    if (len(approval['reviewed_case_ids']) != len(edited_ids) or
            set(approval['reviewed_case_ids']) != set(edited_ids)):
        raise ValueError('Approval must cover every amended case exactly once')
    identifiers = [r['id'] for r in records]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError('Duplicate base case IDs')
    expected = {r['id'] for r in records if r.get('evaluation_type') == 'rag'}
    if set(amendment['audited_case_ids']) != expected:
        raise ValueError('Audit must cover every new RAG case and no legacy or structured cases')
    revised = deepcopy(records)
    by_id = {r['id']: r for r in revised}
    seen = set()
    for edit in amendment['edits']:
        identifier = edit['id']
        if identifier not in expected or identifier in seen:
            raise ValueError('Unknown, out-of-scope, or duplicate edit')
        seen.add(identifier)
        record = by_id[identifier]
        if record['reference']['required_facts'] != edit['before'] or edit['before'] == edit['after']:
            raise ValueError('Stale or empty annotation edit')
        fact_ids = [f['fact_id'] for f in edit['after']]
        if len(fact_ids) != len(set(fact_ids)):
            raise ValueError('Duplicate answer target IDs')
        passages = {p['passage_id'] for p in record['reference']['passages']}
        sources = {s['source_id'] for s in record['reference']['sources']}
        slots = {s['fact_id'] for s in edit['unresolved_answer_slots']}
        if len(slots) != len(edit['unresolved_answer_slots']):
            raise ValueError('Duplicate unresolved slot')
        unresolved = {f['fact_id'] for f in edit['after'] if f['context_support'] != 'supported'}
        if slots != unresolved:
            raise ValueError('Every unavailable or conflicting target needs an explicit unresolved slot')
        for fact in edit['after']:
            links = fact['evidence_passage_ids']
            if not set(links) <= passages or not set(fact['source_ids']) <= sources:
                raise ValueError('Unknown evidence or source link')
            if fact['context_support'] == 'unsupported' and links:
                raise ValueError('Unavailable answer values cannot have supporting passage links')
            if fact['context_support'] == 'supported' and not links:
                raise ValueError('Supported targets require evidence')
            if fact['context_support'] == 'conflicting' and len(links) < 2:
                raise ValueError('Conflicting targets require both conflicting passages')
        record['reference']['required_facts'] = deepcopy(edit['after'])
    if [generation_messages(r) for r in revised] != [generation_messages(r) for r in records]:
        raise ValueError('Annotation correction changed model-visible inputs')
    return revised


def rescore(root=ROOT):
    """Replay sealed inputs and vectors; assert all other measurements identical."""
    root = Path(root)
    amendment = load(root / AMENDMENT)
    config = load(root / 'configs/week-03.json')
    required_base = {'configs/week-03.json', config['dataset'], config['dataset_manifest']}
    required_base.update(config['output'] + '/' + name for name in (
        'run_manifest.json', 'dataset.jsonl', 'inputs.jsonl', 'responses.jsonl',
        'claims.jsonl', 'claim_review.json', 'calibration.json', 'scores.json',
        'embeddings.json', 'embeddings.npz'))
    if set(amendment['base_hashes']) != required_base:
        raise ValueError('Amendment must bind the complete baseline input set')
    for name, expected in amendment['base_hashes'].items():
        if sha256(root / name) != expected:
            raise ValueError('Amendment base changed: ' + name)
    score_stage(root, config, replay=True)
    out = root / config['output']
    records = read_jsonl(out / 'dataset.jsonl')
    revised = apply_amendment(records, amendment, load(root / SCHEMA))
    responses = {r['id']: r for r in read_jsonl(out / 'responses.jsonl')}
    baseline = load(out / 'scores.json')
    scores = score_records(revised, responses, _reviewed_claims(out, records),
                          ReplayEncoder(out), load(out / 'calibration.json')['threshold'])
    permitted = {e['id'] for e in amendment['edits']}
    for old, new in zip(baseline['per_example'], scores['per_example']):
        expected = deepcopy(old)
        if old['id'] in permitted:
            # The frozen evaluator's generic detail says reviewed references.
            # Distinguish the separately approved amendment from frozen labels.
            new['metrics']['context_recall']['details']['support_source'] = 'approved_context_recall_amendment'
            expected['metrics']['context_recall'] = new['metrics']['context_recall']
        if expected != new:
            raise ValueError('A metric other than amended context recall changed: ' + old['id'])
    rows = [{'id': n['id'], 'cohort': n['cohort'], 'language': n['language'],
             'difficulty': n['difficulty'], 'amended': n['id'] in permitted,
             'baseline': b['metrics']['context_recall'], 'corrected': n['metrics']['context_recall']}
            for b, n in zip(baseline['per_example'], scores['per_example'])
            if n['evaluation_type'] == 'rag']
    artifact = {
        'annotation_version': amendment['annotation_version'],
        'review_status': amendment['review_status'],
        'approval': amendment['approval'],
        'interpretation': 'Reviewed annotation-only diagnostic replay; no fresh generation or untouched held-out claim.',
        'checks': {'baseline_exact_replay': True, 'generation_inputs_unchanged': True,
                   'other_per_case_metrics_unchanged': True, 'new_generation_attempts': 0,
                   'audited_new_rag_cases': len(amendment['audited_case_ids']),
                   'amended_cases': len(permitted)},
        'per_case': rows,
        'context_recall_by_cohort': [r for r in result_tables(scores)['rag'] if r['metric'] == 'context_recall'],
        'baseline_context_recall_by_cohort': [r for r in result_tables(baseline)['rag'] if r['metric'] == 'context_recall'],
    }
    return artifact, scores


def run(root=ROOT, replay=False):
    root = Path(root)
    artifact, _ = rescore(root)
    amendment = load(root / AMENDMENT)
    inputs = {**amendment['base_hashes'],
              **{n: sha256(root / n) for n in [AMENDMENT, SCHEMA, *SOURCES]}}
    encoded = json.dumps(artifact, ensure_ascii=False, indent=2) + '\n'
    target = root / OUTPUT
    if replay:
        manifest = load(target / 'manifest.json')
        if (manifest['input_hashes'] != inputs or load(target / 'context_recall.json') != artifact or
                any(manifest[k] != artifact[k] for k in ('annotation_version', 'review_status', 'approval'))):
            raise ValueError('Amendment replay or source hashes differ')
        if manifest['artifact_sha256'] != sha256(target / 'context_recall.json'):
            raise ValueError('Amendment artifact hash differs')
        return {'status': 'exact_replay', **artifact['checks'], 'review_status': artifact['review_status']}
    if target.exists():
        raise FileExistsError('Correction output exists; use --replay or a new annotation version')
    target.mkdir(parents=True)
    (target / 'context_recall.json').write_text(encoded)
    manifest = {'annotation_version': amendment['annotation_version'], 'review_status': amendment['review_status'],
                'approval': amendment['approval'],
                'input_hashes': inputs, 'artifact_sha256': sha256(target / 'context_recall.json')}
    (target / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return {'status': 'complete', **artifact['checks'], 'review_status': artifact['review_status']}
