# Datasets

| Collection | Cases | Artifacts |
| --- | ---: | --- |
| Dialogue v1 | 100 | [JSONL](W01_Evaluation_Dataset_v1.jsonl) · [Manifest](W01_Evaluation_Dataset_v1.manifest.json) |
| Dialogue pilot | 12, included in v1 calibration | [JSONL](W01_Evaluation_Dataset_Pilot_v0.4.jsonl) · [Manifest](W01_Evaluation_Dataset_Pilot_v0.4.manifest.json) |
| Expanded v2 | 200, including all v1 cases | [JSONL](W01_Evaluation_Dataset_v2.jsonl) · [Manifest](W01_Evaluation_Dataset_v2.manifest.json) |
| Expansion pilot | 12, included in new calibration | [JSONL](W03_Evaluation_Dataset_Pilot_v0.1.jsonl) · [Manifest](W03_Evaluation_Dataset_Pilot_v0.1.manifest.json) |
| Approved recall amendment | 17 annotation edits; no new generation | [Versioned annotation](annotations/W03_Context_Recall_v2.0.1.json) |

The expanded collection contains 130 English and 70 Chinese cases across Fari
companion and Senpai educational scenarios: 155 RAG, 10 spatial, 5 temporal,
15 entity, and 15 goal-alignment cases. Its 100 additions comprise 20 calibration
and 80 new held-out cases. Earlier cases retain their historical subsets.
The two collections overlap; do not count them as 300 independent scenarios.

File names, case IDs, schema IDs, content, approval records, and manifests retain
their release identity. The `W01`/`W03` prefixes are historical identifiers.
The recall amendment binds original baseline paths; the
[public layout map](../reproducibility/layout_manifest.json) resolves those
historical references for verified replay. Do not edit its signed-off content to
rename paths or overwrite the frozen v2 required-fact inventory.

Read the [dataset documentation](dataset_documentation.md),
[initial specification](../docs/datasets/dialogue_specification.md),
[expanded specification](../docs/datasets/expanded_specification.md), and
[maintenance workflow](../docs/datasets/expanded_workflow.md) before modifying data.
Changed examples require renewed review; a manifest refresh grants no approval.

```sh
.venv/bin/python scripts/datasets/validate_dataset.py data/W01_Evaluation_Dataset_v1.jsonl --profile release --manifest data/W01_Evaluation_Dataset_v1.manifest.json
.venv/bin/python scripts/datasets/validate_dataset.py data/W01_Evaluation_Dataset_Pilot_v0.4.jsonl --profile pilot --manifest data/W01_Evaluation_Dataset_Pilot_v0.4.manifest.json
.venv/bin/python scripts/datasets/v2/manage_dataset.py validate data/W01_Evaluation_Dataset_v2.jsonl --profile release --manifest data/W01_Evaluation_Dataset_v2.manifest.json
.venv/bin/python scripts/datasets/v2/manage_dataset.py validate data/W03_Evaluation_Dataset_Pilot_v0.1.jsonl --profile pilot --manifest data/W03_Evaluation_Dataset_Pilot_v0.1.manifest.json
```

Native Chinese authorship/reworking and review have been confirmed for the
released dialogue cases. Validation checks attestations and content hashes; it
cannot independently establish authorship or truth. The amendment has its own
separate content-bound review status.
