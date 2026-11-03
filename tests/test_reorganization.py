"""Guard canonical layout integrity, replay portability and report denominators."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import statistics
from zipfile import ZipFile

import pytest

from src.reproducibility import ROOT, MANIFEST, contained, is_recorded_config, original_bytes, restore
from scripts.reporting.build_report_evidence import build, markdown, summary


@pytest.mark.parametrize('name', ['../escape', '/absolute', 'a/../escape', 'a\\escape', 'C:escape', '', './a', 'a//b'])
def test_layout_rejects_unsafe_or_nonportable_paths(tmp_path, name):
    with pytest.raises(ValueError):
        contained(tmp_path, name)


def fixture_repository(tmp_path):
    manifest = json.loads((ROOT / MANIFEST).read_text())
    target = tmp_path / 'suite'
    for name in {MANIFEST, manifest['snapshot']['file'], *[r['current'] for r in manifest['files'] if 'current' in r]}:
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, path)
    return target, manifest


def test_restore_needs_only_public_files_and_preserves_original_identities(tmp_path):
    root, manifest = fixture_repository(tmp_path)
    frozen = restore(tmp_path / 'restored', root)
    assert not (root / '.git').exists()
    assert len(list(p for p in frozen.rglob('*') if p.is_file())) == 149
    assert (frozen / 'configs/week-03.json').read_bytes() == original_bytes('configs/week-03.json')
    with pytest.raises(FileExistsError):
        restore(frozen, root)


@pytest.mark.parametrize('problem', ['changed_result', 'changed_snapshot', 'traversal', 'duplicate'])
def test_restore_rejects_corruption_before_running_source(tmp_path, problem):
    root, manifest = fixture_repository(tmp_path)
    if problem == 'changed_result':
        (root / 'results/extended_baseline/responses.jsonl').write_text('{}\n')
    elif problem == 'changed_snapshot':
        archive = root / manifest['snapshot']['file']
        archive.write_bytes(archive.read_bytes()+b'changed')
    else:
        if problem == 'traversal':
            manifest['files'][0]['original'] = '../outside'
        else:
            manifest['files'].append(deepcopy(manifest['files'][0]))
        (root / MANIFEST).write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        restore(tmp_path / 'restore', root)
    assert not (tmp_path / 'outside').exists()


def test_restore_rejects_symlink_escape(tmp_path):
    root, manifest = fixture_repository(tmp_path)
    row = next(r for r in manifest['files'] if r.get('current') == 'results/extended_baseline/responses.jsonl')
    path = root / row['current']; raw = path.read_bytes(); path.unlink()
    external = tmp_path / 'external'; external.write_bytes(raw); path.symlink_to(external)
    with pytest.raises(ValueError, match='escapes'):
        restore(tmp_path / 'restore', root)


@pytest.mark.parametrize('name', ['configs/rag_baseline.json', 'configs/extended_baseline.json'])
def test_only_semantically_identical_configuration_routes_to_historical_replay(name):
    config = json.loads((ROOT / name).read_text())
    assert is_recorded_config(ROOT, config, name)
    config['generation']['max_new_tokens'] += 1
    assert not is_recorded_config(ROOT, config, name)


def test_report_summary_keeps_undefined_errors_and_population_sd():
    result = summary([{'value': 0, 'status': 'ok'}, {'value': 1, 'status': 'ok'},
                      {'value': None, 'status': 'not_applicable'},
                      {'value': None, 'status': 'invalid_output'}])
    assert result == {'n_eligible': 4, 'n_defined': 2, 'n_not_applicable': 1,
                      'n_error': 1, 'mean': .5, 'population_sd': .5}
    assert summary([])['mean'] is None


def test_report_evidence_matches_inputs_counts_and_nonexclusive_taxonomy():
    evidence = build()
    assert evidence == json.loads((ROOT / 'docs/reports/evidence/summary.json').read_text())
    assert markdown(evidence) == (ROOT / 'docs/reports/evidence_tables.md').read_text()
    recall = next(r for r in evidence['tables'] if (r['experiment'], r['annotation'], r['cohort'], r['dimension'], r['metric']) ==
                  ('extended_baseline', 'context_recall_v2.0.1', 'new_held_out', 'overall', 'context_recall'))
    assert recall['mean'] == pytest.approx(32/43)
    assert (recall['n_defined'], recall['n_eligible'], recall['n_not_applicable'], recall['n_error']) == (43,44,1,0)
    inspected = next(r for r in evidence['technical_inspection'] if r['cohort'] == 'new_held_out')
    assert sum(inspected['rag_verdicts_exclusive'].values()) == 44
    assert sum(inspected['structured_categories_exclusive'].values()) == 15
    assert inspected['structured_eligible'] == 36
    assert evidence['fixed_probes']['perfect_proxy_scores'] == 10


def test_current_metric_code_matches_retained_extended_scores():
    # Separate live-code validation from exact-source historical replay.
    from src.week3_experiment import _reviewed_claims, score_records
    from src.week3_analysis import read_jsonl
    from src.embeddings import ReplayEncoder
    out = ROOT / 'results/extended_baseline'
    records = read_jsonl(out / 'dataset.jsonl')
    responses = {r['id']:r for r in read_jsonl(out / 'responses.jsonl')}
    result = score_records(records, responses, _reviewed_claims(out, records),
                           ReplayEncoder(out), .8)
    assert result == json.loads((out / 'scores.json').read_text())


def test_all_word_relationships_resolve_and_layout_bytes_are_preserved():
    from xml.etree import ElementTree as ET
    from urllib.parse import unquote, urlsplit
    manifest = json.loads((ROOT / MANIFEST).read_text())
    for row in manifest['files']:
        if not row.get('canonical', '').endswith('.docx'):
            continue
        path = ROOT / row['canonical']
        from io import BytesIO
        with ZipFile(path) as current, ZipFile(BytesIO(original_bytes(row['original']))) as previous:
            assert set(current.namelist()) == set(previous.namelist())
            for name in current.namelist():
                if not name.endswith('.rels'):
                    assert current.read(name) == previous.read(name)
                    continue
                for link in ET.fromstring(current.read(name)):
                    if link.get('TargetMode') == 'External':
                        target = urlsplit(link.get('Target'))
                        if target.scheme:
                            assert target.scheme == 'https'
                        else:
                            resolved = (path.parent / unquote(target.path)).resolve()
                            assert resolved.is_relative_to(ROOT) and resolved.is_file()


def test_recorded_rag_baseline_refuses_calibration_and_rescoring_without_replay(monkeypatch):
    from src import experiment
    config = json.loads((ROOT / 'configs/rag_baseline.json').read_text())
    def no_encoder(*args, **kwargs):
        raise AssertionError('Frozen baseline must refuse writes before model initialization')
    monkeypatch.setattr(experiment, '_encoder', no_encoder)
    out = ROOT / config['output']
    before = {p.name:p.read_bytes() for p in out.iterdir() if p.is_file()}
    with pytest.raises(ValueError, match='calibration is frozen'):
        experiment.calibrate_run(ROOT, config)
    with pytest.raises(ValueError, match='scores are frozen'):
        experiment.score_run(ROOT, config, replay=False)
    assert before == {p.name:p.read_bytes() for p in out.iterdir() if p.is_file()}
