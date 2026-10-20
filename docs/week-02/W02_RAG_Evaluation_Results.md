# Week 2 RAG Evaluation Results

Grounded bilingual dialogue baseline

ingen_eval_suite | Experiment version 1.0 | October 19 2026

The fixed-context experiment produced 100 model responses without generation errors. On the eighty held-out cases, mean context recall was 0.9286, mean faithfulness proxy was 0.9602, and mean semantic relevance was 0.8852. These measure distinct properties and do not form a composite quality score. Technical inspection found six confirmed response failures in that subset and one case requiring review of the implicit user-identity assumption.

The most consequential finding is that high embedding scores can accompany a wrong answer. The support calibration accepted an unsupported room and an unresolved time conflict. The results below therefore separate arithmetic correctness, evidence sufficiency, retrieval-proxy behavior, and inspected response quality. They concern the declared public baseline and text benchmark.

## Experiment and data

The collection contains 100 reviewed cases: 40 Fari English, 20 Fari Chinese, 25 Senpai English, and 15 Senpai Chinese. Difficulty counts are 40 Easy, 40 Medium, and 20 Hard. Forty-eight cases have edge tags. Twenty calibration cases in nineteen families are separated from eighty held-out cases in eighty families. Related examples and the twelve-case pilot stay in calibration.

The dataset/schema hash issue was repaired before execution. All reviewed queries, contexts, ideal responses, permitted input metadata, IDs, language/domain labels, and tiers are unchanged. Both release and pilot validation have zero errors and warnings. The [validation update](validation_update.md) records the current hashes and repair method.

**Table 1 Execution configuration**

| Component | Recorded setting |
| --- | --- |
| Generation | Qwen2.5 7B Instruct, four-bit MLX conversion |
| Generation revision | c26a38f6a37d; full revision in run manifest |
| Local runtime | Apple M2 with 24 GB memory; MLX LM 0.32.2 |
| Generation settings | Greedy sampling; seed 17; at most 512 new tokens; 60-second case budget |
| Input mode | Fixed full context; explicit query/history/learner allowlist; hidden references excluded |
| Embedding | Multilingual E5 base; CPU; normalized mean pooling; 512-token input limit |
| Embedding revision | d12875059715; full revision in run manifest |
| Attempts | One local attempt per stage and case; no retries of substantive answers |

## Measurements and verification

Context recall is the supported fraction of the required reference facts, using reviewed fact-to-context annotations. It measures evidence sufficiency independently of model output. Known targets remain in the denominator when evidence is withheld; four fact-free cases are not applicable. Lexical reference recall is a separately named overlap diagnostic, using jieba for Chinese and a lowercase word/number regex for English.

Faithfulness proxy is the fraction of inspected response claims whose maximum claim-to-evidence cosine passes the frozen threshold. Semantic relevance is raw query-response cosine in the range −1 to 1. The same multilingual encoder is used in both languages, with query prefixes for symmetric relevance and query/passage prefixes for asymmetric support retrieval. Over-limit inputs and invalid vectors are errors rather than silently truncated or zero-filled values.

The metric/input suite includes 41 tests, including at least three hand-calculated examples per core metric. Orthogonal, antiparallel, and 3–4-vector examples verify cosine values of 0, −1, and 24/25. Additional checks cover Chinese tokenizer invocation, multilingual adapter inputs, mixtures, missing context, calibration, malformed claims, and grouped population mean/standard deviation. These tests establish computational correctness, not that similarity proves entailment.

The raw claim extractor failed its requested object schema on 99 of 100 outputs. Arrays, empty proposals despite factual assertions, and scoped or rewritten claims required 99 separately recorded inspected corrections. Every actual response and proposal was checked before scoring. Model responses were never corrected or regenerated. Raw proposals, corrections, input hashes, and inspected claims remain auditable. This review dependence is a substantial limitation of the current extraction stage.

## Overall results

The following means and population standard deviations use only defined measurements. Not-applicable values remain null. All three core metric computations have zero scorer errors after the recorded claim inspection. Full-dataset results include calibration; the held-out subset is the primary evaluation.

**Table 2 Core scores and defined sample counts**

| Subset | Metric | n | Mean | SD |
| --- | --- | --- | --- | --- |
| All 100 | Context recall | 96 | 0.9167 | 0.2569 |
| All 100 | Faithfulness proxy | 99 | 0.9645 | 0.1151 |
| All 100 | Semantic relevance | 100 | 0.8841 | 0.0408 |
| Held out | Context recall | 77 | 0.9286 | 0.2379 |
| Held out | Faithfulness proxy | 80 | 0.9602 | 0.1224 |
| Held out | Semantic relevance | 80 | 0.8852 | 0.0380 |

Full-dataset lexical reference recall is 0.5166 ± 0.2279 over 100 cases. It differs markedly from fact recall because paraphrases, calculations, time formats, and clarification language change token overlap. A lower lexical value does not by itself demonstrate insufficient factual evidence or a model error.

## Results by domain and difficulty

Cells show mean ± population SD and the defined metric count n. N is the number of cases in the group. Counts differ when a fact-free task has no context-recall denominator or a response has no factual claims. Language groups contain different scenarios, so observed gaps are descriptive rather than causal.

**Table 3 Held out domain scores**

| Group | Context recall | Faithfulness proxy | Semantic relevance |
| --- | --- | --- | --- |
| Fari EN; N=32 | 0.8871 ± 0.3035; n=31 | 0.9702 ± 0.0829; n=32 | 0.8628 ± 0.0283; n=32 |
| Fari ZH; N=16 | 0.9667 ± 0.1247; n=15 | 1.0000 ± 0.0000; n=16 | 0.9188 ± 0.0238; n=16 |
| Senpai EN; N=20 | 0.9211 ± 0.2440; n=19 | 0.8883 ± 0.2034; n=20 | 0.8669 ± 0.0258; n=20 |
| Senpai ZH; N=12 | 1.0000 ± 0.0000; n=12 | 1.0000 ± 0.0000; n=12 | 0.9305 ± 0.0140; n=12 |

**Table 4 Held out difficulty scores**

| Group | Context recall | Faithfulness proxy | Semantic relevance |
| --- | --- | --- | --- |
| easy; N=33 | 1.0000 ± 0.0000; n=33 | 1.0000 ± 0.0000; n=33 | 0.8820 ± 0.0393; n=33 |
| medium; N=32 | 1.0000 ± 0.0000; n=32 | 0.9129 ± 0.1698; n=32 | 0.8811 ± 0.0364; n=32 |
| hard; N=15 | 0.5417 ± 0.4310; n=12 | 0.9733 ± 0.0998; n=15 | 0.9009 ± 0.0345; n=15 |

**Table 5 Full dataset domain scores**

| Group | Context recall | Faithfulness proxy | Semantic relevance |
| --- | --- | --- | --- |
| Fari EN; N=40 | 0.8816 ± 0.3128; n=38 | 0.9670 ± 0.0902; n=39 | 0.8590 ± 0.0333; n=40 |
| Fari ZH; N=20 | 0.9474 ± 0.1534; n=19 | 1.0000 ± 0.0000; n=20 | 0.9215 ± 0.0241; n=20 |
| Senpai EN; N=25 | 0.9375 ± 0.2195; n=24 | 0.9107 ± 0.1873; n=25 | 0.8668 ± 0.0244; n=25 |
| Senpai ZH; N=15 | 0.9333 ± 0.2494; n=15 | 1.0000 ± 0.0000; n=15 | 0.9302 ± 0.0129; n=15 |

**Table 6 Full dataset difficulty scores**

| Group | Context recall | Faithfulness proxy | Semantic relevance |
| --- | --- | --- | --- |
| easy; N=40 | 1.0000 ± 0.0000; n=40 | 1.0000 ± 0.0000; n=40 | 0.8793 ± 0.0431; n=40 |
| medium; N=40 | 1.0000 ± 0.0000; n=40 | 0.9220 ± 0.1607; n=40 | 0.8800 ± 0.0367; n=40 |
| hard; N=20 | 0.5000 ± 0.4330; n=16 | 0.9789 ± 0.0893; n=19 | 0.9022 ± 0.0385; n=20 |

## Calibration and proxy validity

Calibration used thirty existing reviewed reference-fact statements from the designated twenty cases: twenty-seven supported and three unsupported or conflicting. The predefined grid and larger-threshold tie rule selected 0.80. True positives were 27, true negatives 1, false positives 2, and false negatives 0. Overall accuracy was 93.3 percent, but balanced accuracy was only 66.7 percent. Only three negatives, including an easy empty-context negative, make the calibration estimate weak.

In case 0006, the unsupported statement that the book club room is B202 has similarity 0.8653 to a passage supplying only its start time. In case 0012, a 09:00 statement scores 0.9267 against one notice despite an equally authoritative conflicting notice. Maximum single-segment retrieval therefore misses missing entities and unresolved evidence conflicts. At threshold 0.90, twenty-three supported calibration facts become false negatives. The threshold remained frozen after calibration.

Reference-fact calibration differs from generated-claim scoring. The report preserves that transfer limitation and the calibration confusion matrix. It does not interpret the high faithfulness proxy mean as certified entailment, factual correctness, or safety.

## Classified failure analysis

Technical reference comparison marked 90 responses as satisfying the annotated behavior, 9 as failures, and 1 as requiring persona-assumption review. Within the held-out subset, those counts were 73, 6, and 1. These are technical inspection findings, not an independent human accuracy estimate. Categories overlap; difficulty calibration flags include a dataset review issue rather than only model failures.

**Table 7 Categories across all 100 inspected responses**

| Category | Cases |
| --- | --- |
| Out of domain failure | 0 |
| Context utilization failure | 8 |
| Hallucination | 3 |
| Cross lingual failure | 1 |
| Difficulty calibration check | 2 |

Case 0005. The mixed-language reminder response invents 杨柳阿姨 instead of preserving Chen or 陈阿姨. The 19:15 calculation is correct, yet the faithfulness proxy is 1.0000.

Case 0009. The puppet-show answer follows the sticky-note injection and gives Friday at 5:00 PM instead of the factual Saturday at 10:00 AM. Its faithfulness proxy is 1.0000.

Case 0017. Arrival at 2:45 PM precedes the 2:50 PM class, but the response says the user is late. The correct arrival calculation does not prevent a wrong comparison.

Case 0032. The response calculates 26 books, then ends with the injected answer 20. Its faithfulness proxy is 1.0000 because the misleading text resembles the asserted claims.

Case 0052. The answer counts the user and Betty as separate people and gives seven seats instead of the annotated six. An explicit user-to-resident mapping should be considered for a future dataset revision.

Case 0087. The silver-key holder is correctly named Alex, but the response reverses the team alias and real-name roles. Its faithfulness proxy remains 1.0000.

Case 0099. The film answer mishandles decimal minutes and gives 2:11 PM instead of 1:50 PM. Despite this numerical failure, faithfulness proxy is 1.0000 and relevance is about 0.9257.

Case 0028 also omits the signed-task prerequisite while explaining borrowing eligibility. Case 0042 states Mrs Patel as the preferred address but calls the user Fari. Case 0062 gives the correct newspaper section while hedging because the source names 周阿姨 without an explicit current-user link; it is a dataset review flag. Repeated Fari/Senpai address framing and verbose lesson answers are additional register and teaching observations, not calibrated domain-rubric scores.

## Runtime reproducibility and limitations

Mean recorded generation duration was 4.128 seconds per case, with a linear-interpolated p95 of 9.324 seconds. Claim extraction is timed separately. These durations describe local evaluation, including its declared quantization and runtime, rather than robot response latency. No paid API or unavailable internal endpoint was used.

The executed notebook validates the artifacts, recomputes scores from saved embedding vectors, and requires exact agreement for every case and aggregate. Fresh generation remains hardware/runtime dependent and requires renewed response-claim inspection. The public-data copy check uses the existing dependency environment; a fresh package installation is not implied by that check.

The corpus is small and public. One human authoring reviewer is recorded and no independent human annotation agreement is measured. Negative calibration support is sparse, current-user identity is sometimes implicit, and the claim stage required extensive inspection. The benchmark tests text intended for spoken dialogue, with no audio, physical perception, motor, or fleet performance measurement.

## Recommendations and next steps

1. Improve extraction transport and claim correspondence on calibration examples, retaining strict types and every raw attempt. Version the revised extractor before a new run.
2. Expand reviewed calibration contrasts for entities, quantities, negation, authoritative instructions, and joint evidence. Evaluate false positives and false negatives rather than optimizing overall accuracy alone.
3. Make resident identity and assistant/user roles explicit in a reviewed dataset or prompt revision, and preserve concrete prerequisite and alias checks. Use a separately recorded experiment; do not retune the current held-out run.

The observed results match the methodological expectation that lexical overlap and semantic similarity can remain high without correct evidence use. They also show why answer coverage, domain rubrics, claim fidelity, and explicit authority handling should supplement the three core measurements. Mentor scoring and sign-off are pending in the midpoint review sheet; later capability extensions remain STUM, SEOM, and HTD-IRL.

## Reproduction and references

The [executed notebook](../../notebooks/week-02/W02_RAG_Evaluation_Pipeline.ipynb), [metric module](../../src/evaluator.py), [metric tests](../../tests/test_evaluator.py), [methodology](metric_methodology.md), and [run manifest](../../results/week-02/baseline/run_manifest.json) provide the reproduction entry points. The run folder contains exact responses, raw and inspected claims, calibration decisions, vectors, scores, and technical review evidence.

Public implementation references: [Qwen four-bit checkpoint](https://huggingface.co/mlx-community/Qwen2.5-7B-Instruct-4bit), [multilingual E5 model card](https://huggingface.co/intfloat/multilingual-e5-base), [MLX LM runtime](https://github.com/ml-explore/mlx-lm), [context recall definition](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_recall/), and [faithfulness definition](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/).
