# Phase 579 HSAI Tiny Z3 Backend Execution Packet Role Artifact Import Candidate Metadata

State slice: `Phase 579 HSAI tiny Z3 backend execution packet role artifact import-candidate metadata`.

Phase 579 implements local import-candidate metadata over one exact Phase 577
packet role artifact output plumbing readback. It maps the local bundle to a
quarantined zkbench-core `ExternalResultCandidate` and records deterministic
candidate, validation, quarantine, policy, blocker, and nonpromotion digests.

## Implemented Surface

Phase 579 adds:

- `GATEWAY_FORMAL_TINY_Z3_PACKET_ROLE_ARTIFACT_IMPORT_CANDIDATE_*` constants;
- import-candidate input, output, issue, validation, classification, and label
  types;
- deterministic digest, id, and label bindings over the Phase 577 readback;
- a zkbench-core `ExternalResultCandidate` construction path that remains
  `ExternalResultStatus::Quarantined`;
- validation against `validate_external_result_candidate` and
  `external_result_quarantine_record`;
- policy, blocker, nonpromotion, rule, forbidden-API, and inherited-digest
  digests;
- fail-closed Phase 577 source-state checks for schema, state slice,
  classification, declared files, sidecars, readback digest, Phase 575/573/571
  /569/567/565/563/561/559/557/555 digests, and all no-promotion booleans;
- focused tests for successful quarantined metadata, Phase 577 drift rejection,
  readback-digest drift rejection, and promotion/strong-claim rejection.

## Accepted Input

The only accepted input is one in-memory Phase 577 readback whose manifest:

- uses the exact Phase 577 schema and state slice;
- is classified as `PacketRoleArtifactOutputQuarantinedLocalBundle`;
- recomputes its Phase 577 readback digest;
- contains the exact declared packet-role files and sidecars;
- binds nonzero Phase 575/573/571/569/567/565/563/561/559/557/555 digests;
- keeps every accepted-evidence, Level2+, score-axis, proof, checker,
  solver, Lean, COBALT, Rust-to-Lean, backend-execution, benchmark,
  production, SOTA, full-security, and authority flag false.

## Current Meaning

The correct claim is:

```text
HSAI can map one validated local Phase 577 packet role artifact bundle into a
quarantined local import-candidate metadata record.
```

It does not justify:

```text
HSAI imported an external result.
HSAI accepted external result evidence.
HSAI accepted independent external reproduction.
HSAI has accepted formal evidence.
HSAI has Level2+ evidence.
HSAI populated score axes.
HSAI ran Lean, COBALT, Rust-to-Lean, or another SMT/Z3 backend in this phase.
HSAI created benchmark evidence.
HSAI is SOTA.
HSAI is fully secure.
HSAI proves semantic correctness.
HSAI is production ready.
```

## Next Responsible Boundary

The next phase should be a docs-first review boundary over the Phase 579
quarantined import candidate. Accepted evidence still requires a later reviewed
acceptance policy and a separate accepted-ledger append path.
