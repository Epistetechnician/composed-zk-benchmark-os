# Phase 416 HSAI Tiny Z3 Bounded Formal Evidence Feasibility Boundary

State slice: `Phase 416 HSAI tiny Z3 bounded formal-evidence feasibility boundary`.

## Boundary

Phase 416 defines a docs-first feasibility boundary for a possible future
bounded tiny-Z3 formal-evidence class. It does not implement the class, approve
the class, mutate the accepted Evidence Ledger, change accepted append policy,
create accepted formal evidence, create Level2+ evidence, populate score axes,
generate proof artifacts, generate checker transcripts, generate solver
certificates, execute Lean, execute COBALT, run Rust-to-Lean extraction, submit
benchmarks, deploy to production, or grant action authority.

The current tiny-Z3 policy remains:

```text
AcceptedFormalEvidenceStillForbidden
```

Phase 416 only asks what would have to be true before a later phase could even
consider a bounded tiny-Z3 formal-evidence class.

## Feasibility Question

The feasibility question is:

```text
Can HSAI define a bounded tiny-Z3 formal-evidence class that is local,
reviewed, solver-output-limited, non-Level2+, non-score-axis, non-SOTA, and
non-authoritative, while preserving the existing accepted append guard?
```

The default answer remains no until a later phase implements a policy surface
and tests it.

## Candidate Class Shape

A future bounded class, if ever authorized, would need a name no stronger than:

```text
TinyZ3LocalReviewedFormalEvidenceMetadata
```

This name is intentionally weaker than:

- `FormalPropertyStatement`;
- `MachineCheckedScopedProof`;
- `AcceptedFormalEvidence`;
- `ProofCertificate`;
- `SemanticCorrectnessProof`;
- `Z3ProofCertificate`;
- `GatewayCorrectnessProof`.

The candidate class would describe reviewed local metadata for one tiny-Z3
solver-output lane only. It would not describe proof authority, semantic
correctness, production readiness, or whole-gateway correctness.

## Required Ownership Decision

A future phase must decide whether this candidate class belongs in:

1. the existing `zkbench-core` accepted append path;
2. a separate local tiny-Z3 formal-evidence registry;
3. no accepted or registry path.

Phase 416 makes no ownership decision. It records that option 1 is currently
blocked by the accepted append formal-evidence guard.

## Required Feasibility Criteria

A future bounded tiny-Z3 class would require all of the following:

- exact class name and schema version;
- exact claim boundary below Level2+;
- exact owner path;
- Phase 415 policy-decision digest binding;
- Phase 413 handoff digest binding;
- Phase 411 reviewed-record digest binding;
- Phase 409 review-preview digest binding;
- Phase 407 candidate digest binding;
- Phase 405 output-manifest digest binding;
- Phase 404 execution digest binding;
- Phase 403 probe digest binding;
- source correspondence requirements;
- replay requirements;
- reviewer-policy requirements;
- Z3 solver-output authority limits;
- proof-source nonauthority rules;
- checker-transcript nonauthority rules;
- solver-certificate nonauthority rules;
- accepted Evidence Ledger mutation route, if any;
- score-axis exclusion rule;
- benchmark/SOTA exclusion rule;
- semantic-correctness exclusion rule;
- production-readiness exclusion rule;
- full-security exclusion rule;
- breakthrough-status exclusion rule;
- action-authority exclusion rule.

Missing any criterion means the bounded tiny-Z3 class is infeasible.

## Required Rejection Cases

A future implementation must reject:

- any class name that implies proof authority;
- any class name that implies accepted evidence before an accepted route exists;
- any class name that maps to `FormalPropertyStatement`;
- any class name that maps to `MachineCheckedScopedProof`;
- any class name that implies a Z3 proof certificate;
- any class name that implies gateway semantic correctness;
- any claim boundary above local reviewed metadata;
- any Level2+ evidence creation;
- any score-axis population;
- any benchmark/SOTA comparison claim;
- any semantic-correctness claim;
- any production-readiness claim;
- any full-security claim;
- any breakthrough claim;
- any action-authority claim;
- any accepted Evidence Ledger mutation without an explicit accepted-route
  implementation and tests;
- any attempt to treat the Phase 404 Z3 `unsat` output as proof authority
  without a separately implemented checker/certificate policy;
- any attempt to treat the Phase 411 reviewed record or Phase 415 policy
  decision as accepted evidence.

## Evidence Meaning

The maximum claim after Phase 416 is:

```text
HSAI has a feasibility boundary for a possible future local tiny-Z3 reviewed
formal-evidence metadata class, while current accepted formal evidence remains
forbidden.
```

That still is not:

- a bounded formal-evidence class;
- accepted formal evidence;
- accepted Evidence Ledger mutation;
- accepted append policy change;
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

## Phase 417 Implementation Exit Criteria

Phase 417 may add tiny-Z3 bounded-class feasibility metadata only if it:

- does not mutate the accepted Evidence Ledger;
- does not change accepted append policy;
- does not create accepted formal evidence;
- does not create or approve a bounded formal-evidence class;
- binds one Phase 415 policy-decision digest;
- records the candidate class name as feasibility-only;
- records owner path as unresolved;
- preserves the current accepted append blocker digest;
- rejects Level2+, score-axis, benchmark/SOTA, semantic-correctness,
  production-readiness, full-security, breakthrough, and authority claims.

## Next Slice

Phase 417 may implement local tiny-Z3 bounded-class feasibility metadata under
this boundary. It must not approve the class, mutate accepted evidence, change
accepted append policy, create accepted formal evidence, create Level2+
evidence, populate score axes, claim semantic correctness, claim production
readiness, claim SOTA, claim breakthrough status, claim full security, or grant
authority to execute an action.
