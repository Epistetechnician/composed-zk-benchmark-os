# V58 protocol: per-neuron mechanism analysis of the locked V54 finding

Slices: astral-neuron-level-causal-lane-v58-execution, instrument-validity-gate-v3. Ceiling: LocalDevelopmentUnreviewed. Committed before any V58 run. Delegated by the owner ("okay lets go ahead end to end", chat 2026-10-26); exploratory, post-hoc relative to V54/V56/V57, no new data or downloads.

## Why
V56: about 76% of the ablation effect acts directly on the output logits; V57: four units carry about 70% of the k=32 effect. So the natural mechanism test is unit-level: which neurons carry it, do they act through the direct logit path, and do they compute agreement (help the correct verb form in both singular and plural contexts) rather than a fixed verb-form bias?

## Design (frozen here)
Corpus V54 (digest 59c514f0...), Pythia-2.8b (packet hashes), assess split (800 items). Fit-only selection as in V54; the run aborts unless the k = 32 reselection equals the locked V54 selection. Units: the nested k = 128 selection (fit scores) plus 300 distinct matched-random control units (taken in order from the V54-seeded matched-random draws, excluding selected units).
Per unit: single-unit ablation effect on assess; direct logit attribution (DLA) = mean over items of act_last_position x (W_out column . (gamma * (U_good - U_bad)) with mean-centering) / final-norm std, the same direct-path formula as V50's `direct_effect` applied per unit; DLA and activation by class of the correct form (singular vs plural).
Pre-registered readings (each reported true/false, none retuned):
- **H-concentration:** sum of the single-unit effects of the top 8 units (by single effect) >= 50% of the joint k = 128 effect.
- **H-direct-path:** Spearman correlation between single-unit effect and DLA over the 128 selected units >= 0.5.
- **H-agreement-selective:** for >= 6 of the top 8 units, DLA > 0 for BOTH singular-correct and plural-correct items (the unit pushes toward the correct form in both classes, not a fixed bias), AND every top-8 single effect exceeds the maximum control single effect.
Also reported (not gated): joint effect of the top 8 vs the sum of singles (additivity), top-unit layers and indices, class-conditional activations, control DLA magnitude maximum.
- Limits: DLA is a direct-path, linear-through-final-norm approximation; no indirect paths; one model/split; correlational. Even if all three hold, wording is limited to "a small set of MLP neurons whose direct write to the verb-number logit direction accounts for ..., consistent with a localized agreement computation in Pythia-2.8b"; no circuit, general-mechanism, or proof claim.
- Spend: hard cap USD 2.50 on node v51-full-r1 (new receipt); campaign <= USD 50.00 (about 43.1 spent plus wake minutes). Expected ~USD 1. One run.
