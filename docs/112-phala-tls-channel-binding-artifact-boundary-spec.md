# Phala TLS Channel-Binding Artifact Boundary Spec

Status: docs-first boundary complete; implementation is not authorized by this
documentation-only slice.

## Goal

Define the smallest operator-only path that can record the TLS 1.3 channel used
for a Phala Cloud verification request without weakening the existing claim
boundary. A later implementation may capture RFC 9266 `tls-exporter` keying
material and the response body from the same TLS connection, then materialize
digest-only local metadata outside git.

This boundary does not define RA-TLS. It does not bind a Phala TDX quote to the
TLS endpoint key, and it does not make a client-side capture independently
verifiable. It closes only the narrower operational gap: proving to the local
operator that one saved Phala response and one TLS exporter were observed on
the same client connection.

## State Slice

This docs-first slice may touch only:

- `docs/112-phala-tls-channel-binding-artifact-boundary-spec.md`
- `docs/12-task-list.md`
- `docs/research/zk_external_source_index.md`
- `README.md`
- `AGENTS.md`

A separately authorized implementation may touch only:

- one operator-only example under `crates/hsai-attestation-phala/examples/`
- one hermetic source-contract test under
  `crates/hsai-attestation-phala/tests/`
- `crates/hsai-attestation-phala/Cargo.toml` and `Cargo.lock` only for
  feature-gated TLS dependencies
- one implementation note under `docs/`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `docs/research/zk_external_source_index.md`
- `README.md`
- `AGENTS.md`

## Normative Transport Profile

The future operator path must:

1. require the existing explicit Phala operator acknowledgement;
2. require an HTTPS endpoint with the exact host
   `cloud-api.phala.com` and `/api/v1/attestations/verify` path;
3. negotiate TLS 1.3 with Web PKI server-certificate validation and no custom
   trust-root override;
4. disable redirects and reject a hostname, scheme, port, or path change;
5. send one bounded HTTP request and read one bounded response on one TLS
   connection;
6. derive exactly 32 bytes of exported keying material with the RFC 9266 label
   `EXPORTER-Channel-Binding` and an empty context;
7. hash the exporter, peer certificate chain, request body, and response body;
8. validate the response using the existing Phala managed-verifier mapping;
9. retain no bearer credential, raw exporter, request body, response body, or
   peer certificate in the materialized output; and
10. write only declared digest metadata outside the repository.

TLS 1.2, renegotiation, early data, redirects, connection reuse, proxies,
custom roots, plaintext HTTP, and alternate endpoints are outside this profile.

## Future Artifact Shape

The implementation may materialize exactly:

- `tls-channel/summary.json`
- `tls-channel/exporter.sha256`
- `tls-channel/peer-cert-chain.sha256`
- `tls-channel/request.sha256`
- `tls-channel/response.sha256`

`summary.json` must disclose:

- schema version;
- operator run id;
- endpoint host and path;
- negotiated TLS version and cipher suite;
- RFC 9266 label, empty-context declaration, and exporter length;
- peer-certificate count;
- HTTP status;
- request and completion times;
- Phala checksum and response-verification status;
- maximum claim maturity `Attested`; and
- explicit non-claims.

Every digest sidecar must contain one lowercase SHA-256 hex digest. The output
writer must reject partial roots, undeclared files, symlinks, repository-root
overlap, stale digests, and overwrite without explicit opt-in.

## Required Hermetic Tests

Normal tests must remain network-free and credential-free. The future contract
test must prove that the operator example:

- is feature gated and requires explicit acknowledgement;
- pins TLS 1.3, the host, path, exporter label, context, and length;
- uses Web PKI roots and does not accept insecure certificate bypasses;
- derives the exporter from the same TLS connection that carries the request;
- rejects redirects and bounds request/response sizes and timeouts;
- writes only digest metadata and never writes credential or raw transport
  material;
- keeps `Attested` as the maximum claim; and
- states that the artifact is not RA-TLS, proof, benchmark evidence, official
  evidence, semantic correctness, or accepted Evidence Ledger state.

## Sources

- [RFC 9266](https://www.rfc-editor.org/rfc/rfc9266.html) defines the TLS 1.3
  `tls-exporter` channel binding as 32 bytes derived with label
  `EXPORTER-Channel-Binding` and an empty context. It identifies a TLS
  connection and does not by itself identify an upper-layer protocol instance.
- [RFC 8446 section 7.5](https://www.rfc-editor.org/rfc/rfc8446.html#section-7.5)
  defines TLS 1.3 exporter derivation.
- [Dstack-TEE/dstack](https://github.com/Dstack-TEE/dstack) is the provider
  architecture reference for TLS termination, TLS passthrough, and RA-TLS
  boundaries.
- [flashbots/attested-tls](https://github.com/flashbots/attested-tls) remains a
  design reference for stronger transport-bound attestation. No source is
  vendored or copied by this phase.

## Claim Boundary

The future artifact may establish only that the local operator's client
observed a Phala verification response and RFC 9266 exporter on the same TLS
1.3 connection. The exporter is not secret and must not be used as a key.

The artifact is not RA-TLS, not an attested server certificate, not proof that
the TLS private key resides in the attested CVM, not independent third-party
evidence, not local DCAP verification, not managed-JWT verification, not
benchmark evidence, not official benchmark evidence, not semantic correctness,
not global software-agent uniqueness, and not authorization to mutate an
accepted Evidence Ledger.

## Forbidden In This Docs-First Slice

- Rust source or tests.
- Cargo metadata or lockfile changes.
- Network access or live Phala calls.
- Operator examples or generated artifacts.
- Credentials, secret fixtures, or raw TLS material.
- TLS dependency additions.
- RA-TLS or attested-certificate implementation.
- Benchmark output or official submission.
- Accepted Evidence Ledger mutation.
- Claims above `Attested`.

## Exit Criteria For A Future Code Phase

- The implementation remains opt-in and operator-only.
- Normal tests are hermetic.
- One live run captures TLS 1.3 and an RFC 9266 exporter from the same Phala
  verification connection.
- Only digest-bound output is materialized outside git.
- No secret or generated artifact is committed.
- Focused tests, workspace tests, clippy, docs, source-contract scans, and
  coverage pass.
- Documentation preserves every non-claim in this spec.
