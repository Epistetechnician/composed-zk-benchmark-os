# Phase 336 HSAI Accepted Formal Evidence Policy Decision Boundary

State slice: `Phase 336 HSAI accepted formal-evidence policy-decision boundary`.

## Boundary

Phase 336 defines the docs-first policy decision for accepted formal evidence:

```text
Formal evidence remains forbidden in the current `zkbench-core` accepted append
path.
```

This phase does not implement accepted formal evidence, mutate the accepted
Evidence Ledger, change accepted append policy, create Level2+ evidence,
populate score axes, generate proof artifacts, generate checker transcripts,
generate solver certificates, execute Lean, execute COBALT, run Rust-to-Lean
extraction, submit benchmarks, or deploy to production.

The decision is deliberately narrow. It does not say formal evidence can never
be accepted. It says the existing accepted append path must keep rejecting
formal evidence classes until a separate future phase defines, implements, and
tests a bounded formal-evidence policy.

## Current Code Constraint

The current accepted append guard rejects:

- claim boundaries above `Level1LocalReplay`;
- `FormalPropertyStatement`;
- `MachineCheckedScopedProof`;
- other Level2+ or formal evidence classes;
- score-axis population.

Phase 335 handoff metadata records that blocker and requires the policy
decision to stay unresolved. Phase 336 records the policy answer for the current
path:

```text
AcceptedFormalEvidenceStillForbidden
```

No code is changed by Phase 336. The Phase 335 builder still admits only
`UnresolvedAcceptedAppendBlocksFormalEvidence` until a future code phase adds a
separate policy-decision record.

## Allowed Future Policy Shapes

A future formal-evidence policy may choose one of these paths:

1. Keep formal evidence permanently forbidden in accepted append.
2. Add a separate non-append formal-evidence registry for reviewed local
   evidence only.
3. Add a bounded formal-evidence class below Level2+ with explicit proof-source
   limits and no score-axis population.

Only path 3 could eventually support accepted formal evidence. It would require
new implementation, tests, and claim-boundary docs before any accepted evidence
mutation is allowed.

## Requirements Before Any Bounded Class

Before any future phase can admit a bounded formal-evidence class, it must
define:

- exact evidence class name;
- exact claim boundary;
- whether the accepted append path or a new registry owns it;
- proof-source authority rules;
- checker transcript authority rules;
- solver certificate authority rules;
- source correspondence requirements;
- replay requirements;
- reviewer quorum or reviewer-policy requirements;
- accepted Evidence Ledger mutation route;
- Level2+ exclusion rules;
- score-axis exclusion rules;
- benchmark/SOTA claim exclusion rules;
- semantic-correctness, production-readiness, full-security, and action
  authority exclusion rules.

## Forbidden Shortcuts

A future implementation must reject:

- treating Phase 333 reviewed-record metadata as accepted formal evidence;
- treating Phase 335 handoff metadata as accepted formal evidence;
- changing accepted append policy without tests;
- admitting `FormalPropertyStatement` through the existing Level1 append path;
- admitting `MachineCheckedScopedProof` through the existing Level1 append
  path;
- using solver output as proof authority without a checker policy;
- using a checker transcript as proof authority without a transcript policy;
- using a certificate explanation as proof authority;
- populating score axes from reviewed or handoff metadata;
- claiming benchmark comparison, SOTA, semantic correctness, production
  readiness, full security, breakthrough status, or action authority.

## Evidence Meaning

The maximum claim after Phase 336 is:

```text
HSAI has an explicit policy boundary stating that accepted formal evidence
remains forbidden in the current accepted append path, while preserving a
future path for separately specified bounded formal-evidence policy work.
```

That still is not:

- accepted formal evidence;
- accepted Evidence Ledger mutation;
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

## Future Code Phase Exit Criteria

A future Phase 337 implementation may add local policy-decision metadata only
if it:

- does not mutate the accepted Evidence Ledger;
- does not change accepted append policy;
- does not create accepted formal evidence;
- records the current-path decision as `AcceptedFormalEvidenceStillForbidden`;
- binds one Phase 335 handoff digest;
- preserves the current accepted append blocker digest;
- rejects bounded-class approval in the same record;
- rejects Level2+, score-axis, benchmark/SOTA, semantic-correctness,
  production-readiness, full-security, and authority claims.
