# Report evidence tables

Generated from retained scores by `scripts/reporting/build_report_evidence.py`.
Population SD uses ddof=0. Defined-count means exclude N/A and errors; their counts remain visible.
Cohorts are separate. The amended context recall is a reviewed post-inspection diagnostic.

The [JSON evidence](evidence/summary.json) includes every cohort, domain, difficulty, language, metric and original/amended view.

## New held-out: overall

| Group | Task | Metric | Mean | SD | Defined / eligible | N/A | Errors | Parsed |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all | htd_task_alignment | goal_coverage | 0.8611 | 0.2022 | 6/12 | 1 | 5 | 7 |
| all | htd_task_alignment | goal_precision | 0.6905 | 0.3384 | 7/12 | 0 | 5 | 7 |
| all | htd_task_alignment | task_success | 0.2500 | 0.4330 | 12/12 | 0 | 0 | 7 |
| all | rag | context_recall | 0.7442 | 0.4363 | 43/44 | 1 | 0 | — |
| all | rag | faithfulness_proxy | 0.9050 | 0.2085 | 43/44 | 1 | 0 | — |
| all | rag | lexical_reference_recall | 0.4386 | 0.2137 | 44/44 | 0 | 0 | — |
| all | rag | semantic_relevance | 0.8922 | 0.0369 | 44/44 | 0 | 0 | — |
| all | seom_entities | classification_accuracy | 0.7708 | 0.2787 | 12/12 | 0 | 0 | 12 |
| all | seom_entities | entity_precision | 1.0000 | 0.0000 | 12/12 | 0 | 0 | 12 |
| all | seom_entities | entity_recall | 0.8125 | 0.2724 | 12/12 | 0 | 0 | 12 |
| all | seom_entities | task_success | 0.5833 | 0.4930 | 12/12 | 0 | 0 | 12 |
| all | stum_spatial | spatial_accuracy | 0.8750 | 0.3307 | 8/8 | 0 | 0 | 8 |
| all | stum_spatial | task_success | 0.8750 | 0.3307 | 8/8 | 0 | 0 | 8 |
| all | stum_temporal | temporal_coherence | 1.0000 | 0.0000 | 4/4 | 0 | 0 | 4 |
| all | stum_temporal | temporal_consistency | 1.0000 | 0.0000 | 4/4 | 0 | 0 | 4 |
| all | stum_temporal | temporal_pair_accuracy | 1.0000 | 0.0000 | 4/4 | 0 | 0 | 4 |
| all | stum_temporal | task_success | 1.0000 | 0.0000 | 4/4 | 0 | 0 | 4 |

## New held-out: domain

| Group | Task | Metric | Mean | SD | Defined / eligible | N/A | Errors | Parsed |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fari-en | htd_task_alignment | goal_coverage | 0.8333 | 0.1667 | 2/5 | 0 | 3 | 2 |
| fari-en | htd_task_alignment | goal_precision | 0.8333 | 0.1667 | 2/5 | 0 | 3 | 2 |
| fari-en | htd_task_alignment | task_success | 0.2000 | 0.4000 | 5/5 | 0 | 0 | 2 |
| fari-en | rag | context_recall | 0.7059 | 0.4556 | 17/18 | 1 | 0 | — |
| fari-en | rag | faithfulness_proxy | 0.8056 | 0.2792 | 18/18 | 0 | 0 | — |
| fari-en | rag | lexical_reference_recall | 0.4681 | 0.2366 | 18/18 | 0 | 0 | — |
| fari-en | rag | semantic_relevance | 0.8690 | 0.0311 | 18/18 | 0 | 0 | — |
| fari-en | seom_entities | classification_accuracy | 0.7500 | 0.2500 | 4/4 | 0 | 0 | 4 |
| fari-en | seom_entities | entity_precision | 1.0000 | 0.0000 | 4/4 | 0 | 0 | 4 |
| fari-en | seom_entities | entity_recall | 0.7500 | 0.2500 | 4/4 | 0 | 0 | 4 |
| fari-en | seom_entities | task_success | 0.5000 | 0.5000 | 4/4 | 0 | 0 | 4 |
| fari-en | stum_spatial | spatial_accuracy | 1.0000 | 0.0000 | 4/4 | 0 | 0 | 4 |
| fari-en | stum_spatial | task_success | 1.0000 | 0.0000 | 4/4 | 0 | 0 | 4 |
| fari-zh | htd_task_alignment | goal_coverage | 1.0000 | 0.0000 | 1/3 | 1 | 1 | 2 |
| fari-zh | htd_task_alignment | goal_precision | 0.3333 | 0.3333 | 2/3 | 0 | 1 | 2 |
| fari-zh | htd_task_alignment | task_success | 0.0000 | 0.0000 | 3/3 | 0 | 0 | 2 |
| fari-zh | rag | context_recall | 0.7778 | 0.4157 | 9/9 | 0 | 0 | — |
| fari-zh | rag | faithfulness_proxy | 1.0000 | 0.0000 | 9/9 | 0 | 0 | — |
| fari-zh | rag | lexical_reference_recall | 0.4288 | 0.2251 | 9/9 | 0 | 0 | — |
| fari-zh | rag | semantic_relevance | 0.9260 | 0.0160 | 9/9 | 0 | 0 | — |
| fari-zh | seom_entities | classification_accuracy | 0.7500 | 0.3536 | 3/3 | 0 | 0 | 3 |
| fari-zh | seom_entities | entity_precision | 1.0000 | 0.0000 | 3/3 | 0 | 0 | 3 |
| fari-zh | seom_entities | entity_recall | 0.7500 | 0.3536 | 3/3 | 0 | 0 | 3 |
| fari-zh | seom_entities | task_success | 0.6667 | 0.4714 | 3/3 | 0 | 0 | 3 |
| fari-zh | stum_spatial | spatial_accuracy | 0.0000 | 0.0000 | 1/1 | 0 | 0 | 1 |
| fari-zh | stum_spatial | task_success | 0.0000 | 0.0000 | 1/1 | 0 | 0 | 1 |
| senpai-en | htd_task_alignment | goal_coverage | 0.8333 | 0.2357 | 3/3 | 0 | 0 | 3 |
| senpai-en | htd_task_alignment | goal_precision | 0.8333 | 0.2357 | 3/3 | 0 | 0 | 3 |
| senpai-en | htd_task_alignment | task_success | 0.6667 | 0.4714 | 3/3 | 0 | 0 | 3 |
| senpai-en | rag | context_recall | 0.7000 | 0.4583 | 10/10 | 0 | 0 | — |
| senpai-en | rag | faithfulness_proxy | 0.9352 | 0.1228 | 9/10 | 1 | 0 | — |
| senpai-en | rag | lexical_reference_recall | 0.3910 | 0.1737 | 10/10 | 0 | 0 | — |
| senpai-en | rag | semantic_relevance | 0.8808 | 0.0319 | 10/10 | 0 | 0 | — |
| senpai-en | seom_entities | classification_accuracy | 0.8750 | 0.2165 | 4/4 | 0 | 0 | 4 |
| senpai-en | seom_entities | entity_precision | 1.0000 | 0.0000 | 4/4 | 0 | 0 | 4 |
| senpai-en | seom_entities | entity_recall | 1.0000 | 0.0000 | 4/4 | 0 | 0 | 4 |
| senpai-en | seom_entities | task_success | 0.7500 | 0.4330 | 4/4 | 0 | 0 | 4 |
| senpai-en | stum_spatial | spatial_accuracy | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| senpai-en | stum_spatial | task_success | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| senpai-en | stum_temporal | temporal_coherence | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| senpai-en | stum_temporal | temporal_consistency | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| senpai-en | stum_temporal | temporal_pair_accuracy | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| senpai-en | stum_temporal | task_success | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| senpai-zh | htd_task_alignment | goal_coverage | N/A | N/A | 0/1 | 0 | 1 | 0 |
| senpai-zh | htd_task_alignment | goal_precision | N/A | N/A | 0/1 | 0 | 1 | 0 |
| senpai-zh | htd_task_alignment | task_success | 0.0000 | 0.0000 | 1/1 | 0 | 0 | 0 |
| senpai-zh | rag | context_recall | 0.8571 | 0.3499 | 7/7 | 0 | 0 | — |
| senpai-zh | rag | faithfulness_proxy | 1.0000 | 0.0000 | 7/7 | 0 | 0 | — |
| senpai-zh | rag | lexical_reference_recall | 0.4432 | 0.1711 | 7/7 | 0 | 0 | — |
| senpai-zh | rag | semantic_relevance | 0.9246 | 0.0142 | 7/7 | 0 | 0 | — |
| senpai-zh | seom_entities | classification_accuracy | 0.5000 | 0.0000 | 1/1 | 0 | 0 | 1 |
| senpai-zh | seom_entities | entity_precision | 1.0000 | 0.0000 | 1/1 | 0 | 0 | 1 |
| senpai-zh | seom_entities | entity_recall | 0.5000 | 0.0000 | 1/1 | 0 | 0 | 1 |
| senpai-zh | seom_entities | task_success | 0.0000 | 0.0000 | 1/1 | 0 | 0 | 1 |
| senpai-zh | stum_spatial | spatial_accuracy | 1.0000 | 0.0000 | 1/1 | 0 | 0 | 1 |
| senpai-zh | stum_spatial | task_success | 1.0000 | 0.0000 | 1/1 | 0 | 0 | 1 |
| senpai-zh | stum_temporal | temporal_coherence | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| senpai-zh | stum_temporal | temporal_consistency | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| senpai-zh | stum_temporal | temporal_pair_accuracy | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| senpai-zh | stum_temporal | task_success | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |

## New held-out: difficulty

| Group | Task | Metric | Mean | SD | Defined / eligible | N/A | Errors | Parsed |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| easy | htd_task_alignment | goal_coverage | 1.0000 | 0.0000 | 2/3 | 1 | 0 | 3 |
| easy | htd_task_alignment | goal_precision | 0.6667 | 0.4714 | 3/3 | 0 | 0 | 3 |
| easy | htd_task_alignment | task_success | 0.6667 | 0.4714 | 3/3 | 0 | 0 | 3 |
| easy | rag | context_recall | 1.0000 | 0.0000 | 1/1 | 0 | 0 | — |
| easy | rag | faithfulness_proxy | 1.0000 | 0.0000 | 1/1 | 0 | 0 | — |
| easy | rag | lexical_reference_recall | 0.8333 | 0.0000 | 1/1 | 0 | 0 | — |
| easy | rag | semantic_relevance | 0.9065 | 0.0000 | 1/1 | 0 | 0 | — |
| easy | seom_entities | classification_accuracy | 0.7000 | 0.2449 | 5/5 | 0 | 0 | 5 |
| easy | seom_entities | entity_precision | 1.0000 | 0.0000 | 5/5 | 0 | 0 | 5 |
| easy | seom_entities | entity_recall | 0.8000 | 0.2449 | 5/5 | 0 | 0 | 5 |
| easy | seom_entities | task_success | 0.4000 | 0.4899 | 5/5 | 0 | 0 | 5 |
| easy | stum_spatial | spatial_accuracy | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| easy | stum_spatial | task_success | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| easy | stum_temporal | temporal_coherence | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| easy | stum_temporal | temporal_consistency | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| easy | stum_temporal | temporal_pair_accuracy | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| easy | stum_temporal | task_success | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| hard | htd_task_alignment | goal_coverage | 1.0000 | 0.0000 | 1/2 | 0 | 1 | 1 |
| hard | htd_task_alignment | goal_precision | 1.0000 | 0.0000 | 1/2 | 0 | 1 | 1 |
| hard | htd_task_alignment | task_success | 0.5000 | 0.5000 | 2/2 | 0 | 0 | 1 |
| hard | rag | context_recall | 0.5600 | 0.4964 | 25/26 | 1 | 0 | — |
| hard | rag | faithfulness_proxy | 0.8933 | 0.2398 | 25/26 | 1 | 0 | — |
| hard | rag | lexical_reference_recall | 0.3769 | 0.2057 | 26/26 | 0 | 0 | — |
| hard | rag | semantic_relevance | 0.8939 | 0.0305 | 26/26 | 0 | 0 | — |
| hard | seom_entities | classification_accuracy | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| hard | seom_entities | entity_precision | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| hard | seom_entities | entity_recall | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| hard | seom_entities | task_success | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| hard | stum_spatial | spatial_accuracy | 0.5000 | 0.5000 | 2/2 | 0 | 0 | 2 |
| hard | stum_spatial | task_success | 0.5000 | 0.5000 | 2/2 | 0 | 0 | 2 |
| hard | stum_temporal | temporal_coherence | 1.0000 | 0.0000 | 1/1 | 0 | 0 | 1 |
| hard | stum_temporal | temporal_consistency | 1.0000 | 0.0000 | 1/1 | 0 | 0 | 1 |
| hard | stum_temporal | temporal_pair_accuracy | 1.0000 | 0.0000 | 1/1 | 0 | 0 | 1 |
| hard | stum_temporal | task_success | 1.0000 | 0.0000 | 1/1 | 0 | 0 | 1 |
| medium | htd_task_alignment | goal_coverage | 0.7222 | 0.2079 | 3/7 | 0 | 4 | 3 |
| medium | htd_task_alignment | goal_precision | 0.6111 | 0.0786 | 3/7 | 0 | 4 | 3 |
| medium | htd_task_alignment | task_success | 0.0000 | 0.0000 | 7/7 | 0 | 0 | 3 |
| medium | rag | context_recall | 1.0000 | 0.0000 | 17/17 | 0 | 0 | — |
| medium | rag | faithfulness_proxy | 0.9167 | 0.1566 | 17/17 | 0 | 0 | — |
| medium | rag | lexical_reference_recall | 0.5097 | 0.1830 | 17/17 | 0 | 0 | — |
| medium | rag | semantic_relevance | 0.8886 | 0.0455 | 17/17 | 0 | 0 | — |
| medium | seom_entities | classification_accuracy | 0.7500 | 0.3162 | 5/5 | 0 | 0 | 5 |
| medium | seom_entities | entity_precision | 1.0000 | 0.0000 | 5/5 | 0 | 0 | 5 |
| medium | seom_entities | entity_recall | 0.7500 | 0.3162 | 5/5 | 0 | 0 | 5 |
| medium | seom_entities | task_success | 0.6000 | 0.4899 | 5/5 | 0 | 0 | 5 |
| medium | stum_spatial | spatial_accuracy | 1.0000 | 0.0000 | 4/4 | 0 | 0 | 4 |
| medium | stum_spatial | task_success | 1.0000 | 0.0000 | 4/4 | 0 | 0 | 4 |
| medium | stum_temporal | temporal_coherence | 1.0000 | 0.0000 | 1/1 | 0 | 0 | 1 |
| medium | stum_temporal | temporal_consistency | 1.0000 | 0.0000 | 1/1 | 0 | 0 | 1 |
| medium | stum_temporal | temporal_pair_accuracy | 1.0000 | 0.0000 | 1/1 | 0 | 0 | 1 |
| medium | stum_temporal | task_success | 1.0000 | 0.0000 | 1/1 | 0 | 0 | 1 |

## New held-out: language

| Group | Task | Metric | Mean | SD | Defined / eligible | N/A | Errors | Parsed |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| en | htd_task_alignment | goal_coverage | 0.8333 | 0.2108 | 5/8 | 0 | 3 | 5 |
| en | htd_task_alignment | goal_precision | 0.8333 | 0.2108 | 5/8 | 0 | 3 | 5 |
| en | htd_task_alignment | task_success | 0.3750 | 0.4841 | 8/8 | 0 | 0 | 5 |
| en | rag | context_recall | 0.7037 | 0.4566 | 27/28 | 1 | 0 | — |
| en | rag | faithfulness_proxy | 0.8488 | 0.2464 | 27/28 | 1 | 0 | — |
| en | rag | lexical_reference_recall | 0.4405 | 0.2194 | 28/28 | 0 | 0 | — |
| en | rag | semantic_relevance | 0.8732 | 0.0319 | 28/28 | 0 | 0 | — |
| en | seom_entities | classification_accuracy | 0.8125 | 0.2421 | 8/8 | 0 | 0 | 8 |
| en | seom_entities | entity_precision | 1.0000 | 0.0000 | 8/8 | 0 | 0 | 8 |
| en | seom_entities | entity_recall | 0.8750 | 0.2165 | 8/8 | 0 | 0 | 8 |
| en | seom_entities | task_success | 0.6250 | 0.4841 | 8/8 | 0 | 0 | 8 |
| en | stum_spatial | spatial_accuracy | 1.0000 | 0.0000 | 6/6 | 0 | 0 | 6 |
| en | stum_spatial | task_success | 1.0000 | 0.0000 | 6/6 | 0 | 0 | 6 |
| en | stum_temporal | temporal_coherence | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| en | stum_temporal | temporal_consistency | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| en | stum_temporal | temporal_pair_accuracy | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| en | stum_temporal | task_success | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| zh | htd_task_alignment | goal_coverage | 1.0000 | 0.0000 | 1/4 | 1 | 2 | 2 |
| zh | htd_task_alignment | goal_precision | 0.3333 | 0.3333 | 2/4 | 0 | 2 | 2 |
| zh | htd_task_alignment | task_success | 0.0000 | 0.0000 | 4/4 | 0 | 0 | 2 |
| zh | rag | context_recall | 0.8125 | 0.3903 | 16/16 | 0 | 0 | — |
| zh | rag | faithfulness_proxy | 1.0000 | 0.0000 | 16/16 | 0 | 0 | — |
| zh | rag | lexical_reference_recall | 0.4351 | 0.2033 | 16/16 | 0 | 0 | — |
| zh | rag | semantic_relevance | 0.9254 | 0.0153 | 16/16 | 0 | 0 | — |
| zh | seom_entities | classification_accuracy | 0.6875 | 0.3248 | 4/4 | 0 | 0 | 4 |
| zh | seom_entities | entity_precision | 1.0000 | 0.0000 | 4/4 | 0 | 0 | 4 |
| zh | seom_entities | entity_recall | 0.6875 | 0.3248 | 4/4 | 0 | 0 | 4 |
| zh | seom_entities | task_success | 0.5000 | 0.5000 | 4/4 | 0 | 0 | 4 |
| zh | stum_spatial | spatial_accuracy | 0.5000 | 0.5000 | 2/2 | 0 | 0 | 2 |
| zh | stum_spatial | task_success | 0.5000 | 0.5000 | 2/2 | 0 | 0 | 2 |
| zh | stum_temporal | temporal_coherence | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| zh | stum_temporal | temporal_consistency | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| zh | stum_temporal | temporal_pair_accuracy | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |
| zh | stum_temporal | task_success | 1.0000 | 0.0000 | 2/2 | 0 | 0 | 2 |

## Technical inspection

RAG verdicts are exclusive; failure-category counts may overlap. Structured categories label each non-successful case once.
Inspection is not independent human response assessment. Frozen alias limits are not automatically model errors.

### legacy_calibration

RAG denominator: 20; structured denominator: 0.

| Category set | Category | Cases |
| --- | --- | ---: |
| rag_verdicts_exclusive | fails_reference | 1 |
| rag_verdicts_exclusive | meets_reference | 9 |
| rag_verdicts_exclusive | partial | 9 |
| rag_verdicts_exclusive | reference_ambiguity | 1 |
| rag_categories_overlapping | context_utilization | 2 |
| rag_categories_overlapping | input_reference_ambiguity | 1 |
| rag_categories_overlapping | prompt_injection | 1 |
| rag_categories_overlapping | register | 1 |
| rag_categories_overlapping | speaker_role_confusion | 6 |
| rag_categories_overlapping | unsupported_action_commitment | 1 |
| rag_categories_overlapping | unsupported_assertion | 3 |

### legacy_previously_evaluated

RAG denominator: 80; structured denominator: 0.

| Category set | Category | Cases |
| --- | --- | ---: |
| rag_verdicts_exclusive | fails_reference | 6 |
| rag_verdicts_exclusive | meets_reference | 55 |
| rag_verdicts_exclusive | partial | 18 |
| rag_verdicts_exclusive | reference_ambiguity | 1 |
| rag_categories_overlapping | context_utilization | 1 |
| rag_categories_overlapping | contradiction | 1 |
| rag_categories_overlapping | entity_binding | 2 |
| rag_categories_overlapping | hypothetical_as_fact | 1 |
| rag_categories_overlapping | input_reference_ambiguity | 1 |
| rag_categories_overlapping | negation_failure | 1 |
| rag_categories_overlapping | pedagogical_completeness | 1 |
| rag_categories_overlapping | prerequisite_failure | 1 |
| rag_categories_overlapping | prompt_injection | 1 |
| rag_categories_overlapping | reasoning_error | 3 |
| rag_categories_overlapping | reasoning_justification | 1 |
| rag_categories_overlapping | source_authority | 1 |
| rag_categories_overlapping | speaker_role_confusion | 9 |
| rag_categories_overlapping | uncertainty_failure | 2 |
| rag_categories_overlapping | unsupported_assertion | 7 |
| rag_categories_overlapping | unsupported_verification | 1 |

### new_calibration

RAG denominator: 11; structured denominator: 9.

| Category set | Category | Cases |
| --- | --- | ---: |
| rag_verdicts_exclusive | fails_reference | 1 |
| rag_verdicts_exclusive | meets_reference | 6 |
| rag_verdicts_exclusive | partial | 4 |
| rag_categories_overlapping | contradiction | 1 |
| rag_categories_overlapping | prompt_injection | 1 |
| rag_categories_overlapping | response_completeness | 1 |
| rag_categories_overlapping | speaker_role_confusion | 3 |
| rag_categories_overlapping | unsupported_assertion | 1 |
| structured_categories_exclusive | extra_entity | 1 |
| structured_categories_exclusive | missing_entity | 2 |
| structured_categories_exclusive | missing_goal | 1 |
| structured_categories_exclusive | output_format | 1 |
| structured_categories_exclusive | relation_reasoning | 1 |

### new_held_out

RAG denominator: 44; structured denominator: 36.

| Category set | Category | Cases |
| --- | --- | ---: |
| rag_verdicts_exclusive | fails_reference | 5 |
| rag_verdicts_exclusive | meets_reference | 29 |
| rag_verdicts_exclusive | partial | 10 |
| rag_categories_overlapping | contradiction | 1 |
| rag_categories_overlapping | entity_binding | 1 |
| rag_categories_overlapping | negation_failure | 1 |
| rag_categories_overlapping | prompt_injection | 4 |
| rag_categories_overlapping | reasoning_completeness | 1 |
| rag_categories_overlapping | reasoning_error | 3 |
| rag_categories_overlapping | reasoning_justification | 1 |
| rag_categories_overlapping | register | 1 |
| rag_categories_overlapping | response_completeness | 1 |
| rag_categories_overlapping | source_authority | 1 |
| rag_categories_overlapping | speaker_role_confusion | 4 |
| rag_categories_overlapping | unsupported_action_commitment | 1 |
| rag_categories_overlapping | unsupported_assertion | 1 |
| rag_categories_overlapping | unsupported_capability | 1 |
| rag_categories_overlapping | unsupported_procedure | 1 |
| structured_categories_exclusive | class_error | 1 |
| structured_categories_exclusive | conflict_resolution | 1 |
| structured_categories_exclusive | extra_goal | 2 |
| structured_categories_exclusive | frozen_alias_limitation | 2 |
| structured_categories_exclusive | missing_entity | 4 |
| structured_categories_exclusive | output_format | 5 |
