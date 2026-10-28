"""Verify the measured Week 3 bundle independently of synthetic pipeline tests."""

import json
from pathlib import Path

from src.week3_analysis import demonstration_ids, inspect_run, read_jsonl, score_probes, sha256
from src.week3_experiment import score_stage
from src.embeddings import ReplayEncoder

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'configs/week-03.json').read_text())
OUT = ROOT / CONFIG['output']


def test_complete_real_run_replays_exactly_and_all_seals_match():
    manifest = json.loads((OUT / 'run_manifest.json').read_text())
    assert manifest['status'] == 'complete'
    for name, expected in manifest['artifacts'].items():
        assert sha256(OUT / name) == expected, name
    assert score_stage(ROOT, CONFIG, replay=True) == {'status': 'exact_replay', 'cases': 200}


def test_real_attempts_and_claim_correspondence_cover_the_frozen_collection():
    run = inspect_run(ROOT, CONFIG)
    assert len(run['records']) == len(run['responses']) == 200
    assert len(run['claims']) == len(run['reviews']) == 155
    for stage, rows in [('responses', run['responses']), ('claims', run['claims'])]:
        assert len({r['id'] for r in rows}) == len(rows)
        assert all(r['attempt'] == 1 for r in rows)
        assert {r['id'] for r in read_jsonl(OUT / f'{stage}_attempts.jsonl')} == {r['id'] for r in rows}
    review = json.loads((OUT / 'claim_review.json').read_text())
    assert review['status'] == 'checked' and len(review['reviewed_case_ids']) == 155


def test_supplementary_diagnostics_replay_without_model_inference():
    analysis = OUT / 'analysis'
    manifest = json.loads((analysis / 'manifest.json').read_text())
    for name, expected in manifest['input_hashes'].items():
        assert sha256(OUT / name) == expected, name
    for name, expected in manifest['artifact_hashes'].items():
        assert sha256(analysis / name) == expected, name
    for name, expected in manifest['source_hashes'].items():
        assert sha256(ROOT / name) == expected, name
    records = read_jsonl(OUT / 'dataset.jsonl')
    probes = score_probes(records, ReplayEncoder(analysis), .8)
    assert probes == json.loads((analysis / 'fixed_probes.json').read_text())
    assert len(probes['per_probe']) == 10
    assert sum(p['cohort'] == 'new_held_out' for p in probes['per_probe']) == 8
    assert all(p['source'] == 'fixed_dataset_candidate_not_model_generation' for p in probes['per_probe'])


def test_notebook_is_executed_and_has_required_demonstrations():
    notebook = json.loads((ROOT / 'notebooks/week-03/W03_Extended_Evaluation_Suite.ipynb').read_text())
    code = [c for c in notebook['cells'] if c['cell_type'] == 'code']
    assert code and all(c['execution_count'] is not None for c in code)
    assert not any(o['output_type'] == 'error' for c in code for o in c['outputs'])
    records = read_jsonl(OUT / 'dataset.jsonl')
    assert {k: len(v) for k, v in demonstration_ids(records).items()} == {'STUM': 10, 'SEOM': 6, 'HTD-IRL': 6}
    for capability in ['STUM', 'SEOM', 'HTD-IRL']:
        cell = next(c for c in code if (''.join(c['source']) if isinstance(c['source'], list)
                                       else c['source']).strip() == f'show_demonstrations({capability!r})')
        assert cell['outputs']


def test_week3_reflection_length_and_review_entry_point():
    words = (ROOT / 'weekly/Wk-03-Log.md').read_text().split('\n', 2)[-1].split()
    assert 300 <= len(words) <= 500
    assert (ROOT / 'deliverables/week-03/README.md').is_file()
    assert (ROOT / 'docs/week-03/W03_Extended_Evaluation_Results.md').is_file()
