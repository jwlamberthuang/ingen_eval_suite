"""Build and optionally execute the portable Week 3 demonstration notebook."""

import argparse
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / 'notebooks/week-03/W03_Extended_Evaluation_Suite.ipynb'


def build():
    cells = []
    def md(text):
        cells.append(nbf.v4.new_markdown_cell(text))
    def code(text):
        cells.append(nbf.v4.new_code_cell(text))

    md('''# Week 3 extended evaluation suite

This notebook replays a frozen 200-case text-only experiment and demonstrates
the assigned STUM, SEOM, and HTD-IRL tasks with actual recorded model outputs.
These task labels describe evaluation proxies, not access to internal robot
models. No cell downloads weights, generates answers, or tunes a threshold.

The primary new evidence is the 80 new held-out cases. Twenty new calibration
cases and the 100 previously used Week 2 examples remain separate. Native
scenarios are not matched translations; differences between languages do not
identify a causal language effect. No composite score combines capabilities.
''')
    code('''from pathlib import Path
import html, json, sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display, HTML

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents]
            if (p / 'configs/week-03.json').is_file())
sys.path.insert(0, str(ROOT))
from src.week3_analysis import inspect_run, score_probes, sha256
from src.week3_experiment import score_stage
from src.embeddings import ReplayEncoder
from src.week3_context_recall import rescore, run as replay_amendment, OUTPUT as AMENDED_OUTPUT
config = json.loads((ROOT / 'configs/week-03.json').read_text())
OUT = ROOT / config['output']
ANALYSIS = OUT / 'analysis'
run = inspect_run(ROOT, config)
records, baseline_scores = run['records'], run['scores']
amendment, scores = rescore(ROOT)
FIGURES = ROOT / AMENDED_OUTPUT / 'figures'
FIGURES.mkdir(exist_ok=True)
by_id = {r['id']: r for r in records}
responses = {r['id']: r for r in run['responses']}
scored = {r['id']: r for r in scores['per_example']}
calibration = json.loads((OUT / 'calibration.json').read_text())
print('Run:', config['run_name'])
print('Cases:', len(records), '| support mode:', config['support']['mode'], '| threshold:', calibration['threshold'])
print('Context-recall amendment:', amendment['annotation_version'], '|', amendment['review_status'])
''')
    md('''## Release validation and exact replay

The release contains 100 unchanged legacy examples and 100 approved additions.
Current approval/native-review annotations are authoritative; construction notes
retain their original drafting context. Hashes bind the release, schema, protocol,
input allowlists, generation settings, and scorer before inference. Review
attestation is not independent reviewer agreement.

Replay recomputes every score and aggregate using saved vectors. It checks scoring
reproducibility; fresh generation can differ across hardware or runtime versions.
''')
    code('''from scripts.datasets.v2 import manage_dataset as dataset
rows, raw = dataset.read_records(ROOT / config['dataset'])
report = dataset.validate_records(rows, 'release', raw=raw)
assert report['valid'] and not report['errors'] and not report['warnings']
manifest = json.loads((ROOT / config['dataset_manifest']).read_text())
assert dataset.verify_manifest(manifest, ROOT / config['dataset'], raw, report)
print('Release validation:', report['record_count'], 'cases; zero errors and warnings')
print(score_stage(ROOT, config, replay=True))
print('Annotation correction:', replay_amendment(ROOT, replay=True))
probe_scores = score_probes(records, ReplayEncoder(ANALYSIS), calibration['threshold'])
assert probe_scores == json.loads((ANALYSIS / 'fixed_probes.json').read_text())
print('Fixed-candidate diagnostic: exact replay')
''')
    md('''## Measurements and denominators

Spatial accuracy uses the fixed scene axis and exact relation labels, including
unknown/conflict. Temporal pair accuracy compares requested relations; consistency
rejects contradictions and transitive cycles; coherence is their product. SEOM
recall and class accuracy use the gold inventory denominator; precision separately
penalizes extras. HTD coverage and precision use maximum one-to-one template
matching with required goal precedence. Bilingual slot/entity matching accepts only
the frozen normalization and explicit aliases, not unrestricted semantic equality.

Malformed/missing structured outputs have null core metrics and task success zero.
Undefined empty-inventory ratios remain null, while a correct empty output can have
task success one. These cases make output coverage essential beside mean scores.
''')
    code('''structured = pd.DataFrame([
    {'id': r['id'], 'cohort': r['cohort'], 'type': r['evaluation_type'],
     'language': r['language'], 'difficulty': r['difficulty'], 'status': r['status'],
     'parsed': r['parsed'], 'task_success': r['task_success']['value'],
     **{k: v['value'] for k, v in r['metrics'].items()}}
    for r in scores['per_example'] if r['evaluation_type'] != 'rag'])
display(structured.groupby(['cohort', 'type'], dropna=False).agg(
    n_cases=('id', 'size'), n_parsed=('parsed', 'sum'),
    n_defined_success=('task_success', 'count'), mean_task_success=('task_success', 'mean')))
display(pd.DataFrame([
    {'cohort': row['cohort'], 'type': row['type'], 'metric': name, **stats}
    for row in run['tables']['structured'] for name, stats in row['metrics'].items()
]).round(4))
''')
    md('''## New held-out structured performance

The graph includes every eligible held-out structured case in task success and
parse coverage. Conditional metric means in the table above use defined values
only. Small groups, especially the five total temporal examples, support case
inspection rather than strong population claims.
''')
    code('''held_structured = structured[structured['cohort'] == 'new_held_out']
summary = held_structured.groupby('type').agg(n=('id', 'size'),
    success=('task_success', 'mean'), parse_coverage=('parsed', 'mean'))
summary = summary.reindex(['stum_spatial','stum_temporal','seom_entities','htd_task_alignment'])
labels = ['Spatial', 'Temporal', 'SEOM', 'HTD-IRL']
fig, ax = plt.subplots(figsize=(8.5, 4.2))
x = np.arange(len(summary))
ax.bar(x-.18, summary['success'], width=.36, label='Exact task success', color='#285b78')
ax.bar(x+.18, summary['parse_coverage'], width=.36, label='Valid-output coverage', color='#a3c6c1')
ax.set_xticks(x, [f"{label}\\nn={int(n)}" for label,n in zip(labels,summary['n'])])
ax.set_ylim(0, 1.12); ax.set_ylabel('Fraction of eligible cases')
ax.legend(loc='lower left', bbox_to_anchor=(0,1.01), ncol=2, frameon=False)
ax.set_title('New held-out structured tasks', pad=40); ax.grid(axis='y', alpha=.18)
fig.tight_layout(); plt.show()
display(held_structured.groupby(['type', 'language']).agg(n=('id', 'size'),
    n_parsed=('parsed', 'sum'), mean_task_success=('task_success', 'mean')).round(4))
display(held_structured.groupby(['type', 'difficulty']).agg(n=('id', 'size'),
    mean_task_success=('task_success', 'mean')).round(4))
''')
    md('''## Demonstration selection

Demonstrations use ID order without consulting outcomes: STUM has the first
three English and two Chinese spatial cases plus all five temporal cases (10);
SEOM and HTD-IRL each have the first three English and first three Chinese cases
(6 each). Calibration/held-out labels remain visible. These are subsets of the
recorded dataset, not additional independent examples or favorable-case selection.
''')
    code('''def show_demonstrations(capability):
    for identifier in run['demonstration_ids'][capability]:
        case, output, result = by_id[identifier], responses[identifier], scored[identifier]
        def escaped(value):
            return html.escape(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2))
        blocks = [('Query', case['query']), ('Visible evidence', case['context']),
                  ('Recorded prediction', output.get('response', output['status'])),
                  ('Reference', case['reference']), ('Scoring', result)]
        body = ''.join(f'<b>{label}</b><pre style="white-space:pre-wrap">{escaped(value)}</pre>'
                       for label, value in blocks)
        display(HTML(f'<h3>{html.escape(identifier)} — {result["cohort"]}</h3>' + body))
''')
    for capability, text in [
        ('STUM', 'Spatial and temporal relations are scored against reviewed constraints, not the fluency of an explanation.'),
        ('SEOM', 'Inspect missing entities, extra entities, class labels, and frozen alias matching separately.'),
        ('HTD-IRL', 'Inspect goal slots and task order. A semantically sensible unlisted paraphrase can fail the frozen rubric.')]:
        md(f'## {capability}: recorded demonstrations\n\n{text}')
        code(f"show_demonstrations({capability!r})")
    md('''## RAG metrics on the expanded collection

Context recall is annotation-based evidence sufficiency and is independent of the
generated answer. Faithfulness is an embedding retrieval proxy over inspected
claims; semantic relevance is raw query-response cosine in [-1, 1]. Neither is an
answer-correctness certificate. Lexical reference recall remains a diagnostic.
The 0.80 threshold transfers from Week 2; validity on new scenarios is unestablished.
Raw extraction contract failures remain recorded. Correspondence corrections are
separate inspected artifacts, so post-inspection faithfulness is not a measure
of fully automatic claim-extraction performance.
The original scores remain frozen. The separately versioned 2.0.1 amendment
audits all 55 new RAG inventories and changes 17. Missing requested answer slots
have unresolved values, conflicts remain in the denominator, and case 0186 is N/A
until the person denoted by she is identified. Missingness observations remain
behavior guidance. The intern reviewed and approved all 17 corrections, including
the revised Chinese annotation wording. Approval binds the exact amendment content
separately from original source approval; it is not independent response assessment.
Only context recall changes. This replay uses saved outputs and vectors and does
not turn inspected cases into fresh held-out evidence. Context recall describes
evidence sufficiency, not model accuracy or whether an abstention was correct.
''')
    code('''print('Raw extraction statuses:', pd.Series([r['status'] for r in run['claims']]).value_counts().to_dict())
print('Inspected corrections:', len(json.loads((OUT / 'claim_review.json').read_text())['corrections']))
from src.week3_analysis import result_tables
rag_table = pd.DataFrame(result_tables(scores)['rag'])
display(rag_table[['cohort', 'metric', 'n_total', 'n_scored', 'n_not_applicable',
                   'n_errors', 'mean', 'std_population']].round(4))
display(pd.DataFrame(amendment['baseline_context_recall_by_cohort'])[
    ['cohort', 'mean', 'n_scored', 'n_total']].rename(columns={'mean':'baseline_context_recall'}).round(4))
display(pd.DataFrame([{'id': r['id'], 'cohort': r['cohort'],
    'before': r['baseline']['value'], 'after': r['corrected']['value'],
    'status': r['corrected']['status']} for r in amendment['per_case'] if r['amended']]))
rag = pd.DataFrame([{'id': r['id'], 'cohort': r['cohort'], 'language': r['language'],
                    'difficulty': r['difficulty'],
                    **{k: v['value'] for k, v in r['metrics'].items()}}
                   for r in scores['per_example'] if r['evaluation_type'] == 'rag'])
held_rag = rag[rag['cohort'] == 'new_held_out']
display(held_rag.groupby('language').agg({'id':'size', 'context_recall':['count','mean'],
    'faithfulness_proxy':['count','mean'], 'semantic_relevance':['count','mean']}).round(4))
display(held_rag.groupby('difficulty').agg({'id':'size', 'context_recall':['count','mean'],
    'faithfulness_proxy':['count','mean'], 'semantic_relevance':['count','mean']}).round(4))
fig, axes = plt.subplots(1, 3, figsize=(11, 3.5))
for ax, metric in zip(axes, ['context_recall', 'faithfulness_proxy', 'semantic_relevance']):
    values = [held_rag.loc[held_rag['language'] == lang, metric].dropna().to_numpy() for lang in ['en', 'zh']]
    for pos, group in enumerate(values, 1):
        ax.scatter(pos + np.linspace(-.08, .08, len(group)), group, alpha=.5, s=20, color='#285b78')
        if len(group): ax.plot([pos-.15, pos+.15], [group.mean()]*2, color='#bc573b', linewidth=2)
    ax.set_xticks([1,2], [f'EN n={len(values[0])}', f'ZH n={len(values[1])}'])
    ax.set_ylim((-1.05,1.05) if metric == 'semantic_relevance' else (-.05,1.05))
    ax.set_title(metric.replace('_', ' ')); ax.grid(axis='y', alpha=.18)
fig.suptitle('New held-out RAG: dots are cases; line is mean'); fig.tight_layout()
fig.savefig(FIGURES / 'rag_held_out.png', dpi=150); plt.show()
''')
    md('''## Fixed adversarial metric-boundary probes

These ten candidates were written into the dataset before generation. They are
not model answers. Two calibration probes and eight held-out probes remain
separate. Their annotated support fractions specify an ideal property, not a
prescribed embedding value. The frozen proxy searches all evidence segments,
including quoted instructions: inspect the best segment beside every score.
No threshold or scorer is adjusted using these observations.
''')
    code('''probe_frame = pd.DataFrame([{'id': p['id'], 'cohort': p['cohort'],
    'ideal': p['ideal_faithfulness'], 'proxy': p['faithfulness_proxy']['value'],
    'relevance': p['semantic_relevance']['value']} for p in probe_scores['per_probe']])
display(probe_frame.round(4))
for p in probe_scores['per_probe']:
    print(p['probe_id'], p['cohort'])
    display(pd.DataFrame([{**j, 'annotated_support': a['support']}
                          for j,a in zip(p['faithfulness_proxy']['details']['judgments'], p['claim_annotations'])]))
fig, ax = plt.subplots(figsize=(10, 4.2)); x = np.arange(len(probe_frame))
ax.bar(x-.18, probe_frame['ideal'], width=.36, label='Annotated ideal support', color='#a3c6c1')
ax.bar(x+.18, probe_frame['proxy'], width=.36, label='Frozen embedding proxy', color='#bc573b')
ax.set_xticks(x, [p['id'].split('-')[-2] for p in probe_scores['per_probe']]); ax.set_ylim(0,1.15)
ax.set_ylabel('Supported-claim fraction'); ax.set_xlabel('Case number (0103 and 0168: calibration; rest: held-out)')
ax.legend(loc='lower left', bbox_to_anchor=(0,1.01), ncol=2, frameon=False)
ax.set_title('Prewritten boundary candidates, not generated answers', pad=40)
fig.tight_layout(); plt.show()
''')
    md('''## Failure inspection and limitations

Technical inspection records qualitative judgments against the frozen evidence
and response rubric. It is separate from dataset approval and is **not an
independent human accuracy assessment**. Claim corrections repair extraction
correspondence only; raw answers and raw extractor output remain intact. Frozen
structured matching errors and model reasoning errors require separate diagnosis.
''')
    code('''reviews = pd.DataFrame(run['reviews'])
display(reviews.groupby(['cohort','verdict']).size().rename('n_cases').to_frame())
display(reviews.loc[reviews['verdict'] != 'meets_reference',
                    ['id','cohort','verdict','failure_categories','evidence']])
display(structured.loc[structured['task_success'] != 1,
                       ['id','cohort','type','status','task_success']])
display(pd.DataFrame(run['structured_review'])[['id','cohort','category','evidence','score_adjusted']])
print('Claim correspondence corrections:', len(json.loads((OUT / 'claim_review.json').read_text())['corrections']))
''')
    md('''## Runtime, validation, and interpretation

Times are recorded local per-attempt generation/extraction durations, not robot
response latency or wall time divided by sample count. The same quantized model
both answers and proposes claims; correspondence inspection does not remove all
shared-model bias. The experiment contains one baseline, not a model ranking.
The task labels do not establish physical perception, tool execution, or audio
quality. Review the results report and reflection for specific follow-up work.
''')
    code('''display(pd.DataFrame(run['timing']).T)
tests = json.loads((ROOT / 'deliverables/week-03/validation/tests.json').read_text())
print('Test suite:', tests['passed'], 'passed;', tests['failures'], 'failures;', tests['errors'], 'errors')
print('Primary new held-out: 80 cases, with RAG and structured metric families reported separately.')
''')
    notebook = nbf.v4.new_notebook(cells=cells, metadata={
        'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
        'language_info': {'name': 'python'},
    })
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(notebook, TARGET)
    return notebook


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    notebook = build()
    if args.execute:
        from nbclient import NotebookClient
        NotebookClient(notebook, timeout=120, kernel_name='python3',
                       resources={'metadata': {'path': str(ROOT)}}).execute()
        nbf.write(notebook, TARGET)
    print(TARGET.relative_to(ROOT))
