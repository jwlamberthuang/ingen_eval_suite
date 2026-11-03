# Reproduce the evaluation suite

Use Python 3.12 and run commands from the repository root. The complete pinned
environment includes validation, notebooks, document tooling, embedding scoring,
and platform-marked generation packages:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
```

For a smaller offline replay/test environment, install validation plus evaluation
requirements. Document builders additionally use `requirements-documents.txt`.
Fresh MLX generation uses `requirements-generation.txt` on macOS/arm64; saved
responses and vectors can be scored without MLX inference. A pinned dependency
list does not itself establish cross-platform installation. The
[release-candidate audit](../validation/release_candidate.json) records a fresh
full dependency installation and candidate verification on macOS arm64 with
Python 3.12.14. Other platforms are outside that check's scope. A new clone of
the published tag remains a separate post-publication check.

## Validate and rebuild data

Run the four commands in the [dataset guide](../data/README.md). All dataset,
schema and construction-input hashes are checked. The relocation does not change
dataset construction sources or approved example bytes, so the dataset manifests
remain valid without a cosmetic refresh.

```sh
.venv/bin/python scripts/datasets/build_dataset.py --output-dir build/dialogue
.venv/bin/python scripts/datasets/v2/manage_dataset.py build --output-dir build/expanded
```

Build targets must be fresh; preview builds refuse overwrites. Current dataset
maintenance tests exercise stale-hash rejection, pilot synchronization, content
review invalidation and exact rebuilds. Follow the
[maintenance workflow](datasets/expanded_workflow.md) for reviewed edits.

## Replay recorded experiments

```sh
.venv/bin/python scripts/evaluation/replay.py all
.venv/bin/python scripts/evaluation/replay.py tests
.venv/bin/python scripts/reporting/build_report_evidence.py --check
```

Replay verifies all migration inputs before reconstructing the exact original
public tree. It recomputes 100 RAG scores, 200 extended scores, the approved
annotation diagnostic, and ten fixed-probe scores using saved vectors. The
`tests` target additionally runs the original 336 checks against its original
source; the ordinary root tests exercise the current implementation and layout.
See the [migration contract](../reproducibility/README.md).

The report builder synthesizes recorded scores into subgroup tables and counts.
Its `--check` flag detects stale evidence without overwriting it. To deliberately
refresh the derived evidence after an accepted change:

```sh
.venv/bin/python scripts/reporting/build_report_evidence.py
```

## Execute notebooks

```sh
.venv/bin/python scripts/evaluation/execute_week2_notebook.py
.venv/bin/python scripts/evaluation/build_week3_notebook.py --execute
```

Both commands bind the notebook kernel to the invoking Python interpreter and
capture figures inline, without changing global Jupyter settings. All cells
replay saved artifacts; they do not download weights, fit thresholds,
or initiate generation. Notebook execution requires a Jupyter kernel and local
loopback sockets. Execute tests and notebooks sequentially to avoid advisory-lock
contention. The [notebook guide](../notebooks/README.md) explains their contents.

## Start a prospective experiment

Copy [example_experiment.json](../configs/example_experiment.json), use a distinct
run name/output directory, then use the staged runner with `--config`:

```sh
.venv/bin/python scripts/evaluation/week3.py preflight --config configs/example_experiment.json
```

Preflight checks reviewed data and input boundaries without model calls. Follow
[freeze, calibrate, generation, extraction, review and scoring](methodology/experiment_pipeline.md)
in order. Fresh inference requires the pinned model caches and the supported MLX
runtime. Preserve all raw attempts, including errors; inspect claim correspondence
before assisted scoring. Do not generate into recorded baseline folders.

Exact saved-score replay verifies a recorded computation. It does not imply
identical fresh generations across hardware, independent response accuracy, or
validity of a similarity proxy as logical entailment.
