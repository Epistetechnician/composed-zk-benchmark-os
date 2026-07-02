# Phase 272 HSAI Gateway Formal Backend Adapter Boundary

State slice: `Phase 272 HSAI gateway formal backend adapter boundary`.

## Status

Complete for the docs-first backend-adapter boundary.

## Purpose

Phases 265 through 271 created the local formal-evidence architecture,
metadata adapter, source-correspondence certificate, output bundle, and drift
coverage for one tiny HSAI gateway property lane.

Phase 272 defines the boundary for the first future backend-specific proof
adapter. It does not implement an adapter and does not run a prover.

## Backend Ranking

The first future adapter should use this order:

1. Rust-to-Lean source-correspondence lane for the gateway binding property.
2. SMT/COBALT-style containment lane for boolean claim-boundary and small
   arithmetic gate invariants.
3. Federated dispatch only after the first two lanes have explicit
   correspondence certificates.
4. Repository-scale benchmark evaluation after a backend run exists.
5. Certificate explanation only as an audit/debug aid.

The Rust-to-Lean lane is the best first fit for the existing Phase 266 and
Phase 268 surfaces because the target property is source-level Rust behavior:
deterministic construction, nonce sensitivity, proposal sensitivity, and
agreement with local validation metadata.

The SMT/COBALT-style lane is useful for simpler containment obligations:

- escalation flags stay false in candidate-only outputs;
- accepted Evidence Ledger mutation stays false;
- Level2+ evidence creation stays false;
- score-axis population stays false;
- authority grants stay false;
- freshness windows and bounded integer checks remain within declared ranges.

The SMT lane must not claim to prove the hash transcript, serde model, imported
`report_data_binding`, or whole gateway semantics unless a future slice supplies
an explicit correspondence certificate for each model replacement.

## Future Adapter Inputs

A future adapter request must bind:

- state slice id;
- source commit;
- source file digest set;
- Phase 267 source anchors;
- Phase 268 correspondence certificate digest;
- Phase 270 output-bundle manifest digest;
- proof obligation ids;
- backend kind;
- tool name and version;
- toolchain lock digest;
- model assumptions;
- modeled replacements;
- unsupported Rust features;
- input/output schema digest;
- expected proof artifact format;
- expected checker transcript format;
- requested claim boundary;
- explicit nonclaims.

Inputs may reference external tools by URL and version, but must not vendor
external source into this repo in the boundary slice.

## Future Adapter Outputs

A future backend adapter may produce only candidate evidence unless a later
accepted-evidence phase explicitly promotes it.

The output shape must include:

- proof request digest;
- correspondence certificate digest;
- backend run report digest;
- proof artifact digest if one exists;
- checker transcript digest if one exists;
- toolchain lock digest;
- model assumption digest;
- unsupported feature digest;
- reviewer decision;
- claim boundary;
- nonclaims;
- proof maturity label.

The proof maturity label must distinguish:

- `NotRun`;
- `ModelOnly`;
- `BackendCheckedCandidate`;
- `CorrespondenceCheckedCandidate`;
- `AcceptedEvidenceEligible`.

Only a future accepted-evidence phase may move beyond candidate status.

## Verification Order

A future adapter must validate in this order:

1. Source-correspondence certificate is valid.
2. Output bundle readback is valid.
3. Toolchain lock digest is present and nonzero.
4. Backend kind matches the requested lane.
5. Model assumptions are explicit.
6. Unsupported Rust features are explicit.
7. Proof obligation ids match the source-correspondence certificate.
8. Backend result is local and digest-bound.
9. Checker transcript is digest-bound.
10. Review decision is metadata-only or candidate-only.
11. Claim boundary and nonclaims are intact.

No backend result may bypass the source-correspondence certificate.

## Required Future Tests

A future implementation phase must add tests for:

- adapter request digest determinism;
- missing source-correspondence certificate rejection;
- output-bundle digest drift rejection;
- backend-kind mismatch rejection;
- toolchain lock digest absence rejection;
- model assumption absence rejection;
- unsupported-feature silence rejection;
- proof obligation mismatch rejection;
- proof artifact digest drift rejection;
- checker transcript digest drift rejection;
- claim-boundary escalation rejection;
- accepted-evidence mutation rejection;
- Level2+ evidence escalation rejection;
- score-axis population rejection;
- authority grant rejection;
- forbidden public claim text rejection.

## Anti-Goals

This phase does not permit:

- Rust implementation changes;
- Cargo metadata changes;
- package runtime files;
- proof assistant setup files;
- external repo clones;
- vendored source;
- Lean, Coq, TLA+, SMT, Z3, CBMC, model-checker, Aeneas, Hax, rust-lean, or
  COBALT execution;
- generated proof artifacts;
- generated checker transcripts;
- accepted Evidence Ledger mutation;
- Level2+ evidence;
- score-axis population;
- benchmark evidence;
- official benchmark submission;
- live provider calls;
- credential handling;
- semantic-correctness claims;
- production-readiness claims;
- SOTA claims;
- breakthrough claims;
- full-security claims;
- global software-agent uniqueness claims;
- authority to execute an action.

## Next Slice

Phase 273 implements the inert backend-adapter request/report metadata surface
in `hsai-agent-admission`. It does not run Lean, SMT, COBALT, or any external
tool. Its output is local candidate metadata that binds Phase 268 and Phase 270
digests and fails closed on claim escalation.
