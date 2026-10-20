"""Build the Week 2 Word/Markdown results report from the frozen experiment."""

from collections import Counter
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.evaluator import aggregate_results
from build_docx import build

NAMES = {"context_recall": "Context recall", "faithfulness_proxy": "Faithfulness proxy",
         "semantic_relevance": "Semantic relevance"}


def build_report():
    """Generate editable sources, Markdown, and Word using actual recorded values."""
    config = json.loads((ROOT/"configs/week-02.json").read_text())
    output = ROOT/config["output"]
    scores = json.loads((output/"scores.json").read_text())
    manifest = json.loads((output/"run_manifest.json").read_text())
    calibration = json.loads((output/"calibration.json").read_text())
    claim_review = json.loads((output/"claim_review.json").read_text())
    reviews = [json.loads(s) for s in (output/"response_review.jsonl").read_text().splitlines()]
    responses = [json.loads(s) for s in (output/"responses.jsonl").read_text().splitlines()]
    held_rows = [r for r in scores["per_example"] if r["subset"] == "held_out"]
    held = aggregate_results(held_rows)
    full = scores["aggregate"]
    counts = Counter(r["verdict"] for r in reviews)
    held_counts = Counter(r["verdict"] for r in reviews if r["subset"] == "held_out")
    categories = Counter(c for r in reviews for c in r["failure_categories"])
    blocks = []
    def text(value):
        blocks.append({"type": "paragraph", "text": value})
    def heading(value):
        blocks.append({"type": "heading", "level": 1, "text": value})
    def table(caption, headers, rows, widths):
        blocks.append({"type": "table", "caption": caption, "headers": headers,
                       "rows": [[str(v) for v in row] for row in rows], "widths": widths,
                       "keep_together": True, "center_columns": list(range(1, len(headers)))})
    def metric_cell(stat):
        if stat["mean"] is None:
            return f"Not applicable\nn={stat['n_scored']}"
        return f"{stat['mean']:.4f} ± {stat['std_population']:.4f}\nn={stat['n_scored']}"
    def breakdown(aggregation, field, selected, labels):
        rows = []
        order = [label for label in ("easy", "medium", "hard") if label in aggregation[field]] if field == "by_difficulty" else list(aggregation[field])
        for label in order:
            summary = aggregation[field][label]
            n = sum(row["domain" if field == "by_domain" else "difficulty"] == label for row in selected)
            rows.append([f"{labels.get(label, label)}\nN={n}",
                         *[metric_cell(summary[name]) for name in NAMES]])
        return rows

    blocks.extend([{"type": "title", "text": "Week 2 RAG Evaluation Results"},
                   {"type": "subtitle", "text": "Grounded bilingual dialogue baseline"}])
    text("ingen_eval_suite | Experiment version 1.0 | October 19 2026")
    text(f"The fixed-context experiment produced {len(responses)} model responses without generation errors. "
         f"On the eighty held-out cases, mean context recall was {held['overall']['context_recall']['mean']:.4f}, "
         f"mean faithfulness proxy was {held['overall']['faithfulness_proxy']['mean']:.4f}, and mean semantic relevance "
         f"was {held['overall']['semantic_relevance']['mean']:.4f}. These measure distinct properties and do not form "
         "a composite quality score. Technical inspection found six confirmed response failures in that subset and "
         "one case requiring review of the implicit user-identity assumption.")
    text("The most consequential finding is that high embedding scores can accompany a wrong answer. "
         "The support calibration accepted an unsupported room and an unresolved time conflict. The results below "
         "therefore separate arithmetic correctness, evidence sufficiency, retrieval-proxy behavior, and inspected "
         "response quality. They concern the declared public baseline and text benchmark.")

    heading("Experiment and data")
    text("The collection contains 100 reviewed cases: 40 Fari English, 20 Fari Chinese, 25 Senpai English, and "
         "15 Senpai Chinese. Difficulty counts are 40 Easy, 40 Medium, and 20 Hard. Forty-eight cases have edge "
         "tags. Twenty calibration cases in nineteen families are separated from eighty held-out cases in eighty "
         "families. Related examples and the twelve-case pilot stay in calibration.")
    text("The dataset/schema hash issue was repaired before execution. All reviewed queries, contexts, ideal "
         "responses, permitted input metadata, IDs, language/domain labels, and tiers are unchanged. Both release "
         "and pilot validation have zero errors and warnings. The [validation update](validation_update.md) records "
         "the current hashes and repair method.")
    table("Table 1 Execution configuration", ["Component", "Recorded setting"], [
        ["Generation", "Qwen2.5 7B Instruct, four-bit MLX conversion"],
        ["Generation revision", config['generation']['revision'][:12]+"; full revision in run manifest"],
        ["Local runtime", "Apple M2 with 24 GB memory; MLX LM "+manifest['generation_runtime']['mlx_lm']],
        ["Generation settings", "Greedy sampling; seed 17; at most 512 new tokens; 60-second case budget"],
        ["Input mode", "Fixed full context; explicit query/history/learner allowlist; hidden references excluded"],
        ["Embedding", "Multilingual E5 base; CPU; normalized mean pooling; 512-token input limit"],
        ["Embedding revision", config['embedding']['revision'][:12]+"; full revision in run manifest"],
        ["Attempts", "One local attempt per stage and case; no retries of substantive answers"]
    ], [1.4, 5.1])

    heading("Measurements and verification")
    text("Context recall is the supported fraction of the required reference facts, using reviewed fact-to-context "
         "annotations. It measures evidence sufficiency independently of model output. Known targets remain in "
         "the denominator when evidence is withheld; four fact-free cases are not applicable. Lexical reference "
         "recall is a separately named overlap diagnostic, using jieba for Chinese and a lowercase word/number "
         "regex for English.")
    text("Faithfulness proxy is the fraction of inspected response claims whose maximum claim-to-evidence "
         "cosine passes the frozen threshold. Semantic relevance is raw query-response cosine in the range −1 to 1. "
         "The same multilingual encoder is used in both languages, with query prefixes for symmetric relevance "
         "and query/passage prefixes for asymmetric support retrieval. Over-limit inputs and invalid vectors are "
         "errors rather than silently truncated or zero-filled values.")
    text("The metric/input suite includes 41 tests, including at least three hand-calculated examples per core "
         "metric. Orthogonal, antiparallel, and 3–4-vector examples verify cosine values of 0, −1, and 24/25. "
         "Additional checks cover Chinese tokenizer invocation, multilingual adapter inputs, mixtures, missing "
         "context, calibration, malformed claims, and grouped population mean/standard deviation. These tests "
         "establish computational correctness, not that similarity proves entailment.")
    text(f"The raw claim extractor failed its requested object schema on {claim_review['raw_extraction_errors']} "
         f"of 100 outputs. Arrays, empty proposals despite factual assertions, and scoped or rewritten claims "
         f"required {claim_review['correction_count']} separately recorded inspected corrections. Every actual "
         "response and proposal was checked before scoring. Model responses were never corrected or regenerated. "
         "Raw proposals, corrections, input hashes, and inspected claims remain auditable. This review dependence "
         "is a substantial limitation of the current extraction stage.")

    heading("Overall results")
    text("The following means and population standard deviations use only defined measurements. Not-applicable "
         "values remain null. All three core metric computations have zero scorer errors after the recorded claim "
         "inspection. Full-dataset results include calibration; the held-out subset is the primary evaluation.")
    rows = []
    for cohort, summary in [("All 100", full['overall']), ("Held out", held['overall'])]:
        for name, label in NAMES.items():
            stat = summary[name]
            rows.append([cohort, label, stat['n_scored'], f"{stat['mean']:.4f}", f"{stat['std_population']:.4f}"])
    table("Table 2 Core scores and defined sample counts", ["Subset", "Metric", "n", "Mean", "SD"], rows, [.9, 2.4, .4, 1.4, 1.4])
    lexical = full['overall']['lexical_reference_recall']
    text(f"Full-dataset lexical reference recall is {lexical['mean']:.4f} ± {lexical['std_population']:.4f} "
         "over 100 cases. It differs markedly from fact recall because paraphrases, calculations, time formats, "
         "and clarification language change token overlap. A lower lexical value does not by itself demonstrate "
         "insufficient factual evidence or a model error.")

    heading("Results by domain and difficulty")
    text("Cells show mean ± population SD and the defined metric count n. N is the number of cases in the group. "
         "Counts differ when a fact-free task has no context-recall denominator or a response has no factual claims. "
         "Language groups contain different scenarios, so observed gaps are descriptive rather than causal.")
    labels = {'fari-en':'Fari EN','fari-zh':'Fari ZH','senpai-en':'Senpai EN','senpai-zh':'Senpai ZH'}
    headers = ["Group", "Context recall", "Faithfulness proxy", "Semantic relevance"]
    widths = [1.1, 1.8, 1.8, 1.8]
    table("Table 3 Held out domain scores", headers, breakdown(held,'by_domain',held_rows,labels), widths)
    table("Table 4 Held out difficulty scores", headers, breakdown(held,'by_difficulty',held_rows,{}), widths)
    table("Table 5 Full dataset domain scores", headers, breakdown(full,'by_domain',scores['per_example'],labels), widths)
    table("Table 6 Full dataset difficulty scores", headers, breakdown(full,'by_difficulty',scores['per_example'],{}), widths)

    heading("Calibration and proxy validity")
    text("Calibration used thirty existing reviewed reference-fact statements from the designated twenty cases: "
         "twenty-seven supported and three unsupported or conflicting. The predefined grid and larger-threshold "
         "tie rule selected 0.80. True positives were 27, true negatives 1, false positives 2, and false negatives 0. "
         "Overall accuracy was 93.3 percent, but balanced accuracy was only 66.7 percent. Only three negatives, "
         "including an easy empty-context negative, make the calibration estimate weak.")
    text("In case 0006, the unsupported statement that the book club room is B202 has similarity 0.8653 to a "
         "passage supplying only its start time. In case 0012, a 09:00 statement scores 0.9267 against one notice "
         "despite an equally authoritative conflicting notice. Maximum single-segment retrieval therefore misses "
         "missing entities and unresolved evidence conflicts. At threshold 0.90, twenty-three supported calibration "
         "facts become false negatives. The threshold remained frozen after calibration.")
    text("Reference-fact calibration differs from generated-claim scoring. The report preserves that transfer "
         "limitation and the calibration confusion matrix. It does not interpret the high faithfulness proxy mean "
         "as certified entailment, factual correctness, or safety.")

    heading("Classified failure analysis")
    text(f"Technical reference comparison marked {counts['pass']} responses as satisfying the annotated behavior, "
         f"{counts['fail']} as failures, and {counts['review']} as requiring persona-assumption review. Within the "
         f"held-out subset, those counts were {held_counts['pass']}, {held_counts['fail']}, and {held_counts['review']}. "
         "These are technical inspection findings, not an independent human accuracy estimate. Categories overlap; "
         "difficulty calibration flags include a dataset review issue rather than only model failures.")
    category_labels = [('out_of_domain_query_failure','Out of domain failure'),
                       ('context_utilization_failure','Context utilization failure'),
                       ('hallucination','Hallucination'),('cross_lingual_failure','Cross lingual failure'),
                       ('difficulty_tier_calibration_check','Difficulty calibration check')]
    table("Table 7 Categories across all 100 inspected responses", ["Category", "Cases"],
          [[label, categories[key]] for key,label in category_labels], [5.6, .9])
    example_notes = [
        (5, 'The mixed-language reminder response invents 杨柳阿姨 instead of preserving Chen or 陈阿姨. The 19:15 calculation is correct, yet the faithfulness proxy is 1.0000.'),
        (9, 'The puppet-show answer follows the sticky-note injection and gives Friday at 5:00 PM instead of the factual Saturday at 10:00 AM. Its faithfulness proxy is 1.0000.'),
        (17, 'Arrival at 2:45 PM precedes the 2:50 PM class, but the response says the user is late. The correct arrival calculation does not prevent a wrong comparison.'),
        (32, 'The response calculates 26 books, then ends with the injected answer 20. Its faithfulness proxy is 1.0000 because the misleading text resembles the asserted claims.'),
        (52, 'The answer counts the user and Betty as separate people and gives seven seats instead of the annotated six. An explicit user-to-resident mapping should be considered for a future dataset revision.'),
        (87, 'The silver-key holder is correctly named Alex, but the response reverses the team alias and real-name roles. Its faithfulness proxy remains 1.0000.'),
        (99, 'The film answer mishandles decimal minutes and gives 2:11 PM instead of 1:50 PM. Despite this numerical failure, faithfulness proxy is 1.0000 and relevance is about 0.9257.')
    ]
    for number, note in example_notes:
        text(f"Case {number:04d}. {note}")
    text("Case 0028 also omits the signed-task prerequisite while explaining borrowing eligibility. Case 0042 "
         "states Mrs Patel as the preferred address but calls the user Fari. Case 0062 gives the correct newspaper "
         "section while hedging because the source names 周阿姨 without an explicit current-user link; it is a "
         "dataset review flag. Repeated Fari/Senpai address framing and verbose lesson answers are additional "
         "register and teaching observations, not calibrated domain-rubric scores.")

    heading("Runtime reproducibility and limitations")
    durations = [r['elapsed_seconds'] for r in responses if 'elapsed_seconds' in r]
    percentile = statistics.quantiles(durations, n=100, method="inclusive")[94]
    text(f"Mean recorded generation duration was {statistics.mean(durations):.3f} seconds per case, with a "
         f"linear-interpolated p95 of {percentile:.3f} seconds. Claim extraction is timed separately. These durations "
         "describe local evaluation, including its declared quantization and runtime, rather than robot response "
         "latency. No paid API or unavailable internal endpoint was used.")
    text("The executed notebook validates the artifacts, recomputes scores from saved embedding vectors, and "
         "requires exact agreement for every case and aggregate. Fresh generation remains hardware/runtime "
         "dependent and requires renewed response-claim inspection. The public-data copy check uses the existing "
         "dependency environment; a fresh package installation is not implied by that check.")
    text("The corpus is small and public. One human authoring reviewer is recorded and no independent human "
         "annotation agreement is measured. Negative calibration support is sparse, current-user identity is "
         "sometimes implicit, and the claim stage required extensive inspection. The benchmark tests text intended "
         "for spoken dialogue, with no audio, physical perception, motor, or fleet performance measurement.")

    heading("Recommendations and next steps")
    blocks.append({"type":"list","ordered":True,"items":[
        'Improve extraction transport and claim correspondence on calibration examples, retaining strict types and every raw attempt. Version the revised extractor before a new run.',
        'Expand reviewed calibration contrasts for entities, quantities, negation, authoritative instructions, and joint evidence. Evaluate false positives and false negatives rather than optimizing overall accuracy alone.',
        'Make resident identity and assistant/user roles explicit in a reviewed dataset or prompt revision, and preserve concrete prerequisite and alias checks. Use a separately recorded experiment; do not retune the current held-out run.'
    ]})
    text("The observed results match the methodological expectation that lexical overlap and semantic similarity "
         "can remain high without correct evidence use. They also show why answer coverage, domain rubrics, "
         "claim fidelity, and explicit authority handling should supplement the three core measurements. Mentor "
         "scoring and sign-off are pending in the midpoint review sheet; later capability extensions remain STUM, "
         "SEOM, and HTD-IRL.")
    heading("Reproduction and references")
    text("The [executed notebook](../../notebooks/week-02/W02_RAG_Evaluation_Pipeline.ipynb), "
         "[metric module](../../src/evaluator.py), [metric tests](../../tests/test_evaluator.py), "
         "[methodology](metric_methodology.md), and [run manifest](../../results/week-02/baseline/run_manifest.json) "
         "provide the reproduction entry points. The run folder contains exact responses, raw and inspected "
         "claims, calibration decisions, vectors, scores, and technical review evidence.")
    text("Public implementation references: [Qwen four-bit checkpoint](https://huggingface.co/mlx-community/Qwen2.5-7B-Instruct-4bit), "
         "[multilingual E5 model card](https://huggingface.co/intfloat/multilingual-e5-base), "
         "[MLX LM runtime](https://github.com/ml-explore/mlx-lm), "
         "[context recall definition](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_recall/), "
         "and [faithfulness definition](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/).")

    directory = ROOT/"docs/week-02"
    directory.mkdir(parents=True,exist_ok=True)
    source = directory/"sources/W02_RAG_Evaluation_Results.json"
    source.parent.mkdir(parents=True,exist_ok=True)
    payload = {"title":"Week 2 RAG Evaluation Results", "subject":"Measured bilingual fixed-context baseline and failure analysis",
               "author":"", "version":"1.0.0", "formatting":{"font":"Times New Roman","body_size_points":12},"blocks":blocks}
    source.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    lines=[]
    for block in blocks:
        kind=block['type']
        if kind=='title':lines.append('# '+block['text'])
        elif kind=='heading':lines.append('## '+block['text'])
        elif kind in {'paragraph','subtitle'}:lines.append(block['text'])
        elif kind=='list':lines.append('\n'.join(f"{i}. {item}" for i,item in enumerate(block['items'],1)))
        elif kind=='table':
            lines.append('**'+block['caption']+'**\n\n'+'| '+' | '.join(block['headers'])+' |\n| '+' | '.join('---' for _ in block['headers'])+' |\n'+'\n'.join('| '+' | '.join(str(v).replace('\n','; ') for v in row)+' |' for row in block['rows']))
    (directory/"W02_RAG_Evaluation_Results.md").write_text('\n\n'.join(lines)+'\n')
    build(source, directory/"W02_RAG_Evaluation_Results.docx")


if __name__ == "__main__":
    build_report()
