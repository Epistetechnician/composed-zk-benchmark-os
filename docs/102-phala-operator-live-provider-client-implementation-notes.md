# Phala Operator Live Provider Client Implementation Notes

Status: implemented as an opt-in operator-owned provider client only.

This slice implements the smallest concrete provider-client surface following
`docs/101-phala-operator-live-provider-client-boundary-spec.md`. It adds a
feature-gated Phala/dstack HTTP client behind the existing Phase 100
`PhalaOperatorLiveClient` seam. The feature is disabled by default, normal
workspace tests remain hermetic, and the successful output path still flows
through the redacted Phase 85/100 `operator-live/*` artifact bundle.

This is not a live Phala run. No normal test calls a provider endpoint, no
credential value is committed, no generated operator artifact is committed, no
local Intel DCAP quote verification exists, no PCCS collateral is fetched, no
JWKS is fetched, no managed-service signature is validated, no TLS channel is
bound, no benchmark evidence is created, no official benchmark is submitted,
and no accepted Evidence Ledger is mutated.

## State Slice

This implementation touches:

- `crates/hsai-attestation-phala/Cargo.toml`
- `crates/hsai-attestation-phala/src/lib.rs`
- `crates/hsai-attestation-phala/src/operator_live_provider.rs`
- `crates/hsai-attestation-phala/tests/phala_operator_live_provider_client.rs`
- `crates/hsai-e2e-harness/tests/claim_boundary_source_scan.rs`
- `Cargo.lock`
- `docs/102-phala-operator-live-provider-client-implementation-notes.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `docs/research/zk_external_source_index.md`
- `README.md`
- `AGENTS.md`

No examples, scripts, package runtime files, fixtures, generated operator
artifacts, benchmark packs, accepted Evidence Ledgers, official submission
artifacts, external repo clones, vendored source, or Phase 4 registry semantics
are changed by this slice.

The `hsai-e2e-harness` source scan is updated only to allow `ureq::` in the
single feature-gated Phase 102 provider module. It continues to reject other
process and network APIs across HSAI crates.

## Implemented Surface

The crate now exposes the following items only when built with
`--features operator-live-provider`:

- `PhalaOperatorLiveProviderConfig`, with explicit endpoint, bounded timeout,
  and allowlisted credential sources;
- `PhalaOperatorLiveTransport`, a narrow POST-JSON transport seam used by
  hermetic tests;
- `UreqPhalaOperatorLiveTransport`, the blocking HTTP transport for
  operator-owned runs;
- `PhalaEnvCredentialProvider`, an explicit process-environment credential
  loader that requires `env:` source IDs and an allowlist;
- `PhalaOperatorLiveProviderClient`, the concrete
  `PhalaOperatorLiveClient` implementation;
- `PhalaOperatorLiveRawResponse`, retained only in memory so the client can
  digest the raw provider body without writing it;
- `PhalaOperatorLiveProviderError`, the provider-client failure taxonomy.

The client:

- validates endpoint, timeout, and credential source allowlist before
  transport use;
- serializes only the declared non-secret `PhalaManagedVerifierRequest`;
- sends the credential only as outbound bearer material;
- disables redirects in the shipped HTTP transport;
- maps 401 and 403 responses to authentication failure;
- maps unexpected status codes to fail-closed diagnostics;
- parses successful bodies as `PhalaManagedVerifierResponse`;
- replaces any provider-supplied raw-response digest with the SHA-256 digest of
  the actual raw response body;
- relies on the Phase 100 invocation orchestrator for normalized-response
  validation, retry behavior, replay rejection, redacted bundle construction,
  and output-root writes.

## Tests

`crates/hsai-attestation-phala/tests/phala_operator_live_provider_client.rs`
exercises the feature-gated client with fake transport and test-only
environment variables:

- successful provider invocation writes a redacted digest-bound bundle;
- raw response bodies are not retained on disk;
- credential values and credential source names are not serialized to
  artifacts;
- empty endpoint, out-of-bounds timeout, and missing allowlist fail before
  transport use;
- environment credential loading requires an allowed, available, non-empty
  source;
- authentication failure, unexpected HTTP status, malformed response, and
  transport failure map to fail-closed errors;
- provider rejection flows through the Phase 100 orchestrator without creating
  accepted evidence.

All tests are hermetic. They use fake transport, require no real operator
credential, write only temp-root artifacts, and perform no live Phala call.

## Source Refresh

The implementation phase re-checked the current Phala documentation on
2026-06-22 and intentionally avoided freezing a provider endpoint path or
response schema in the repository. The operator must supply the endpoint, and
the client accepts only the repo's normalized `PhalaManagedVerifierResponse`
shape after transport. Source attribution is recorded in
`docs/research/zk_external_source_index.md`.

## Claim Boundary

Successful provider-client output remains capped at `Attested`. It is not
proof, not local DCAP verification, not PCCS collateral verification, not
managed-service signature/JWKS/JWT verification, not TLS channel binding, not
benchmark evidence, not official benchmark evidence, not semantic correctness,
not global software-agent uniqueness, and not authorization to mutate an
accepted Evidence Ledger.

## Explicitly Still Missing

- live external backend execution;
- operator-run live Phala provider call;
- operator live test that calls Phala;
- local Intel DCAP quote verification;
- PCCS or collateral fetch/caching;
- JWKS fetching;
- managed-service signature fetch/verification;
- TLS or attested-TLS channel binding;
- generated durable operator artifact campaign;
- official benchmark submission;
- accepted Evidence Ledger mutation.
