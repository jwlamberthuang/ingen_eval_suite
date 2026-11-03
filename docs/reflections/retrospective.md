# AI evaluation retrospective

This internship broadened my understanding of AI evaluation beyond RAG. Evaluating
dialogue alongside spatial and temporal reasoning, entity recognition, and goal
alignment helped me see more practical applications of AI in everyday life. The
project uses public models as text proxies, so it does not establish the performance
of physical robots. It nevertheless made the range of evaluation problems in
physical AI more concrete for me.

## Approximation and metric design

The connection to Math REU ideas about convex relaxation and approximation bounds
is the need to explain what a tractable surrogate preserves. Computing a score
correctly does not, by itself, establish that the score captures the intended
behavior. Here, embedding similarity made support scoring practical, but the fixed
counterexamples exposed failures involving negation, evidence authority, and entity
identity. All ten flawed probes received a perfect proxy score. The study provides
no formal approximation bound connecting that proxy to factual support. Stopping
at passing tests and aggregate scores would have hidden this gap. The useful
mathematical discipline is to specify the target, state the approximation, and
actively look for cases in which their relationship breaks down.

## Transfer and adaptation

My earlier benchmarking internship gave me an evaluation pipeline perspective
that carried into this project. Separating generation from scoring, preserving
artifacts, and inspecting individual cases remained useful. The main change was
the scale and variety of the work. Earlier evaluation involved larger-scale,
more standard approaches. This internship let me build a suite from scratch and
run smaller, more detailed and diversified experiments.

That shift required different task contracts. Spatial relations, entity
inventories, and plans could not all be judged with the same dialogue similarity
score. Planning also showed why output validity belongs beside conditional
metrics: only three of twelve new held-out plans achieved exact task success,
although coverage among six defined cases averaged 0.8611. Keeping these
denominators visible made the result more informative.

## Career direction

I am still exploring AI engineering, machine learning engineering, and forward
deployed engineering. This experience has made their practical work more tangible:
building a reliable system, deciding what evidence supports a result, and adapting
evaluation to an application's needs. I do not yet want to narrow that choice to
one role. I want to keep exploring work that connects mathematical reasoning with
useful AI systems, while developing the engineering judgment needed to evaluate
those systems carefully.
