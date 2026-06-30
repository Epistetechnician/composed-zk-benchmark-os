# Phase 249 HSAI Gateway-To-Attestation Binding Notes

Status: complete for local pure-data gateway-to-attestation challenge binding.

This phase implements the missing bridge named by Phase 248: derive an
attestation challenge input from one concrete gateway admission proposal without
running a provider, writing live artifacts, executing a model, granting
authority, or mutating an accepted Evidence Ledger.

## State Slice

This phase touches:

- `crates/hsai-agent-admission/Cargo.toml`
- `crates/hsai-agent-admission/src/lib.rs`
- `Cargo.lock`
- `docs/249-hsai-gateway-attestation-binding-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No generated artifacts, credentials, fixtures, provider responses, raw quotes,
raw JWKS documents, raw TLS exporters, model prompts, model outputs, package
runtime files, signer/tool integrations, benchmark outputs, official submission
artifacts, or accepted Evidence Ledgers are changed by this phase.

## Implemented Surface

`hsai-agent-admission` now depends on `hsai-attestation` only to reuse the
canonical `report_data_binding()` function.

The crate adds:

- `GATEWAY_ATTESTATION_BINDING_SCHEMA_VERSION`;
- `GATEWAY_ATTESTATION_BINDING_CLAIM_BOUNDARY`;
- `GatewayAttestationChallengeBinding`;
- `GatewayAttestationBindingError`;
- `gateway_attestation_binding_required_nonclaims`;
- `build_gateway_attestation_challenge_binding`;
- `validate_gateway_attestation_challenge_binding`.

The binding contains:

- gateway proposal id;
- subject;
- admission policy id;
- external runtime anchor id;
- agent public key bytes as SPKI hex;
- nonce;
- challenge validity window;
- gateway case hash;
- expected report-data hex;
- deterministic challenge id;
- explicit nonclaims;
- `authority_granted=false`.

## Binding Rule

The gateway case hash is:

```text
GatewayActionProposal::digest()
```

The expected report data is:

```text
report_data_binding(agent_pubkey_spki_bytes, nonce, gateway_case_hash)
```

That is the same canonical HSAI report-data binding used by the attestation
lane. The external runtime can carry the emitted `expected_report_data_hex` into
a future Phala/dstack, DCAP, managed-verifier, or other attestation capture.

## Validation Behavior

`validate_gateway_attestation_challenge_binding` rejects:

- wrong schema version;
- proposal id mismatch;
- subject mismatch;
- policy id mismatch;
- empty anchor id;
- malformed public-key or report-data hex;
- invalid challenge windows;
- not-yet-valid challenges;
- expired challenges;
- gateway case hash drift;
- report-data drift;
- challenge-id drift;
- `authority_granted=true`;
- missing required nonclaims.

## Why This Matters

Before this phase, the gateway stack and external attestation lane were
connected only by a public evidence map. After this phase, the gateway can emit
a deterministic, provider-neutral challenge binding for a specific typed action
proposal.

This is the first local bridge where the exact gateway action proposal is the
case hash inside the attestation challenge.

## Nonclaims

This phase does not prove:

- attestation evidence;
- live provider evidence;
- live gateway execution;
- live model behavior;
- verifier-agent runtime behavior;
- accepted Evidence Ledger mutation;
- score-axis population;
- official benchmark evidence;
- Level2+ evidence;
- production readiness;
- semantic correctness;
- SOTA status;
- breakthrough status;
- full security;
- signer, wallet, exchange, custody, MCP, ACP, or tool authority;
- global software-agent uniqueness;
- any claim above `Attested`.

The binding is capture input metadata only. It is not a provider response and
not evidence that hardware carried the challenge.

## Validation Commands

The focused Phase 249 checks are:

```sh
cargo fmt --all --check
git diff --check
cargo check -p hsai-agent-admission
cargo test -p hsai-agent-admission --lib gateway_attestation
cargo test -p hsai-agent-admission --lib
cargo test -p zkbench-core --test repo_hygiene
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test --workspace --quiet
```

These commands are hermetic. They do not call Phala, fetch JWKS, fetch PCCS
collateral, run `dcap-qvl`, execute a model, submit a benchmark, or mutate
accepted evidence.

## Buyer-Facing Wording

Use:

```text
HSAI can bind a concrete gateway action proposal into an attestation challenge
using the same report-data binding as the external evidence lane. The output is
capture input metadata, not live attestation evidence.
```

Do not use:

```text
attested gateway execution
accepted external evidence
production ready
SOTA proven
breakthrough proven
fully secure
```

## Next Evidence Step

The next phase should materialize an ignored operator bundle that includes:

- one gateway report bundle digest;
- one gateway attestation challenge binding;
- one repo-external operator-live attestation artifact reference or saved-output
  digest;
- an explicit statement that it is still not accepted evidence until a separate
  reviewed promotion phase.
