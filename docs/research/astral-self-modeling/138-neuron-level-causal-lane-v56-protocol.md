# V56 protocol: exploratory path analysis H2' on the locked V54 selection

Slices: astral-neuron-level-causal-lane-v56-execution, instrument-validity-gate-v3. Ceiling: LocalDevelopmentUnreviewed. Committed before any V56 run. Delegated by the owner ("keep going end to end", chat 2026-10-25); post-hoc and exploratory.

## Why
H2 (mechanism) aborted in V51-V54 with "too few valid control draws": it compared ratio shares (indirect/total, top-2/indirect), which are undefined for matched-random controls whose total effect is <= 0, about half of draws. So H2 could never be tested. V56 replaces ratios with absolute quantities, defined for every draw. This is a redesign after seeing the failure and is labeled post-hoc.

## Design (frozen here)
- Uses the V54 corpus (digest 59c514f0...), Pythia-2.8b (packet-verified), and the **locked V54 selection** (the run reselects on fit data and aborts if the 96 units differ from `v54-run/results/out_v54.json`). No new selection or gate; V54 remains the H1 verdict.
- For the selected units and each of 1000 matched-random draws (same pool/seed as V54), on the <=64 same-length assessment docs: total effect, direct effect (last-position path to unembedding), indirect_abs = total - direct (logits), block-level activation-patching mediator shares (only if indirect_abs > 0), and top2_abs = (top-2 mediator share) * max(indirect_abs, 0).
- H2' holds iff one-sided matched-random p for indirect_abs and for top2_abs both reject under Holm (alpha 0.05) AND the selected top-2 mediator share >= 0.5 (the frozen top2_min_share). Mediators reported by name.
- Wording if H2' holds: "activation patching (correlational) indicates the effect is mediated mainly by components X and Y downstream of the selected units"; this is **not** a circuit, causal-pathway proof, or general mechanism claim. If H2' fails, no mechanism wording and no retuning.
- Spend: hard cap USD 3.00 on node v51-full-r1 (new receipt); campaign total <= 50.00 (about 41.6 spent). Expected ~USD 1.5. Closed after one run.
