# Phala Cloud API Live Artifact Implementation Notes

Status: implemented as an operator-only artifact materialization example.

This phase closes the narrow gap between an operator-run Phala Cloud
`/attestations/verify` call and the repository's existing redacted
`operator-live/*` artifact format. It does not add normal-test network access
or a committed live artifact.

## State Slice

This implementation touches:

- `crates/hsai-attestation-phala/examples/operator_live_phala_api_artifact.rs`
- `crates/hsai-attestation-phala/tests/phala_operator_live_api_artifact_contract.rs`
- `docs/106-phala-cloud-api-live-artifact-implementation-notes.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `README.md`
- `AGENTS.md`

No Cargo metadata, `Cargo.lock`, committed credentials, credential fixtures,
committed generated operator artifacts, benchmark packs, accepted Evidence
Ledgers, official submission artifacts, package runtime files, or Phase 4
registry semantics are changed by this slice.

## Operator Flow

The operator performs the live Phala Cloud call outside normal tests:

```text
phala api /attestations/verify -X POST --input <quote-json> > <raw-response-json>
```

The example then materializes the existing redacted artifact shape:

```text
HSAI_PHALA_OPERATOR_ACK=I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN
HSAI_PHALA_API_ARTIFACT_INPUT_JSON=<non-secret-input-json>
cargo run -p hsai-attestation-phala --example operator_live_phala_api_artifact
```

The input JSON names:

- `operator_run_id`
- `artifact_bundle_path`
- `phala_verify_response_path`
- `phala_verify_endpoint`
- `output_root`
- `request_time`
- `started_at`
- `finished_at`
- `timeout_seconds`
- `retry_limit`
- optional `overwrite`

The example reads the saved Phala response, verifies `success=true`,
`quote.verified=true`, `TEE_TDX`, and report-data prefix binding to the captured
artifact bundle. It maps Phala's public verification response into the local
`PhalaManagedVerifierResponse`, hashes but does not retain the raw response
body, and writes through `write_phala_operator_live_artifact_output_root`.

## Claim Boundary

Successful materialization remains capped at `Attested`. The Phala API call is
live provider evidence that the submitted quote was accepted by Phala Cloud's
verification API. The local artifact additionally records the captured
report-data binding, compose hash, RTMR values, and checksum in the existing
redacted bundle format.

This is not proof, not local Intel DCAP verification, not PCCS collateral
verification, not managed-service signature/JWKS/JWT verification, not TLS or
attested-TLS channel binding, not benchmark evidence, not official benchmark
evidence, not semantic correctness, not global software-agent uniqueness, and
not authorization to mutate an accepted Evidence Ledger.

## Tests

`crates/hsai-attestation-phala/tests/phala_operator_live_api_artifact_contract.rs`
is hermetic. It checks that the example requires explicit acknowledgement and
input files, uses the existing output-root writer/reader, does not spawn a
process, does not use direct network APIs, and does not write a raw response
body file.

Normal workspace tests do not call Phala and do not require credentials.
