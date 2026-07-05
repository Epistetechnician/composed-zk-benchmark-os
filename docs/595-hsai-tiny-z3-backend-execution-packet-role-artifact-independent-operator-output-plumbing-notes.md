# Phase 595 HSAI Tiny Z3 Backend Execution Packet Role Artifact Independent Operator Output Plumbing Notes

State slice: `Phase 595 HSAI tiny Z3 backend execution packet role artifact independent-operator output plumbing`.

Phase 595 implements the local output-root plumbing authorized by Phase 594.
It writes and reads back one caller-owned quarantined local packet-role
artifact independent-operator bundle from one exact Phase 593 output metadata
record.

## Implemented Surface

Phase 595 adds typed local plumbing to `hsai-agent-admission`:

- `GatewayFormalTinyZ3PacketRoleArtifactIndependentOperatorOutputPlumbingRequest`;
- `GatewayFormalTinyZ3PacketRoleArtifactIndependentOperatorOutputPlumbingManifest`;
- `GatewayFormalTinyZ3PacketRoleArtifactIndependentOperatorOutputPlumbingReadback`;
- `GatewayFormalTinyZ3PacketRoleArtifactIndependentOperatorOutputPlumbingError`;
- `materialize_gateway_formal_tiny_z3_packet_role_artifact_independent_operator_output_bundle`;
- `read_gateway_formal_tiny_z3_packet_role_artifact_independent_operator_output_bundle`.

The implementation accepts only an exact Phase 593
`PacketRoleArtifactIndependentOperatorOutputMissing` metadata record. It
requires nonzero digest bindings through Phase 593, Phase 591, Phase 589,
Phase 587, Phase 585, and the inherited backend-execution source chain.

## Local Bundle Shape

The only written namespace is:

```text
packet-role-artifact-independent-operator-packet/
```

The declared JSON files are:

- `operator-identity.json`;
- `operator-statement.json`;
- `environment-declaration.json`;
- `captured-output-summary.json`;
- `redaction-report.json`;
- `replay-correspondence.json`;
- `import-ownership.json`;
- `manifest.json`.

Every declared JSON file receives one `.sha256` sidecar computed from the
exact serialized bytes. Readback rejects missing files, stale sidecars,
undeclared files, symlinked files, malformed JSON, retained secrets, raw log
retention, positive proof/checker/solver promotion, Level2 promotion, and score
axis population.

## Local Classification

Successful readback classifies the bundle as:

```text
PacketRoleArtifactIndependentOperatorOutputQuarantinedLocalBundle
```

This classification means the local files passed the Phase 595 bundle contract.
It is not an import candidate, not accepted evidence, not accepted independent
external reproduction, and not accepted formal evidence.

## Validation Coverage

The focused Phase 595 tests cover:

- valid local materialization and deterministic readback;
- protected output-root rejection;
- Phase 593 source-state drift rejection;
- stale sidecar rejection;
- undeclared-file rejection;
- retained-secret rejection;
- Unix sidecar symlink rejection.

## Meaning

The correct statement is:

```text
HSAI can locally materialize and read back a quarantined packet-role artifact
independent-operator output bundle from exact Phase 593 metadata.
```

It does not justify:

```text
HSAI imported external result evidence.
HSAI accepted independent external reproduction.
HSAI accepted formal evidence.
HSAI has Level2+ evidence.
HSAI populated score axes.
HSAI ran Lean, COBALT, Rust-to-Lean, or another SMT/Z3 backend.
HSAI is SOTA.
HSAI is fully secure.
HSAI proves semantic correctness.
HSAI is production ready.
```
