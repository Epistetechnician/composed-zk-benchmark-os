# V59 protocol: sufficiency (class-swap) and cross-task transfer (reflexive agreement)

Slices: astral-neuron-level-causal-lane-v59-execution, instrument-validity-gate-v3. Ceiling: LocalDevelopmentUnreviewed. Committed before any V59 corpus build or model run. Delegated by the owner ("okay lets do so end to end ... best innovative way", chat 2026-10-26); exploratory, post-hoc relative to V54/V58.

## Why (expected-value logic)
V53-V58 establish necessity: ablating a small set of MLP units removes the agreement preference. The two highest-value, cheap upgrades are (i) **sufficiency**: if the number-selective units are really the carrier, swapping them into the other number's state should push the model toward the other verb form; and (ii) **transfer**: if they carry subject number (not just a verb-form bias), ablating them should also hurt number agreement of reflexive pronouns (himself/themselves). Each result is informative whichever way it comes out.

## Units (fixed from V58)
The top-8 V58 units (v58-run/results/out_v58.json `top_units`); the run aborts unless a fresh k = 32 reselection equals the locked V54 selection. Number-selective sets from V58 class activations: plural-selective P = {20414, 25229, 2952, 28532}, singular-selective S = {24862, 13691, 22664}; unit 14134 (non-selective) is excluded from the swap (7 units); the ablation task uses all 8.

## Task A: class-swap sufficiency (V54 assess items, 800)
For each item, replace the 7 units' activations (all positions, as in ablation) by their mean activation in the **opposite** class (computed on the fit split, per unit, from `unit_stats` mean last-position activation by class of the correct form... fit-split means of the class-conditional activations). Metric: margin drop = baseline margin - swapped margin, reported separately for singular-correct items (expected drop > 0) and plural-correct items (expected drop > 0), and their mean. Controls: 100 matched-random 7-unit sets (matched on layer and magnitude bin to the 7), each unit replaced by its own opposite-class fit mean. Sufficiency is "supported" iff BOTH directional drops exceed the maximum of the 100 controls and the combined mean drop >= 0.1 logits. Not claimed even if supported: full sufficiency of the 7 units for the entire verb choice; only a directional causal push.

## Task R: reflexive-pronoun agreement transfer
New items from the already-local V54 books (assess documents only, spaCy 3.8.16 / en_core_web_sm 3.8.0, no network): prefix up to a reflexive in {himself, herself, itself, themselves} whose governing verb has a subject whose number is clear (NN/NNP/he/she/it singular; NNS/NNPS/they plural) and compatible with the observed form (singular -> himself/herself/itself; plural -> themselves; otherwise dropped). Gold = observed form; bad = " themselves" for singular items and " itself" for plural items. Exact class balance, per-doc cap 400, prefix >= 4 tokens, 100-item label audit (AI-assisted; > 5% error closes R). If either class has < 100 items, R is skipped and reported.
Measure: ablation of the 8 units (zero) -> margin drop on R items vs 100 matched-random 8-unit sets. "Transfer supported" iff the 8-unit drop exceeds all 100 controls and is >= 0.1 logits; "verb-form-specific" iff not. Both are reported without retuning.

## Budget and rules
Hard cap USD 2.50 on node v51-full-r1 (new receipt), campaign <= USD 50.00 (about 44 spent plus wake minutes); expected under USD 1. One run. No downloads or new data. Any positive result is correlational/interventional on one model and split: no circuit, general, proof, Level2+, independent, SOTA, benchmark or production claim.
