# Week 3 review package

The 200-case release, formal protocol, extended metrics, recorded baseline,
executed demonstration notebook, and reflection are assembled for review.
Model execution and exact score replay are complete. **Read the measurement
limitations before interpreting or publishing the results**: all raw extraction
proposals failed their output contract; the support proxy accepts flawed boundary
candidates; and the separately approved context-recall amendment is a
post-inspection diagnostic. The original dataset and completed experiment remain frozen.

## Start here

1. [Results and failure analysis](../../docs/week-03/W03_Extended_Evaluation_Results.md)
2. [Executed evaluation notebook](../../notebooks/week-03/W03_Extended_Evaluation_Suite.ipynb)
3. [Methodological reflection](../../weekly/Wk-03-Log.md)
4. [Formal protocol: Word](../../docs/week-03/W03_Evaluation_Protocol.docx) · [Markdown](../../docs/week-03/W03_Evaluation_Protocol.md)
5. [Approved context recall correction: Word](../../docs/week-03/W03_Context_Recall_Review_v2.0.1.docx) · [Markdown](../../docs/week-03/context_recall_correction.md)

The annotation amendment audits all 55 new RAG cases and changes 17. Corrected
context recall becomes **0.8182 (11/11 defined)** in new calibration and **0.7442
(43/44 defined)** in new held-out. The frozen baseline remains 1.0000 for each.
All other metrics and model-visible inputs are unchanged; no generation was run.
The intern reviewed and approved all 17 corrections, including missing answer
slots, conflicts, case 0186's N/A decision, and revised Chinese annotation wording.
The approval binds exact amendment content and all reviewed case IDs. Original
dialogue and authorship approval remains specific to the frozen source.

Primary results use 80 new held-out cases: 44 RAG and 36 structured. New
calibration and previously evaluated legacy examples are reported separately.

| New held-out task | Valid outputs | Exact task success |
| --- | ---: | ---: |
| Spatial | 8/8 | 7/8 |
| Temporal | 4/4 | 4/4 |
| SEOM | 12/12 | 7/12 |
| HTD-IRL | 7/12 | 3/12 |

The report separates malformed plans, omitted entities/goals, extra tasks,
reasoning errors, and two frozen HTD alias limitations. Conditional metric means
retain their denominators. The notebook includes 10 STUM, 6 SEOM, and 6 HTD
recorded demonstrations, language/tier summaries, and visualizations. Small
samples and technical qualitative inspection do not establish independent human
accuracy or performance of internal robot systems.

## Required deliverables

| Deliverable | Canonical artifact |
| --- | --- |
| Expanded dataset, at least 200 cases | [200-case JSONL](../../data/W01_Evaluation_Dataset_v2.jsonl) · [Manifest](../../data/W01_Evaluation_Dataset_v2.manifest.json) |
| Extended evaluation notebook | [Executed notebook](../../notebooks/week-03/W03_Extended_Evaluation_Suite.ipynb) |
| Formal evaluation protocol | [Word](../../docs/week-03/W03_Evaluation_Protocol.docx) · [Markdown](../../docs/week-03/W03_Evaluation_Protocol.md) |
| At least 20 additional metric tests | [76 extended metric tests](../../tests/test_extended.py) |
| Methodological reflection, 300–500 words | [Week 3 log](../../weekly/Wk-03-Log.md) |

## Dataset and review copies

The original 100 JSONL lines are unchanged. The additions contain 55 RAG,
15 STUM (10 spatial/5 temporal), 15 SEOM, and 15 HTD cases, with 65 EN/35 ZH,
20 Easy/40 Medium/40 Hard, and a fresh 20/80 calibration/held-out split.
All 100 new content/reference reviews are approved. Native authorship or
substantial native reworking and review of all 35 new Chinese cases were
confirmed separately on October 27, 2026. Independent reviewer agreement has
not been measured. Historical construction notes retain drafting context;
current review annotations establish approval status.

- [Twelve-case pilot JSONL](../../data/W03_Evaluation_Dataset_Pilot_v0.1.jsonl) · [Manifest](../../data/W03_Evaluation_Dataset_Pilot_v0.1.manifest.json)
- [Pilot Word packet](../../docs/week-03/W03_Dataset_Pilot_Review_v0.1.docx) · [Markdown](../../docs/week-03/pilot_review.md)
- [88 additions Word packet](../../docs/week-03/W03_Dataset_Additions_Review_v0.1.docx) · [Markdown](../../docs/week-03/additions_review.md)
- [Coverage, evidence convention, and maintenance](../../docs/week-03/dataset_v2_workflow.md)
- [Reviewed design specification](../../docs/week-03/dataset_v2_specification.md)
- [Release schema](../../schemas/w03_evaluation_case.schema.json) · [Allocation configuration](../../configs/dataset-v2.json)

The original three Word documents preserve Times New Roman and Songti SC. Their 67 pages
are visually verified. The correction review sheet follows the same fonts and
all ten pages are visually verified.
New evidence/event descriptions use explicit names, user,
or specific objects/events; dialogue keeps natural pronouns. The results report
documents the approved denominator amendment separately from the frozen run.

## Implementation and recorded evidence

- [Metric API and limitations](../../docs/week-03/extended_metrics.md) · [Metric module](../../src/extended_evaluator.py)
- [Experiment guide](../../docs/week-03/experiment_pipeline.md) · [Configuration](../../configs/week-03.json)
- [Input/RAG adapters](../../src/week3_inputs.py) · [Staged pipeline](../../src/week3_experiment.py)
- [Analysis functions](../../src/week3_analysis.py) · [Analysis command](../../scripts/evaluation/analyze_week3.py) · [Notebook builder](../../scripts/evaluation/build_week3_notebook.py)
- [Run manifest](../../results/week-03/w03-qwen25-7b-mlx4bit-text-v1/run_manifest.json) · [Frozen scores](../../results/week-03/w03-qwen25-7b-mlx4bit-text-v1/scores.json)
- [Annotation amendment](../../data/annotations/W03_Context_Recall_v2.0.1.json) · [Amendment schema](../../schemas/w03_context_recall_amendment.schema.json)
- [Correction replay](../../results/week-03/context-recall-v2.0.1/context_recall.json) · [Correction manifest](../../results/week-03/context-recall-v2.0.1/manifest.json) · [Replay command](../../scripts/evaluation/correct_week3_context_recall.py)
- [Raw responses](../../results/week-03/w03-qwen25-7b-mlx4bit-text-v1/responses.jsonl) · [Raw extraction](../../results/week-03/w03-qwen25-7b-mlx4bit-text-v1/claims.jsonl) · [Inspected claim corrections](../../results/week-03/w03-qwen25-7b-mlx4bit-text-v1/claim_review.json)
- [Technical RAG inspection](../../results/week-03/w03-qwen25-7b-mlx4bit-text-v1/response_review.jsonl) · [Inspection scope/definitions](../../results/week-03/w03-qwen25-7b-mlx4bit-text-v1/response_review_metadata.json)
- [Structured failure inspection](../../results/week-03/w03-qwen25-7b-mlx4bit-text-v1/structured_failure_review.jsonl) · [Fixed probes](../../results/week-03/w03-qwen25-7b-mlx4bit-text-v1/analysis/fixed_probes.json) · [Supplementary manifest](../../results/week-03/w03-qwen25-7b-mlx4bit-text-v1/analysis/manifest.json)

There are 200 recorded answer attempts and 155 extraction attempts, with no
substantive retries. Raw extraction coverage is 0/155 under the strict contract;
post-inspection claims permit assisted scoring. The transferred support threshold
is 0.80. All ten prewritten flawed candidates receive proxy 1.0, demonstrating
that similarity does not establish factual support. No new threshold was fitted.

## Validation and reproduction

- [Full verification summary](validation/tests.json)
- [Actual pipeline and replay verification](validation/pipeline.json)
- [Release validation](validation/collection.json) · [Pilot validation](validation/pilot.json)
- [Dataset/review tests](../../tests/test_dataset_v2.py) · [Collection tests](../../tests/test_dataset_v2_collection.py)
- [Adapter tests](../../tests/test_week3_inputs.py) · [Pipeline tests](../../tests/test_week3_experiment.py)
- [Analysis checks](../../tests/test_week3_analysis.py) · [Recorded-artifact checks](../../tests/test_week3_artifacts.py)
- [Annotation-correction checks](../../tests/test_week3_context_recall.py)

All **336 tests pass**. Release/pilot validation has zero errors and warnings. Collection, pilot, and
both manifests rebuild byte for byte. All original Week 1/2 protected artifacts
remain unchanged. Metric tests use hand-worked synthetic fixtures; real results
are recorded separately and replay exactly from portable vectors.

```sh
.venv/bin/python scripts/evaluation/week3.py replay
.venv/bin/python scripts/evaluation/analyze_week3.py --replay
.venv/bin/python scripts/evaluation/correct_week3_context_recall.py --replay
.venv/bin/python scripts/evaluation/build_week3_notebook.py --execute
.venv/bin/python -m pytest -q
```

The [Week 1 package](../week-01/README.md) and [Week 2 experiment](../week-02/README.md)
remain available independently. All Week 3 deliverables and the separately
approved annotation correction are prepared for submission. Measurement limitations
remain explicit in the report and notebook.
