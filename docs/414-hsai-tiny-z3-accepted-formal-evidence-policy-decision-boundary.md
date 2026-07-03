# Phase 414 HSAI Tiny Z3 Accepted Formal Evidence Policy Decision Boundary

State slice: `Phase 414 HSAI tiny Z3 accepted formal-evidence policy-decision boundary`.

## Boundary

Phase 414 defines the docs-first current-path policy decision for tiny-Z3
accepted formal evidence:

```text
Tiny-Z3 accepted formal evidence remains forbidden in the current `zkbench-core`
accepted append path.
```

This phase does not implement accepted formal evidence, mutate the accepted
Evidence Ledger, change accepted append policy, create Level2+ evidence,
populate score axes, generate proof artifacts, generate checker transcripts,
generate solver certificates, execute Lean, execute COBALT, run Rust-to-Lean
extraction, submit benchmarks, deploy to production, or grant action
authority.

The decision is deliberately narrow. It does not say tiny-Z3 formal evidence
can never be accepted. It says the existing accepted append path must keep
rejecting formal evidence classes until a separate future phase defines,
implements, and tests a bounded tiny-Z3 formal-evidence policy.

## Current Code Constraint

The current accepted append guard rejects:

- claim boundaries above `Level1LocalReplay`;
- `FormalPropertyStatement`;
- `MachineCheckedScopedProof`;
- other Level2+ or formal evidence classes;
- score-axis population.

Phase 413 handoff metadata records that blocker and requires the handoff policy
decision to stay unresolved. Phase 414 records the policy answer for the
current path:

```text
AcceptedFormalEvidenceStillForbidden
```

No code is changed by Phase 414. The Phase 413 builder still admits only
`UnresolvedAcceptedAppendBlocksFormalEvidence` until a future code phase adds a
separate policy-decision record.

## Allowed Future Policy Shapes

A future tiny-Z3 formal-evidence policy may choose one of these paths:

1. Keep tiny-Z3 formal evidence permanently forbidden in accepted append.
2. Add a separate non-append tiny-Z3 formal-evidence registry for reviewed
   local evidence only.
3. Add a bounded tiny-Z3 formal-evidence class below Level2+ with explicit
   solver/checker/source-correspondence limits and no score-axis population.

Only path 3 could eventually support accepted formal evidence. It would require
new implementation, tests, and claim-boundary docs before any accepted evidence
mutation is allowed.

## Requirements Before Any Bounded Class

Before any future phase can admit a bounded tiny-Z3 formal-evidence class, it
must define:

- exact evidence class name;
- exact claim boundary;
- whether the accepted append path or a new registry owns it;
- solver-output authority rules;
- checker transcript authority rules;
- solver certificate authority rules;
- source correspondence requirements;
- replay requirements;
- reviewer quorum or reviewer-policy requirements;
- accepted Evidence Ledger mutation route;
- Level2+ exclusion rules;
- score-axis exclusion rules;
- benchmark/SOTA claim exclusion rules;
- semantic-correctness, production-readiness, full-security, breakthrough, and
  action-authority exclusion rules.

## Forbidden Shortcuts

A future implementation must reject:

- treating Phase 411 reviewed-record metadata as accepted formal evidence;
- treating Phase 413 handoff metadata as accepted formal evidence;
- changing accepted append policy without tests;
- admitting `FormalPropertyStatement` through the existing Level1 append path;
- admitting `MachineCheckedScopedProof` through the existing Level1 append
  path;
- using Z3 `unsat` output as proof authority without a checker policy;
- using a checker transcript as proof authority without a transcript policy;
- using a certificate explanation as proof authority;
- using COBALT, Lean, or Rust-to-Lean claims without actually executing those
  lanes and binding their artifacts;
- populating score axes from reviewed or handoff metadata;
- claiming benchmark comparison, SOTA, semantic correctness, production
  readiness, full security, breakthrough status, or action authority.

## Evidence Meaning

The maximum claim after Phase 414 is:

```text
HSAI has an explicit tiny-Z3 policy boundary stating that accepted formal
evidence remains forbidden in the current accepted append path, while
preserving a future path for separately specified bounded tiny-Z3
formal-evidence policy work.
```

That still is not:

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

## Phase 415 Implementation Conditions

Phase 415 may implement local tiny-Z3 policy-decision metadata only if it:

- does not mutate the accepted Evidence Ledger;
- does not change accepted append policy;
- does not create accepted formal evidence;
- records the current-path decision as `AcceptedFormalEvidenceStillForbidden`;
- binds one Phase 413 handoff digest;
- preserves the current accepted append blocker digest;
- rejects bounded-class approval in the same record;
- rejects Level2+, score-axis, benchmark/SOTA, semantic-correctness,
  production-readiness, full-security, breakthrough, and authority claims.

## Next Slice

Phase 415 may implement local tiny-Z3 accepted formal-evidence policy-decision
metadata under this boundary. It must not mutate accepted evidence, create
accepted formal evidence, create Level2+ evidence, populate score axes, claim
semantic correctness, claim production readiness, claim SOTA, claim
breakthrough status, claim full security, or grant authority to execute an
action.
