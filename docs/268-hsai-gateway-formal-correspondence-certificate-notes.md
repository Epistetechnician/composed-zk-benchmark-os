# Phase 268 HSAI Gateway Formal Correspondence Certificate Notes

State slice: `Phase 268 HSAI gateway formal correspondence-certificate metadata`.

## Status

Complete for the local pure-data certificate metadata type.

## Scope

This phase implements the first local source-correspondence certificate surface
for the Phase 267 mapping. It does not run a formal backend.

The implemented `hsai-agent-admission` surface is:

- `GatewayFormalCorrespondenceCertificate`
- `GatewayFormalCorrespondenceValidation`
- `GatewayFormalCorrespondenceIssue`
- `GatewayFormalSourceFileDigest`
- `GatewayFormalSourceAnchor`
- `GatewayFormalToolStatus`
- `GatewayFormalProofObligationId`
- `GatewayFormalBackendKind`
- `GatewayFormalToolExecutionStatus`
- `GatewayFormalCorrespondenceProofStatus`
- `GatewayFormalCorrespondenceReviewDecision`
- `validate_gateway_formal_correspondence_certificate`

## Certificate Contract

A valid certificate must bind:

- `crates/hsai-agent-admission/src/lib.rs`
- `crates/hsai-attestation/src/lib.rs`
- all Phase 267 source anchors;
- all four Phase 267 obligations;
- source commit metadata;
- nonzero source digests;
- tool name, tool version, and toolchain lock digest;
- trusted assumptions for serde JSON determinism, SHA-256 modeling, and imported
  `report_data_binding`;
- modeled replacements for `hash_tagged` and `report_data_binding`;
- input/output schema digest;
- metadata-only reviewer approval;
- explicit nonclaims.

## Fail-Closed Checks

Validation rejects:

- missing or unsafe source files;
- missing source digests;
- duplicate source files;
- missing anchors;
- duplicate anchors;
- anchor/file mismatches;
- missing P267 obligations;
- empty tool metadata;
- zero toolchain lock digest;
- executed backend status;
- proof status above `CorrespondenceOnly`;
- proof artifact digest submission;
- missing trusted assumptions;
- missing modeled replacements;
- zero input/output schema digest;
- missing reviewer;
- non-metadata-only review decisions;
- claim-boundary mismatch;
- formal backend execution request;
- accepted Evidence Ledger mutation request;
- Level2+ evidence request;
- score-axis population request;
- production-readiness claim;
- semantic-correctness claim;
- SOTA claim;
- full-security claim;
- authority-grant request;
- forbidden claim text;
- missing required nonclaims.

## Validation

Executed:

```bash
cargo test -p hsai-agent-admission gateway_formal_correspondence
```

Result: passed.

## Nonclaims

This phase does not run Lean, Coq, TLA+, SMT, Z3, CBMC, model checkers, Aeneas,
Rust-to-Lean extraction, COBALT, VeriSoftBench, Federated Formal Verification,
or certificate-explanation tooling.

It does not clone external repositories, vendor source, create proof assistant
setup files, generate proof artifacts, mutate accepted evidence, populate score
axes, submit benchmark results, call live providers, handle credentials, prove
semantic correctness, establish production readiness, establish SOTA, establish
breakthrough status, establish full security, or grant execution authority.

## Next Slice

Phase 269 defines the docs-first output-bundle boundary for future
correspondence-certificate materialization. Any follow-on implementation must
remain local filesystem metadata only and must not run a prover or promote the
certificate into accepted evidence.
