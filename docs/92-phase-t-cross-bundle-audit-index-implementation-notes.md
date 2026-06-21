# Phase T Cross-Bundle Audit Index Implementation Notes

Status: complete for in-memory implementation.

This phase implements the in-memory cross-bundle audit-index planning surface
described in `docs/91-phase-t-cross-bundle-audit-index-boundary-spec.md`. The
view is local presentation metadata over two or more supplied valid
`LocalAuditIndexManifest` values. It is not accepted evidence, not official
benchmark evidence, not ZK backend performance evidence, not Level2+ evidence,
and not proof.

## State Slice

This phase changes only:

- `crates/zkbench-core/src/audit_index.rs`
- `crates/zkbench-core/src/lib.rs`
- `crates/zkbench-core/tests/phase_t_cross_bundle_audit_index.rs`
- `docs/92-phase-t-cross-bundle-audit-index-implementation-notes.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`

No generated cross-bundle output, benchmark artifact, local replay result,
report bundle, audit-index output, Phase S ergonomics output, Evidence Record,
Score Report, accepted Evidence Ledger, package runtime file, command-line tool,
or UI artifact is added.

## Implemented Surface

`zkbench-core` now exposes:

- `LocalAuditIndexCrossBundleInput`
- `LocalAuditIndexCrossBundleRequest`
- `LocalAuditIndexCrossBundleGroupKey`
- `LocalAuditIndexCrossBundleSortKey`
- `LocalAuditIndexCrossBundleIssueKind`
- `LocalAuditIndexCrossBundleIssue`
- `LocalAuditIndexCrossBundleValidation`
- `LocalAuditIndexCrossBundleSignalKind`
- `LocalAuditIndexCrossBundleSignal`
- `LocalAuditIndexCrossBundleSourceSummary`
- `LocalAuditIndexCrossBundleGroupSummary`
- `LocalAuditIndexCrossBundleWarningSummary`
- `LocalAuditIndexCrossBundleView`
- `required_local_audit_index_cross_bundle_limitations`
- `validate_local_audit_index_cross_bundle_request`
- `build_local_audit_index_cross_bundle_view`
- `serialize_local_audit_index_cross_bundle_view_json`
- `deserialize_local_audit_index_cross_bundle_view_json`

The builder accepts supplied manifests only. It validates every source manifest
with the existing Phase R validator before deriving any cross-bundle metadata.
It computes deterministic source manifest digests, deterministic groups,
duplicate/conflict signals, warning summaries, required limitation labels, and
deterministic Markdown.

## Failure Behavior

The implementation fails closed for:

- fewer than two source manifests;
- empty source ids;
- source ids with path, URL, shell, wildcard, or expression syntax;
- duplicate source ids;
- invalid source `LocalAuditIndexManifest` values;
- source manifest digest computation failure.

The implementation records local audit signals for:

- duplicate manifest ids with identical digests;
- duplicate manifest ids with conflicting digests;
- duplicate input ids with identical artifact refs;
- duplicate input ids with conflicting artifact refs;
- repeated failed-readiness state;
- hidden local-only warnings;
- input claim-boundary ceiling mismatch;
- limitation-label mismatch.

Signals are local planning warnings only. They do not repair source manifests,
drop inputs, mutate source metadata, create accepted evidence, or raise claim
boundaries.

## Tests

Focused coverage lives in
`crates/zkbench-core/tests/phase_t_cross_bundle_audit_index.rs`.

It verifies:

- deterministic cross-bundle view construction;
- required limitation-label preservation;
- `Level0DesignNote` output cap;
- duplicate input id with same artifact signal;
- duplicate input id with conflicting artifact signal;
- duplicate manifest id with identical digest signal;
- duplicate manifest id with conflicting digest signal;
- repeated failed-readiness signal;
- input claim-boundary ceiling mismatch signal;
- request rejection for too few manifests;
- unsafe source-id rejection;
- invalid manifest rejection;
- JSON round trip;
- source scan proving no Phase T writer/reader API, output constants, process
  execution hooks, or network hooks were added.

Validation run:

```sh
cargo fmt --all --check
cargo test -p zkbench-core --test phase_t_cross_bundle_audit_index
```

## Non-Claims

Cross-bundle audit-index views are local presentation metadata only.

Cross-bundle audit-index views are not accepted evidence.

Cross-bundle audit-index views are not official benchmark evidence.

Cross-bundle audit-index views do not create Level2+ evidence.

Cross-bundle audit-index views do not prove ZK backend performance.

Duplicate local metadata is an audit signal, not independent confirmation.

Phase T does not add materialized output-root plumbing. Any future output-root
work requires its own docs-first boundary before implementation.
