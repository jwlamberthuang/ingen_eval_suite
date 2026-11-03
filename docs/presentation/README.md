# Capstone presentation

The ten-slide presentation summarizes the reviewed technical report and retained
experiment evidence. The intern reported reviewing the prepared changes on
3 November 2026. Release approval and rehearsal remain separate steps.

- [Presentation PDF](W04_Capstone_Deck.pdf)
- [Editable PowerPoint](capstone.pptx)
- [Slide text, tables, and evidence notes](capstone.md)
- [Technical report](../technical_report.pdf)
- [Numeric evidence](../reports/evidence/summary.json)

| Slide | Focus |
| --- | --- |
| 1 | Contribution and experimental scope |
| 2 | Capability-to-metric mapping |
| 3 | Dataset composition, split, and overlapping edge categories |
| 4 | RAG aggregate and domain means, population SDs, and counts |
| 5 | Quantified response failures and the raw extraction contract |
| 6 | Structured task success, validity, and conditional planning coverage |
| 7 | A concrete counterexample to the faithfulness approximation |
| 8 | Repository structure, saved-artifact replay, and release status |
| 9 | Three actionable recommendations |
| 10 | Three prospective studies and the repository URL |

## Editing and export

`capstone.pptx` is the editable presentation source. Tables and both quantitative
charts are native PowerPoint objects; the chart workbooks contain the displayed
count snapshots. Speaker notes record sources and interpretation limits. The
cover image in [assets/dialogue_inspection.png](assets/dialogue_inspection.png)
is a conceptual illustration rather than experimental evidence.

Use Arial for Latin text and Songti SC for Chinese. Edit the native objects and
notes in PowerPoint, reconcile wording and values with `capstone.md`, and export
the same ten slides to `W04_Capstone_Deck.pdf`. Inspect every exported slide for
font substitution, clipping, and changed table or chart geometry. Check numeric
edits against the evidence summary and the report before replacing either final
file. The checked-in PDF is the stable viewing copy.

The deck retains the distinction between fixed scorer probes and generated
answers, assisted and automatic scoring, post-inspection recall correction and
fresh evaluation, and conditional metrics and full-denominator task success.
It reports one public-model baseline. Planned studies are not measured
improvements.
