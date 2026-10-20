# V49 on a second model family with natural text (c1) (LocalDevelopmentUnreviewed)

Slices: astral-neuron-level-causal-lane-v49-execution, instrument-validity-gate-v1, neuron-control-lanes-unreviewed-execution-v1. Code committed before the run; output `c1.json`; same H100 node, offline. Model: HuggingFaceTB/SmolLM2-1.7B (Llama-style, layers 8/12/18, 24 total), downloaded once on the node. Corpus: 1200 natural Wikipedia sentences ("The ... is/are/was/were", built by `build_corpus.py` from wikitext-103), 400 per group, split by source-document group (fit/tune/assess disjoint by document block; not template-based). Seed 70. Known-bad rule replaced as preregistered: shuffled-label readout effect must be < 10% of the selected effect (no z arm).

## Result
- V49: **Candidate**. Selected-32 margin drop 1.29 (tune) / 1.27 (assess); matched-random gaps at the p = 0.001 floor; Holm rejects both; text-only 0, shuffled 0.013, constant 0 do not separate. Margin z = 62.4, logprob z = 12.6.
- Lane B gate: **InstrumentNotValid**, single failure: known-bad shuffled-label readout effect 0.142 = 11.2% of the selected effect (> 10% floor; z 37.9). Passed: tail shape (min -12.2, max 8.3, excess kurtosis 20.2), both signs (46% positive), two readouts, positive control (top-512: 2.47), near-miss (0.25).
- Verdict `NotValidated` by the preregistered rule; not retuned.

## What the near-miss tells us
The broken readout still moves 0.14, i.e. part of the selected set's effect does not depend on getting the agreement label right. In this corpus classes are imbalanced (singular verbs dominate), so ablation that shifts a general verb-form (is/was vs are/were) bias survives random label flipping. Interpretation, untested: the 32 neurons carry a verb-form bias component in addition to agreement-sensitive signal. This would also qualify the earlier template-based results.

## Combined picture across all V49 runs
Candidate in every run (r2, r3, r4, g1, g2, c1): Qwen3-1.7B, Qwen3-4B-Base, SmolLM2-1.7B; templated and natural text. Fully instrument-validated: g2 (4B) only, plus r4 after a post-hoc criterion change. Not validated by the preregistered rule: r3, g1, c1.

Limits: three models, one phenomenon (subject-verb agreement), zero-ablation with first-order selection, no path/circuit analysis, heuristic prefix extraction (noisy labels possible), single runs, unreviewed. Not accepted evidence, Level2+, proof, SOTA, production or introspection claim. Spend so far $8.11 of USD 30; node stopped.
