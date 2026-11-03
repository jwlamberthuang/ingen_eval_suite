"""Replay immutable published measurements offline from the current layout."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.reproducibility import recorded_call, recorded_workspace, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', choices=('all', 'rag', 'extended', 'amendment', 'analysis', 'tests'), default='all', nargs='?')
    args = parser.parse_args()
    if args.target == 'tests':
        import subprocess
        with recorded_workspace() as workspace:
            result = subprocess.run([sys.executable, '-m', 'pytest', '-q'], cwd=workspace)
            raise SystemExit(result.returncode)
    result = verify() if args.target == 'all' else recorded_call(args.target)
    if args.target == 'rag':
        result = {'status': 'exact_replay', 'cases': len(result['per_example'])}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
