# Phase 427 HSAI Tiny Z3 Audit Package Serialization Preview Notes

State slice: `Phase 427 HSAI tiny Z3 audit package serialization preview metadata implementation`.

Phase 427 implements deterministic pure-data serialization-preview metadata
over one Phase 425 local non-accepted tiny-Z3 audit package. The preview stores
only digests, policy metadata, an in-memory logical preview path, and explicit
nonclaims. It does not write filesystem artifacts, create package files, create
archives, mutate the accepted Evidence Ledger, change accepted append policy,
create accepted formal evidence, create Level2+ evidence, populate score axes,
generate proof artifacts, generate checker transcripts, generate solver
certificates, run Lean, run SMT, run COBALT, run Rust-to-Lean extraction, submit
benchmarks, claim semantic correctness, claim production readiness, claim SOTA,
claim breakthrough status, claim full security, or grant authority to execute an
action.

## Implemented Surface

The implementation is additive in `crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalTinyDigestBackendZ3AuditPackageSerializationPreviewInput`;
- `GatewayFormalTinyDigestBackendZ3AuditPackageSerializationPreview`;
- `GatewayFormalTinyDigestBackendZ3AuditPackageSerializationPreviewIssue`;
- `GatewayFormalTinyDigestBackendZ3AuditPackageSerializationPreviewValidation`;
- `gateway_formal_tiny_digest_backend_z3_audit_package_serialization_preview_claim_boundary`;
- `gateway_formal_tiny_digest_backend_z3_audit_package_serialization_preview_required_nonclaims`;
- `gateway_formal_tiny_digest_backend_z3_audit_package_serialization_preview_field_order`;
- `gateway_formal_tiny_digest_backend_z3_audit_package_serialization_preview_json_shape`;
- `gateway_formal_tiny_digest_backend_z3_audit_package_serialization_preview_redaction_policy`;
- `build_gateway_formal_tiny_digest_backend_z3_audit_package_serialization_preview`;
- `validate_gateway_formal_tiny_digest_backend_z3_audit_package_serialization_preview_input`.

## Required Bindings

Each preview input must bind:

- one Phase 425 audit package digest;
- one Phase 425 audit package input digest;
- one Phase 423 review digest;
- one Phase 421 metadata digest;
- one Phase 405 local Z3 output-manifest digest;
- one Phase 404 local Z3 execution digest;
- the current accepted append blocker set and digest;
- one package manifest digest;
- one serialization profile id;
- one canonical field-order digest;
- one canonical JSON-shape digest;
- one canonical JSON-payload digest;
- one redaction-policy digest;
- one portable logical preview path under `local-preview/tiny-z3/`;
- explicit nonclaims and their digest.

## Rejection Cases

Validation rejects:

- wrong schema version;
- invalid preview id;
- invalid serialization profile id;
- missing preview timestamp;
- zero required digests;
- drift from the Phase 425 audit package record;
- promoted or drifted Phase 425 package state;
- accepted append blocker drift;
- canonical field-order, JSON-shape, or JSON-payload digest drift;
- redaction-policy digest drift;
- explicit nonclaim drift;
- non-portable logical preview paths;
- filesystem-write, materialized-package, raw backend, raw proof, raw checker,
  raw solver, benchmark, secret, credential, or mutable accepted-ledger payload
  flags;
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

The maximum claim after Phase 427 is:

```text
HSAI can construct deterministic in-memory serialization-preview metadata for
one local non-accepted tiny-Z3 audit package while preserving the current
accepted formal-evidence blocker.
```

This is not a materialized artifact, not accepted evidence, not formal proof,
not backend execution, not a Lean/SMT/COBALT run, not Rust-to-Lean extraction
evidence, not Level2+ evidence, not score-axis evidence, not semantic
correctness, not production readiness, not SOTA, not breakthrough status, and
not full security.

## Tests

Phase 427 adds tests that:

- build deterministic tiny-Z3 serialization-preview metadata;
- verify the preview binds the Phase 425 package digest;
- verify the preview binds the Phase 423 review digest;
- verify the preview binds Phase 404/405 local Z3 backend replay digests through
  the package;
- reject package digest drift;
- reject canonical JSON-payload digest drift;
- reject redaction-policy digest drift;
- reject non-portable logical preview paths;
- reject filesystem writes, materialized package files, raw backend output, and
  raw solver-certificate payloads;
- reject promotional preview-summary text;
- reject accepted-evidence, Level2+, score-axis, proof, checker, solver, SOTA,
  semantic-correctness, production-readiness, breakthrough, full-security, and
  action-authority promotion attempts.

## Next Slice

Phase 428 defines the docs-first review boundary for Phase 427
serialization-preview metadata in
`docs/428-hsai-tiny-z3-serialization-preview-review-boundary.md`. That boundary
does not write filesystem artifacts, create materialized package files, mutate
the accepted Evidence Ledger, change accepted append policy, create accepted
formal evidence, create Level2+ evidence, populate score axes, run Lean, run
SMT, run COBALT, run Rust-to-Lean extraction, or claim semantic correctness,
production readiness, SOTA, breakthrough status, full security, or action
authority.
