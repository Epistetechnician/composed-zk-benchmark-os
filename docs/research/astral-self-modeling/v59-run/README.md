# V59 result (LocalDevelopmentUnreviewed, exploratory, post-hoc, not independent)
Class-swap sufficiency and reflexive transfer for the V58 top units, Pythia-2.8b, node v51-full-r1, protocol doc 141 (+ addendum 1). RC 0; spend USD 0.40 of the 2.50 cap (runner meter; wake minutes extra). Campaign total about USD 45 of 50.00. Node stopped.

## Items for Task R
1252 singular and 143 plural reflexive candidates from the 35 V54 books (addendum 1), balanced to 143 per class = 286 items; label audit 60 items judged by Claude (AI-assisted), 0 errors; `refl-public.json`.

## Task A: class-swap sufficiency (assess, 800 items): SUPPORTED
Replacing the 7 number-selective units (P = {20414, 25229, 2952, 28532}, S = {24862, 13691, 22664}) with their mean activation in the **opposite** number class lowers the correct-minus-wrong verb margin by **1.31 logits** on average (singular-correct items 1.45, plural-correct items 1.16). The 100 matched-random 7-unit sets, each swapped to its own opposite-class fit means, give a mean of 0.003 and a maximum of 0.072 (singular 0.106, plural 0.037). Both directional effects exceed the control maxima, and the combined effect exceeds the 0.1 floor by 13x (p = 0.0099, the 100-draw floor).
Reading: the seven units are not only necessary (ablation 0.74) but sufficient to move the model's verb choice toward the other number: a causal handle, not only a dependency. The swap effect (1.31) is larger than ablation (0.7-0.8), which is expected when units are driven to the opposite-class code rather than silenced.

## Task R: reflexive-pronoun transfer: NOT SUPPORTED by the frozen floor (but above controls)
Ablating the 8 units lowers the reflexive-agreement margin by **0.061** logits; 100 matched-random 8-unit sets give mean -0.005, max 0.020 (p = 0.0099). That exceeds all controls but is below the pre-registered 0.1 floor, so "transfer supported" = false. Descriptive reading: the units are mostly verb-form-specific (reflexive effect is about 8% of their verb-task effect), with a small but control-exceeding residual effect on reflexive number agreement.

## Limits
Constants are written at all positions (as in ablation) from last-position class means, a heavy out-of-distribution intervention; the matched controls use the identical operation, which is what makes the contrast informative, but the absolute size 1.31 should not be over-read. One model, one split, 100 controls (p floor 0.0099), post-hoc relative to V54, addendum made before the run but after counting items, AI-assisted audits. No circuit, general-mechanism, proof, Level2+, SOTA or independent claim.
Files: `results/out_v59.json`, `results/out_v59.json.jsonl`, `refl-public.json`.
