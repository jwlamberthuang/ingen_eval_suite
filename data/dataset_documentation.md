# Week 1 bilingual dialogue dataset

[Dataset v1](W01_Evaluation_Dataset_v1.jsonl) contains 100 reviewed base cases in
99 scenario families. The [pilot](W01_Evaluation_Dataset_Pilot_v0.4.jsonl) is a
derived view of twelve calibration cases, adding no cases to the collection.

| Domain | Easy | Medium | Hard | Total | Calibration | Held out |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Fari English | 16 | 16 | 8 | 40 | 8 | 32 |
| Fari Chinese | 8 | 8 | 4 | 20 | 4 | 16 |
| Senpai English | 10 | 10 | 5 | 25 | 5 | 20 |
| Senpai Chinese | 6 | 6 | 3 | 15 | 3 | 12 |
| Total | 40 | 40 | 20 | 100 | 20 | 80 |

Calibration contains 19 families and held-out contains 80. The English and Chinese
reminder cases in `fam-0002` share a calibration family. Every domain has all three
tiers in both subsets. Exact cell quotas, seed, family-ranking method, and selected
IDs are in [dataset_config.json](../dataset_config.json).

All cases received authoring and annotation review. No held-out case has been
used for model selection or scorer tuning. Week 2 scores the held-out cases with
the frozen scorer and records those results in its weekly review package. This is a
partition within a public evaluation dataset; it does not establish that the
examples are absent from every model's training data.

The collection has 48 edge-tagged cases. Tags overlap:

| Tag | Cases |
| --- | ---: |
| partial_context | 28 |
| mixed_language | 5 |
| culturally_specific_zh | 4 |
| no_relevant_context | 3 |
| adversarial | 6 |
| conflicting_context | 3 |
| out_of_domain | 2 |

Every record has nine required fields: `id`, `domain`, `language`, `difficulty`,
`query`, `context`, `ideal_response`, `evaluation_labels`, and `construction_notes`.
Optional `input_metadata` supplies dialogue history and learner profiles. Senpai
records include a learner level and learning objective. The
[specification](../docs/dataset_specification.md) defines operational tier rules,
expected behavior, evidence support, edge tags, and annotation fields. The
[JSON Schema](../schemas/w01_dialogue_case.schema.json) is version 1.1.0.

Difficulty is assigned before inspecting model output: direct single-source
retrieval is Easy; necessary multi-step reasoning or passage integration is
Medium; missing/ambiguous evidence, scope challenges, or deliberate adversarial
probes are Hard. Language alone does not determine tier.

Inputs and reference answers are text intended for spoken dialogue. Fari uses
brief respectful wording. Senpai uses simple child queries and accessible
explanations. Mixed-language queries blend English content words into Chinese
syntax. The dataset measures no audio quality, pronunciation, prosody,
transcription, or audio latency.

I reviewed all English and Chinese queries and sample answers and
confirmed native authorship of all 35 Chinese cases on 2026-10-13. Release
preparation checked support links, quantities, deductions, tier rules, behavior,
family grouping, and public source eligibility. One human reviewer is recorded;
independent human annotation agreement has not been measured. English author
identity is unspecified where it has not been established.

Reviewed queries, contexts, ideal responses, and permitted input metadata are
preserved. Stale review-pending text was removed from rationale notes. The
notebook-cost criterion now permits the reviewed verbal explanation without
explicit multiplication notation. A route rationale correctly describes a
resurfacing closure. Sources and substantive factual labels are unchanged.

People, schedules, class policies, and contact details in original scenarios are
fictional. Cultural passages have public citations in each record and the
[source register](../docs/public_sources.md). Hidden canonical facts support
missing-evidence tests but must not be supplied to the model under test.

Validate from the repository root:

```sh
.venv/bin/python scripts/datasets/validate_dataset.py data/W01_Evaluation_Dataset_v1.jsonl --profile release --manifest data/W01_Evaluation_Dataset_v1.manifest.json
.venv/bin/python scripts/datasets/validate_dataset.py data/W01_Evaluation_Dataset_Pilot_v0.4.jsonl --profile pilot --manifest data/W01_Evaluation_Dataset_Pilot_v0.4.manifest.json
.venv/bin/python -m pytest -q
```

Validation rejects malformed records, stale hashes, broken evidence/source
references, unreviewed releases, and family leakage; it cannot establish truth or
authorship by itself. Manifests record hashes and review scope. See the
[framework](../docs/evaluation_framework.md) for metrics, applicability,
calibration, model input boundaries, and reporting.
