# Phase T Cross-Bundle Audit Index Output Implementation Notes

Status: complete for local output-root implementation.

This phase implements the materialized output-root surface authorized by
`docs/93-phase-t-cross-bundle-audit-index-output-plumbing-spec.md`. The output
is local presentation metadata over an already-valid
`LocalAuditIndexCrossBundleRequest` and deterministically rederived
`LocalAuditIndexCrossBundleView`. It is not accepted evidence, not official
benchmark evidence, not ZK backend performance evidence, not Level2+ evidence,
and not proof.

## State Slice

This phase changes only:

- `crates/zkbench-core/src/audit_index.rs`
- `crates/zkbench-core/src/lib.rs`
- `crates/zkbench-core/tests/phase_t_cross_bundle_audit_index.rs`
- `docs/94-phase-t-cross-bundle-audit-index-output-implementation-notes.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`

No generated cross-bundle output, benchmark artifact, local replay result,
report bundle, audit-index output, Phase S ergonomics output, Evidence Record,
Score Report, accepted Evidence Ledger, package runtime file, command-line tool,
or UI artifact is added.

## Implemented Surface

`zkbench-core` now exposes:

- `AUDIT_INDEX_CROSS_BUNDLE_VIEW_PATH`
- `AUDIT_INDEX_CROSS_BUNDLE_MARKDOWN_PATH`
- `AUDIT_INDEX_CROSS_BUNDLE_VIEW_DIGEST_PATH`
- `AUDIT_INDEX_CROSS_BUNDLE_MARKDOWN_DIGEST_PATH`
- `LocalAuditIndexCrossBundleOutput`
- `write_local_audit_index_cross_bundle_outputs`
- `read_local_audit_index_cross_bundle_outputs`

The writer materializes exactly:

```text
cross-bundle-audit-index/
  cross-bundle-view.json
  rendered/cross-bundle-view.md
  digests/cross-bundle-view-json.sha256
  digests/cross-bundle-view-markdown.sha256
```

The reader verifies declared-file-only layout, SHA-256 digest sidecars,
canonical view JSON, Markdown byte equality, request validation, deterministic
view rederivation, required limitation labels, and `Level0DesignNote` output
claim boundary.

## Failure Behavior

The implementation fails closed for:

- invalid output roots;
- protected-path overlap before writes;
- symlink-resolved protected-path overlap before writes;
- output roots that are existing files;
- non-empty output roots without explicit overwrite;
- unexpected files;
- symlinks;
- partial bundles;
- stale JSON or Markdown digest sidecars;
- materialized Markdown drift;
- invalid source manifests or requests;
- supplied views that do not match deterministic request derivation;
- missing required limitation labels;
- claim-boundary escalation above `Level0DesignNote`.

Explicit overwrite is not a repair path. When existing files are present, the
writer first reads and validates the complete existing bundle against the same
request and supplied view. Corrupted roots remain rejected.

## Tests

Focused coverage lives in
`crates/zkbench-core/tests/phase_t_cross_bundle_audit_index.rs`.

It verifies:

- declared-file write/read round trip;
- canonical JSON and Markdown byte matching;
- source request and view deterministic rederivation;
- invalid request rejection;
- invalid, drifted, claim-elevated, and limitation-incomplete view rejection;
- non-overwrite rejection;
- explicit overwrite refusing materialized drift;
- stale JSON digest rejection;
- partial-bundle rejection;
- unexpected-file rejection;
- protected-path overlap rejection before writes;
- relative/absolute protected-path overlap equivalence;
- symlink-resolved protected-path overlap rejection;
- symlink rejection;
- source immutability;
- duplicate/conflict signal preservation through the existing Phase T view
  tests;
- source scan proving no process, network, package-runtime, or external hooks
  were added.

Validation run:

```sh
cargo fmt --all --check
cargo test -p zkbench-core --test phase_t_cross_bundle_audit_index
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
git diff --check
```

## Non-Claims

Materialized cross-bundle audit-index output is local presentation metadata
only.

Materialized cross-bundle audit-index output is not accepted evidence.

Materialized cross-bundle audit-index output is not official benchmark
evidence.

Materialized cross-bundle audit-index output does not create Level2+ evidence.

Materialized cross-bundle audit-index output does not prove ZK backend
performance.

Duplicate local metadata is an audit signal, not independent confirmation.
