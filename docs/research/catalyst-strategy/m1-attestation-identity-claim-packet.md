# M1 Attestation And Identity Claim Packet

State slice: `catalyst-strategy-m1-claim-packet-v1`.

Status: complete for bounded public claim packaging of module M1.

This is a claim packet stamped by the claim-packet forge
(`claim-packet-forge.md`). Module M1 is Attestation & agent identity. This packet
answers catalyst C1 (chat-log discovery) and C2 (on-device positioning) from
`catalyst-ledger.md`. It follows the Phase 254 gateway claim-packet anatomy.

## What This Packet Covers

This packet covers module M1: attestation and agent identity. The underlying
crates are `hsai-attestation`, `hsai-agent-anchor-registry`, and the
`hsai-e2e-harness` source-scan and digest-checker contract tests.

- Phase 44: interface-level attestation verification lane (`hsai-attestation`).
- Phase 51: proof-of-agent anchor registry (`hsai-agent-anchor-registry`).
- Managed-token verifier, anchor-validity claim envelopes, and distinctness
  envelope closure.

## Pinned Commits

Public commit: `6791f0769a16d084fcc149f4ab5f44ac5dbf8ee2` (`6791f07 Implement
Phase 800 serving efficiency lane inert metadata`). Later commits are outside
this packet unless a new packet names them.

## Public Claim

At the pinned commit, HSAI has a local, interface-level attestation and
agent-identity stack that:

- verifies managed attestation tokens at the interface level — checking anchor
  id, nonce, report-data binding, measurements, and freshness — and emits an
  `Attested` (never `Proven`) anchor-validity claim envelope;
- conjoins that attestation envelope with a distinct-agent envelope to close the
  distinctness assumption the distinct-agent lane carries open; and
- expresses, through the Phase 4 anchor registry, one active HSAI identity per
  accepted, non-reused registered anchor set.

This is hardware-bounded distinctness only. It is not competence, not safety, and
not global uniqueness.

Managed-attestation Phase 4 anchor-registry output means one active HSAI identity per accepted, non-reused registered anchor set.

This is an interface-level `Attested` distinctness claim only.

## Exact Verifier Commands

The public claim depends on each command below exiting successfully:

```text
cargo test -p hsai-attestation --lib --quiet
cargo test -p hsai-attestation --test phase1_managed_attestation --quiet
cargo test -p hsai-attestation --test managed_jwks_artifact_contract --quiet
cargo test -p hsai-agent-anchor-registry --test phase4_real_phala_authorization --quiet
cargo test -p hsai-e2e-harness --test claim_boundary_source_scan --quiet
cargo test -p hsai-e2e-harness --test gateway_proposal_digest_checker_contract --quiet
cargo test -p zkbench-core --test repo_hygiene --quiet
cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet
```

## Claim Level And Maturity

- Claim level: interface-level `Attested` distinctness only.
- Max claim maturity: `Attested`.
- The reference `ManagedTokenVerifier` does NOT cryptographically verify the
  managed attestation service's signature over the token. That signature check is
  the deferred real step where the stack leaves the pure-data regime.

## Explicit Nonclaims

This packet is not:

- accepted evidence;
- final acceptance;
- accepted Evidence Ledger mutation;
- Level2+ evidence;
- live provider evidence;
- live attestation capture;
- benchmark evidence;
- score-axis population;
- production readiness;
- semantic correctness;
- SOTA status;
- breakthrough status;
- full security;
- global software-agent uniqueness;
- local DCAP quote verification;
- managed-service signature verification;
- any claim above `Attested`.

## Structured Claim-Packet Manifest

This manifest is parsed by the local reproduction checker. It is not accepted
evidence and does not strengthen the public claim.

The `manifest_digest_sha256` value is computed over the manifest `key=value`
lines grouped by sorted key, excluding the `manifest_digest_sha256` line itself,
with one newline after each included line.

```claim-packet-manifest-v1
packet_id=m1-attestation-identity-claim-packet
packet_path=docs/research/catalyst-strategy/m1-attestation-identity-claim-packet.md
base_commit=6791f0769a16d084fcc149f4ab5f44ac5dbf8ee2
top_commit=6791f07 Implement Phase 800 serving efficiency lane inert metadata
claim_level=interface_level_attested_distinctness_only
max_claim_maturity=Attested
forge=claim-packet-forge.md
catalyst_ledger=catalyst-ledger.md
answers_catalyst=C1
answers_catalyst=C2
validated_module=hsai-attestation
validated_module=hsai-agent-anchor-registry
validated_module=hsai-e2e-harness
verifier_command=cargo test -p hsai-attestation --lib --quiet
verifier_command=cargo test -p hsai-attestation --test phase1_managed_attestation --quiet
verifier_command=cargo test -p hsai-attestation --test managed_jwks_artifact_contract --quiet
verifier_command=cargo test -p hsai-agent-anchor-registry --test phase4_real_phala_authorization --quiet
verifier_command=cargo test -p hsai-e2e-harness --test claim_boundary_source_scan --quiet
verifier_command=cargo test -p hsai-e2e-harness --test gateway_proposal_digest_checker_contract --quiet
verifier_command=cargo test -p zkbench-core --test repo_hygiene --quiet
verifier_command=cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet
packet_validation_command=cargo test -p zkbench-core --test catalyst_forge_packet_reproduction --quiet
packet_validation_command=cargo test -p zkbench-core --test repo_hygiene --quiet
packet_validation_command=cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet
summary_flag=mutates_accepted_evidence_ledger:false
summary_flag=creates_level2_evidence:false
summary_flag=populates_score_axes:false
summary_flag=grants_authority:false
summary_flag=performs_local_dcap_verification:false
summary_flag=performs_managed_service_signature_verification:false
summary_flag=claims_global_agent_uniqueness:false
nonclaim=accepted evidence
nonclaim=final acceptance
nonclaim=accepted Evidence Ledger mutation
nonclaim=Level2+ evidence
nonclaim=live provider evidence
nonclaim=live attestation capture
nonclaim=benchmark evidence
nonclaim=score-axis population
nonclaim=production readiness
nonclaim=semantic correctness
nonclaim=SOTA status
nonclaim=breakthrough status
nonclaim=full security
nonclaim=global software-agent uniqueness
nonclaim=local DCAP quote verification
nonclaim=managed-service signature verification
nonclaim=any claim above Attested
do_not_use=HSAI has proven global software-agent uniqueness.
do_not_use=HSAI has accepted live attestation evidence.
do_not_use=HSAI performs local DCAP quote verification.
do_not_use=HSAI verifies the managed attestation service signature.
do_not_use=HSAI is SOTA.
do_not_use=HSAI is fully secure.
manifest_digest_sha256=d863a0bf9e542aa53140d11c1d6806f44508bb11706e6fc86857725f412ad320
```
