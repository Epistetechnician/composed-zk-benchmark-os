# Phase 349 HSAI Audit Package Serialization Preview Metadata Notes

State slice: `Phase 349 HSAI audit package serialization preview metadata
implementation`.

Phase 349 implements deterministic pure-data serialization-preview metadata
over one Phase 347 local non-accepted audit package. The preview stores only
digests and policy metadata. It does not write filesystem artifacts, store raw
package bytes, mutate the accepted Evidence Ledger, change accepted append
policy, create accepted formal evidence, create Level2+ evidence, populate score
axes, generate proof artifacts, generate checker transcripts, generate solver
certificates, run Lean, run SMT, run COBALT, run Rust-to-Lean extraction, submit
benchmarks, claim semantic correctness, claim production readiness, claim SOTA,
claim breakthrough status, claim full security, or grant authority to execute an
action.

## Implemented Surface

The implementation is additive in `crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalRealCommandLaneLocalAuditPackageSerializationPreviewInput`;
- `GatewayFormalRealCommandLaneLocalAuditPackageSerializationPreview`;
- `GatewayFormalRealCommandLaneLocalAuditPackageSerializationPreviewIssue`;
- `GatewayFormalRealCommandLaneLocalAuditPackageSerializationPreviewValidation`;
- `gateway_formal_real_command_lane_local_audit_package_serialization_preview_claim_boundary`;
- `gateway_formal_real_command_lane_local_audit_package_serialization_preview_required_nonclaims`;
- `gateway_formal_real_command_lane_local_audit_package_serialization_preview_field_order`;
- `gateway_formal_real_command_lane_local_audit_package_serialization_preview_json_shape`;
- `build_gateway_formal_real_command_lane_local_audit_package_serialization_preview`;
- `validate_gateway_formal_real_command_lane_local_audit_package_serialization_preview_input`.

## Required Bindings

Each preview input must bind:

- one Phase 347 audit package digest;
- one Phase 347 audit package input digest;
- one Phase 345 review record digest;
- one Phase 343 local reviewed metadata digest;
- the current accepted append blocker set and digest;
- serialization profile id;
- canonical field-order digest;
- canonical JSON shape digest;
- expected package bytes digest;
- explicit nonclaims and their digest.

## Rejection Cases

Validation rejects:

- wrong schema version;
- invalid preview id;
- invalid serialization profile id;
- missing preview timestamp;
- zero required digests;
- drift from the Phase 347 package record;
- promoted or drifted Phase 347 package state;
- accepted append blocker drift;
- canonical field-order digest drift;
- canonical JSON shape digest drift;
- nonclaim drift;
- filesystem paths;
- materialized file references;
- raw package bytes;
- raw proof artifacts;
- raw checker transcripts;
- raw solver certificates;
- live backend outputs;
- benchmark outputs;
- secrets or credentials;
- mutable accepted-ledger state;
- preview summaries that claim accepted evidence, Level2+ evidence, score-axis
  evidence, proof authority, checker authority, solver-certificate authority,
  benchmark evidence, semantic correctness, production readiness, SOTA,
  breakthrough status, full security, or action authority;
- accepted evidence mutation requests;
- accepted append policy change requests;
- accepted formal evidence creation;
- Level2+ evidence creation;
- score-axis population;
- proof artifact promotion;
- checker transcript promotion;
- solver certificate promotion;
- benchmark or SOTA comparison claims;
- semantic correctness claims;
- production-readiness claims;
- SOTA claims;
- breakthrough claims;
- full-security claims;
- action-authority claims.

## Claim Boundary

The maximum claim after Phase 349 is:

HSAI can construct deterministic digest-only serialization-preview metadata for
one local non-accepted Phase 347 audit package while preserving the current
accepted formal-evidence blocker.

This is not a materialized artifact, not accepted evidence, not formal proof,
not backend execution, not a Lean/SMT/COBALT run, not Rust-to-Lean extraction
evidence, not Level2+ evidence, not score-axis evidence, not semantic
correctness, not production readiness, not SOTA, not breakthrough status, and
not full security.

## Tests

Phase 349 adds tests that:

- build deterministic serialization-preview metadata;
- verify the preview binds the Phase 347 package digest;
- verify the preview binds the Phase 345 review digest;
- reject package digest drift;
- reject filesystem paths and raw package bytes;
- reject promotional preview-summary text;
- reject accepted-evidence, Level2, score-axis, proof, checker, solver, SOTA,
  full-security, and action-authority promotion attempts.

## Next Slice

Phase 350 defines a docs-first boundary for reviewing serialization preview
metadata before any materialized artifact path is authorized. That boundary does
not write filesystem artifacts, store raw package bytes, mutate the accepted
Evidence Ledger, change accepted append policy, create accepted formal evidence,
create Level2+ evidence, populate score axes, run Lean, run SMT, run COBALT, run
Rust-to-Lean extraction, or claim semantic correctness, production readiness,
SOTA, breakthrough status, full security, or action authority.
