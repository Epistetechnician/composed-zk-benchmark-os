# V61 result (LocalDevelopmentUnreviewed, exploratory, post-hoc, not independent)
Minimal-pair donor patching for the 7 swap units, locked V54 selection, Pythia-2.8b, node v51-full-r1, protocol doc 201, code 2d84c6cf. RC 0; spend USD 0.08 of the 1.00 cap (runner meter; node wake minutes extra). Campaign total about USD 45.6 of 50.00. Node stopped.

## Setup
800 synthetic items (400 pairs) whose prefixes differ only in the subject noun's number ("The key near the cabinets" vs "The keys near the cabinets"); donor = the mate; metric = baseline minus patched (correct - wrong verb) margin. Mean unpatched margin on these items: 4.86 logits.

## Result: Task M SUPPORTED, minimal pair confirmed
- Self-donor (identity patch): exactly 0.0, so the pipeline check passed.
- Minimal-pair donor patch: mean drop **0.482** logits (singular-subject items 0.472, plural-subject 0.492), about 10% of the baseline margin. 100 matched-random 7-unit sets: mean -0.005, max 0.019 (singular 0.021, plural 0.022). p = 0.0099 (100-draw floor).
- Same-number donor diagnostic (different pair, same number): -0.033, i.e. essentially no effect.

## Reading
With everything else held fixed, changing only the subject's number in these 7 units' last-position activations moves the verb preference toward the other number, specific to number (same-number donors do nothing) and 25x above the strongest matched-random control. The effect is much smaller than V60's 1.40 (different real sentences) and than the 1.05 last-position swap: part of V60's donor effect came from non-number differences between donor and recipient, and the 7 units carry only a modest share of the number signal in a minimal-pair setting. The sufficiency claim therefore stands, but at roughly half a logit, not 1.4.

## Limits
Synthetic templates (short, "The N prep the N" prefixes), one model, 100 controls (p floor 0.0099), post-hoc relative to V54, effect is a fraction of the baseline margin (other units clearly carry the rest). No circuit, general-mechanism, proof, Level2+, SOTA or independent claim.
Files: `results/out_v61.json`, `results/out_v61.json.jsonl`, `allocation-receipt.json`.
