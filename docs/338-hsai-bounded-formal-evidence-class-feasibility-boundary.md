# Phase 338 HSAI Bounded Formal Evidence Class Feasibility Boundary

State slice: `Phase 338 HSAI bounded formal-evidence class feasibility boundary`.

## Boundary

Phase 338 defines a docs-first feasibility boundary for a possible future
bounded formal-evidence class. It does not implement the class, approve the
class, mutate the accepted Evidence Ledger, change accepted append policy,
create Level2+ evidence, populate score axes, generate proof artifacts,
generate checker transcripts, generate solver certificates, execute Lean,
execute COBALT, run Rust-to-Lean extraction, submit benchmarks, or deploy to
production.

The current policy remains:

```text
AcceptedFormalEvidenceStillForbidden
```

Phase 338 only asks what would have to be true before a later phase could even
consider a bounded class.

## Feasibility Question

The feasibility question is:

```text
Can HSAI define a bounded formal-evidence class that is local, reviewed,
non-Level2+, non-score-axis, non-SOTA, and non-authoritative, while preserving
the existing accepted append guard?
```

The default answer remains no until a later phase implements a policy surface
and tests it.

## Candidate Class Shape

A future bounded class, if ever authorized, would need a name no stronger than:

```text
LocalReviewedFormalEvidenceMetadata
```

This name is intentionally weaker than:

- `FormalPropertyStatement`;
- `MachineCheckedScopedProof`;
- `AcceptedFormalEvidence`;
- `ProofCertificate`;
- `SemanticCorrectnessProof`.

The candidate class would describe reviewed local metadata only. It would not
describe proof authority, semantic correctness, or production readiness.

## Required Ownership Decision

A future phase must decide whether this candidate class belongs in:

1. the existing `zkbench-core` accepted append path;
2. a separate local formal-evidence registry;
3. no accepted or registry path.

Phase 338 makes no ownership decision. It records that option 1 is currently
blocked by the accepted append formal-evidence guard.

## Required Feasibility Criteria

A future bounded class would require all of the following:

- exact class name and schema version;
- exact claim boundary below Level2+;
- exact owner path;
- evidence-source digest requirements;
- Phase 333 reviewed-record digest binding;
- Phase 335 handoff digest binding;
- Phase 337 policy-decision digest binding;
- source correspondence requirements;
- replay requirements;
- reviewer-policy requirements;
- explicit nonclaims;
- proof-source nonauthority rules;
- checker-transcript nonauthority rules;
- solver-certificate nonauthority rules;
- accepted Evidence Ledger mutation route, if any;
- score-axis exclusion rule;
- benchmark/SOTA exclusion rule;
- semantic-correctness exclusion rule;
- production-readiness exclusion rule;
- full-security exclusion rule;
- action-authority exclusion rule.

Missing any criterion means the bounded class is infeasible.

## Required Rejection Cases

A future implementation must reject:

- any class name that implies proof authority;
- any class name that implies accepted evidence before an accepted route exists;
- any class name that maps to `FormalPropertyStatement`;
- any class name that maps to `MachineCheckedScopedProof`;
- any claim boundary above local reviewed metadata;
- any Level2+ evidence creation;
- any score-axis population;
- any benchmark/SOTA comparison claim;
- any semantic-correctness claim;
- any production-readiness claim;
- any full-security claim;
- any action-authority claim;
- any accepted Evidence Ledger mutation without an explicit accepted-route
  implementation and tests.

## Evidence Meaning

The maximum claim after Phase 338 is:

```text
HSAI has a feasibility boundary for a possible future local reviewed
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
- whole-system proof;
- semantic correctness;
- production readiness;
- SOTA;
- breakthrough status;
- full security;
- authority to execute an action.

## Phase 339 Implementation Exit Criteria

Phase 339 may add bounded-class feasibility metadata only if it:

- does not mutate the accepted Evidence Ledger;
- does not change accepted append policy;
- does not create or approve a bounded formal-evidence class;
- binds one Phase 337 policy-decision digest;
- records the candidate class name as feasibility-only;
- records owner path as unresolved;
- preserves the current accepted append blocker digest;
- rejects Level2+, score-axis, benchmark/SOTA, semantic-correctness,
  production-readiness, full-security, and authority claims.

Phase 339 implements that metadata in
`docs/339-hsai-bounded-formal-evidence-feasibility-metadata-notes.md`. It still
does not approve the class or create accepted formal evidence.
