# V49 generalization + real Lanes C/D (LocalDevelopmentUnreviewed)

Slices: astral-neuron-level-causal-lane-v49-execution, instrument-validity-gate-v1, caduceus-mechanism-vs-behavior-lane-v1, continual-learning-recursive-generalization-diagnostic-v1, neuron-control-lanes-unreviewed-execution-v1. Code committed before the runs (one harness bug in the logprob readout, hit before any result, was fixed and rerun). Outputs: g1.json, g2.json, cd.json. Node spend across everything: $6.17 of USD 30; node stopped.

## Generalization (fresh templates B, fresh documents, seed-independent selection refit)
| Run | Model | V49 verdict | Assess effect (margin drop) | z (margin / logprob) | Lane B gate |
|---|---|---|---|---|---|
| r4 (ref) | Qwen3-1.7B, templates A | Candidate | 1.14 | 19.3 / 5.6 | valid (criterion changed post hoc) |
| g1 | Qwen3-1.7B, templates B | Candidate | 1.06 | 21.2 / 3.3 | **not valid**: known-bad z 3.79 (effect 0.027, 2.6% of selected) fails the |z|<2 arm |
| g2 | Qwen3-4B-Base (layers 13/21/29), templates B | Candidate | 0.82 | 30.9 / 9.1 | **valid**, all checks pass (known-bad z -0.59, pos control 1.99, near-miss 0.26) |

All three: Holm rejects tune+assess at the 1000-draw p floor; text-only, shuffled, constant controls do not separate.

## Lane C (real, descriptive, not a gate): fine-tune with checkpoints, Qwen3-1.7B (fp32)
Update: AdamW lr 1e-5, 80 steps on the correct-verb margin. Behavioral gate (assess accuracy) is saturated at 1.0 at every checkpoint, so it cannot move; yet the matched-random ablation delta of the step-0 selected set rises 1.17 -> 1.29 -> 1.38 -> 1.70 -> 1.92 (steps 0/10/20/40/80) and mean margin rises 4.3 -> 125.7. The loss is unbounded, so this update drives margins to a degenerate scale; the finding is only that the mechanism-side delta moves while the behavior gate is blind.

## Lane D (real, descriptive): same checkpoints
Share of the 8 strongest selected neurons' activation mass on adjacent (held-out agreement) vs unrelated inputs: 0.874, 0.822, 0.829, 0.834, 0.832. No local growth (`grows_local=false`); a small drop then flat. Spec deviation: measured on this run's checkpoints, not the closed-family artifacts. No retention/forgetting/improvement claim.

## What can honestly be claimed
Supportable (Level1-local, unreviewed): in two Qwen3 base models (1.7B, 4B), a small fit-selected set of 32 MLP neurons (3 layers) carries a causal share of subject-verb-agreement preference beyond matched-random neurons, on templates held out from selection, replicated on fresh templates and documents and at a second model size, with the strongest fully instrument-validated replication being g2 (4B). Effects are about 1 logit; controls null.
NOT supportable: a general claim (one model family, one syntactic phenomenon, templated sentences, one run each); a mechanistic circuit claim (first-order gradient selection, zero-ablation, no path analysis); the Lane B gate passes for r4 only after a post-hoc criterion change and g1 fails it; independence of r3/r4 (same neurons selected). No accepted-evidence, Level2+, proof, SOTA, production or introspection claim.

## Next steps that would change the claim ceiling
Independent human review of this packet; a different model family and a non-templated corpus; fix the known-bad rule to use the absolute-effect floor alone (needs a fresh identity); path/circuit analysis for any mechanistic wording.
