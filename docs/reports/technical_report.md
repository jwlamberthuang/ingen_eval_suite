# Technical evaluation of bilingual dialogue and structured reasoning

ingen_eval_suite | Technical report v1.0 | 2 November 2026

## Abstract

This study develops a reproducible evaluation suite for bilingual companion and
educational dialogue and three structured reasoning capabilities: spatial and
temporal understanding, entity recognition and classification, and explicit-goal
alignment. A reviewed 200-case collection combines 100 historical dialogue cases
with 100 additions, separating 20 new calibration cases from 80 new held-out
cases. A pinned, quantized Qwen2.5-7B-Instruct baseline is evaluated with
reference-based context recall, an embedding faithfulness proxy, semantic
relevance, and strict structured-task metrics. The new held-out results show
exact task success of 7/8 spatial, 4/4 temporal, 7/12 entity, and 3/12 planning
cases. Assisted faithfulness averages 0.9050 over 43 defined RAG cases, yet all
ten deliberately flawed fixed probes receive a perfect proxy score. Every raw
claim proposal fails its strict output contract. A separately approved
annotation correction yields context recall of 0.7442 over 43 defined held-out
cases without changing generated answers. These findings motivate explicit
coverage reporting, authority-aware support assessment, and prospective output
and matching improvements. Exact offline replay establishes computational
reproducibility while exposing substantive limits in measurement validity.

## Introduction

Grounded dialogue must use the supplied evidence, address the user's question,
and respond appropriately when information is missing or contradictory. A robot
interaction also raises questions about spatial relationships, temporal ordering,
entity identity and requested actions. A single similarity score cannot establish
all of these properties.

The suite evaluates text tasks in Fari companion and Senpai educational settings.
The [framework](../methodology/evaluation_framework.md) in the public suite [1] maps the assigned GRPO,
STUM, SEOM and HTD-IRL capability labels to observable evaluation objectives.
These are task proxies: the study has no access to internal InGen models and does
not measure perception, robot actuation or audio delivery. The
[public source register](../references/public_sources.md) distinguishes public
product descriptions from assigned capability terminology. AMDC and CRL-MRS
remain future evaluation areas.

The contribution is a reviewed bilingual collection, explicit metric contracts,
controlled model inputs, tested scoring, and retained artifacts that expose both
model failures and failures of the measurement approximation. The initial
[RAG study](rag_baseline.md) supplies historical evidence; the
[extended study](extended_baseline.md) supplies the primary new cohort.

<!-- pagebreak -->

## Methodology

### Data and experimental boundaries

The reviewed collection contains 130 English and 70 Chinese cases: 155 RAG, 10 spatial, 5 temporal, 15 entity and 15 goal-alignment tasks. Cases contain queries, supplied evidence, hidden references, scenario families and subsets. Fictional contexts are self-contained; public facts have citations. New evidence uses explicit names or user references. Native Chinese authorship or substantive native reworking and review were confirmed. This review is distinct from independent assessment of generated responses.

The 100 historical cases retain their original subsets. The 100 additions have 20 calibration and 80 new held-out cases (44 RAG, 36 structured). Families and input allowlists were frozen before generation. The collections overlap. Models see queries, evidence and permitted metadata, not expected answers, support labels, hidden graphs or goal references. The [protocol](../methodology/evaluation_protocol.md) and [specification](../datasets/expanded_specification.md) provide full contracts.

### Models and protocol

The pinned four-bit Qwen2.5-7B-Instruct conversion [2] uses MLX [5], temperature zero, seed 17, 512 output tokens and a 4096-token input limit. Multilingual-e5-base [3] embeds text on CPU. The same generator proposes claims. The support threshold transfers unchanged at 0.80 from initial calibration; sparse negative labels limit cross-language validity. Revisions, prompts, runtime and attempts remain in the run manifest. No tuning uses held-out results.

### Formal metric specifications

Let F be required facts, C the context and S(f, C) reviewed support. Context recall is Σ S(f, C) / |F|, with an empty F marked N/A. The approved annotation v2.0.1 changes 17 inventories after inspection without changing model inputs or other metrics; it is a diagnostic, not fresh held-out evidence.

For inspected claims A, proxy faithfulness is Σ 1[max cosine(Eq(a), Ep(c)) ≥ 0.80] / |A|, over a in A and segmented evidence c in C. Eq and Ep use E5 query and passage prefixes. Appropriate claim-free responses are N/A. This approximation to claim support [4] does not prove entailment. Semantic relevance is cosine(Eq(query), Eq(response)), in [-1, 1]; invalid vectors or over-limit inputs are scorer errors. Lexical reference recall is supplementary and wording-sensitive.

Spatial accuracy indicates an exact relation match. Temporal pair accuracy is correct/requested pairs; coherence multiplies this by binary consistency against contradictions/cycles. Entity recall and class accuracy divide correct identities and correctly classified identities by gold count; precision divides matches by predictions. Goal coverage is M/G and precision M/P for maximum one-to-one matches M, gold goals G and predictions P, with precedence and frozen aliases.

Means and population SDs use defined values (ddof=0). N/A and errors retain counts. Malformed structured outputs have null core metrics and task success zero; valid empty inventories follow explicit denominator rules. Exact success and parse coverage accompany conditional means. No composite score combines capabilities. [Saved-vector replay](../reproducibility.md) verifies recorded computations independently of fresh inference.


<!-- pagebreak -->

## Results

### New held-out RAG measurements

Table 1. Core RAG results for the new held-out cohort.

| Measurement | Mean | Population SD | Defined / eligible | N/A | Errors |
| --- | ---: | ---: | ---: | ---: | ---: |
| Context recall, annotation v2.0.1 | 0.7442 | 0.4363 | 43/44 | 1 | 0 |
| Inspected-claim faithfulness proxy | 0.9050 | 0.2085 | 43/44 | 1 | 0 |
| Semantic relevance | 0.8922 | 0.0369 | 44/44 | 0 | 0 |
| Lexical reference recall | 0.4386 | 0.2137 | 44/44 | 0 | 0 |

The recall diagnostic gives 0.8182 ± 0.2405 on 11 new calibration cases (9/11) and 0.7442 ± 0.4363 on 43 defined held-out cases (32/43).
The original fact inventories yielded mean 1.0000 ± 0.0000 for all 11 and 44 respective
cases; supported descriptions of missingness could receive full recall despite
unavailable requested information. The amended inventory makes that distinction
visible and makes one held-out ambiguous-speaker case N/A. Original annotations
and scores remain available beside the amendment.

### New held-out structured tasks

Table 2. Structured tasks retain invalid outputs in the eligible denominator.

| Task | Valid / eligible | Exact success: n/N; mean ± SD | Core mean ± population SD (defined count) |
| --- | ---: | ---: | --- |
| Spatial | 8/8 | 7/8; 0.8750 ± 0.3307 | Accuracy 0.8750 ± 0.3307 (8) |
| Temporal | 4/4 | 4/4; 1.0000 ± 0.0000 | Pair accuracy, consistency, coherence each 1.0000 ± 0.0000 (4) |
| Entity | 12/12 | 7/12; 0.5833 ± 0.4930 | Recall 0.8125 ± 0.2724 (12); class accuracy 0.7708 ± 0.2787 (12); precision 1.0000 ± 0.0000 (12) |
| Goal planning | 7/12 | 3/12; 0.2500 ± 0.4330 | Coverage 0.8611 ± 0.2022 (6); precision 0.6905 ± 0.3384 (7) |

Five malformed held-out plans have undefined core metrics and zero task success.
One valid no-goal reference has undefined coverage; an extra prediction gives
precision zero. Conditional planning coverage therefore does not summarize
end-to-end planning success. Four successful temporal cases are too few for a
strong generalization claim.

<!-- pagebreak -->

### Domain and difficulty results

Table 3. New held-out RAG subgroups. Each metric cell is mean ± population SD, followed by defined/eligible count. Context recall uses annotation v2.0.1.

| Group | Context recall | Faithfulness proxy | Semantic relevance |
| --- | ---: | ---: | ---: |
| Fari EN | 0.7059 ± 0.4556; 17/18 | 0.8056 ± 0.2792; 18/18 | 0.8690 ± 0.0311; 18/18 |
| Fari ZH | 0.7778 ± 0.4157; 9/9 | 1.0000 ± 0.0000; 9/9 | 0.9260 ± 0.0160; 9/9 |
| Senpai EN | 0.7000 ± 0.4583; 10/10 | 0.9352 ± 0.1228; 9/10 | 0.8808 ± 0.0319; 10/10 |
| Senpai ZH | 0.8571 ± 0.3499; 7/7 | 1.0000 ± 0.0000; 7/7 | 0.9246 ± 0.0142; 7/7 |
| Tier: Easy | 1.0000 ± 0.0000; 1/1 | 1.0000 ± 0.0000; 1/1 | 0.9065 ± 0.0000; 1/1 |
| Tier: Medium | 1.0000 ± 0.0000; 17/17 | 0.9167 ± 0.1566; 17/17 | 0.8886 ± 0.0455; 17/17 |
| Tier: Hard | 0.5600 ± 0.4964; 25/26 | 0.8933 ± 0.2398; 25/26 | 0.8939 ± 0.0305; 26/26 |
| Language: English | 0.7037 ± 0.4566; 27/28 | 0.8488 ± 0.2464; 27/28 | 0.8732 ± 0.0319; 28/28 |
| Language: Chinese | 0.8125 ± 0.3903; 16/16 | 1.0000 ± 0.0000; 16/16 | 0.9254 ± 0.0153; 16/16 |

The [domain, tier and language tables](evidence_tables.md) retain small group
sizes and all denominators. English and Chinese scenarios are authored natively
rather than matched translations. Descriptive language differences cannot isolate
a causal language effect. Differences from the earlier baseline also mix changed
scenario composition, input transport and claim inspection; they do not establish
model improvement.

Hard cases have amended recall 0.5600 ± 0.4964 (25/26 defined), while the single easy case and 17 medium cases have recall 1.0000 ± 0.0000. The easy stratum supports no broad estimate. All 16 Chinese RAG examples receive proxy faithfulness 1.0000 ± 0.0000; this is compatible with the measurement failures below and cannot certify answer correctness.

For historical context, the initial RAG experiment's 80 held-out cases have recall 0.9286 ± 0.2379 (77 defined), faithfulness proxy 0.9602 ± 0.1224 (80), and relevance 0.8852 ± 0.0380 (80). These are descriptive earlier-run results, not an independent comparison or evidence of model improvement.

<!-- pagebreak -->

## Error analysis

The initial 100-case RAG inspection flagged context utilization in 8/100 cases (8%), hallucination in 3/100 (3%), cross-language failure in 1/100 (1%), difficulty-tier calibration checks in 2/100 (2%), and no out-of-domain failure. These overlapping flags describe the earlier run; they are separate from the new held-out cohort below. Difficulty flags concern dataset calibration as well as model behavior.

All 200 response attempts returned nonempty outputs. Raw extraction completed
155 attempts, but 0/155 satisfied the strict claims-object contract: 153 bare
arrays and two malformed JSON proposals remain recorded as scorer errors.
The separate inspection contains 155 corrections: 70 transport normalizations
and 85 content/scope changes. Two inspected responses are claim-free. Reported
faithfulness is consequently an assisted diagnostic, not a fully automatic result.

Technical inspection of 44 new held-out RAG responses assigns 29 meets-reference,
10 partial and five fails-reference verdicts. This is a technical inspection,
not independent human accuracy. Categories overlap: prompt injection and speaker
role confusion each appear in 4/44 cases (9.1%), reasoning error in 3/44 (6.8%); other
categories and their exact counts are in the [failure tables](evidence_tables.md).
These counts must not be summed as mutually exclusive failures.

Of 36 new held-out structured cases, 15 lack exact success. Table 4 assigns one inspection category to each such case. Fractions use all 36 eligible structured cases, including successes. The two alias cases retain strict scores despite legitimate unlisted paraphrases; they are matcher limitations rather than demonstrated model intent failures.

Table 4. Exclusive structured inspection categories in the new held-out cohort.

| Category | Cases / 36 | Fraction |
| --- | ---: | ---: |
| Output format | 5/36 | 13.9% |
| Missing entity | 4/36 | 11.1% |
| Frozen alias limitation | 2/36 | 5.6% |
| Extra goal | 2/36 | 5.6% |
| Class error | 1/36 | 2.8% |
| Conflict resolution | 1/36 | 2.8% |

The measurement counterexamples are consequential. All ten prewritten flawed
candidates receive faithfulness proxy 1.0 despite ideal supported-claim fractions
of zero or one half. They are fixed probes, not model generations. In case 0170,
permission to take a tablet is similar to evidence about a prohibition; in 0103,
a wrong seven-star assertion can match an untrusted quoted instruction despite
trusted arithmetic giving twenty. These examples expose missing authority,
negation and quantity reasoning in cosine similarity. Original model outputs,
probe texts and inspected explanations remain accessible in the
[extended report](extended_baseline.md).

The Chinese case w03-rag-fari-zh-0171-base makes the identity error explicit. Trusted context states “钥匙是给陈阿姨留的，包裹才是给王阿姨的。” and locates the key at the service desk. The actual model response is “那把钥匙是给王阿姨留的，放在服务台。” The recipient is wrong while the location is right. The separately prewritten two-claim probe has ideal support 1/2 but proxy score 1.0. Similar topic and wording do not preserve entity binding.


<!-- pagebreak -->

## Discussion

Three prospective improvements follow from the retained evidence:

1. **Validate evidence support against bilingual negative labels.** Build reviewed
   authority, contradiction, quantity, negation and entity-binding judgments before
   a new calibration. Compare the current proxy with a proposed support method on
   false-positive rate, balanced accuracy and per-language coverage. Freeze the
   method on calibration and evaluate untouched families; do not optimize a mean
   similarity score on the inspected held-out cases.
2. **Improve the claims output contract and measure correspondence separately.**
   Evaluate constrained structured extraction or explicit transport normalization
   in a new version. Report raw parse coverage, omitted/duplicated assertions,
   correspondence errors and assisted versus automatic scoring. The baseline is
   0/155 strict contract success; a future pipeline must preserve raw attempts and
   distinguish formatting improvements from faithful claim extraction.
3. **Separate structured output reliability from reference matching.** Test schema
   enforcement, entity completeness and goal precision, and review bilingual alias
   coverage before freezing a new version. Report exact success over every eligible
   case, parsing coverage, conditional metric means and alias disagreement counts.
   The current 3/12 planning exact success and two retained alias limitations define
   concrete targets for a prospective comparison without rewriting the baseline.

The study has one quantized public model, small structured groups, constructed
scenarios, sparse negative calibration labels and non-independent technical
inspection. Saved-score replay establishes reproducibility of computations, not
construct validity. Future AMDC and CRL-MRS work needs its own observable task
contract and data specification before implementation. Audio, sensing and physical
execution require separate experiments and evidence.

## Conclusion

The suite provides an auditable bilingual dataset, manually verified metric
implementations and exact replay across a project-oriented repository layout.
The strongest findings concern measurement: high embedding support scores can
accept false or unauthorized assertions, and conditional planning coverage can
hide malformed outputs and extra goals. Coverage, explicit denominators, separate
failure inspection and retained raw artifacts make these limits visible. The
next evaluation cycle should validate support judgments and output contracts
prospectively on new scenario families while preserving the recorded baseline.

<!-- pagebreak -->

## References and reproducibility

### Public methodological references

[1] ingen_eval_suite. [Public evaluation repository](https://github.com/jwlamberthuang/ingen_eval_suite). The artifact paths below identify the retained study evidence.

[2] Qwen team. [Qwen2.5 7B Instruct model card](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct); MLX Community. [Four-bit conversion](https://huggingface.co/mlx-community/Qwen2.5-7B-Instruct-4bit). The study evaluates the pinned conversion, not every configuration of the parent model.

[3] intfloat. [Multilingual E5 base model card](https://huggingface.co/intfloat/multilingual-e5-base). Embedding prefixes, pooling, token limits and interpretation.

[4] Ragas. [Context recall](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_recall/) and [faithfulness](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/). Claim-support definitions provide methodological context; the suite's cosine proxy is a distinct implementation.

[5] MLX team. [MLX LM](https://github.com/ml-explore/mlx-lm). Runtime for the recorded quantized inference.

### Artifact and source identities

Table 5. Repository-relative paths identify the report's evidence. They require no private files.

| Evidence | Repository path |
| --- | --- |
| Complete numeric tables and input hashes | `docs/reports/evidence/summary.json` |
| Protocol and task definitions | `docs/methodology/evaluation_protocol.md` |
| Dataset and approved release manifest | `data/W01_Evaluation_Dataset_v2.jsonl` and matching `.manifest.json` |
| Actual model responses and inspections | `results/extended_baseline/` |
| Approved annotation-only diagnostic | `results/context_recall_v2.0.1/` |
| Exact historical source and layout identities | `reproducibility/layout_manifest.json` |

The generation revision is `c26a38f6a37d0a51b4e9a1eb3026530fa35d9fed`; the embedding revision is `d128750597153bb5987e10b1c3493a34e5a4502a`. Full prompts, settings, raw attempts and source fingerprints remain in the recorded run. Historical source paths resolve through the verified layout migration; experiment identities were not resealed.

From the repository root, run `python scripts/evaluation/replay.py all` to recompute the RAG and extended scores, approved amendment and fixed probes without downloads or new inference. Run `python scripts/reporting/build_report_evidence.py --check` to verify the report's derived tables against retained inputs. Setup and pinned dependencies are documented in `docs/reproducibility.md`.

Replay proves that saved computations reproduce. It does not establish identical fresh generations across hardware, logical entailment from embedding similarity, or independent human agreement. The recorded data and inspection status govern interpretation of every table.
