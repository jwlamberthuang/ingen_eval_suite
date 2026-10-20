# Week 2 methodological log

The most unexpected failure was in the support scorer itself. A multilingual
embedding proxy accepted an unsupported room and an unresolved time conflict as
supported facts. The statements were close to the evidence in topic, but their
decisive factual content was not established. This exposed the gap between
retrieval similarity and the faithfulness property the proxy is intended to
approximate.

Calibration used thirty reviewed reference facts from the twenty designated
calibration cases: twenty-seven supported and three unsupported or conflicting.
At the selected threshold of 0.80, the proxy correctly accepted all twenty-seven
supported facts but rejected only one negative. Overall accuracy was therefore
28/30, or 93.3 percent, while balanced accuracy was only two thirds. A seemingly
strong aggregate concealed weak negative discrimination. The three negatives
are too few to support a confident general claim about hallucination detection.

The missing-room case makes the problem concrete. Its supplied Chinese passage
states that the book club begins at 15:00. The canonical room B202 is withheld.
Nevertheless, the room statement receives cosine similarity of approximately
0.865 against the start-time passage and passes the support threshold. Shared
event vocabulary makes the pair similar without supplying a location. In the
conflicting-notice case, the proxy finds one notice supporting 09:00 and overlooks
the equally authoritative contradictory notice. Maximum single-segment matching
cannot establish whether the evidence as a whole resolves the conflict.

Simply increasing the threshold did not solve the problem. At 0.90, twenty-three
of the twenty-seven supported calibration facts were rejected. The larger
threshold traded many genuine supports for one additional correct rejection.
The predefined grid and tie rule selected 0.80; that setting remains frozen rather
than being adjusted after inspecting held-out outputs.

This changes how the results should be interpreted. Core context recall uses
reviewed required-fact support to measure evidence sufficiency. Lexical reference
recall remains a separate overlap diagnostic. Faithfulness proxy values must be
shown alongside the calibration confusion matrix, inspected response behavior,
and concrete false-positive examples. Mathematical unit tests verify the fraction,
cosine, and aggregation computations; they cannot establish semantic entailment.

The next refinement should add reviewed negative contrasts within calibration
families, including changed quantities, entities, and polarity, and evaluate
conflict handling and joint evidence explicitly. These changes require a new
scorer version and a separately recorded experiment. The present result is useful
because it identifies an approximation failure that a high average alone would
hide, while preserving the held-out boundary and the original evidence.
