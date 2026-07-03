# Phase 353 HSAI Materialized Audit Package Artifact Plumbing Notes

State slice: `Phase 353 HSAI materialized audit package artifact plumbing
implementation`.

Phase 353 implements local materialized audit package artifact plumbing for one
Phase 351 serialization-preview review. The implementation writes only declared
metadata files under a caller-selected output root and verifies the package by
read-back. It does not mutate the accepted Evidence Ledger, change accepted
append policy, create accepted formal evidence, create Level2+ evidence,
populate score axes, generate proof artifacts, generate checker transcripts,
generate solver certificates, run Lean, run SMT, run COBALT, run Rust-to-Lean
extraction, submit benchmarks, claim semantic correctness, claim production
readiness, claim SOTA, claim breakthrough status, claim full security, or grant
authority to execute an action.

## Implemented Surface

The implementation is additive in `crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalRealCommandLaneLocalAuditPackageArtifactOutputRequest`;
- `GatewayFormalRealCommandLaneLocalAuditPackageArtifactManifest`;
- `GatewayFormalRealCommandLaneLocalAuditPackageArtifactOutputError`;
- `gateway_formal_real_command_lane_local_audit_package_artifact_claim_boundary`;
- `gateway_formal_real_command_lane_local_audit_package_artifact_required_nonclaims`;
- `gateway_formal_real_command_lane_local_audit_package_artifact_declared_files`;
- `gateway_formal_real_command_lane_local_audit_package_artifact_declared_sidecars`;
- `materialize_gateway_formal_real_command_lane_local_audit_package_artifact`;
- `read_gateway_formal_real_command_lane_local_audit_package_artifact`.

## Declared Files

The artifact package writes exactly these logical files:

- `audit-package/manifest.json`;
- `audit-package/review.json`;
- `audit-package/serialization-preview.json`;
- `audit-package/nonclaims.json`;
- `audit-package/claim-boundary.txt`;
- `audit-package/digests.json`.

Each declared file receives a `.sha256` sidecar. Read-back rejects stale
sidecars, missing declared files, undeclared files, symlinks, and malformed
declared files.

## Bound Inputs

The materialized manifest binds:

- one Phase 351 serialization-preview review digest;
- one Phase 351 review input digest;
- one Phase 349 serialization-preview digest;
- one Phase 349 serialization-preview input digest;
- one Phase 347 audit package digest;
- one Phase 345 review record digest;
- one Phase 343 local reviewed metadata digest;
- the current accepted append blocker digest;
- serialization profile id;
- canonical field-order digest;
- canonical JSON shape digest;
- expected package bytes digest;
- artifact profile id;
- declared files and sidecars;
- declared file digests;
- explicit nonclaims.

## Rejection Cases

Validation rejects:

- invalid package id;
- invalid artifact profile id;
- protected output roots;
- existing output roots without overwrite;
- output roots that are files or symlinks;
- bundle directory symlinks;
- declared file symlinks;
- declared sidecar symlinks;
- undeclared files;
- stale sidecar digests;
- malformed declared files;
- Phase 351 review drift;
- Phase 349 serialization-preview drift;
- manifest semantic drift;
- nonclaim drift;
- any promotion attempt in the manifest or source review.

## Claim Boundary

The maximum claim after Phase 353 is:

HSAI can locally materialize a declared digest-bound audit package for one Phase
351 serialization-preview review while preserving the accepted formal-evidence
blocker.

This is not accepted evidence, not formal proof, not backend execution, not a
Lean/SMT/COBALT run, not Rust-to-Lean extraction evidence, not Level2+ evidence,
not score-axis evidence, not semantic correctness, not production readiness, not
SOTA, not breakthrough status, and not full security.

## Tests

Phase 353 adds tests that:

- materialize and read back a valid local audit package artifact;
- verify declared files and sidecars exist;
- verify manifest digest bindings and nonpromotion flags;
- reject stale sidecar digests;
- reject undeclared files;
- reject promotion attempts before writing.

## Next Slice

Phase 354 defines a docs-first boundary for reviewing a materialized local audit
package artifact before any accepted-evidence proposal path is considered. That
boundary keeps local materialization separate from accepted formal evidence,
accepted Evidence Ledger mutation, accepted append policy changes, Level2+
evidence, score axes, Lean execution, SMT execution, COBALT execution,
Rust-to-Lean extraction, semantic correctness, production readiness, SOTA,
breakthrough status, full security, and action authority.
