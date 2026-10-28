# V62 protocol: hardware and dtype robustness of the V61-local pipeline

Slices: astral-neuron-level-causal-lane-v62-execution, instrument-validity-gate-v3, governed by neuron-control-lanes-unreviewed-execution-v1. Ceiling: LocalDevelopmentUnreviewed. Authorized by the owner in chat 2026-10-28 ("yes I approve it end to end"), including two downloads: Pythia-2.8b weights (EleutherAI/pythia-2.8b @ 2a259cdd, config.json + model.safetensors, ~5.6 GB, huggingface.co, SHA-256 checked against v50-run/packet.json) and the V54 Gutenberg books plus spaCy/en_core_web_sm in an isolated venv (~300 MB, gutenberg.org, corpus digest must equal 59c514f0...). No other hosts, no credentials, no provider, zero spend. Committed before any V62 run.

## Question
Does the V61-local result (T0/L/P supported; swap set and candidate list) survive changing device and numeric precision, which the V60-local failure showed can change unit selection?

## Design (frozen)
The V61 pipeline (doc 201, FROZEN61 digest unchanged) is run unchanged, once per arm, on the same weights and corpus. Only device and dtype change. Arms:
- A `mps_f32`: V61 path (bf16-loaded weights cast to float32), Apple MPS. Determinism replicate of V61-local.
- B `cpu_f32`: same weight path, CPU.
- C `mps_bf16`: bf16, no cast, MPS.
- D `mps_fp16`: fp16-loaded weights (checkpoint-native), MPS.
Per arm wall-clock cap 8 h; an arm exceeding it is reported NotCompleted, not retried. Arms run sequentially; no arm is rerun or retuned.

## Reported per arm (descriptive, no new thresholds)
Candidate-list Jaccard and swap-set overlap versus V61-local; T0/L/P selected combined drop, control max, supported flag, p; same-class-donor diagnostic; headline_reproduced_and_hardened.

## Decision rule (frozen)
- "Robust" iff every completed arm has T0, L and P all supported (the decision rule of doc 201 applied per arm).
- "Effect robust, selection precision-sensitive" iff every completed arm has all three supported but swap-set Jaccard versus V61-local is below 0.5 in any arm.
- "Not robust" otherwise; the failing arms and tasks are named. Arm A must match V61-local's verdicts, else determinism itself is in question and is reported first.
Abort: weight or corpus digest mismatch.

## Limits
One model, one corpus, single machine (Apple M4 Max), no CUDA arm, 100 controls (p floor 0.0099), post-hoc relative to V54-V61, no independent review. Claims: no mechanism, circuit, general, proof, Level2+, independent, SOTA, benchmark, production claim. Raw text and weights stay outside the repo.
