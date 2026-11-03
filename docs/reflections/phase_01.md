# Week 1 methodological log

Faithfulness required the most care to operationalize because an answer can sound
helpful, remain on topic, and still introduce a fact that the evidence does not
support. In companion dialogue, an invented appointment time can mislead the
user. In educational dialogue, a confident explanation can reinforce an incorrect
calculation. Semantic resemblance alone cannot distinguish these failures from a
correct answer.

The design separates three quantities. Context recall measures whether supplied
evidence contains the required answer information. Faithfulness measures the
fraction of the response's factual claims supported by that evidence. Answer
coverage measures whether the response actually conveys the required facts.
This separation avoids blaming generation for missing evidence and avoids
rewarding an answer that is grounded but incomplete.

Case `w01-fari-zh-0006-base` makes the distinction concrete. The user asks when the
book club starts and which room it uses. The passages provide three o'clock but
omit the room. The two reference facts remain in the annotation inventory, with
one supported and one unsupported. Context recall is therefore one half. The
ideal response states the known time and asks for a notice giving the location.
Its world-factual time claim is supported, while its uncertainty and clarification
are evaluated through behavior criteria. Inventing a room would fail grounding
even if the response were fluent and reassuring.

Atomic claim boundaries are part of the measurement instrument. A sentence that
gives an event's day and start time contains two independently checkable claims.
Quantities, names, and negation must survive decomposition. Otherwise a changed
number can be hidden inside an apparently similar sentence. Empty responses and
claim-free clarifications do not receive perfect faithfulness by default; they
receive explicit applicability and adequacy statuses.

The planned automated baseline retrieves the most similar evidence segment for
each claim using multilingual embeddings. This is a practical support proxy,
not proof of entailment. It can miss multi-passage deductions and accept an
unsupported claim with high topical similarity. Thresholds will be chosen only
against reviewed calibration claims, with contradictions and disagreements
reported separately. Manually verified metric tests must precede scored runs.

The dataset now assigns twenty cases to calibration and eighty to held-out
evaluation while keeping related scenario families together. Authoring review
covers every case, but held-out examples have not been used to tune a scorer or
select a model. The main limitation is evaluator validity: structural tests and
natural wording do not establish that an automated support checker captures
faithfulness. The next stage must test that approximation directly rather than
interpret a convenient scalar as the property itself.
