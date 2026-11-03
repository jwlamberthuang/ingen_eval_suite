# Final methodological reflection

The central decision in the final synthesis was to preserve the recorded baseline
while making the limits of its interpretation explicit. Correct computations and
useful measurements require different evidence. The suite can replay a saved
score exactly, yet that score may still miss a behavior that matters to the
application. The report and presentation therefore retain the metric definitions,
coverage, and counterexamples together.

The faithfulness proxy makes this distinction concrete. For each response, it
computes the fraction of inspected claims whose closest evidence segment reaches
a cosine threshold of 0.80. Its new held-out mean is 0.9050 over 43 defined RAG
cases. However, all ten
prewritten flawed probes receive 1.0 despite ideal supported-claim fractions of
zero or one half. Similar wording can conceal a reversed permission, a wrong
quantity, or an incorrect recipient. These fixed challenges evaluate the scorer;
they are separate from generated model responses. Inspected claim corrections
also remain separate from the raw extractor, whose 155 proposals all failed the
strict output contract.

An approximation perspective changes the next question. The study does not
provide an error bound connecting embedding support to factual support, so a
higher average cannot establish that connection. A prospective comparison needs
reviewed bilingual negative examples and measures of false-positive support,
balanced accuracy, and coverage. Changing the threshold after inspecting the
current held-out failures would obscure the very evidence that motivated the
comparison. Future evaluation needs untouched scenario families.

Structured planning reinforces the importance of the population being summarized.
Coverage averages 0.8611 across six defined held-out cases, while exact task
success is three of twelve. Five malformed outputs receive zero task success and
undefined core metrics. A valid empty reference creates another undefined
coverage denominator. Conditional coverage and end-to-end success answer
different questions; both need their counts. The two retained alias limitations
likewise remain visible instead of disappearing through retrospective matcher
changes.

The context-recall amendment follows the same principle. Seventeen approved
inventory corrections change the diagnostic without changing model-visible
inputs, generations, or other metrics. Its held-out mean of 0.7442 over 43 defined
cases describes a post-inspection annotation correction, not a new independent
experiment. The original evidence remains available for comparison.

The final methodological priority is therefore a separately versioned evaluation
cycle that tests support validity and output reliability together. Reproducible
artifacts make those comparisons inspectable. Explicit assumptions and preserved
failures make their interpretation defensible.
