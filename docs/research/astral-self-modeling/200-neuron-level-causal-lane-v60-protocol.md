# V60 protocol: cleaner sufficiency tests (last-position-only swap, counterfactual donor activation patching)

Slices: astral-neuron-level-causal-lane-v60-execution, instrument-validity-gate-v3, governed by neuron-control-lanes-unreviewed-execution-v1. Ceiling: LocalDevelopmentUnreviewed. Authorized by the owner in chat 2026-10-26 ("option 1"). Committed before any V60 code or model run. Exploratory, post-hoc relative to V54/V58/V59.

## Why
V59's headline (swapping 7 number-selective units to opposite-class means drops the verb margin by 1.31 logits vs control max 0.07) used constants written at ALL positions, a heavy out-of-distribution edit. V60 removes that caveat two ways, on the same locked units and the same 800 assess items.

## Units and items (fixed from V59)
swap_units = [20414, 25229, 2952, 28532, 24862, 13691, 22664] (plural-selective 4 + singular-selective 3). Run aborts unless a fresh k=32 reselection equals the locked V54 selection and V58 top units equal the frozen list. Items: V54 assess split (800).

## Task L: last-position-only class swap
Same as V59 Task A (opposite-class fit mean per unit) but written at the LAST position only; earlier positions untouched. Controls: 100 matched-random 7-unit sets (layer and magnitude matched), identical operation. Supported iff the singular-correct and plural-correct mean drops each exceed the control maxima and the combined mean drop >= 0.1 logits.

## Task P: counterfactual donor activation patching
For every assess item, a donor is drawn by a seeded permutation from items of the OPPOSITE correct-form class (donor = a different real sentence with the other number; not a minimal pair, disclosed). The donor prefix is run unpatched and the last-position activations of the units are captured; they replace the recipient's last-position activations. Metric: margin drop (baseline - patched), singular and plural reported separately and combined. Controls: the same donor pairing and operation on the 100 matched-random 7-unit sets. Supported iff both directional drops exceed the control maxima and the combined drop >= 0.1 logits.
Diagnostic (not a gate): the same patch from a SAME-class donor for the 7 units; should be near 0 and is reported.

## Decision rule (frozen)
"Headline hardened" iff L and P are both supported. If only one holds, report it as such; if neither, the V59 swap effect is attributed mainly to the all-position intervention. No threshold changes after data. V59's 1.31 is reported alongside for comparison only; no expectation on magnitude.

## Budget and rules
Hard cap USD 1.50 on node v51-full-r1 (new receipt), expected about USD 0.40. Campaign ceiling USD 50.00 (about 45 spent). One run, no new data or downloads, offline model. A selection mismatch, spend breach or missing receipt closes V60 without retuning. Claims: single model, single split, 100 controls (p floor 0.0099); no mechanism, circuit, general, proof, Level2+, independent, SOTA, benchmark or production claim.
