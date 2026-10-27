# V61-local result (LocalDevelopmentUnreviewed, exploratory, not independent)
Protocol doc 201; code db05a3b9; Apple MPS, float32, Pythia-2.8b (weights hash-verified), V54 corpus rebuilt (digest 59c514f0...). Zero spend, 6806 s wall. Pipeline: fit-select 96 candidates, rank on tune, swap set = top 8 by tune effect, test on assess (800 items) vs 100 matched-random 8-unit sets.

Swap set: 2952, 13691, 20414, 22664, 24862, 25229, 27989, 28532 — 7 of 8 are V59 units (V59's 14134 replaced by 27989). Only 32 of 96 candidates overlap the H100-era V54 selection, so selection is hardware/dtype sensitive, but the top units are stable.

| Task | Selected drop (sing / plur / all) | Control max (all) | Supported |
|---|---|---|---|
| T0 all-position class swap | 1.52 / 1.20 / **1.36** | 0.009 | yes |
| L last-position-only swap | 1.11 / 1.08 / **1.09** | 0.009 | yes |
| P counterfactual donor patching | 1.59 / 1.31 / **1.45** | 0.011 | yes |

All p = 0.0099 (100-draw floor). Decision rule met: headline reproduced and hardened. V59's 1.31 reproduces (1.36) on held-out-selected units, and the effect survives the last-position-only edit (1.09), so it is not an artifact of writing constants at all positions.

Caveats: the same-class-donor diagnostic is 0.098 (plural 0.139), not near zero as hoped, so part of the patching effect may reflect generic donor-activation mismatch, though controls patched identically stay at 0.011; donors are real sentences, not minimal pairs; one model, one split, 100 controls, post-hoc relative to V54/V58/V59, AI-assisted prior audits, no independent review. No mechanism, circuit, general, proof, Level2+, SOTA or independent claim.
Files: results/out_v61_local.json (+ .jsonl).
