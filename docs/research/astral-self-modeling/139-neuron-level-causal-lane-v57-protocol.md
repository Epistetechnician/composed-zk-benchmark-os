# V57 protocol: robustness of the locked V54 finding (dose-response, mean ablation)

Slices: astral-neuron-level-causal-lane-v57-execution, instrument-validity-gate-v3. Ceiling: LocalDevelopmentUnreviewed. Committed before any V57 run. Delegated by the owner ("skip the independent reviewer and go ahead end to end", chat 2026-10-25); exploratory, post-hoc relative to V54, no new data or downloads.

## Why
Item 2 of the next-steps list: before scaling, check that the Pythia-2.8b result is not an artifact of one unit count or of zero-ablation.

## Design (frozen here)
Corpus = V54 corpus (digest 59c514f0...), Pythia-2.8b (packet hashes), assessment split only (800 items), fit-only selection with the same per-layer scores as V54. The run reselects k = 32 and aborts unless it equals the locked V54 selection; other k values come from the same fit scores (nested top-|score| per layer).
- **A. Dose-response:** k in {4, 8, 16, 32, 64, 128}; for each k the selected-unit effect on assess and 100 matched-random draws (the first 100 of the V54-seeded 1000-draw procedure, matched on layer and magnitude bin). Dose-response is "supported" iff the effects are strictly increasing in k AND the selected effect exceeds all 100 controls at every k. Reported per k: effect, control mean and max, one-sided p (floor 1/101), effect per unit.
- **B. Mean ablation (k = 32):** replace each selected unit's activation with its mean over all positions of the fit documents (instead of zero), with the same 100 controls under mean ablation. "Supported" iff the mean-ablation effect exceeds all 100 controls AND is at least 50% of the zero-ablation effect.
- Not done (stated limits): counterfactual swap and cross-task (gender agreement) specificity need new items; deferred. No gate or specificity re-run; V54 remains the H1 verdict.
- Spend: hard cap USD 2.50 on node v51-full-r1 (new receipt); total campaign <= USD 50.00 (about 42.3 spent, plus node wake minutes). Expected ~USD 1.3. One run; failed or unsupported outcomes are reported, not retuned. No mechanism, general, Level2+, independent, SOTA, benchmark or production claim.
