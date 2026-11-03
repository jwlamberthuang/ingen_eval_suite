# Demonstration notebooks

- [RAG evaluation](rag_evaluation.ipynb): manually verified metric demonstrations,
  release validation, exact saved-score replay, distributions and failure analysis.
- [Extended evaluation](extended_evaluation.ipynb): spatial/temporal, entity, and
  goal-alignment demonstrations, output coverage, amended recall, and fixed probes.

Open either notebook from the repository environment. Saved outputs are included;
all code cells can run without downloading weights or generating new answers.

```sh
.venv/bin/python scripts/evaluation/execute_week2_notebook.py
.venv/bin/python scripts/evaluation/build_week3_notebook.py --execute
```

The script names retain their original development-phase identity. Recorded
experiments replay with exact historical source bytes through the
[verified migration](../reproducibility/README.md); analysis cells use canonical
project locations. Running the extended builder rebuilds its notebook before
execution. Run notebook execution and tests sequentially.
