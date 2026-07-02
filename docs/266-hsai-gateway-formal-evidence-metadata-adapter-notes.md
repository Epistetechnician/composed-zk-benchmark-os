# Phase 266 HSAI Gateway Formal Evidence Metadata Adapter Notes

State slice: `Phase 266 HSAI gateway formal-evidence metadata adapter`.

## Status

Complete for the local metadata adapter.

## Scope

This phase implements the first bounded follow-on from
`docs/265-hsai-formal-verification-evidence-architecture-boundary.md` inside
`hsai-agent-admission`.

The adapter is intentionally narrow. It models one property candidate:

`gateway attestation challenge binding is deterministic for identical inputs and changes when the nonce or gateway action proposal changes`

The implemented surface is:

- `GatewayFormalEvidenceRequest`
- `GatewayFormalEvidenceReport`
- `GatewayFormalEvidenceValidation`
- `GatewayFormalEvidenceLocalCheck`
- `GatewayFormalEvidencePropertyKind`
- `GatewayFormalEvidenceCheckStatus`
- `GatewayFormalEvidenceIssue`
- `build_gateway_formal_evidence_report`
- `validate_gateway_formal_evidence_request`

## Evidence Boundary

The adapter rebuilds the existing
`GatewayAttestationChallengeBinding` from a concrete
`GatewayActionProposal`, policy id, anchor id, SPKI hex key, nonce, and
challenge window. It then records a local metadata check over:

- identical-input determinism;
- nonce sensitivity;
- proposal-digest sensitivity;
- expected binding digest agreement;
- portable source-file attribution;
- source digest and source commit presence;
- explicit nonclaims.

This is a local Rust metadata check. It is not a formal proof, not Lean
evidence, not SMT evidence, not accepted Evidence Ledger evidence, not
benchmark evidence, and not Level2+ evidence.

## Claim Boundary

The report always sets:

- `creates_formal_proof = false`
- `mutates_accepted_evidence_ledger = false`
- `creates_level2_evidence = false`
- `populates_score_axes = false`
- `grants_authority = false`

Validation rejects requests that claim or request:

- formal backend execution;
- proof artifact digest submission;
- accepted Evidence Ledger mutation;
- Level2+ evidence;
- score-axis population;
- production readiness;
- semantic correctness;
- SOTA status;
- full security;
- authority to execute an action.

## Validation

Executed:

```bash
cargo test -p hsai-agent-admission gateway_formal_evidence
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

Phase 267 defines the source-correspondence spec for this gateway binding
property. Any follow-on should remain docs-first unless explicitly authorized to
implement a pure-data correspondence-certificate type or a real proof backend.
