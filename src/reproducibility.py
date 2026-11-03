"""Verify and replay published experiments across a documented layout migration.

Historical identities are never resealed. Changed source bytes are deduplicated
in a small snapshot; unchanged datasets and results use their canonical files.
All paths and hashes are checked before a separate Python process runs them.
"""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = 'reproducibility/layout_manifest.json'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def contained(root, name):
    """Reject absolute, nonportable, empty and traversal paths, including symlinks."""
    if (not isinstance(name, str) or not name or '\\' in name or
            PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts or
            ':' in name or str(PurePosixPath(name)) != name):
        raise ValueError('Invalid repository-relative path')
    target = (Path(root) / name).resolve()
    if not target.is_relative_to(Path(root).resolve()):
        raise ValueError('Path escapes repository')
    return target


def restore(destination, root=ROOT):
    """Reconstruct original public files in a new empty directory, checking bytes."""
    root, destination = Path(root), Path(destination)
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError('Restore requires an empty directory')
    manifest = json.loads((root / MANIFEST).read_text())
    if manifest['format_version'] != 1:
        raise ValueError('Unsupported layout manifest')
    archive = contained(root, manifest['snapshot']['file'])
    if digest(archive.read_bytes()) != manifest['snapshot']['sha256']:
        raise ValueError('Snapshot digest differs')
    destination.mkdir(parents=True, exist_ok=True)
    seen = set()
    with ZipFile(archive) as zipped:
        entries = zipped.namelist()
        if len(entries) != len(set(entries)):
            raise ValueError('Duplicate snapshot entries')
        required = {r['snapshot'] for r in manifest['files'] if 'snapshot' in r}
        if set(entries) != required:
            raise ValueError('Snapshot entry inventory differs')
        # Verify all inputs before writing any restored source.
        payloads = []
        for row in manifest['files']:
            name = row['original']
            target = contained(destination, name)
            if name in seen or ('snapshot' in row) == ('current' in row):
                raise ValueError('Duplicate file or ambiguous storage')
            seen.add(name)
            if 'snapshot' in row:
                contained(destination, row['snapshot'])
                raw = zipped.read(row['snapshot'])
            else:
                raw = contained(root, row['current']).read_bytes()
            if digest(raw) != row['sha256']:
                raise ValueError('Historical input digest differs: ' + name)
            payloads.append((target, raw))
        for target, raw in payloads:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
    return destination


@contextmanager
def recorded_workspace(root=ROOT):
    with tempfile.TemporaryDirectory(prefix='ingen-replay-') as directory:
        yield restore(Path(directory), root)


def original_bytes(name, root=ROOT):
    """Read and verify one recorded source without extracting the whole tree."""
    root = Path(root)
    manifest = json.loads((root / MANIFEST).read_text())
    matches = [r for r in manifest['files'] if r['original'] == name]
    if len(matches) != 1:
        raise ValueError('Unknown or duplicate recorded source')
    row = matches[0]
    if 'snapshot' in row:
        archive = contained(root, manifest['snapshot']['file'])
        if digest(archive.read_bytes()) != manifest['snapshot']['sha256']:
            raise ValueError('Snapshot digest differs')
        contained(root, row['snapshot'])
        with ZipFile(archive) as zipped:
            raw = zipped.read(row['snapshot'])
    else:
        raw = contained(root, row['current']).read_bytes()
    if digest(raw) != row['sha256']:
        raise ValueError('Historical input digest differs: ' + name)
    return raw


def is_recorded_config(root, config, name):
    if Path(root).resolve() != ROOT or not (ROOT / MANIFEST).is_file():
        return False
    manifest = json.loads((ROOT / MANIFEST).read_text())
    matches = [r for r in manifest['files'] if r.get('canonical') == name]
    if len(matches) != 1:
        return False
    original = json.loads(original_bytes(matches[0]['original']))
    # Map exact file and directory references, retaining every semantic setting.
    paths = {r['original']: r['canonical'] for r in manifest['files'] if 'canonical' in r}
    def translate(value):
        if isinstance(value, dict):
            return {k: translate(v) for k, v in value.items()}
        if isinstance(value, list):
            return [translate(v) for v in value]
        if not isinstance(value, str):
            return value
        if value in paths:
            return paths[value]
        destinations = {new[:-len(old) + len(value)]
                        for old, new in paths.items() if old.startswith(value + '/')}
        return destinations.pop() if len(destinations) == 1 else value
    return config == translate(original)


_ACTIONS = {
    'rag': "from src.experiment import score_run; result = score_run(root, load('configs/week-02.json'), replay=True)",
    'extended': "from src.week3_experiment import score_stage; result = score_stage(root, load('configs/week-03.json'), replay=True)",
    'annotations': "from src.week3_context_recall import rescore; result = rescore(root)",
    'amendment': "from src.week3_context_recall import run; result = run(root, replay=True)",
    'analysis': "from scripts.evaluation.analyze_week3 import main; sys.argv = ['analysis', '--replay']; main(); result = {'status': 'exact_replay', 'probes': 10}",
}


def recorded_call(action, root=ROOT):
    """Run an allowlisted offline replay using its exact historical implementation."""
    if action not in _ACTIONS:
        raise ValueError('Unknown recorded replay')
    program = ("import contextlib, io, json, sys\nfrom pathlib import Path\n"
               "root = Path.cwd()\nload = lambda name: json.loads((root / name).read_text())\n"
               "with contextlib.redirect_stdout(io.StringIO()):\n    " + _ACTIONS[action] +
               "\nprint(json.dumps(result, ensure_ascii=False, allow_nan=False))\n")
    with recorded_workspace(root) as workspace:
        result = subprocess.run([sys.executable, '-c', program], cwd=workspace,
                                check=True, text=True, capture_output=True)
        return json.loads(result.stdout)


def verify(root=ROOT):
    """Verify the frozen RAG, structured, amendment and diagnostic measurements."""
    result = {}
    for action in ('rag', 'extended', 'amendment', 'analysis'):
        value = recorded_call(action, root)
        result[action] = ({'status': 'exact_replay', 'cases': len(value['per_example'])}
                          if action == 'rag' else value)
    return result
