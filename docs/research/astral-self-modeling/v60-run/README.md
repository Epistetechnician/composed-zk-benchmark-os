# V60 result (LocalDevelopmentUnreviewed, exploratory, post-hoc, not independent)
Cleaner sufficiency tests for the V59 headline: last-position-only class swap (Task L) and counterfactual donor activation patching (Task P), locked V54 selection, 7 swap units, Pythia-2.8b, 800 assess items, node v51-full-r1, protocol doc 200. Spend USD 0.51 of the 1.50 cap (runner meter). Campaign total about USD 45.5 of 50.00. Node stopped.

## Task L: last-position-only swap: SUPPORTED
Mean margin drop **1.045** logits (singular 1.051, plural 1.039). 100 matched-random 7-unit sets, same operation: mean 0.004, max 0.011 (singular 0.013, plural 0.012). p = 0.0099 (100-draw floor).

## Task P: counterfactual donor patching: SUPPORTED
Patching the 7 units' last-position activations from an opposite-class donor sentence: mean drop **1.398** (singular 1.530, plural 1.265). Controls: mean 0.004, max 0.012. Same-class-donor diagnostic: 0.105 (not a gate; small but nonzero, partly sentence-level differences between donors).

## Decision (frozen rule)
Headline hardened = true: both L and P supported. The V59 sufficiency effect survives removal of the all-positions caveat (1.31 -> 1.05 with a last-position-only write) and holds under real-activation donor patching.

## Limits
Donors are different real sentences, not minimal pairs; one model, one split, 100 controls (p floor 0.0099), post-hoc relative to V54. No circuit, general-mechanism, proof, Level2+, SOTA or independent claim.
Files: `results/out_v60.json`, `results/out_v60.json.jsonl`, `allocation-receipt.json`.
