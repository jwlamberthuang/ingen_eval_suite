# Configurations

- [dataset_config.json](../dataset_config.json): released 100-case collection,
  pilot membership, family split, and review attestations.
- [dataset-v2.json](dataset-v2.json): expanded schema, quotas, action catalog,
  and pre-generation split policy. Drafting notes retain their original context;
  the released per-case approvals and manifests record completed review.
- [rag_baseline.json](rag_baseline.json) and
  [extended_baseline.json](extended_baseline.json): convenience configurations
  pointing to the canonical recorded result folders. Use verified replay.
- [example_experiment.json](example_experiment.json): prospective configuration
  template with a distinct run/output identity under `results/experiments/`.

For fresh generation, copy the example to a separately named configuration,
retain pinned revisions, and follow the
[experiment protocol](../docs/methodology/evaluation_protocol.md). Existing
inspected cases support regression analysis; a fresh held-out performance claim
requires untouched scenario families. Historical sealed configurations remain
available through the [layout migration](../reproducibility/README.md).
