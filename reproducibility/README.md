# Verified layout migration

The project-oriented layout replaces chronological review folders. Recorded
experiments bind exact source/configuration bytes and original path strings;
rewriting those identities would erase evidence of the implementation actually
used. The migration preserves them explicitly.

[layout_manifest.json](layout_manifest.json) inventories all 149 tracked files of
baseline commit `e701bc57f568c293d922a1921c60d46def7a6a74`. Each entry records its
original path and SHA-256. Byte-identical files are read from their canonical
current locations. Changed sources, original navigation pages, and original
notebooks are deduplicated in [frozen_sources.zip](frozen_sources.zip). Large
unchanged datasets, responses, scores, and vectors are not duplicated.

`src/reproducibility.py` validates path containment, the snapshot digest, entry
inventory, and every original file hash. It reconstructs an exact public baseline
in a temporary directory and invokes the original implementation in a separate
Python process. Restoration never requires Git history, model downloads, private
files, or workstation paths. Historical week paths inside the manifest/snapshot
are resolvable public experiment identities, not links outside this repository.

```sh
.venv/bin/python scripts/evaluation/replay.py all
.venv/bin/python scripts/evaluation/replay.py tests
```

The first command recomputes the RAG and extended scores, approved amendment,
and fixed-probe analysis. The second runs the original 336 regression tests
against the reconstructed baseline. The ordinary root test suite also tests
current code, canonical documentation, dataset maintenance, migration safeguards,
and report synthesis. These are different verification scopes.

Current metric implementations retain their mathematical behavior. Historical
replay proves the saved experiment reproduces with its recorded implementation;
it does not by itself validate future changes to the live implementation.
No generation input, score, threshold, review attestation, or sealed run manifest
was changed during this migration. Current convenience configurations and
notebooks use canonical locations; archived originals retain original identities.
