# V53 protocol: many-item constant control with paired specificity test

Slices: astral-neuron-level-causal-lane-v53-execution, instrument-validity-gate-v3. Ceiling: LocalDevelopmentUnreviewed. Committed before any V53 run.

## Why
V52 (v52-run/README.md): gate valid, matched-random contrast strong (effect 0.81, p=0.001), but the single-item constant control (0.605 >= 0.5) forced NoCandidate. One item cannot say whether the units encode subject-verb agreement or a generic good/bad-verb bias. V53 measures exactly that, and is a post-hoc redesign after seeing V52; results are exploratory.

## Changes (frozen; everything else identical to V52/V51: model, corpus, layers, k, 1000 draws, seed 71, gate v3)
- The `constant` control now replaces every assessment item's sentence with the bare prefix "The" while keeping that item's good/bad verb pair, and measures per-document margin drops with and without ablation (constant drops c_i; real drops r_i on the real items).
- Specificity (all required): mean(c_i) < 0.5 (unchanged absolute rule); mean(r_i - c_i) >= 0.5; paired z = mean(r_i - c_i)/SE >= 4.0. If it fails, the control counts as "separates" (-> NoCandidate). Thresholds fixed here before data.
- Reported regardless: const_mean, specific_gap, z, const_frac_of_real. Actionable reading: a fail with large const_frac means the units mostly carry a generic verb-preference bias, not agreement.
- Spend: hard cap USD 6.00 on node v51-full-r1 (new receipt in `v53-run/`). Total neuron campaign stays under the owner's USD 40.00 ceiling (about 31.6 spent). Owner chose this option in chat 2026-10-23 ("option 2 ... actionable insights").
- Failed gate or spend breach closes V53 without retuning. No Level2+, proof, SOTA, general, independent, or mechanism claim; path analysis only after a valid Candidate.
