# V49 class-balanced natural-text control (b1, b2) (LocalDevelopmentUnreviewed)

Slices: astral-neuron-level-causal-lane-v49-execution, instrument-validity-gate-v1, neuron-control-lanes-unreviewed-execution-v1. Code committed before the runs; outputs `b1.json`, `b2.json`; same H100 node, offline, 3527 s total. Corpus: 1500 natural wikitext sentences ("The ... is/are"), exactly 250 "is" and 250 "are" gold per document group (fit/tune/assess disjoint by document block), same verb pair per item. Gate rule (preregistered in c1's record): known-bad shuffled readout effect < 10% of the selected effect.

| Run | Model | V49 | Assess margin drop | z (margin/logprob) | Known-bad effect (% of selected) | Gate |
|---|---|---|---|---|---|---|
| b1 | SmolLM2-1.7B (layers 8/12/18) | Candidate | 1.22 (tune 1.22) | 69.8 / 14.4 | 0.106 (8.7%) | **valid** |
| b2 | Qwen3-4B-Base (layers 13/21/29) | Candidate | 0.88 (tune 0.91) | 61.8 / 11.7 | 0.080 (9.1%) | **valid** |

Both: Holm rejects tune and assess at the 1000-draw p floor; text-only 0, constant -0.03/-0.06 do not separate; positive control (top-512) 2.38 / 1.72; near-miss 0.25 / 0.19; both signs present; heavy tails (excess kurtosis 24 / 27).

## Reading
Balancing classes cut the shuffled-readout residual (c1: 11.2% -> b1: 8.7%) and both runs pass the preregistered floor, but only narrowly: the broken readout still moves 0.08-0.11 with z of 24-31, so a small label-independent component remains in the selected set's effect. The bias explanation is partly but not fully supported; the passes sit just under the threshold and should not be read as the bias being absent.

## Cumulative picture (all unreviewed, single runs)
Candidate in all nine V49 runs. Gate-valid under the preregistered rule: g2 (Qwen3-4B, templates B), b1 (SmolLM2, balanced natural), b2 (Qwen3-4B, balanced natural); r4 only after a post-hoc criterion change; failed: r3 (lens z-gap rule), g1 and c1 (known-bad). Models: Qwen3-1.7B, Qwen3-4B-Base, SmolLM2-1.7B (two families). Corpora: templated (A, B) and natural Wikipedia text.

Supportable (Level1-local, unreviewed): in two small-LM families, a fit-selected set of 32 MLP neurons across three layers carries a causal share of subject-verb-number agreement preference beyond matched-random neurons, on held-out documents/templates, in templated and natural text, with the instrument gate passing in the class-balanced natural-text runs for both families.
Not supportable: a general claim (one phenomenon, small models, Wikipedia-style "The ..." subjects only, heuristic labels); a circuit/mechanism claim (zero-ablation, first-order selection, no path analysis, residual label-independent component); independence between runs sharing selection procedure; any review-grade, Level2+, SOTA, production or introspection claim.

Spend: $13.04 of USD 30 for the whole campaign; node stopped.
