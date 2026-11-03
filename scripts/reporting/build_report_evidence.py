"""Build deterministic report tables from retained measurements; never fit or infer."""
from collections import Counter
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[2]
INPUTS = [
    'results/rag_baseline/scores.json',
    'results/extended_baseline/scores.json',
    'results/context_recall_v2.0.1/context_recall.json',
    'results/extended_baseline/response_review.jsonl',
    'results/extended_baseline/structured_failure_review.jsonl',
    'results/extended_baseline/claims.jsonl',
    'results/extended_baseline/claim_review.json',
    'results/extended_baseline/analysis/fixed_probes.json',
]


def summary(values):
    defined = [m['value'] for m in values if m['value'] is not None]
    return {'n_eligible': len(values), 'n_defined': len(defined),
            'n_not_applicable': sum(m['status'] == 'not_applicable' for m in values),
            'n_error': sum(m['value'] is None and m['status'] != 'not_applicable' for m in values),
            'mean': statistics.mean(defined) if defined else None,
            'population_sd': statistics.pstdev(defined) if defined else None}


def tables(records, experiment, annotation):
    out = []
    for cohort in sorted({r['cohort'] for r in records}):
        base = [r for r in records if r['cohort'] == cohort]
        groups = [('overall', 'all', base)]
        for dimension in ('domain', 'difficulty', 'language'):
            groups += [(dimension, key, [r for r in base if r[dimension] == key])
                       for key in sorted({r[dimension] for r in base})]
        for dimension, label, group in groups:
            for kind in sorted({r['evaluation_type'] for r in group}):
                eligible = [r for r in group if r['evaluation_type'] == kind]
                names = sorted({k for r in eligible for k in r['metrics']})
                if kind != 'rag':
                    names += ['task_success']
                for name in names:
                    values = [r['task_success'] if name == 'task_success' else r['metrics'][name] for r in eligible]
                    out.append({'experiment': experiment, 'annotation': annotation,
                                'cohort': cohort, 'dimension': dimension, 'group': label,
                                'evaluation_type': kind, 'metric': name,
                                'n_parsed': sum(bool(r.get('parsed')) for r in eligible) if kind != 'rag' else None,
                                **summary(values)})
    return out


def load(root, name):
    text = (root / name).read_text()
    return [json.loads(l) for l in text.splitlines()] if name.endswith('.jsonl') else json.loads(text)


def build(root=ROOT):
    inputs = {n: load(root, n) for n in INPUTS}
    initial = deepcopy(inputs[INPUTS[0]]['per_example'])
    for row in initial:
        row['cohort'] = row['subset']; row['evaluation_type'] = 'rag'
    frozen = inputs[INPUTS[1]]['per_example']
    amendment = inputs[INPUTS[2]]
    amended = deepcopy(frozen)
    corrections = {r['id']: r['corrected'] for r in amendment['per_case']}
    for row in amended:
        if row['id'] in corrections:
            row['metrics']['context_recall'] = corrections[row['id']]
    all_tables = (tables(initial, 'rag_baseline', 'frozen_v1') +
                  tables(frozen, 'extended_baseline', 'frozen_v2') +
                  tables(amended, 'extended_baseline', 'context_recall_v2.0.1'))
    rag_reviews, structured_reviews = inputs[INPUTS[3]], inputs[INPUTS[4]]
    failures = []
    for cohort in sorted({r['cohort'] for r in frozen}):
        rag = [r for r in rag_reviews if r['cohort'] == cohort]
        structured = [r for r in structured_reviews if r['cohort'] == cohort]
        n_structured = sum(r['cohort'] == cohort and r['evaluation_type'] != 'rag' for r in frozen)
        failures.append({'cohort': cohort, 'rag_eligible': len(rag),
                         'rag_verdicts_exclusive': dict(sorted(Counter(r['verdict'] for r in rag).items())),
                         'rag_categories_overlapping': dict(sorted(Counter(c for r in rag for c in set(r['failure_categories'])).items())),
                         'structured_eligible': n_structured,
                         'structured_non_successes': len(structured),
                         'structured_categories_exclusive': dict(sorted(Counter(r['category'] for r in structured).items()))})
    claims = inputs[INPUTS[5]]
    probes = inputs[INPUTS[7]]['per_probe']
    return {'schema_version': '1.0.0', 'scope': 'Descriptive synthesis of recorded experiments; no new inference or fitting.',
            'population_sd_ddof': 0,
            'input_sha256': {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in INPUTS},
            'builder_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'tables': all_tables, 'technical_inspection': failures,
            'claim_extraction': {'eligible': len(claims), 'status_counts': dict(sorted(Counter(r['status'] for r in claims).items())),
                                 'inspected_corrections': len(inputs[INPUTS[6]]['corrections']),
                                 'independent_human_assessment': False},
            'fixed_probes': {'eligible': len(probes),
                             'perfect_proxy_scores': sum(r['faithfulness_proxy']['value'] == 1 for r in probes),
                             'ideal_scores_below_one': sum(r['ideal_faithfulness'] < 1 for r in probes),
                             'source': 'fixed_dataset_candidate_not_model_generation'},
            'amendment_checks': amendment['checks']}


def number(value):
    return 'N/A' if value is None else f'{value:.4f}'


def markdown(evidence):
    lines = ['# Report evidence tables', '',
             'Generated from retained scores by `scripts/reporting/build_report_evidence.py`.',
             'Population SD uses ddof=0. Defined-count means exclude N/A and errors; their counts remain visible.',
             'Cohorts are separate. The amended context recall is a reviewed post-inspection diagnostic.', '',
             'The [JSON evidence](evidence/summary.json) includes every cohort, domain, difficulty, language, metric and original/amended view.', '']
    for dimension in ('overall', 'domain', 'difficulty', 'language'):
        lines += [f'## New held-out: {dimension}', '',
                  '| Group | Task | Metric | Mean | SD | Defined / eligible | N/A | Errors | Parsed |',
                  '| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |']
        for row in evidence['tables']:
            if (row['experiment'], row['annotation'], row['cohort'], row['dimension']) != ('extended_baseline','context_recall_v2.0.1','new_held_out',dimension):
                continue
            lines.append(f"| {row['group']} | {row['evaluation_type']} | {row['metric']} | {number(row['mean'])} | {number(row['population_sd'])} | {row['n_defined']}/{row['n_eligible']} | {row['n_not_applicable']} | {row['n_error']} | {row['n_parsed'] if row['n_parsed'] is not None else '—'} |")
        lines += ['']
    lines += ['## Technical inspection', '',
              'RAG verdicts are exclusive; failure-category counts may overlap. Structured categories label each non-successful case once.',
              'Inspection is not independent human response assessment. Frozen alias limits are not automatically model errors.', '']
    for row in evidence['technical_inspection']:
        lines += [f"### {row['cohort']}", '', f"RAG denominator: {row['rag_eligible']}; structured denominator: {row['structured_eligible']}.", '',
                  '| Category set | Category | Cases |', '| --- | --- | ---: |']
        for field in ('rag_verdicts_exclusive','rag_categories_overlapping','structured_categories_exclusive'):
            for category,count in row[field].items():
                lines.append(f'| {field} | {category} | {count} |')
        lines += ['']
    return '\n'.join(lines).rstrip()+'\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if tracked evidence differs from a fresh deterministic build.')
    args = parser.parse_args()
    evidence = build()
    outputs = {'docs/reports/evidence/summary.json': json.dumps(evidence, ensure_ascii=False, indent=2, allow_nan=False)+'\n',
               'docs/reports/evidence_tables.md': markdown(evidence)}
    for name, text in outputs.items():
        path = ROOT / name
        if args.check:
            if not path.exists() or path.read_text() != text:
                raise SystemExit('Report evidence is stale: '+name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text)
    print('Report evidence matches retained inputs.' if args.check else 'Built report evidence and subgroup tables.')


if __name__ == '__main__':
    main()
