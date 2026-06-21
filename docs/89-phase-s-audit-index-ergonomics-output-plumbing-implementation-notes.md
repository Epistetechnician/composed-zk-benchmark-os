# Phase S Audit Index Ergonomics Output Plumbing Implementation Notes

Status: complete for local output-root plumbing.

This phase implements the local materialized ergonomics output surface described
in `docs/88-phase-s-audit-index-ergonomics-output-plumbing-spec.md`. The output
is local presentation metadata over one valid `LocalAuditIndexManifest`, one
valid `LocalAuditIndexErgonomicsRequest`, and one deterministic
`LocalAuditIndexErgonomicsView`. It is not accepted evidence, not official
benchmark evidence, not ZK backend performance evidence, and not Level2+
evidence.

## State Slice

This phase changes only:

- `crates/zkbench-core/src/audit_index.rs`
- `crates/zkbench-core/src/lib.rs`
- `crates/zkbench-core/tests/phase_s_audit_index_ergonomics.rs`
- `docs/89-phase-s-audit-index-ergonomics-output-plumbing-implementation-notes.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`

No generated ergonomics output, benchmark artifact, local replay result, report
bundle, audit-index output, Evidence Record, Score Report, accepted Evidence
Ledger, package runtime file, command-line tool, or UI artifact is added.

## Implemented Surface

`zkbench-core` now exposes:

- `AUDIT_INDEX_ERGONOMICS_VIEW_PATH`
- `AUDIT_INDEX_ERGONOMICS_MARKDOWN_PATH`
- `AUDIT_INDEX_ERGONOMICS_VIEW_DIGEST_PATH`
- `AUDIT_INDEX_ERGONOMICS_MARKDOWN_DIGEST_PATH`
- `LocalAuditIndexErgonomicsOutput`
- `serialize_local_audit_index_ergonomics_view_json`
- `deserialize_local_audit_index_ergonomics_view_json`
- `write_local_audit_index_ergonomics_outputs`
- `read_local_audit_index_ergonomics_outputs`

The materialized output shape is exactly:

```text
audit-index-ergonomics/
  ergonomics-view.json
  rendered/
    ergonomics-view.md
  digests/
    ergonomics-view-json.sha256
    ergonomics-view-markdown.sha256
```

The writer validates the source manifest/request, rederives the supplied view,
checks claim-boundary and limitation labels, rejects protected path overlap, and
writes only the four declared files. The reader rejects undeclared files,
symlinks, stale digest sidecars, invalid UTF-8, malformed JSON, Markdown drift,
and view drift from the supplied manifest/request.

## Failure Behavior

The output plumbing fails closed for:

- invalid source manifest or request;
- supplied view drift from deterministic source manifest/request derivation;
- output claim boundary above `Level0DesignNote`;
- missing required limitation labels in the view or rendered Markdown;
- output roots with parent-directory components, URL-like content, shell-like
  content, or protected path overlap;
- non-empty output roots without explicit overwrite;
- overwrite attempts over unexpected files, symlinks, partial bundles, stale
  digest sidecars, or materialized byte drift;
- unexpected files, symlinks, partial bundles, stale JSON digest sidecars, stale
  Markdown digest sidecars, and Markdown byte drift on read.

Explicit overwrite is not a repair operation for corrupted materialized output.
The caller must remove a corrupted local output root and write a clean bundle.

## Tests

Focused coverage lives in
`crates/zkbench-core/tests/phase_s_audit_index_ergonomics.rs`.

It verifies:

- declared-file write/read round trip;
- canonical pretty JSON and Markdown byte matching;
- source file immutability;
- invalid manifest rejection;
- deterministic view rederivation;
- claim-boundary and limitation-label rejection;
- non-overwrite rejection;
- stale JSON and Markdown digest rejection;
- partial bundle rejection;
- unexpected-file rejection;
- protected path overlap rejection;
- symlink rejection on Unix;
- source scan for no external execution hooks.

Validation run:

```sh
cargo fmt --all --check
cargo test -p zkbench-core --test phase_s_audit_index_ergonomics
cargo test -p zkbench-core --test phase_r_audit_index
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
```

## Non-Claims

Audit-index ergonomics output is local presentation metadata only.

Audit-index ergonomics output is not accepted evidence.

Audit-index ergonomics output is not official benchmark evidence.

Audit-index ergonomics output does not create Level2+ evidence.

Audit-index ergonomics output does not prove ZK backend performance.

Audit-index ergonomics output does not mutate source packs, source reports,
report bundles, audit-index outputs, or accepted Evidence Ledgers.
