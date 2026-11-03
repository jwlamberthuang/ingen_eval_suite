# Recorded experiments

| Record | Folder | Scope |
| --- | --- | --- |
| RAG baseline | [rag_baseline](rag_baseline/run_manifest.json) | 100 fixed-context responses; 20 calibration, 80 historical held-out |
| Extended baseline | [extended_baseline](extended_baseline/run_manifest.json) | 200 responses; primary evidence is 80 new held-out cases |
| Annotation diagnostic | [context_recall_v2.0.1](context_recall_v2.0.1/manifest.json) | Approved correction to 17 required-fact inventories; no new inference |
| Fixed-probe diagnostics | [extended analysis](extended_baseline/analysis/manifest.json) | Ten prewritten candidates, separate from generated responses |

Responses and raw extraction attempts are retained alongside separate claim and
response inspections, scores, saved vectors, pinned runtime metadata, and sealed
manifests. A successful generation is not necessarily a correct answer. An
inspected claim correction is not a repaired model response or an independent
human accuracy label.

Historical manifests retain the original relative path strings and source hashes.
Use the [layout map and frozen sources](../reproducibility/README.md) to verify
these identities. The current [configurations](../configs/README.md) point to the
canonical named folders. Do not rewrite sealed manifests for cosmetic path changes.

```sh
.venv/bin/python scripts/evaluation/replay.py all
```

See [baseline reports](../docs/README.md) and the
[consolidated evidence tables](../docs/reports/evidence_tables.md) for interpretation.
