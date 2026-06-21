# Phase S Audit Index Ergonomics Implementation Notes

Status: complete for in-memory single-index ergonomics only.

This phase implements the code surface authorized after
`docs/86-phase-s-audit-index-ergonomics-boundary-spec.md`. The implementation is
local presentation metadata over one valid `LocalAuditIndexManifest`. It does not
write files, execute replay commands, call external services, construct
cross-bundle audit indexes, mutate source packs, mutate source reports, mutate
report bundles, mutate audit-index outputs, populate score axes, or create
accepted, official, backend-performance, or Level2+ evidence.

## State Slice

This phase changes only:

- `crates/zkbench-core/src/audit_index.rs`
- `crates/zkbench-core/src/lib.rs`
- `crates/zkbench-core/tests/phase_s_audit_index_ergonomics.rs`
- `docs/87-phase-s-audit-index-ergonomics-implementation-notes.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`

No generated benchmark artifact, local replay result, report bundle, audit-index
output file, Evidence Record, Score Report, accepted Evidence Ledger, package
runtime file, command-line tool, or UI artifact is added.

## Implemented Utilities

- `LocalAuditIndexErgonomicsRequest`
- `LocalAuditIndexErgonomicsFilter`
- `LocalAuditIndexErgonomicsFilterField`
- `LocalAuditIndexErgonomicsGroupKey`
- `LocalAuditIndexErgonomicsSortKey`
- `LocalAuditIndexErgonomicsValidation`
- `LocalAuditIndexErgonomicsIssue`
- `LocalAuditIndexErgonomicsIssueKind`
- `LocalAuditIndexErgonomicsGroupSummary`
- `LocalAuditIndexErgonomicsWarningSummary`
- `LocalAuditIndexErgonomicsView`
- `required_local_audit_index_ergonomics_limitations`
- `validate_local_audit_index_ergonomics_request`
- `build_local_audit_index_ergonomics_view`

The builder accepts one existing `LocalAuditIndexManifest` and one request. It
first runs the existing audit-index manifest validator, then validates exact
filters before deriving selected input ids, group summaries, warning summaries,
required limitation labels, and deterministic Markdown. Successful views remain
`Level0DesignNote`.

## Validation Rules

The request validator fails closed when:

- the supplied audit-index manifest is invalid;
- filter values contain path traversal, slashes, URL-like content, shell-like
  payloads, wildcard markers, or expression-like syntax;
- boolean filter values are not exactly `true` or `false`.

The typed request API restricts fields, sort keys, and group keys to the
manifest-field set authorized by Phase S. Unknown field names cannot be expressed
through the Rust API and malformed serialized variants are rejected by serde.

The view repeats these required limitation labels:

- Audit-index ergonomics are not accepted evidence.
- Audit-index ergonomics are local presentation metadata only.
- Audit-index ergonomics do not create official benchmark evidence.
- Audit-index ergonomics do not create Level2+ evidence.
- Audit-index ergonomics do not prove backend performance.
- Local replay artifacts are not official benchmark evidence.
- Internal timing telemetry is not ZK backend performance.

## Tests

Focused coverage lives in
`crates/zkbench-core/tests/phase_s_audit_index_ergonomics.rs`.

It verifies:

- filtered, grouped, sorted in-memory view construction;
- deterministic Markdown with required limitation labels;
- fail-closed unsafe filter values;
- fail-closed invalid boolean filters;
- fail-closed invalid source manifests, including hidden failed-readiness state
  and source-mutation flags through the existing audit-index validator;
- no Phase S runtime surface for read/write ergonomics outputs or external
  execution hooks.

Validation run:

```sh
cargo test -p zkbench-core --test phase_s_audit_index_ergonomics
cargo test -p zkbench-core --test phase_r_audit_index
```

## Non-Claims

Audit-index ergonomics are not accepted evidence.

Audit-index ergonomics are local presentation metadata only.

Audit-index ergonomics do not create official benchmark evidence.

Audit-index ergonomics do not create Level2+ evidence.

Audit-index ergonomics do not prove backend performance.

Local replay artifacts are not official benchmark evidence.

Internal timing telemetry is not ZK backend performance.
