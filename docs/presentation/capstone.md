# Capstone slide text and evidence notes

This is the readable content companion to the [editable presentation](capstone.pptx)
and [ten-slide PDF](W04_Capstone_Deck.pdf). The PowerPoint preserves the slide layout,
native tables and charts, and speaker notes. Values describe the retained study;
recommendations and proposed experiments are prospective.

## 1. A bilingual benchmark makes metric limits visible

200 reviewed cases

80 new held-out cases

One public-model baseline

### Evidence and interpretation

The collection supports reproducible evaluation of bilingual dialogue and structured text tasks. Public Qwen and E5 models provide task proxies. The results establish neither internal InGen model performance nor physical robot capability. Sources: docs/reports/technical_report.md; docs/reports/evidence/summary.json. Cover image is a conceptual illustration in assets/dialogue_inspection.png.

Sources: docs/reports/technical_report.md.

## 2. Each capability needs its own scoring contract

| Assigned capability | Observable task | Measurements |
| --- | --- | --- |
| GRPO | Grounded dialogue | Context recall, faithfulness proxy, semantic relevance |
| STUM spatial | Spatial relations | Exact relation accuracy |
| STUM temporal | Event ordering | Pair accuracy, consistency, coherence |
| SEOM | Entity inventory | Recall, class accuracy, precision |
| HTD-IRL | Explicit goals and precedence | Goal coverage, precision, exact task success |

Pinned Qwen2.5-7B-Instruct 4-bit baseline and multilingual-e5-base embeddings

Audio, perception and robot execution require separate experiments

### Evidence and interpretation

The assigned capability labels describe text-task proxies. Context recall examines required facts against supplied context. The faithfulness approximation thresholds E5 cosine at 0.80 over inspected claims. Relevance compares query/response embeddings and has range [-1,1]. Spatial and temporal tasks require explicit relations. Entity and plan scoring use frozen matching rules. N/A, errors and parse coverage accompany the scores. Full definitions and empty-inventory rules are in the protocol. Public model cards: [Qwen model card](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct) and [E5 model card](https://huggingface.co/intfloat/multilingual-e5-base)

Sources: docs/methodology/evaluation_protocol.md; docs/methodology/extended_metrics.md.

## 3. 200 reviewed cases preserve a fresh 20/80 split

Task counts across the collection<br>
RAG: 155<br>
Spatial: 10<br>
Temporal: 5<br>
Entities: 15<br>
Goal planning: 15<br>

| Dataset property | Cases |
| --- | --- |
| English / Chinese | 130 / 70 |
| Easy / Medium / Hard | 60 / 80 / 60 |
| Fari / Senpai | 120 / 80 |
| Any edge-case tag | 145 / 200 |

Original 100 historical cases remain separate.<br>
New 100 cases contain 20 calibration and 80 held-out cases.<br>

Tagged challenges overlap: hallucination 11, adversarial/injection 20, mixed language 12, culture 6, out of domain 11

### Evidence and interpretation

The original 100 cases are historical. The 100 additions have a distinct family-safe 20 calibration / 80 held-out split. The new held-out set has 44 RAG and 36 structured cases. Counts describe the reviewed 200-case release. English and Chinese cases are native scenarios rather than matched translations. Edge counts use union of explicit tags: adversarial or prompt_injection; mixed_language or multilingual_mixture; culturally_specific_zh or cultural_context. Counts overlap across challenge categories. Native review attestation does not imply independent response assessment.

Sources: data/W01_Evaluation_Dataset_v2.jsonl; docs/datasets/expanded_specification.md.

## 4. High RAG similarity leaves correctness unresolved

| New held-out RAG | Mean ± population SD | Defined / eligible |
| --- | --- | --- |
| Context recall v2.0.1 | 0.7442 ± 0.4363 | 43/44 |
| Faithfulness proxy | 0.9050 ± 0.2085 | 43/44 |
| Semantic relevance | 0.8922 ± 0.0369 | 44/44 |

| Domain (N) | Context recall | Faithfulness proxy | Relevance |
| --- | --- | --- | --- |
| Fari EN (18) | 0.7059 ± 0.4556 | 0.8056 ± 0.2792 | 0.8690 ± 0.0311 |
| Fari ZH (9) | 0.7778 ± 0.4157 | 1.0000 ± 0.0000 | 0.9260 ± 0.0160 |
| Senpai EN (10) | 0.7000 ± 0.4583 | 0.9352 ± 0.1228 | 0.8808 ± 0.0319 |
| Senpai ZH (7) | 0.8571 ± 0.3499 | 1.0000 ± 0.0000 | 0.9246 ± 0.0142 |

Domain N/A: Fari EN recall 1, Senpai EN faithfulness 1. All scores show mean ± population SD.<br>
Recall is post-inspection. Faithfulness uses inspected claims.<br>

### Evidence and interpretation

All displayed values are mean and population SD, ddof=0. Domain parentheses give eligible counts. Fari EN recall excludes one N/A; Senpai EN faithfulness excludes one N/A. Every other domain score is defined for all eligible cases. New held-out RAG contains 44 cases. The context-recall v2.0.1 row is an approved post-inspection annotation diagnostic. It changes 17 fact inventories across 55 new RAG cases while retaining model inputs and all other metrics. Faithfulness uses inspected claim corrections and is assisted scoring. Higher Chinese scores cannot isolate a causal language effect because scenarios and group sizes differ. Lexical recall is auxiliary and appears in the full report.

Sources: docs/reports/evidence/summary.json; docs/reports/technical_report.md.

## 5. Raw extraction fails all 155 strict output contracts

Selected RAG failure flags (44 cases)<br>
Role confusion: 4<br>
Prompt injection: 4<br>
Reasoning error: 3<br>

Raw claim proposals across all 155 RAG cases

| Output type | Cases |
| --- | --- |
| Bare arrays | 153 |
| Malformed JSON | 2 |
| Strict claims objects | 0 |

29 meet / 10 partial / 5 fail reference<br>
Inspection verdicts across 44 new held-out RAG cases<br>

155 separate inspected corrections enable assisted scoring

RAG flags overlap. Extraction and response inspection measure different stages.

### Evidence and interpretation

The extraction denominator is every RAG case in the 200-case collection, not just new held-out cases. Every raw proposal is a scorer error under the frozen object contract: 153 bare arrays, 2 malformed JSON. The separate 155 inspected corrections comprise 70 transport changes and 85 content/scope changes, with two claim-free responses. The chart shows selected overlapping failure flags in the 44 new held-out RAG responses. Technical inspection assigns 29 meets-reference, 10 partial and 5 fails-reference verdicts. This inspection is not independent human accuracy. Other flags remain in the evidence tables.

Sources: results/extended_baseline/claim_review.json; docs/reports/evidence/summary.json.

## 6. Only 3 of 12 plans meet the full task contract

| Task | Valid / eligible | Exact success | Success mean ± SD |
| --- | --- | --- | --- |
| STUM spatial | 8/8 | 7/8 | 0.8750 ± 0.3307 |
| STUM temporal | 4/4 | 4/4 | 1.0000 ± 0.0000 |
| SEOM entities | 12/12 | 7/12 | 0.5833 ± 0.4930 |
| HTD-IRL goals | 7/12 | 3/12 | 0.2500 ± 0.4330 |

Planning core coverage: 0.8611 ± 0.2022 across 6 defined cases

Five malformed plans keep task success zero. Conditional coverage excludes those failures.

### Evidence and interpretation

All cases belong to the 36 new held-out structured tasks. Exact success is binary, so means and population SDs summarize success over all eligible cases. Parse-valid counts remain visible. Five malformed plans retain zero task success and undefined core metrics. Planning coverage is conditional on six defined cases, including the exclusion of one valid empty-reference case. The two frozen alias limitations retain their strict scores. Four temporal examples support only a small descriptive result.

Sources: docs/reports/evidence/summary.json; results/extended_baseline/scores.json.

## 7. All ten flawed probes receive faithfulness 1.0

Trusted evidence

钥匙是给陈阿姨留的，包裹才是给王阿姨的。

The key is for Aunt Chen.<br>
The parcel is for Aunt Wang.<br>
The key is at the service desk.<br>

Actual model response

那把钥匙是给王阿姨留的，放在服务台。

The recipient is wrong. The location is right.

Separate fixed two-claim probe

| Claim | Support |
| --- | --- |
| Key for Aunt Wang | 0 |
| Key at service desk | 1 |

Ideal support  0.5<br>
Proxy score    1.0<br>

Proxy = mean 1[cosine ≥ 0.80]

### Evidence and interpretation

The Chinese example is case w03-rag-fari-zh-0171-base. The actual model response is separate from the prewritten fixed two-claim probe. Trusted evidence leaves the key for Aunt Chen, the parcel for Aunt Wang, and places the key at the service desk. The generated answer assigns the key to Aunt Wang. The separate fixed probe has ideal supported-claim fraction 1/2 but receives proxy 1.0. All ten fixed flawed probes receive 1.0, although their ideal fractions are 0 or 1/2. These tests establish a measurement counterexample, not a model-generation accuracy rate. The proxy averages indicators that maximum claim-to-evidence E5 cosine reaches 0.80. No entailment or approximation guarantee follows from that similarity threshold.

Sources: docs/reports/technical_report.md; results/extended_baseline/analysis/fixed_probes.json.

## 8. Saved artifacts reproduce the reported computations

| Repository area | Evidence |
| --- | --- |
| data/ | Reviewed cases and manifests |
| src/ and tests/ | Metrics and verified examples |
| results/ | Outputs, inspections and scores |
| notebooks/ | Executed demonstrations |
| reproducibility/ | Historical source and layout map |

Recorded checks

357 tests passed<br>
Exact saved-score replay<br>

`python -m pytest -q`

`python scripts/evaluation/replay.py all`

Final clean-clone installation and release tag remain pending

[Public repository](https://github.com/jwlamberthuang/ingen_eval_suite)

### Evidence and interpretation

The project is organized by topic. The public reproduction guide documents installation, tests, notebooks and offline replay. The latest recorded full-suite check passed 357 tests. This is a recorded outcome, not a claim that the final release has completed clean-clone dependency installation. Exact replay uses saved vectors and responses and does not establish identical fresh inference on different hardware. The source/layout manifest preserves original identities. Publication and the final release tag remain separate steps. Public repository: [Public repository](https://github.com/jwlamberthuang/ingen_eval_suite)

Sources: docs/reproducibility.md; reproducibility/README.md; validation/layout_validation.json.

## 9. Three targeted changes address the main failure modes

### 1. Bilingual support judgments

Ten flawed probes score 1.0. Reviewed negative labels can test authority, contradiction and entity binding.

Measure false-positive support, balanced accuracy and per-language coverage.

### 2. Claims output and correspondence

All 155 raw proposals fail the contract. Constrained extraction can improve format reliability.

Measure raw parse coverage, omitted claims and assisted versus automatic scoring.

### 3. Structured validity and matching

Five held-out plans are malformed. Two cases expose frozen alias limitations.

Test schema enforcement and reviewed aliases with task success and conditional coverage.

### Evidence and interpretation

These are prospective recommendations. No completed baseline, threshold, aliases or model-visible inputs have changed. Support validation needs reviewed bilingual negative examples and untouched families. Extraction needs contract-valid output and correspondence measurements separately. Structured reliability needs schema enforcement and reviewed alias coverage, with exact success over all eligible cases. Any selected changes must be frozen on calibration before a new held-out evaluation.

Sources: docs/reports/technical_report.md, Discussion; docs/reports/evidence_tables.md.

## 10. Three controlled studies can test the proposed fixes

### 1. Support validity across languages

New reviewed negative examples test contradiction, authority, quantity and identity.

### 2. Extraction contract ablation

Compare constrained output with the frozen baseline and inspect claim correspondence.

### 3. Structured generalization

New goal, precedence and alias families test reliability beyond the inspected cases.

AMDC and CRL-MRS need task contracts. Audio and physical execution remain separate work.

[Public repository](https://github.com/jwlamberthuang/ingen_eval_suite)

### Evidence and interpretation

Second-cycle studies need new reviewed scenario families, calibration-only selection and a frozen evaluation contract. These are planned experiments, not measured improvements. A support study can compare the current cosine proxy with an authority-aware support method. An extraction ablation can separate schema success from claim correspondence. A structured generalization study can test goals, precedence and bilingual aliases. AMDC and CRL-MRS remain future task-contract work, while audio and physical execution require separate evidence. Repository: [Public repository](https://github.com/jwlamberthuang/ingen_eval_suite)

Sources: docs/reports/technical_report.md, Discussion and Conclusion.
