# Phase 402 HSAI Backend-Execution Readiness Reconciliation

State slice: `Phase 402 HSAI backend-execution readiness reconciliation`.

Phase 402 reconciles the post-400 tiny backend-execution boundary with the
already-existing Phase 321-327 formal command-lane work. It records what is
ready, what has already executed locally, what is unavailable in the current
environment, and what remains blocked before accepted evidence or stronger
claims can be made.

This phase does not implement Rust code, change Cargo metadata, write
filesystem artifacts, run a new backend, run Lean, run SMT, run COBALT, run
Rust-to-Lean extraction, create proof artifacts, create checker transcripts,
create solver certificates, mutate the accepted Evidence Ledger, change
accepted append policy, create accepted formal evidence, create Level2+
evidence, populate score axes, submit benchmarks, deploy to production, claim
semantic correctness, claim production readiness, claim SOTA, claim
breakthrough status, claim full security, or grant authority to execute an
action.

## Current Local Tool Availability

The Phase 402 local inspection found:

```text
z3=/opt/homebrew/bin/z3
lean=unavailable
lake=unavailable
cobalt=unavailable
python3=/Users/shaanp/.pyenv/shims/python3
rustc=1.93.1 (01f6ddf75 2026-02-11)
```

This is an environment observation only. It is not accepted evidence, not a
proof artifact, and not a durable toolchain lock.

## Existing Backend-Execution Surface

The repo already contains a scoped process-crossing lane:

- Phase 321 defines `local_smt_tiny_gateway_invariant`.
- Phase 326 implements
  `run_gateway_formal_real_command_lane_fixed_smt_process` for one
  preflight-authorized fixed local executable.
- Phase 327 materializes and reads back the quarantined fixed-SMT execution
  output bundle with digest sidecars and promotion-drift rejection.

That prior lane supports only this claim:

```text
HSAI has a local quarantined fixed-process SMT-LIB2 execution lane that can run one preflight-authorized local executable and classify bounded solver-like output without evidence promotion.
```

It does not support a system Z3 proof, Lean proof, COBALT containment proof,
Rust-to-Lean extraction proof, accepted formal evidence, Level2+ evidence,
score-axis population, semantic correctness, production readiness, SOTA, full
security, or action authority.

## Phase 401 Target Reconciliation

Phase 401 selected a future tiny property:

```text
gateway-local-digest-binding-determinism-v1
```

Phase 321 selected an older local SMT command-lane property:

```text
attestation_challenge_binding_deterministic_input_sensitive
```

These are related but not identical. The next implementation must not conflate
them. A future Phase 403 code slice may either:

1. add a narrow availability/probe metadata record for the Phase 401 property;
2. add a new quarantined fixed-Z3 execution wrapper for the Phase 401 property;
3. update the Phase 321-327 real command lane with an explicit property mapping
   record that keeps both property ids distinct.

Any of those choices must keep missing Lean/lake/COBALT recorded as
unavailable unless those tools are locally detected in that phase.

## Accepted-Evidence Blocker

Accepted formal evidence remains blocked by the current policy ladder:

- Phase 336 states that formal evidence remains forbidden in the current
  accepted append path.
- Phase 337 records that decision in local policy-decision metadata.
- Phases 356-397 explore proposal, review, quarantine, closure, and blocker
  metadata but never authorize an accepted formal-evidence append.
- Phase 399 freezes the stronger public-claim nonclaims.
- Phase 400 requires a new boundary before any accepted evidence, proof
  artifacts, score axes, or public-claim changes.

Phase 402 therefore records readiness to choose the next backend-execution
implementation slice. It does not cross the accepted-evidence boundary.

## Required Next Slice

The next responsible slice is:

```text
Phase 403 HSAI tiny digest-binding backend probe implementation
```

Phase 403 should implement only one of these:

- a no-spawn Rust metadata record that binds Phase 401 property inputs,
  local tool availability, and explicit unavailable statuses; or
- a fixed local Z3 execution path for the Phase 401 property, reusing the
  Phase 321-327 quarantine and nonpromotion discipline.

Phase 403 must not implement Lean execution, COBALT execution, Rust-to-Lean
extraction, accepted evidence, Level2+ evidence, score axes, public strong
claims, or generic backend runners in the same slice.

## Exit Criteria

HSAI now has a reconciled map from the post-400 backend-execution boundary to
the existing fixed-SMT execution lane and the current local tool availability.
The repo is ready for a narrowly scoped Phase 403 backend-probe implementation
but is still not ready for accepted formal evidence, Level2+ evidence, score
axes, semantic correctness, production readiness, SOTA, full security, or
action authority.
