# Phase R Audit Index Output Implementation Notes

Status: implemented for adjacent local output plumbing.

This note records the Phase R implementation slice following the docs-first
boundary in `docs/75-phase-r-audit-index-output-plumbing-spec.md`.

## State Slice

This implementation is limited to:

- `crates/zkbench-core/src/audit_index.rs`
- public exports from `crates/zkbench-core/src/lib.rs`
- `crates/zkbench-core/tests/phase_r_audit_index.rs`
- documentation and navigation updates under `docs/`, `README.md`, and
  `AGENTS.md`

It adds adjacent local output plumbing for a caller-selected `audit-index/`
root only. It does not add command-line tools, UI dashboards, browser apps,
JavaScript or TypeScript runtime files, package metadata, replay-command
execution, external replay, live backend execution, external repo clones,
vendored source, external result import, generated benchmark artifacts,
accepted Evidence Ledger mutation, official benchmark evidence, ZK backend
performance claims, Level2+ evidence, source pack mutation, source report
mutation, or report-bundle mutation.

## Implemented Surface

The Rust implementation adds:

- `AUDIT_INDEX_MANIFEST_PATH`
- `AUDIT_INDEX_MANIFEST_DIGEST_PATH`
- `LocalAuditIndexOutput`
- `write_local_audit_index_outputs`
- `read_local_audit_index_outputs`

The writer materializes exactly:

```text
audit-index/
  audit-index-manifest.json
  digests/
    audit-index-manifest.sha256
```

The reader validates exactly that local output shape and returns
`LocalAuditIndexOutput`. Both APIs preserve `Level0DesignNote` as the output
claim boundary.

## File Integrity

The manifest JSON is serialized with the existing pretty JSON helper. The
digest sidecar stores the SHA-256 hex digest over the materialized manifest JSON
bytes. A read fails if the sidecar is missing, non-UTF-8, stale, malformed by
digest mismatch, or inconsistent with the materialized manifest bytes.

Overwrite is opt-in. An overwrite of an existing audit-index root is allowed
only when the existing root contains no unexpected files or symlinks, the
existing output validates, and the existing manifest equals the supplied
manifest.

## Validation Rules

The output plumbing fails closed when:

- the supplied `LocalAuditIndexManifest` is invalid;
- the output root is an existing file;
- the output root contains parent-directory components, URL-like content,
  backslashes, or shell-like fragments;
- the output root is non-empty and overwrite is not explicitly approved;
- existing output bytes drift from the supplied manifest;
- any unexpected file exists below the audit-index root;
- any symlink exists below the audit-index root;
- manifest JSON bytes do not match the digest sidecar;
- the materialized manifest hides failed readiness or local-only warnings;
- the materialized manifest claims official benchmark evidence, ZK backend
  performance, Level2+ evidence, accepted Evidence Ledger mutation, source
  mutation, replay-command execution output, external replay, or score-axis
  population from local-only metadata.

## Claim Boundary

The maximum output boundary is `Level0DesignNote`.

Audit-index output files are local integrity summaries only. They are not
accepted evidence, not official benchmark evidence, not benchmark outputs, not
backend performance evidence, not Level2+ evidence, and not proof.

## Verification

Focused regression coverage lives in
`crates/zkbench-core/tests/phase_r_audit_index.rs` and checks:

- write/read round trip for the two authorized output files;
- source-file immutability while writing adjacent audit-index output;
- invalid manifest rejection before writing;
- unsafe output-root rejection;
- non-overwrite and overwrite-drift rejection;
- stale digest and tampered manifest rejection;
- unexpected-file rejection on read and overwrite;
- symlink rejection on read and overwrite;
- source scan for external execution hooks.
