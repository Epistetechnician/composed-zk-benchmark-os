# Phala Operator Live Artifact Plumbing Implementation Notes

## Status And Claim Boundary

This slice implements local, in-memory operator-live artifact plumbing for the
Phala/dstack managed-verifier path. It does not perform filesystem writes,
provider HTTP, network access, credential loading, live Phala API calls,
operator live tests, local Intel DCAP verification, managed-service
signature/JWKS/JWT fetching, benchmark execution, accepted Evidence Ledger
mutation, or claims above `Attested`.

The implemented plumbing validates declared logical artifact files only:

```text
operator-live/request.json
operator-live/normalized-response.json
operator-live/trust-roots.json
operator-live/redaction-report.json
operator-live/audit.json
operator-live/raw-response.sha256
```

Validation output is local regression evidence only. It is not proof, not local
DCAP verification, not benchmark evidence, not live provider evidence, not
global software-agent uniqueness, and not semantic correctness.

## State Slice

This implementation phase may touch only:

```text
crates/hsai-attestation-phala/src/lib.rs
crates/hsai-attestation-phala/tests/phala_operator_live_artifact.rs
docs/83-phala-operator-live-artifact-plumbing-implementation-notes.md
docs/12-task-list.md
README.md
AGENTS.md
```

It must not touch Cargo metadata, `Cargo.lock`, fixtures, accepted Evidence
Ledgers, benchmark packs, report bundles, audit indexes, generated artifacts,
package runtime files, examples, scripts, or operator secrets.

## Implemented Surface

The implementation adds:

- `PhalaOperatorLiveArtifactBundle`;
- `PhalaOperatorLiveTrustRoots`;
- `PhalaOperatorLiveRedactionReport`;
- `PhalaOperatorLiveRetainedField`;
- `PhalaOperatorLiveAudit`;
- `ValidatedPhalaOperatorLiveArtifact`;
- `PhalaOperatorLiveArtifactError`;
- `parse_phala_operator_live_artifact_files`;
- `validate_phala_operator_live_artifact_bundle`;
- `validate_phala_operator_live_artifact_files`;
- `phala_operator_live_json_digest`.

The file-set parser takes an in-memory `BTreeMap<String, Vec<u8>>`. It performs
no filesystem I/O. It rejects missing files, undeclared extra files, absolute
paths, path traversal, empty path segments, and backslash-separated paths.

The bundle validator checks:

- schema versions;
- provider and mode consistency;
- `Attested` claim boundary;
- required non-claim statements;
- SHA-256 digest shape and digest equality;
- managed-verifier response validation through the existing hermetic verifier
  rules;
- trust-root consistency between `trust-roots.json` and the normalized
  response;
- redaction retained-field rationales;
- retained secret-shaped field or value rejection.

## Tests

`crates/hsai-attestation-phala/tests/phala_operator_live_artifact.rs` covers:

- valid in-memory bundle round trip;
- missing required file;
- undeclared extra file;
- path traversal rejection;
- audit digest mismatch;
- schema mismatch;
- stale normalized response rejection;
- missing trust root rejection;
- retained field without rationale;
- token-shaped retained value rejection;
- attempted claim above `Attested`;
- rejected provider verdict fail-closed behavior.

Normal workspace tests remain hermetic and require no credentials or network.

## Non-Claims

- Local artifact plumbing is not proof.
- Local artifact plumbing is not local Intel DCAP verification.
- Local artifact plumbing is not benchmark evidence.
- Local artifact plumbing is not live provider evidence.
- Local artifact plumbing is not global software-agent uniqueness.
- Local artifact plumbing is not semantic correctness.
- A validated bundle remains capped at `Attested`.
