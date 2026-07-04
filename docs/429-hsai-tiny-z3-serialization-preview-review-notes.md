# Phase 429 HSAI Tiny Z3 Serialization Preview Review Notes

State slice: `Phase 429 HSAI tiny Z3 serialization preview review metadata implementation`.

Phase 429 implements deterministic pure-data review metadata over one Phase 427
tiny-Z3 serialization preview. The review stores only digests, reviewer
metadata, a bounded review label, explicit nonclaims, and nonpromotion flags. It
does not write filesystem artifacts, create package files, create archives,
store raw package bytes, mutate the accepted Evidence Ledger, change accepted
append policy, create accepted formal evidence, create Level2+ evidence,
populate score axes, generate proof artifacts, generate checker transcripts,
generate solver certificates, run Lean, run SMT, run COBALT, run Rust-to-Lean
extraction, submit benchmarks, claim semantic correctness, claim production
readiness, claim SOTA, claim breakthrough status, claim full security, or grant
authority to execute an action.

## Implemented Surface

The implementation is additive in `crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalTinyDigestBackendZ3SerializationPreviewReviewInput`;
- `GatewayFormalTinyDigestBackendZ3SerializationPreviewReview`;
- `GatewayFormalTinyDigestBackendZ3SerializationPreviewReviewLabel`;
- `GatewayFormalTinyDigestBackendZ3SerializationPreviewReviewIssue`;
- `GatewayFormalTinyDigestBackendZ3SerializationPreviewReviewValidation`;
- `gateway_formal_tiny_digest_backend_z3_serialization_preview_review_claim_boundary`;
- `gateway_formal_tiny_digest_backend_z3_serialization_preview_review_required_nonclaims`;
- `build_gateway_formal_tiny_digest_backend_z3_serialization_preview_review`;
- `validate_gateway_formal_tiny_digest_backend_z3_serialization_preview_review_input`.

## Review Labels

The implemented review labels are:

- `tiny_z3_serialization_preview_scope_acceptable`;
- `tiny_z3_serialization_preview_rejected`;
- `tiny_z3_serialization_profile_blocked`;
- `tiny_z3_canonical_shape_blocked`;
- `tiny_z3_materialization_still_blocked`.

`tiny_z3_materialization_still_blocked` is explicitly non-promotional. It
preserves the current block on materialized tiny-Z3 package artifacts.

## Required Bindings

Each review input must bind:

- one Phase 427 serialization-preview digest;
- one Phase 427 serialization-preview input digest;
- one Phase 425 audit package digest;
- one Phase 423 review record digest;
- one Phase 421 local reviewed metadata digest;
- one Phase 405 local Z3 output-manifest digest;
- one Phase 404 local Z3 execution digest;
- the current accepted append blocker set and digest;
- one package manifest digest;
- serialization profile id;
- canonical field-order digest;
- canonical JSON-shape digest;
- canonical JSON-payload digest;
- redaction-policy digest;
- logical preview path digest;
- reviewer policy id;
- reviewer decision id;
- reviewer decision timestamp;
- review summary and digest;
- explicit nonclaims and their digest.

## Rejection Cases

Validation rejects:

- wrong schema version;
- invalid review id;
- invalid reviewer policy id;
- invalid reviewer decision id;
- missing review timestamp;
- missing reviewer decision timestamp;
- zero required digests;
- drift from the Phase 427 serialization-preview record;
- promoted or drifted Phase 427 preview state;
- accepted append blocker drift;
- review-summary digest drift;
- nonclaim drift;
- filesystem artifact writes;
- materialized package files;
- raw package bytes;
- raw backend stdout or stderr;
- raw proof artifacts;
- raw checker transcripts;
- raw solver certificates;
- live backend outputs;
- benchmark outputs;
- secrets or credentials;
- mutable accepted-ledger state;
- review summaries that claim accepted evidence, Level2+ evidence, score-axis
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

The maximum claim after Phase 429 is:

```text
HSAI can construct deterministic local review metadata for one tiny-Z3
serialization preview while preserving the current accepted formal-evidence
blocker and still blocking materialized audit package artifacts.
```

This is not a materialized artifact, not accepted evidence, not formal proof,
not backend execution, not a Lean/SMT/COBALT run, not Rust-to-Lean extraction
evidence, not Level2+ evidence, not score-axis evidence, not semantic
correctness, not production readiness, not SOTA, not breakthrough status, and
not full security.

## Tests

Phase 429 adds tests that:

- build deterministic tiny-Z3 serialization-preview review metadata;
- verify the review binds the Phase 427 preview digest;
- verify the review binds the Phase 425 package digest;
- verify the review binds Phase 423 review and Phase 421 metadata digests;
- verify the review binds Phase 404/405 local Z3 backend replay digests through
  the preview;
- verify `tiny_z3_materialization_still_blocked` remains non-promotional;
- reject serialization-preview digest drift;
- reject review-summary digest drift;
- reject promoted preview state;
- reject filesystem writes, materialized package files, raw backend output, and
  raw solver-certificate payloads;
- reject promotional review-summary text;
- reject accepted-evidence, Level2+, score-axis, proof, checker, solver, SOTA,
  semantic-correctness, production-readiness, breakthrough, full-security, and
  action-authority promotion attempts.

## Next Slice

Phase 430 defines the docs-first materialized artifact boundary for reviewed
tiny-Z3 serialization-preview metadata in
`docs/430-hsai-tiny-z3-materialized-audit-package-artifact-boundary.md`. That
boundary keeps materialized artifact output separate from accepted formal
evidence, accepted Evidence Ledger mutation, accepted append policy changes,
Level2+ evidence, score axes, Lean execution, SMT execution, COBALT execution,
Rust-to-Lean extraction, semantic correctness, production readiness, SOTA,
breakthrough status, full security, and action authority.
