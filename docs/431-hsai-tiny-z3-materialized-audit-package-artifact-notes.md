# Phase 431 HSAI Tiny Z3 Materialized Audit Package Artifact Notes

State slice: `Phase 431 HSAI tiny Z3 materialized audit package artifact plumbing`.

## Summary

Phase 431 implements local materialized artifact plumbing for one Phase 429
tiny-Z3 serialization-preview review. The implementation writes only a declared
digest-bound metadata package under a caller-selected output root:

- `tiny-z3-audit-package/manifest.json`
- `tiny-z3-audit-package/review.json`
- `tiny-z3-audit-package/serialization-preview.json`
- `tiny-z3-audit-package/nonclaims.json`
- `tiny-z3-audit-package/claim-boundary.txt`
- `tiny-z3-audit-package/digests.json`

Each declared file receives a `.sha256` sidecar. Read-back validation rejects
undeclared files, stale sidecars, symlinks, malformed declared JSON, mismatched
manifest semantics, nonclaim drift, and promotion attempts.

## Implemented Surface

The Phase 431 code is contained in
`crates/hsai-agent-admission/src/lib.rs` and adds:

- Phase 431 schema, state-slice, and claim-boundary constants.
- `GatewayFormalTinyDigestBackendZ3AuditPackageArtifactOutputRequest`.
- `GatewayFormalTinyDigestBackendZ3AuditPackageArtifactManifest`.
- `GatewayFormalTinyDigestBackendZ3AuditPackageArtifactOutputError`.
- Declared file and sidecar helpers.
- `materialize_gateway_formal_tiny_digest_backend_z3_audit_package_artifact`.
- `read_gateway_formal_tiny_digest_backend_z3_audit_package_artifact`.

The manifest binds the Phase 429 review digest, Phase 427 serialization-preview
digest, Phase 425 package digest, Phase 423 review-record digest, Phase 421
metadata digest, Phase 404/405 local Z3 replay digests, accepted append blocker
digest, package manifest digest, serialization digests, redaction-policy digest,
logical preview path digest, declared file digests, claim boundary, and explicit
nonclaims.

## Tests

Focused Phase 431 tests cover:

- successful materialization and read-back;
- stale digest rejection;
- undeclared file rejection;
- promotion rejection before writing the output root.

## Claim Boundary

This phase creates local filesystem regression evidence only. It does not create
accepted formal evidence, mutate the accepted Evidence Ledger, change accepted
append policy, create Level2+ evidence, populate score axes, generate or promote
proof artifacts, promote checker transcripts, promote solver certificates, run
Lean, run SMT beyond the already-scoped local tiny-Z3 replay path, run COBALT,
run Rust-to-Lean extraction, submit benchmarks, prove semantic correctness,
establish production readiness, establish SOTA, establish breakthrough status,
establish full security, or grant authority to execute an action.
