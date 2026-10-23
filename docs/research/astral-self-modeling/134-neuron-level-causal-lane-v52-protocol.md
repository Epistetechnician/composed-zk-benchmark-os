# V52 protocol: V51 re-test with sufficient budget and incremental checkpointing

Slices: astral-neuron-level-causal-lane-v52-execution, instrument-validity-gate-v3. Ceiling: LocalDevelopmentUnreviewed. Written and committed before any V52 data or model run.

## Why
V51 (doc 133) closed inconclusive on budget: two attempts, no result, ~USD 6.26 spent, nothing saved because the runner held results in memory. V52 changes only budget and persistence. Corpus (the V51 item-disjoint 2400 items, attractor waiver included), model (pythia-2.8b @ 2a259cdd...), layers, k, draws, seed 71, gate v3 (Z_NULL 4.0, Z_SIGNAL 10.0, min effect 0.5) and all hypothesis rules are unchanged from V51. The gate remains post-hoc-designed after V50; results are exploratory.

## Changes (frozen)
- Spend cap for V52: USD 10.00. **Owner decision in chat 2026-10-23 ("higher budget") gave no figure; the figure 10.00 and the raised total ceiling USD 40.00 (28.1 spent + 10.00 + margin) are the assistant's interpretation, stated here.** Total neuron-campaign spend must stay <= USD 40.00.
- Reuse of the stopped node `v51-full-r1` (weights already on disk, hashes re-verified at start) under a new allocation receipt in `v52-run/allocation-receipt.json`.
- Every backend call appends an fsync'd JSONL line (`<out>.jsonl`); a watchdog kill also logs. A partial run therefore yields stage-level evidence, but only a completed run with a gate verdict is a V52 result.
- No reruns for implementation errors beyond the cap. Failed gate, audit, spend breach, or missing receipt closes V52 without retuning. No Level2+, proof, SOTA, general, independent, or mechanism claim.
