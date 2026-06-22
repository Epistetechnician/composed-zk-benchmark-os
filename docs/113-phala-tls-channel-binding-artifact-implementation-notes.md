# Phala TLS Channel-Binding Artifact Implementation Notes

Status: implemented and exercised as an operator-only TLS 1.3 connection
artifact path.

This phase implements the narrow transport profile authorized by
`docs/112-phala-tls-channel-binding-artifact-boundary-spec.md`. It captures an
RFC 9266 exporter and a Phala verification response from the same TLS 1.3
connection, then writes digest-only metadata outside git.

## State Slice

This implementation touches:

- `crates/hsai-attestation-phala/examples/operator_live_tls_channel_artifact.rs`
- `crates/hsai-attestation-phala/tests/phala_operator_live_tls_channel_contract.rs`
- `crates/hsai-attestation-phala/Cargo.toml`
- `crates/hsai-e2e-harness/tests/claim_boundary_source_scan.rs`
- `Cargo.lock`
- `docs/113-phala-tls-channel-binding-artifact-implementation-notes.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `docs/research/zk_external_source_index.md`
- `README.md`
- `AGENTS.md`

No credential, secret fixture, generated artifact, raw exporter, raw request,
raw response, peer certificate, accepted Evidence Ledger, official submission,
benchmark pack, or Phase 4 registry semantic is committed by this slice.

## Implementation

The disabled-by-default `operator-live-tls-channel` feature enables a direct
`rustls` client that:

1. requires `HSAI_PHALA_OPERATOR_ACK`;
2. reads a non-secret JSON input named by
   `HSAI_PHALA_TLS_CHANNEL_INPUT_JSON`;
3. accepts only a bounded JSON request containing one `hex` quote field;
4. connects only to `cloud-api.phala.com:443`;
5. sends only `POST /api/v1/attestations/verify` over HTTP/1.1;
6. negotiates TLS 1.3 with Web PKI roots and no certificate bypass;
7. disables redirects and requests connection closure after one response;
8. bounds request, response, and timeout values;
9. derives 32 bytes with label `EXPORTER-Channel-Binding` and empty context;
10. validates HTTP 200, `success=true`, `quote.verified=true`, and `TEE_TDX`;
11. hashes the request body, response body, exporter, and length-framed peer
    certificate chain; and
12. stages exactly five declared files under `tls-channel/` outside git.

Existing roots require explicit overwrite, exact declared files, no symlinks,
and digest sidecars consistent with the existing summary. Repository overlap,
parent traversal, partial roots, undeclared files, stale digests, and raw output
files are rejected.

The HSAI source-contract scan allows only this feature-gated example to use
`std::net`/`TcpStream` and allows only the companion contract test to contain
forbidden transport strings as assertions. The exception does not apply to
library code or normal tests.

## Operator Flow

The input JSON names `operator_run_id`, `request_body_path`, `output_root`,
`started_at`, `finished_at`, `timeout_seconds`, and optional `overwrite`. The
request body uses the documented Phala shape:

```json
{"hex":"<non-secret-tdx-quote-hex>"}
```

The operator runs:

```text
HSAI_PHALA_OPERATOR_ACK=I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN
HSAI_PHALA_TLS_CHANNEL_INPUT_JSON=<non-secret-input-json>
cargo run -p hsai-attestation-phala \
  --example operator_live_tls_channel_artifact \
  --features operator-live-tls-channel
```

Normal tests do not enable the feature, call Phala, or require credentials.

## Live Run Result

The 2026-06-22 operator run submitted the previously accepted non-secret TDX
quote and received HTTP 200 for checksum:

```text
5c99c72274ed0745f7788cdf272cc359099c07629833306d1a13f1b8e34596bd
```

The same connection negotiated `TLSv1_3` with
`TLS13_AES_256_GCM_SHA384`. The Web PKI peer chain contained three
certificates. The digest-only values were:

```text
request:          bfa6d8f52b0c3bc1548067b93a3430dc5e62b429ded4501c7af261d2633bc0e4
response:         161ad4f3eb4f47b223f00d3627eb796373652bfb56641c43e7ff5c104f2db98c
tls exporter:     a88d764e3daf48ec6a56cb31890304d3cbc5c4a8d6b140e07b5504d485bde9d7
peer cert chain:  3c6a556f76e4aeb5ad26f3a8610dc94a5b4874d2d310391792587afa78351537
```

The generated artifact remains outside git at:

```text
/tmp/zkbench-tls-channel-20260622162935/artifact-output/tls-channel
```

## Tests

The hermetic contract tests scan for the pinned host, path, TLS version,
exporter profile, Web PKI roots, same-connection derivation, declared files,
output safety, and non-claims. Feature-enabled example unit tests cover request
validation, content-length response parsing, chunked response parsing, malformed
inputs, and repository-root rejection.

## Claim Boundary

The artifact records that one local client observed an accepted Phala response
and RFC 9266 exporter on the same TLS 1.3 connection. It is capped at
`Attested`.

This is not RA-TLS, not an attested server certificate, not proof that the TLS
private key resides in the attested CVM, not independently verifiable evidence,
not local DCAP verification, not managed-JWT verification, not benchmark
evidence, not official benchmark evidence, not semantic correctness, not
global software-agent uniqueness, and not authorization to mutate an accepted
Evidence Ledger.
