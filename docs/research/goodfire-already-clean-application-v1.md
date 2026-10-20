# Goodfire already-clean application v1 (excerpt: Lanes B-D, prerequisites, nonclaims)

Claim ceiling: `Level0DesignNote`. Documentation only; no lane is authorized.

### Lane B: instrument-validity gate (hard lane, docs-first)

Proposed slice: `instrument-validity-gate-v1` (not authorized).
Content: a checklist-as-contract any mechanistic or measurement claim must
pass before effects are read: (i) activation-shape check (raw activation
ranges and tail shape, not percentiles alone; express thresholds in tokens or
pages); (ii) both-sign inspection for gated/SwiGLU units (positive and
negative poles, double-negative regime separated); (iii) a lens-sensitivity
check (result must survive at least two independent readouts); (iv)
positive-control and near-miss test for every explanation; (v) known-bad
instrument control (a deliberately broken readout must fail the gate).
Relation to existing work: reuses the repo's existing no-op/zero-parity,
repeatability and control discipline; adds items (i), (ii), (iv), (v).
"Theseus Lab" is not defined anywhere in this repository; any mapping to it
is a labeled assumption pending a source.

### Lane C: Caduceus mechanism-versus-behavior lane (speculative)

Proposed slice: `caduceus-mechanism-vs-behavior-lane-v1` (not authorized).
"Caduceus" is not defined in this repository's documentation; this lane
therefore records only an interface intent. If a governed update ever
changes model weights, add an optional lane that reports a matched-random
control ablation delta next to the behavioral gates, as a *descriptive*
addition. It must not become a gate, a score, or part of any PRD until a
preregistered design and independent review exist.

### Lane D: continual-learning descriptive diagnostic

Proposed slice: `continual-learning-recursive-generalization-diagnostic-v1`
(not authorized).
Hypothesis H-D (descriptive only): in the existing synthetic and cached-model
continual-learning harnesses, activations of an updated unit's strongest
neurons grow offshoots along adjacent, related inputs across checkpoints
(local growth) rather than attaching unrelated inputs (non-local). Method:
checkpoint-by-checkpoint neighborhood measurements on the already-closed
synthetic families; no new model execution. Closed families
(plasticity-recovery V1/V2, recursive-update-policy V1/V2) stay closed; this
may only add a read-only diagnostic over their frozen artifacts if a future
slice authorizes reading them. It generates hypotheses and supports no
forgetting, retention, or improvement claim.

## 5. Execution prerequisites (all lanes)

No lane may run until all of the following exist and are recorded:
1. a fresh named state slice per lane plus the governance slice;
2. a frozen, digest-bound packet (source, model, runtime, corpus, controls,
   estimand, thresholds, multiplicity, power, locks);
3. an independent, packet-bound signed Ed25519 `ACCEPT` (the operator cannot
   self-sign) for model-bearing or provider-bearing execution;
4. offline model execution against a pre-materialized cached checkpoint;
5. for any remote compute: exact provider and node identity, a positive hard
   USD ceiling, a no-spend preflight, and an allocation receipt. Observed in
   this session: `gcloud` is installed (auth and project unchecked); `aws`
   and any `gman` CLI are absent. The name `gman` is not defined in this
   repository; if it is the GiveMeANode client, its path, version and
   allocation receipt must be supplied. No cloud call was made.

## 6. Nonclaims

This document is not a replication, not evidence about any model, not a
reinterpretation of Astral V42-V48 or any closed slice, not an instrument
audit, not a mechanistic result, not benchmark evidence, and not a basis for
any score, Level2+, proof, SOTA, breakthrough, production-readiness,
security, or action-authority claim. No model, provider, cloud, or network
execution occurred in producing it. The essay's claims remain author-reported
and unreproduced.
