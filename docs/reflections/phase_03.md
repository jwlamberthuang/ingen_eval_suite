# Week 3 methodological reflection

The most consequential finding this week concerns the faithfulness metric. The
implementation measures the fraction of extracted claims whose closest evidence
segment exceeds a multilingual embedding threshold. That definition is precise
and reproducible, but the word faithfulness can suggest a stronger conclusion:
that the evidence actually supports the answer. The new boundary cases show why
those interpretations must remain separate.

The ten fixed adversarial candidates all received proxy scores of 1.0, although
their annotated supported-claim fractions were zero or one half. Two belong to
calibration and eight to held-out. These prewritten scorer challenges expose
measurement failure separately from generated model failures.

Two mechanisms are visible in the saved evidence matches. In case 0170, the
claim that a library tablet may be taken home matches a policy saying it cannot
be taken home, with cosine about 0.849. Shared topic and wording outweigh the
permission reversal. In case 0103, the incorrect claim that seven paper stars
remain matches a quoted instruction to give that answer. The trusted arithmetic
instead gives twenty. A closest-segment search can therefore reward both a
contradiction and an instruction that should never serve as factual authority.

This changes how a high score should be read. It establishes retrieval similarity
under the frozen representation and threshold, rather than logical entailment,
source authority, arithmetic correctness, or correct entity binding. Raising the
threshold after inspecting these cases would not establish those missing
properties. It would also contaminate the held-out evidence. The transferred
Week 2 threshold remains 0.80, with its limited applicability stated explicitly.

The real extraction stage also rejected every raw proposal: 153 were bare arrays
and two had malformed JSON. Separate correspondence inspection made scoring
possible, but its results must be labeled as assisted diagnostics rather than
evidence of a fully automatic extraction pipeline.

The structured extensions make another useful distinction: an explicit scoring
contract can be exact about its own rules without capturing every valid natural
language answer. Entity aliases, action slots, and task precedence must therefore
be inspected alongside parsing coverage and case-level outputs. Undefined ratios
and malformed answers must remain visible instead of disappearing into favorable
conditional means.

The context-recall audit found a second measurement issue: missing-information
statements received credit instead of unavailable requested answers. A separate
annotation amendment records 17 approved corrections across 55 inspected inventories,
preserving the source and experiment. Unknown values remain unresolved; conflicts
stay in the denominator and an unidentified referent produces N/A. Saved-response
replay changes only context recall: new calibration becomes 0.8182 and held-out
0.7442, with 43 of 44 defined. Intern review approved every correction. This
post-inspection correction cannot establish fresh held-out performance.

The next methodological improvement should be a separately versioned comparison
of support judgments that account for contradiction and evidence authority.
Numbers, negation, and identity links need targeted checks; bilingual negative
labels need broader coverage before calibration claims. Technical inspection
helps explain failures but does not replace independent human response assessment.
