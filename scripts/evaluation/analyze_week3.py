"""Build reproducible supplementary tables and fixed-candidate diagnostics."""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.embeddings import ReplayEncoder
from src.week3_analysis import inspect_run, score_probes, sha256
from src.week3_experiment import local_encoder, score_stage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay', action='store_true', help='Use saved vectors only; verify exact supplementary results.')
    args = parser.parse_args()
    config = json.loads((ROOT / 'configs/week-03.json').read_text())
    output = ROOT / config['output']
    score_stage(ROOT, config, replay=True)
    run = inspect_run(ROOT, config)
    analysis = output / 'analysis'
    analysis.mkdir(exist_ok=True)
    calibration = json.loads((output / 'calibration.json').read_text())
    encoder = ReplayEncoder(analysis) if args.replay else local_encoder(config, analysis)
    probes = score_probes(run['records'], encoder, calibration['threshold'])
    summary = {'tables': run['tables'], 'timing': run['timing'],
               'demonstration_ids': run['demonstration_ids'],
               'technical_inspection': {
                   'n_rag': len(run['reviews']),
                   'verdict_counts': dict(Counter(r['verdict'] for r in run['reviews'])),
                   'structured_failure_categories': dict(Counter(r['category'] for r in run['structured_review'])),
                   'independent_human_assessment': False,
               }}
    if args.replay:
        assert probes == json.loads((analysis / 'fixed_probes.json').read_text())
        assert summary == json.loads((analysis / 'summary.json').read_text())
        manifest = json.loads((analysis / 'manifest.json').read_text())
        for name, expected in manifest['input_hashes'].items():
            assert sha256(output / name) == expected, name
        for name, expected in manifest['artifact_hashes'].items():
            assert sha256(analysis / name) == expected, name
        print('Exact replay: 200 scores, analysis tables, and 10 fixed-candidate probes.')
    else:
        if (analysis / 'manifest.json').exists():
            raise ValueError('Supplementary analysis already exists; use --replay.')
        encoder.save(analysis)
        for name, value in [('fixed_probes.json', probes), ('summary.json', summary)]:
            (analysis / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
        manifest = {
            'scope': 'Supplementary analysis; fixed candidates are not model generations.',
            'input_hashes': {name: sha256(output / name) for name in
                            ['run_manifest.json', 'dataset.jsonl', 'scores.json', 'response_review.jsonl',
                             'response_review_metadata.json', 'structured_failure_review.jsonl', 'calibration.json']},
            'source_hashes': {name: sha256(ROOT / name) for name in
                             ['src/week3_analysis.py', 'scripts/evaluation/analyze_week3.py']},
            'artifact_hashes': {name: sha256(analysis / name) for name in
                               ['fixed_probes.json', 'summary.json', 'embeddings.json', 'embeddings.npz']},
        }
        (analysis / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        print('Supplementary tables and fixed-candidate diagnostics saved.')


if __name__ == '__main__':
    main()
