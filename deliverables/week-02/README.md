# Week 2 review package

Week 2 implements and tests the three core RAG measurements, evaluates the fixed
context bilingual dataset, and analyzes failure modes. The technical package is
complete. The midpoint review still requires the mentor's scores and sign-off.

| Deliverable | Artifact |
| --- | --- |
| Evaluation module | [Core metrics](../../src/evaluator.py) and [methodology](../../docs/week-02/metric_methodology.md) |
| Executed notebook | [Pipeline walkthrough and analysis](../../notebooks/week-02/W02_RAG_Evaluation_Pipeline.ipynb) |
| Metric test suite | [41 metric/input tests](../../tests/test_evaluator.py) |
| Results report | [Word](../../docs/week-02/W02_RAG_Evaluation_Results.docx) and [Markdown](../../docs/week-02/W02_RAG_Evaluation_Results.md) |
| Weekly reflection | [399-word methodological log](../../weekly/Wk-02-Log.md) |
| Midpoint review | [Mentor scores and sign-off pending](../../docs/week-02/midpoint_review.md) |
| Validation repair | [Explanation and hashes](../../docs/week-02/validation_update.md), [release result](validation/dataset.json), and [pilot result](validation/pilot.json) |
| Experiment evidence | [Run manifest](../../results/week-02/baseline/run_manifest.json), [scores](../../results/week-02/baseline/scores.json), and [response review](../../results/week-02/baseline/response_review.jsonl) |

## Suggested review order

1. Check the validation repair and the zero-error release/pilot results above.
2. Read the results report, particularly claim-extraction reliability and proxy calibration.
3. Open the executed notebook for score replay, domain/tier distributions, and failure examples.
4. Inspect the metric implementation and its hand-calculated tests.
5. Complete the midpoint sheet, including mentor scores, sign-off, and later scope.

The report, notebook, implementation, and frozen experiment evidence describe the
same run. Technical readiness for review does not imply mentor approval or a
fully automated claim stage.

## Main findings

All 100 response attempts completed without generation errors. Held-out means
are 0.9286 for context recall, 0.9602 for the faithfulness proxy, and 0.8852 for
semantic relevance. The proxy assigns perfect scores to several incorrect
answers. Calibration balanced accuracy is only 66.7 percent with three negative
support statements. The raw claim stage required 99 inspected corrections; raw
attempts and amendments are retained. Read these limitations alongside the means.

## Implementation and validation

All 102 checks pass, including 41 metric/input tests. Both datasets have zero
validation errors and warnings. The public-only copy executes every notebook
cell and exactly replays all scores without a model download. See the
[verification summary](validation/tests.json).

- [Evaluation module](../../src/evaluator.py)
- [Metric test suite](../../tests/test_evaluator.py)
- [Manifest regression tests](../../tests/test_manifest_integrity.py)
- [Generation input boundaries](../../src/model_inputs.py)
- [Generation runtime](../../src/generation.py)
- [Calibration and replay](../../src/experiment.py)

The reviewed dataset remains under [Week 1](../week-01/README.md). Shared modules
and tests retain their canonical locations so subsequent weeks can reuse them.
