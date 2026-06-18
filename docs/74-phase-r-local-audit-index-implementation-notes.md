# Phase R Local Audit Index Implementation Notes

Status: implemented for inert in-memory metadata only.

This note records the Phase R implementation slice following the docs-first
boundary in `docs/73-phase-r-local-audit-index-boundary-spec.md`.

## State Slice

This implementation is limited to:

- `crates/zkbench-core/src/audit_index.rs`
- public exports from `crates/zkbench-core/src/lib.rs`
- `crates/zkbench-core/tests/phase_r_audit_index.rs`
- documentation and navigation updates under `docs/`, `README.md`, and
  `AGENTS.md`

It does not add audit-index file output, writer APIs, reader APIs, command-line
tools, UI dashboards, JavaScript or TypeScript runtime files, package metadata,
external replay, live backend execution, external result import, generated
benchmark artifacts, accepted Evidence Ledger mutation, official benchmark
evidence, ZK backend performance claims, Level2+ evidence, source pack mutation,
source report mutation, or report-bundle mutation.

## Implemented Surface

The Rust implementation adds:

- `LocalAuditIndexVersion`
- `LocalAuditIndexInputKind`
- `LocalAuditIndexInputRef`
- `LocalAuditIndexManifest`
- `LocalAuditIndexValidation`
- `LocalAuditIndexValidationIssue`
- `LocalAuditIndexValidationIssueKind`
- `build_local_audit_index_manifest_from_report_bundles`
- `compute_local_audit_index_manifest_digest`
- JSON serialization and deserialization helpers
- `validate_local_audit_index_manifest`

The builder consumes existing `ReportBundleManifest` metadata and constructs an
in-memory local audit-index manifest. It records report-bundle manifests,
manifest digest sidecars, source metadata refs, and rendered Markdown refs as
digest-bound local inputs. It does not read or write filesystem output.

## Validation Rules

Validation fails closed when:

- required identity fields are empty;
- inputs are missing;
- input ids or artifact URIs collide;
- artifact refs are absolute, path-traversing, URL-like, backslash-containing,
  or shell-like;
- digests are not SHA-256, are not 64 hex characters, or have zero byte length;
- source refs point at missing input ids;
- any input claim boundary exceeds `Level1LocalReplay`;
- the output claim boundary is not `Level0DesignNote`;
- failed readiness is hidden;
- report-bundle local-only warnings are hidden;
- source pack, source report, or report-bundle mutation is claimed;
- replay-command execution output is included;
- external replay is authorized or claimed;
- Level2+ evidence, official benchmark evidence, or ZK backend performance is
  claimed;
- accepted Evidence Ledger mutation is claimed;
- score axes are populated from local-only metadata;
- required limitation labels are missing.

## Claim Boundary

The maximum output boundary is `Level0DesignNote`.

Audit-index manifests are local integrity summaries only. They are not accepted
evidence, not official benchmark evidence, not benchmark outputs, not backend
performance evidence, not Level2+ evidence, and not proof.

## Verification

Focused regression coverage lives in
`crates/zkbench-core/tests/phase_r_audit_index.rs` and checks:

- valid construction from existing report-bundle metadata;
- deterministic JSON round trip and digesting;
- claim-boundary and forbidden-claim rejection;
- source mutation claim rejection;
- unsafe refs, malformed digests, and missing source refs;
- hidden failed-readiness rejection;
- hidden local-only warning rejection;
- source scan for output writer and execution hooks.
