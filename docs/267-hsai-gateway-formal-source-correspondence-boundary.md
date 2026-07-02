# Phase 267 HSAI Gateway Formal Source Correspondence Boundary

State slice: `Phase 267 HSAI gateway formal-evidence source correspondence boundary`.

## Status

Complete for the docs-first correspondence boundary.

## Purpose

Phase 266 introduced a local metadata adapter for one formal-evidence candidate:

```text
gateway attestation challenge binding is deterministic for identical inputs and
changes when the nonce or gateway action proposal changes
```

Phase 267 defines what a future Lean, Rust-to-Lean, SMT, or federated
verification obligation would have to correspond to before any formal result can
be called HSAI evidence.

This phase does not implement a prover backend. It defines the mapping contract.

## Source Anchor Set

Any future proof or solver obligation for this property must cite and bind the
following source anchors:

| Anchor | File | Current role |
| --- | --- | --- |
| `GatewayActionProposal` | `crates/hsai-agent-admission/src/lib.rs` | Typed gateway action input. |
| `GatewayActionProposal::digest` | `crates/hsai-agent-admission/src/lib.rs` | Domain-tagged proposal digest. |
| `GatewayAttestationChallengeBinding` | `crates/hsai-agent-admission/src/lib.rs` | Challenge-binding output record. |
| `GatewayAttestationChallengeBinding::digest` | `crates/hsai-agent-admission/src/lib.rs` | Domain-tagged binding digest. |
| `build_gateway_attestation_challenge_binding` | `crates/hsai-agent-admission/src/lib.rs` | Canonical constructor for the binding. |
| `validate_gateway_attestation_challenge_binding` | `crates/hsai-agent-admission/src/lib.rs` | Local semantic validator for reconstructed bindings. |
| `gateway_attestation_challenge_id` | `crates/hsai-agent-admission/src/lib.rs` | Challenge id derivation over selected binding fields. |
| `GatewayFormalEvidenceLocalCheck` | `crates/hsai-agent-admission/src/lib.rs` | Phase 266 local metadata check shape. |
| `gateway_formal_evidence_local_check` | `crates/hsai-agent-admission/src/lib.rs` | Phase 266 local witness generation for determinism and sensitivity. |
| `report_data_binding` | `crates/hsai-attestation/src/lib.rs` | Imported report-data digest profile. |

The first correspondence artifact must record a source digest and commit for
each cited file. A clean source correspondence artifact cannot cite only a doc
or only a generated proof file.

## Property Decomposition

The future obligation must be split into small claims.

### P267-A Deterministic Constructor

For fixed valid inputs:

- `proposal`
- `policy_id`
- `anchor_id`
- `agent_pubkey_spki_hex`
- `nonce`
- `challenge_created_at`
- `challenge_expires_at`

two calls to `build_gateway_attestation_challenge_binding` return identical
`GatewayAttestationChallengeBinding` values.

### P267-B Nonce Sensitivity

For fixed valid inputs except `nonce`, changing `nonce` changes at least:

- `expected_report_data_hex`
- `challenge_id`
- `GatewayAttestationChallengeBinding::digest`

This property depends on the imported `report_data_binding` profile. A future
proof must either prove that function too or mark it as an explicit assumption.

### P267-C Proposal Sensitivity

For fixed valid inputs except the gateway proposal content, changing any
proposal field that changes `GatewayActionProposal::digest` changes at least:

- `gateway_case_hash_hex`
- `expected_report_data_hex`
- `challenge_id`
- `GatewayAttestationChallengeBinding::digest`

This does not prove semantic correctness of the proposal. It only proves binding
sensitivity to the serialized proposal digest.

### P267-D Validation Agreement

If the constructor returns a binding for valid inputs, then
`validate_gateway_attestation_challenge_binding` should accept the same
proposal, same policy id, same binding, and an in-window timestamp.

This does not prove that a real managed attestation is valid. It only checks the
local gateway binding contract.

## Correspondence Obligations

A future proof package must contain a correspondence certificate with:

- source file paths;
- source digests;
- source commit;
- exact function or type anchors;
- proof obligation id;
- proof backend;
- backend version and toolchain lock;
- trusted assumptions;
- unsupported Rust features or modeled replacements;
- extracted or modeled input/output schemas;
- proof status;
- proof artifact digest;
- reviewer decision;
- explicit nonclaims.

The correspondence certificate must fail closed if any source digest changes,
any anchor is missing, the proof target omits an imported dependency, or the
proof artifact claims a property outside the scoped obligation.

## Backend-Specific Rules

### Rust-to-Lean Path

A Rust-to-Lean path may use Aeneas, Hax, rust-lean, or a successor tool only for
small pure-data functions. It must record:

- unsupported Rust constructs;
- manual model replacements;
- serializer and hash assumptions;
- whether any Lean theorem uses `sorry`, unchecked axioms, or admitted lemmas;
- whether the checked theorem covers the actual source anchors listed above.

### SMT or COBALT-Inspired Path

An SMT path may model a reduced arithmetic or action-boundary property only when
the model states exactly which source behavior it abstracts away. It must record:

- Z3 or solver version;
- encoded variables and domains;
- uninterpreted functions;
- hash-function abstraction;
- completeness limits;
- solver certificate or replay transcript, if available.

SMT success is not source proof unless the correspondence certificate maps the
model back to the Rust anchors.

### Federated Path

A federated path may combine local Rust tests, Lean, SMT, and certificate
explanations only if each backend result has an explicit claim boundary and a
correspondence certificate. Cross-backend agreement is not proof by itself.

## Required Nonclaims

Any future artifact derived from this boundary must state:

- not a proof of HSAI;
- not semantic correctness;
- not full security;
- not production readiness;
- not SOTA status;
- not benchmark evidence;
- not accepted Evidence Ledger evidence;
- not Level2+ evidence unless an accepted-evidence phase separately admits it;
- not live provider evidence;
- not authority to execute an action.

## Anti-Goals

This phase does not permit:

- Rust implementation changes;
- Cargo metadata changes;
- package runtime files;
- proof assistant setup files;
- external repo clones;
- vendored source;
- Lean, Coq, TLA+, SMT, Z3, CBMC, or model-checker execution;
- generated proof artifacts;
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
- global software-agent uniqueness claims.

## Next Slice

Phase 268 implements the local pure-data correspondence-certificate type for
this source mapping. Any follow-on should remain certificate-adjacent unless
explicitly authorized to run a prover. The next safe slice is a docs-first
output-bundle boundary for the correspondence certificate.
