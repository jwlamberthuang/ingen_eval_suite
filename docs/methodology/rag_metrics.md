# Week 2 metric implementation

The implementation in [evaluator.py](../../src/evaluator.py) returns per-example
values and population mean/standard deviation by domain, tier, language, subset,
and edge tag. Errors, inapplicable measurements, and empty responses retain
separate statuses. All undefined measurements serialize as null rather than zero.

## Context recall and lexical recall

Core context recall is supported required facts divided by all required facts.
Support comes from the reviewed fact-to-context annotations in the frozen dataset.
It measures evidence sufficiency and is independent of model output. A known
target withheld from context remains in the denominator; a true fact-free task
is not applicable. The implementation rejects positive support with empty context.
The claim-support interpretation follows the
[Ragas context recall definition](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_recall/).

Reference facts refine the ideal answer into independently checkable targets.
They also preserve a missing factual target when the correct ideal response is a
clarification. This avoids awarding perfect recall simply because a clarification
repeats words from an incomplete context.

The separate lexical_reference_recall diagnostic divides unique reference-answer
tokens found in context by all unique reference-answer tokens. English uses a
lowercase word/number regular expression. Chinese uses jieba segmentation after
Unicode NFC normalization, including mixed Chinese text. Punctuation-only tokens
are excluded. This is lexical overlap, not factual support: synonymy, time formats,
deductions, and boilerplate uncertainty can change it without changing truth.

## Faithfulness through a retrieval proxy

Atomic factual claims are proposed by a separately prompted generation stage,
then inspected against the actual responses. Quantities, negation, and asserted
actions must survive extraction. Raw proposals, inspected corrections, and full
response inputs are retained separately. A strict parser requires a JSON object
with exactly one `claims` key whose value is an array of strings, optionally
normalizing one enclosing Markdown JSON fence. Bare arrays, additional keys,
and malformed claim types are rejected. Extraction failures remain scorer
errors, without an invented fallback value.

For each claim, the proxy takes the maximum cosine against punctuation-based
evidence segments using query/passage prefixes. A claim passes if its cosine is
at least the frozen calibration threshold. Faithfulness_proxy is the passing
fraction. No evidence means zero for a response with claims; a claim-free
clarification is not applicable. This approximates the
[supported-claim faithfulness definition](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/).

The threshold grid is 0.50, 0.60, 0.70, 0.80, and 0.90. Selection maximizes balanced
accuracy and breaks ties toward the larger threshold. Both support classes are
required. Calibration uses only reviewed reference-fact support statements from
the designated twenty calibration cases. A frozen calibration artifact records
all candidates and the confusion matrix. No held-out input chooses the threshold.
Reference statements differ from generated claims, so calibration transfer remains
a limitation.

Semantic similarity does not certify entailment. Changed numbers, polarity,
topical but invented assertions, and deductions requiring several segments are
explicit failure probes. Manually inspected response quality is reported
separately from proxy scores.

## Semantic relevance and embeddings

Semantic relevance is raw cosine between query and response embeddings, ranging
from −1 to 1. Both inputs use the query prefix for symmetric similarity. Claim
retrieval uses query and passage prefixes. The pinned model is
[multilingual E5 base](https://huggingface.co/intfloat/multilingual-e5-base), using
attention-mask mean pooling and L2 normalization through Sentence Transformers.
The adapter rejects inputs exceeding 512 tokens and never silently truncates.

An empty response is an adequacy failure with no relevance score. Zero-norm,
non-finite, or malformed vectors are scorer errors. Topical similarity remains
different from answering the question correctly. The same multilingual encoder
is used for English, Chinese, and cross-language query/response pairs.

## Execution and reproducibility

The selected local generation checkpoint is the
[four-bit MLX conversion of Qwen2.5 7B Instruct](https://huggingface.co/mlx-community/Qwen2.5-7B-Instruct-4bit).
This is a separately identified quantized runtime for the public baseline; it does
not establish performance of an unavailable InGen endpoint. Generation uses
greedy sampling, seed 17, at most 512 new tokens, full permitted context, and the
checkpoint's chat template. The Apple Silicon runtime is
[MLX LM](https://github.com/ml-explore/mlx-lm). Embedding inference uses CPU.

The run manifest records immutable model revisions, settings, input hashes,
source hashes, timestamps, token counts, finish reasons, and errors. Model input
contains only the declared task, query, evidence, and applicable history or learner
information. Hidden references and labels are excluded. Each stage makes one
local attempt per case; substantive answers are never retried to improve scores.

Saved response, claim, calibration, and embedding artifacts permit scoring replay
without inference or a model download. Replay uses the same metric functions and
requires exact agreement with the stored per-case and aggregate JSON. Fresh model
execution remains a separately recorded run; bitwise generation equality across
different hardware or runtime versions is not assumed.

## Verification

The metric suite contains independently hand-computed expectations for at least
three examples per core metric. Tests also cover Chinese tokenizer invocation,
the multilingual embedding adapter, language mixtures, input limits, empty
evidence, malformed outputs, hidden-reference exclusion, calibration, and grouped
mean/standard deviation. Geometry fixtures establish arithmetic correctness;
they do not establish the real embedding model's entailment validity.

The primary evaluation subset is the eighty held-out cases. Full-dataset and
calibration summaries are also reported with their sample counts. Population
standard deviation uses ddof=0. Related scenario families stay together, and
edge-tag groups may overlap. No uncalibrated composite quality score is produced.
