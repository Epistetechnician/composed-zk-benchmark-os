# Phala Operator Live Artifact Output Plumbing Implementation Notes

## Status And Claim Boundary

This slice implements local filesystem output-root plumbing for the
operator-only Phala/dstack managed-verifier artifact bundle described in
`docs/84-phala-operator-live-artifact-output-plumbing-boundary-spec.md`.

The implementation is local output plumbing only. It is not a live provider run,
not proof, not benchmark evidence, not local Intel DCAP quote verification, not
managed-service signature verification, not global software-agent uniqueness,
and not semantic correctness. Successful validation remains capped at
`Attested`.

## State Slice

This phase touched only:

```text
crates/hsai-attestation-phala/src/lib.rs
crates/hsai-attestation-phala/tests/phala_operator_live_artifact.rs
docs/85-phala-operator-live-artifact-output-plumbing-implementation-notes.md
docs/12-task-list.md
README.md
AGENTS.md
```

It did not change Cargo metadata, `Cargo.lock`, fixtures, examples, scripts,
package runtime files, generated operator artifacts, accepted Evidence Ledgers,
benchmark packs, report bundles, audit indexes, or Phase 4 registry semantics.

## Implemented Surface

`hsai-attestation-phala` now exposes:

- `PhalaOperatorLiveOutputOverwriteMode`;
- `write_phala_operator_live_artifact_output_root`;
- `read_phala_operator_live_artifact_output_root`.

The writer validates the in-memory `PhalaOperatorLiveArtifactBundle` before
writing, materializes only the six declared `operator-live/*` files, stages the
bundle under a temporary directory, reads the staged bundle through the Phase 83
validator, then publishes the local `operator-live/` directory.

The reader scans only the caller-owned output root, rejects undeclared files,
rejects symlinks, reconstructs the declared logical file map, and passes it
through `validate_phala_operator_live_artifact_files`.

## Local Failure Behavior

The output-root plumbing fails closed for:

- empty output roots;
- repository root as output root;
- non-directory output roots;
- symlink output roots;
- symlink bundle files;
- unexpected pre-existing files;
- missing required files;
- undeclared extra files;
- stale digest materialization;
- raw response body retention by default;
- invalid JSON or invalid UTF-8 in `raw-response.sha256`;
- invalid in-memory Phase 83 validation.

Overwrite is explicit through `PhalaOperatorLiveOutputOverwriteMode`. The
default `RefuseExisting` mode rejects an existing materialized bundle; replacing
an existing complete bundle requires `ReplaceExisting`.

## Tests

`crates/hsai-attestation-phala/tests/phala_operator_live_artifact.rs` now covers:

- materialized write/read round trip without live I/O;
- repository-root and empty output-root rejection;
- explicit overwrite requirement;
- partial bundle rejection;
- extra file rejection;
- stale digest rejection;
- raw response body retention rejection;
- symlink output-root rejection;
- symlink bundle-file rejection;
- `Attested`-only claim-boundary preservation.

All tests remain hermetic and require no credentials, no network, and no live
Phala provider.

## Non-Claims

- Local output plumbing is not proof.
- Local output plumbing is not benchmark evidence.
- Local output plumbing is not local DCAP verification.
- Local output plumbing is not live provider evidence.
- Local output plumbing is not managed-service signature verification.
- Local output plumbing is not global software-agent uniqueness.
- Local output plumbing is not semantic correctness.
