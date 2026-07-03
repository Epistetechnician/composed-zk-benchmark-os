# Phase 412 HSAI Tiny Z3 Accepted Formal Evidence Handoff Boundary

State slice: `Phase 412 HSAI tiny Z3 accepted-formal-evidence handoff boundary`.

## Boundary

Phase 412 defines a docs-first handoff boundary from Phase 411 local tiny-Z3
reviewed formal-evidence record metadata toward a future accepted
formal-evidence path for:

```text
gateway-local-digest-binding-determinism-v1
```

This phase does not implement accepted formal evidence, mutate the accepted
Evidence Ledger, change accepted append policy, create Level2+ evidence,
populate score axes, generate proof artifacts, generate checker transcripts,
generate solver certificates, execute Lean, execute COBALT, run Rust-to-Lean
extraction, submit benchmarks, deploy to production, or grant action
authority.

The current accepted-ledger append transaction remains authoritative for local
accepted evidence mutation. Phase 412 does not bypass that guard and does not
create a parallel accepted-evidence path.

## Current Tiny-Z3 Evidence Ladder

The tiny-Z3 formal-evidence lane now has this local ladder:

```text
quarantined_z3_output_bundle
-> formal_evidence_candidate
-> reviewed_formal_evidence_preview
-> reviewed_formal_evidence
-> future_accepted_formal_evidence_handoff
```

The final state above is only a future handoff target. It is not implemented by
Phase 412.

## Required Future Handoff Inputs

A future tiny-Z3 accepted formal-evidence handoff package must bind:

- Phase 411 reviewed-record digest.
- Phase 411 reviewed-record input digest.
- Phase 409 review-preview digest.
- Phase 409 review-preview input digest.
- Phase 407 candidate digest.
- Phase 407 candidate-input digest.
- Phase 405 output-manifest digest.
- Phase 404 execution digest.
- Phase 403 probe digest.
- reviewer and verifier policy ids.
- reviewer decision id, timestamp, and label.
- reviewed-scope statement digest.
- accepted-evidence-disabled acknowledgement digest.
- requested accepted-evidence class.
- requested claim boundary.
- accepted append policy version.
- formal-evidence acceptance policy version.
- explicit nonclaims for accepted evidence.
- rejection proof that no Level2+, score-axis, benchmark/SOTA, semantic
  correctness, production-readiness, full-security, breakthrough, or authority
  claim is being made.

## Required Future Policy Decision

Before implementation, the repository must make one explicit policy decision:

```text
Does accepted formal evidence remain forbidden by the accepted append path,
or does a new bounded formal-evidence class become admissible under a new
claim boundary below Level2+?
```

Until that decision is implemented in code and tests, Phase 411 reviewed-record
metadata cannot become accepted formal evidence.

## Forbidden Shortcuts

A future implementation must reject:

- direct mutation of the accepted Evidence Ledger from `hsai-agent-admission`;
- any append path that bypasses `zkbench-core` accepted append policy;
- any accepted formal-evidence record that lacks Phase 411 reviewed-record
  digest binding;
- any accepted formal-evidence record that lacks Phase 409, Phase 407, Phase
  405, Phase 404, and Phase 403 provenance binding;
- any accepted formal-evidence record that claims Level2+ evidence;
- any accepted formal-evidence record that populates score axes;
- any accepted formal-evidence record that claims benchmark comparison or SOTA;
- any accepted formal-evidence record that claims semantic correctness,
  production readiness, full security, breakthrough status, or action
  authority;
- any accepted formal-evidence record that treats a solver verdict, checker
  transcript, certificate, or reviewed metadata as proof authority without a
  separate proof/checker policy;
- any claim that the tiny-Z3 record proves the HSAI gateway, model inference,
  attestation stack, economic membrane, or production system end to end.

## Evidence Meaning

The maximum claim after Phase 412 is:

```text
HSAI has a documented handoff boundary from one local tiny-Z3 reviewed
formal-evidence record toward a future accepted formal-evidence path, while
preserving the current accepted append guard and blocking Level2+, score-axis,
SOTA, semantic-correctness, production-readiness, full-security, and action
authority claims.
```

That still is not:

- accepted formal evidence;
- Level2+ evidence;
- score-axis evidence;
- a Lean proof;
- a COBALT containment proof;
- a Rust-to-Lean proof;
- a checker transcript;
- a solver certificate;
- source correspondence proof;
- whole-system proof;
- semantic correctness;
- production readiness;
- SOTA;
- breakthrough status;
- full security;
- authority to execute an action.

## Phase 413 Implementation Conditions

Phase 413 may implement local handoff metadata only if it:

- does not mutate the accepted Evidence Ledger;
- does not change accepted append policy;
- does not create accepted formal evidence;
- binds Phase 411, Phase 409, Phase 407, Phase 405, Phase 404, and Phase 403
  digests;
- records the current accepted append formal-evidence blocker explicitly;
- records the future policy decision as unresolved;
- rejects Level2+, score-axis, benchmark/SOTA, semantic-correctness,
  production-readiness, full-security, breakthrough, and authority claims;
- keeps accepted evidence creation blocked until a separate policy phase
  changes the accepted append boundary.

## Next Slice

Phase 413 may implement local tiny-Z3 accepted-formal-evidence handoff metadata
under this boundary. It must not mutate accepted evidence, create accepted
formal evidence, create Level2+ evidence, populate score axes, claim semantic
correctness, claim production readiness, claim SOTA, claim breakthrough status,
claim full security, or grant authority to execute an action.
