# Dataset integrity and validation update

The metadata integrity issue is resolved. The dataset, pilot, and schema were
structurally valid, but their manifests still recorded hashes from before the
reviewer identity metadata was updated. The review snapshots and construction
input hashes also needed to match the current files.

The reviewed queries, contexts, ideal responses, input metadata, IDs, domains,
languages, and difficulty labels were compared with the earlier accepted
release and are unchanged. The pilot was confirmed to match its configured
master records byte for byte before refreshing it. No direct pilot edit was
discarded and no dialogue was reconstructed from an older builder.

The repair refreshed the review snapshots, dataset and schema hashes, source
collection hashes, and both manifests. The validator now checks construction
inputs and claimed review snapshots as well as the data and schema. Regression
tests reject stale schema, construction, and review hashes.

| Artifact | SHA 256 |
| --- | --- |
| Dataset v1 | 3d974dbcac596c4698b3a070c5865e96f045c1ab75ff30c521b622c5738a7e54 |
| Pilot v0.4 | 4bd7236d724283aea2ab3b7f5aaf9a4e9bcbf05d7fe28818964f42969b1226b1 |
| Schema 1.1.0 | 7dbf46ed47f20e81b6a927e18605ad31ad04d38c765829c787636661948cadb9 |

The release validates all 100 records and the pilot validates all twelve. Both
have zero errors and zero warnings. All 35 Chinese cases retain their approved
native authorship and language review records. The current 20/80 family-safe
partition and all reviewed factual annotations are preserved.

The [current verification summary](../../deliverables/week-02/validation/tests.json)
records 102 passing checks, including 41 metric/input tests, exact score replay,
notebook execution, and Word layout review. Machine-readable results are available
for the [release](../../deliverables/week-02/validation/dataset.json) and
[pilot](../../deliverables/week-02/validation/pilot.json).

Run the checks from the repository root:

```sh
.venv/bin/python scripts/datasets/validate_dataset.py data/W01_Evaluation_Dataset_v1.jsonl --profile release --manifest data/W01_Evaluation_Dataset_v1.manifest.json
.venv/bin/python scripts/datasets/validate_dataset.py data/W01_Evaluation_Dataset_Pilot_v0.4.jsonl --profile pilot --manifest data/W01_Evaluation_Dataset_Pilot_v0.4.manifest.json
.venv/bin/python -m pytest -q
```

Future substantive content changes require renewed review. Refreshing manifests
alone cannot grant approval, verify factual truth, or establish native authorship.
