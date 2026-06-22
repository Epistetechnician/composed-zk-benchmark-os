# Phala DCAP/PCCS Collateral Implementation Notes

Status: implemented as an operator-only collateral materialization path.

This phase closes the narrow live collateral-fetch part of the DCAP/PCCS gap
for the existing Phala-verified TDX quote. It does not implement local Intel
QVL/DCAP quote-signature verification and does not operate a local PCCS.

## State Slice

This implementation touches:

- `crates/hsai-attestation-phala/examples/operator_live_dcap_pccs_artifact.rs`
- `crates/hsai-attestation-phala/tests/phala_operator_live_dcap_pccs_contract.rs`
- `docs/107-phala-dcap-pccs-collateral-implementation-notes.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `docs/research/zk_external_source_index.md`
- `README.md`
- `AGENTS.md`

No Cargo metadata, `Cargo.lock`, committed credentials, credential fixtures,
committed generated collateral artifacts, benchmark packs, accepted Evidence
Ledgers, official submission artifacts, package runtime files, local PCCS
service configuration, or Phase 4 registry semantics are changed by this slice.

## Operator Flow

The operator fetches collateral for an already verified Phala attestation
checksum outside normal tests:

```text
phala api /attestations/collateral/<checksum> > <raw-collateral-json>
```

The example then writes digest-only local collateral metadata:

```text
HSAI_PHALA_OPERATOR_ACK=I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN
HSAI_PHALA_DCAP_PCCS_INPUT_JSON=<non-secret-input-json>
cargo run -p hsai-attestation-phala --example operator_live_dcap_pccs_artifact
```

The input JSON names:

- `operator_run_id`
- `checksum`
- `phala_verify_endpoint`
- `phala_collateral_endpoint`
- `phala_verify_response_path`
- `phala_collateral_response_path`
- `output_root`
- `started_at`
- `finished_at`

The example validates that the saved verification response was accepted,
matches the expected checksum, and is a `TEE_TDX` quote. It validates that the
collateral response contains the expected Phala collateral fields:

- `tcb_info`
- `tcb_info_issuer_chain`
- `tcb_info_signature`
- `qe_identity`
- `qe_identity_issuer_chain`
- `qe_identity_signature`
- `pck_crl`
- `pck_crl_issuer_chain`
- `root_ca_crl`

It writes only:

- `dcap-pccs/summary.json`
- `dcap-pccs/raw-verification-response.sha256`
- `dcap-pccs/raw-collateral-response.sha256`

It does not retain the raw collateral response body in the output bundle.

## Live Run Result

The Phase 107 operator run fetched collateral for checksum:

```text
5c99c72274ed0745f7788cdf272cc359099c07629833306d1a13f1b8e34596bd
```

The returned collateral contained TCB info, QE identity, issuer chains,
signatures, PCK CRL, and root CA CRL. The digest-only materialized output was
written outside git.

## Claim Boundary

Successful materialization remains capped at `Attested`. It proves only that
the operator fetched and locally bound provider-disclosed collateral metadata
for the reviewed Phala attestation checksum.

This is not proof, not local DCAP quote-signature verification, not local PCCS
operation, not managed-service signature/JWKS/JWT verification, not TLS or
attested-TLS channel binding, not benchmark evidence, not official benchmark
evidence, not semantic correctness, not global software-agent uniqueness, and
not authorization to mutate an accepted Evidence Ledger.

## Tests

`crates/hsai-attestation-phala/tests/phala_operator_live_dcap_pccs_contract.rs`
is hermetic. It checks that the example requires explicit acknowledgement and
input files, writes only digest/summary outputs, does not spawn a process, does
not use direct network APIs, does not retain raw collateral bodies, and keeps
the non-claims explicit.

Normal workspace tests do not call Phala and do not require credentials.
