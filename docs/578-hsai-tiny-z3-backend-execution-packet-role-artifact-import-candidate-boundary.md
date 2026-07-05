# Phase 578 HSAI Tiny Z3 Backend Execution Packet Role Artifact Import Candidate Boundary

State slice: `Phase 578 HSAI tiny Z3 backend execution packet role artifact import-candidate boundary`.

Phase 578 defines the docs-first boundary for a future import-candidate
metadata step over a Phase 577 quarantined local packet role artifact bundle.
It does not implement import-candidate code, import external results, mutate
the accepted Evidence Ledger, accept independent external reproduction, or
advance to Level2+ evidence.

## Current Input

The only allowed source is one exact Phase 577 packet role artifact output
plumbing readback whose manifest classification is:

```text
PacketRoleArtifactOutputQuarantinedLocalBundle
```

That readback must bind:

- the exact Phase 575 packet role artifact output metadata;
- the exact Phase 573 materialization metadata;
- Phase 571 packet metadata;
- Phase 569 independent-reproduction requirement metadata;
- Phase 567 policy-resolution metadata;
- Phase 565 accepted-result eligibility metadata;
- Phase 563 review metadata;
- Phase 561 quarantined candidate metadata;
- Phase 559 capture metadata;
- Phase 557 handoff packet metadata;
- Phase 555 manual handoff metadata;
- inherited backend-execution digests from Phase 553/551/549/547/545/543/541
  /535/533/531/529/527.

## Future Import Candidate Scope

A future implementation may create local import-candidate metadata only. It may
define:

- an import-candidate input record;
- a deterministic candidate digest over the Phase 577 readback manifest;
- declared artifact references for the local packet role bundle manifest;
- quarantine metadata;
- local validation metadata;
- policy and nonpromotion digests;
- a candidate status that remains quarantined;
- a bounded label indicating the bundle is ready for later review, not
  accepted evidence.

The future implementation must not append to the accepted Evidence Ledger and
must not treat the local bundle as an accepted external result.

## Required Future Validation

A future implementation must fail closed unless:

- the Phase 577 manifest schema and state slice are exact;
- the Phase 577 classification is
  `PacketRoleArtifactOutputQuarantinedLocalBundle`;
- every declared JSON file and `.sha256` sidecar was read back and validated;
- the Phase 577 readback digest recomputes from exact manifest fields;
- no undeclared files, symlinks, stale sidecars, secrets, raw logs, raw provider
  bodies, proof artifacts, checker transcripts, solver certificates, Level2
  artifacts, score-axis artifacts, benchmark artifacts, or production
  artifacts are present;
- the Phase 575 source metadata remains exact and unpromoted;
- all inherited Phase 573/571/569/567/565/563/561/559/557/555 and backend
  execution digest bindings are nonzero and unchanged;
- the candidate maps to local quarantine only.

## Future Candidate Classification

A future implementation may use classifications such as:

- `PacketRoleArtifactImportCandidateRejected`;
- `PacketRoleArtifactImportCandidateQuarantinedLocalBundle`;
- `PacketRoleArtifactImportCandidateReadyForReviewBoundary`.

The strongest classification this boundary can authorize is:

```text
PacketRoleArtifactImportCandidateQuarantinedLocalBundle
```

`PacketRoleArtifactImportCandidateReadyForReviewBoundary` requires a later
review boundary. Accepted evidence requires a later reviewed acceptance policy
and an accepted-ledger append path.

## Forbidden In This Phase

Phase 578 does not permit:

- Rust implementation code;
- Cargo metadata changes;
- new dependencies;
- binaries or scripts;
- import-candidate implementation;
- new output-root reads or writes;
- filesystem artifact writes;
- external-result import;
- accepted-evidence artifact writes;
- accepted Evidence Ledger mutation;
- external replay execution;
- backend execution;
- Lean, SMT/Z3, COBALT, Rust-to-Lean, Aeneas, Hax, Coq, TLA+, CBMC, or
  model-checker execution;
- proof artifact generation or promotion;
- checker transcript generation or promotion;
- solver certificate generation or promotion;
- accepted external result evidence;
- accepted independent external reproduction;
- accepted formal evidence;
- Level2+ evidence;
- score-axis population;
- benchmark submission;
- production deployment;
- external-audit claims;
- semantic-correctness claims;
- production-readiness claims;
- SOTA or breakthrough claims;
- full-security claims;
- authority to execute an action.

## Future Phase 579 Exit Criteria

A future Phase 579 may implement import-candidate metadata only if it:

- accepts exactly one Phase 577 readback;
- validates all Phase 577, Phase 575, Phase 573, Phase 571, Phase 569, Phase
  567, Phase 565, Phase 563, Phase 561, Phase 559, Phase 557, Phase 555, and
  inherited backend-execution digest bindings;
- rejects any malformed or promoted Phase 577 manifest;
- maps the local bundle to a quarantined local import candidate;
- records deterministic candidate, validation, quarantine, policy, and
  nonpromotion digests;
- does not import external results;
- does not mutate the accepted Evidence Ledger;
- does not create accepted external result evidence, accepted independent
  reproduction, accepted formal evidence, Level2+ evidence, or score axes;
- does not run Lean, COBALT, Rust-to-Lean, another SMT/Z3 backend, or a
  benchmark;
- adds focused tests for successful quarantined candidate metadata, Phase 577
  drift rejection, readback-digest drift rejection, nondeclared/promoted
  artifact rejection, accepted-ledger mutation rejection, and strong-claim
  rejection.

## Meaning

Phase 578 moves the path forward by defining how a local packet role artifact
bundle can later become a quarantined import candidate.

The correct statement is:

```text
HSAI has a local packet role artifact bundle and a documented boundary for
future quarantined import-candidate metadata.
```

It does not justify:

```text
HSAI imported an external result.
HSAI accepted external result evidence.
HSAI accepted independent external reproduction.
HSAI has Level2+ evidence.
HSAI has accepted formal evidence.
HSAI populated score axes.
HSAI ran Lean, COBALT, Rust-to-Lean, or another SMT/Z3 backend in this phase.
HSAI is SOTA.
HSAI is fully secure.
HSAI proves semantic correctness.
HSAI is production ready.
```
