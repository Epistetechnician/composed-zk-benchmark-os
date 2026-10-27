# V61-local protocol: end-to-end local replication with held-out unit selection and cleaner sufficiency tests

Slices: astral-neuron-level-causal-lane-v61-local-execution, instrument-validity-gate-v3, governed by neuron-control-lanes-unreviewed-execution-v1. Ceiling: LocalDevelopmentUnreviewed. Authorized by the owner in chat 2026-10-27 ("lets do 2 end to end properly"). Committed before any V61 code or model run. Exploratory; supersedes the closed V60-local (selection mismatch) with a different, fully local experiment. No provider, no spend.

## Why this design
V60-local failed because the locked V54 selection does not reproduce across hardware/dtype. V61 makes the whole pipeline local and removes a weakness inherited from V58/V59: those ranked units on the same assess split they were then tested on. V61 selects on fit, ranks on tune, tests on assess, in float32 to reduce numeric sensitivity.

## Pipeline (all frozen)
Model/corpus: Pythia-2.8b at revision 2a259cdd (weights hash-verified), V54 corpus rebuilt locally (manifest digest 59c514f0...; counts 800/800/800); Apple MPS, torch float32, offline.
1. **Select (fit):** per-layer top-32 units by fit-split score (v50.select_per_layer, layers 10/18/26) = 96 candidates. Lock the candidate list and digest before any tune/assess measurement. Overlap with the V54 selection is reported descriptively only; there is no equality guard.
2. **Rank (tune):** single-unit ablation effect on the tune split (margin readout); swap set = top 8 by tune effect (ties by unit id). The assess split is not touched before the swap set is locked.
3. **Test (assess, 800 items), against 100 matched-random 8-unit sets** (layer and magnitude matched, drawn disjoint from the candidates, identical operation, seed 71+1):
   - **T0 all-position class swap** (V59 operation, each unit replaced by its opposite-class fit mean at all positions).
   - **L last-position-only class swap** (same, last position only).
   - **P donor activation patching** (last position; donor = seeded real item of the opposite class, seed 6060; plus same-class-donor diagnostic, seed 6061).
   Each reports singular-correct and plural-correct mean margin drops and the combined drop.
4. **Supported** (per task) iff both directional drops exceed the control maxima and the combined drop >= 0.1 logits. Combined p is the one-sided rank p over 100 draws (floor 0.0099).

## Decision rule (frozen)
"Headline reproduced and hardened" iff T0, L and P are all supported. Report each separately regardless. If L or P fails while T0 holds, the V59 effect is attributed mainly to the all-position intervention. If T0 fails, the V59 headline did not reproduce on held-out-selected units. No thresholds change after data; no rerun with another dtype or seed.

## Limits and rules
Single model, single split, 100 controls, post-hoc relative to V54/V58/V59, units are chosen by this pipeline (not the same 7-8 units as V59; overlap reported), float32 on MPS only. Aborts: weight/corpus digest mismatch, locked candidate digest changed between steps. Claims: no mechanism, circuit, general, proof, Level2+, independent, SOTA, benchmark, production claim. Raw text and weights stay outside the repo; the repo holds code, protocol, public result JSON. Zero spend.
