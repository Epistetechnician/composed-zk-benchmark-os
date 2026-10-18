# Findings: interpretability and continual learning

This repository is a long implementation log. If you read only one file, read this one. It covers the two lines of work most relevant to alignment research. Everything is bounded, local, and unreplicated, and the negative results are the main output. The full report is [RESEARCH.md](RESEARCH.md).

## Mechanistic interpretability (Astral, Gemma 3)

**One narrow positive.** Gemma 3 V4 trace qualification passed: pooled NMSE 0.0457 against a 0.05 gate, with parity, repeat, no-op, intervention reach, event replay and feature stability all passing. This is a measurement qualification for one model, runtime and asset set. It is not a causal-graph or introspection result.

**Terminal negatives.**
- Gemma causal-feature-effects V2: tune sign agreement 0.75 against a 0.80 gate, one Holm-corrected gate failed, and the held-out split was never opened.
- Astral V42-V46 and V48 (target reliability, localization, measurement invariance, response-anchored and answer-aligned targets, cross-view transport) all ended `NoCandidate`. The program stopped instead of searching more layers, wrappers or corpora.

## Continual learning

- **BillSum LoRA curriculum (V2-V9).** V2 and V3 stopped before model load, V4 hit its wall-clock limit, V5 ran out of memory, V6 failed on an unexpected adapter file. V7 completed: local assurance `INTERNAL_PASS`, scientific disposition `NoCandidate`, because the selected curriculum missed the selected-versus-random ROUGE-L gate.
- **Plasticity recovery (V1, V2).** `NoCandidate` both times. The mechanism family is closed.
- **Recursive update policy.** V2 ran a 64-case synthetic campaign; recursive selection lost to random.
- **Oak Lab V2.** Four real panels, target power 0.8074, measured CPU energy, independent validation. No algorithm passed the strict gate. Protocols V3-V6 were each rejected at independent review before any execution.

Infrastructure failures are recorded as stops, not as results, so a crashed run is never counted as a negative about the idea.

## What this does not show

No general alignment, introspection, or causal self-modelling result, no benchmark superiority, and no independent replication. A `NoCandidate` means a frozen gate was not met on the stated slice. It does not show the idea is wrong in general.

## Where the evidence lives

Raw model outputs and traces are held in owner-only custody and are not in this repository. Results that depend on them are marked in [RESEARCH.md](RESEARCH.md) and in the per-experiment folders under `experiments/`. Items that do not need custody replay with `cargo test --workspace`.
