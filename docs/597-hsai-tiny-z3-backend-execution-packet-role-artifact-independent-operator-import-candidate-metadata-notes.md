# Phase 597 HSAI Tiny Z3 Backend Execution Packet Role Artifact Independent Operator Import Candidate Metadata

State slice: `Phase 597 HSAI tiny Z3 backend execution packet role artifact independent-operator import-candidate metadata`.

Phase 597 implements local import-candidate metadata over one exact Phase 595
packet-role artifact independent-operator output plumbing readback. It maps the
local bundle to a quarantined zkbench-core `ExternalResultCandidate` and records
deterministic candidate, validation, quarantine, policy, blocker, and
nonpromotion digests.

## Implemented Surface

Phase 597 adds:

- `GATEWAY_FORMAL_TINY_Z3_PACKET_ROLE_ARTIFACT_INDEPENDENT_OPERATOR_IMPORT_CANDIDATE_*` constants;
- independent-operator import-candidate input, output, issue, validation,
  classification, and label types;
- deterministic digest, id, and label bindings over the Phase 595 readback;
- a zkbench-core `ExternalResultCandidate` construction path that remains
  `ExternalResultStatus::Quarantined`;
- validation against `validate_external_result_candidate` and
  `external_result_quarantine_record`;
- policy, blocker, nonpromotion, rule, forbidden-API, and inherited-digest
  digests;
- fail-closed Phase 595 source-state checks for schema, state slice,
  classification, declared files, sidecars, readback digest, Phase 593/591/589
  /587/585 digests, and all no-promotion booleans;
- focused tests for successful quarantined metadata, Phase 595 drift rejection,
  readback-digest drift rejection, and promotion/strong-claim rejection.

## Accepted Input

The only accepted input is one in-memory Phase 595 readback whose manifest:

- uses the exact Phase 595 schema and state slice;
- is classified as
  `PacketRoleArtifactIndependentOperatorOutputQuarantinedLocalBundle`;
- recomputes its Phase 595 readback digest;
- contains the exact declared packet-role artifact independent-operator files
  and sidecars;
- binds nonzero Phase 593/591/589/587/585 digests;
- keeps every accepted-evidence, Level2+, score-axis, proof, checker, solver,
  Lean, COBALT, Rust-to-Lean, backend-execution, benchmark, production, SOTA,
  full-security, and authority flag false.

Phase 597 records the older Phase 583/581/579/577/575/573/571/569/567/565
/563/561/559/557/555 chain as inherited transitive requirements because those
fields are bound through the Phase 593 output digest rather than repeated in
the Phase 595 readback manifest.

## Current Meaning

The correct claim is:

```text
HSAI can map one validated local Phase 595 packet-role artifact
independent-operator bundle into a quarantined local import-candidate metadata
record.
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

The next phase should be a docs-first review boundary over the Phase 597
quarantined independent-operator import candidate. Accepted evidence still
requires a later reviewed acceptance policy and a separate accepted-ledger
append path.
