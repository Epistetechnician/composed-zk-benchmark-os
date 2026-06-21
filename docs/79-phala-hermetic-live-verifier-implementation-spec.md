# Phala Hermetic Live-Verifier Implementation Spec

## Status And Claim Boundary

This is a code-phase authorization spec for a future hermetic Phala/dstack live
managed-verifier implementation. This spec itself is documentation-only and
authorizes no Rust implementation in this slice.

The future implementation may prepare the smallest safe code surface needed to
support Phala live managed-verifier integration later:

- provider client trait;
- offline test-double client;
- normalized response model;
- failure taxonomy;
- trust-root mapping into `VerifiedAttestation`;
- replay and freshness checks;
- `Attested`-only envelope mapping.

The future implementation must keep normal tests hermetic. It must not perform
live Phala API calls, network access, authenticated provider calls, local DCAP,
PCCS collateral handling, deployment orchestration, benchmark execution, or
claims above `Attested`.

This preserves the Phase 78 boundary in
`docs/78-phala-live-managed-verifier-boundary-spec.md`.

## State Slice For This Spec

This documentation slice may touch only:

```text
docs/79-phala-hermetic-live-verifier-implementation-spec.md
docs/12-task-list.md
README.md
AGENTS.md
```

It must not touch Rust source, Cargo metadata, fixtures, accepted evidence
ledgers, benchmark packs, report bundles, audit indexes, generated artifacts, or
operator secrets.

## Future Code State Slice

A later implementation phase may touch only:

```text
crates/hsai-attestation-phala/src/lib.rs
crates/hsai-attestation-phala/tests/
docs/<future phase notes>
README.md
AGENTS.md
```

Cargo metadata changes are not authorized unless that later phase proves a
specific dependency is required. The expected first implementation should use
trait abstractions and deterministic in-memory test doubles, not an HTTP client.

No future implementation in this profile may touch:

```text
crates/zkbench-core
crates/hsai-agent-anchor-registry
crates/hsai-e2e-harness
Cargo.lock
benchmark packs
accepted Evidence Ledgers
Phala real-artifact fixtures
report-bundle outputs
audit-index outputs
```

If a later implementation truly needs any excluded path, it must open a separate
explicit phase before modifying that path.

## Provider Boundary

The only provider and mode authorized for the future code phase are:

```text
provider: Phala/dstack
mode: live managed verifier through caller-supplied client abstraction
```

The future code may define a trait representing the provider client boundary,
but the repository's normal test path must use a deterministic fake client.

The trait must not imply that the crate owns credentials, account state, network
transport, TLS roots, or deployment lifecycle. Those remain caller/operator
responsibilities.

## Future Public Surface

The future implementation may add names equivalent to:

```text
PhalaManagedVerifierClient
PhalaManagedVerifierRequest
PhalaManagedVerifierResponse
PhalaManagedVerifierError
PhalaLiveManagedVerifier
InMemoryPhalaManagedVerifierClient
PhalaReplayGuard
```

Names may change to match local style, but the roles must stay separate:

- request construction;
- provider client boundary;
- normalized response;
- validation and mapping;
- replay/freshness guard;
- deterministic fake client for tests.

## Request Contract

The future request type must be non-secret and deterministic:

```text
anchor_id
agent_pubkey
case_hash
nonce
expected_report_data_binding
expected_compose_hash
expected_runtime_measurements
expected_image_digest
freshness_window
managed_verifier_endpoint_id
request_time
```

The request must not contain:

- API tokens;
- bearer tokens;
- cookies;
- private keys;
- cloud account secrets;
- raw credential headers;
- deployment credentials.

## Response Normalization

The provider client trait must return an already captured response object. The
verifier must normalize it before mapping to `VerifiedAttestation`.

Required normalized fields:

```text
provider
verification_mode
provider_verdict
anchor_id
nonce
report_data
compose_hash
runtime_measurements
image_digest
issued_at
expires_at
raw_response_digest
provider_trust_roots
```

The verifier must reject responses that omit a required field or rely on an
implicit trust root.

The raw provider body may be represented only as caller-supplied bytes or a
digest. The normal test suite must not fetch a raw body from the network.

## Failure Taxonomy

The future implementation must distinguish at least:

```text
client_unavailable
malformed_response
wrong_provider
unsupported_mode
provider_rejected
stale_response
replayed_nonce
anchor_mismatch
nonce_mismatch
report_data_mismatch
compose_hash_mismatch
runtime_measurement_mismatch
image_digest_mismatch
missing_trust_root
claim_boundary_violation
```

These errors are diagnostic states only. They must not become proof claims,
benchmark results, or accepted evidence.

## Verification Order

The future verifier must fail closed in this order:

1. build request from non-secret caller inputs;
2. call the injected client trait;
3. normalize the response;
4. reject wrong provider or unsupported mode;
5. reject provider rejection;
6. reject stale response;
7. reject replayed nonce;
8. reject anchor, nonce, and report-data mismatch;
9. reject compose, runtime, and image mismatch;
10. reject missing provider or hardware trust roots;
11. map to `VerifiedAttestation`;
12. emit an `Attested` claim envelope only.

Rejected responses must emit no guarantees and no trust roots, and must not
mutate Phase 4 anchor-registry state.

## Replay And Freshness

The future implementation may include only an in-memory replay guard unless a
later phase authorizes persistent storage.

The guard must:

- reject the same nonce twice for the same verifier instance;
- remain deterministic in tests;
- expose no filesystem or database dependency;
- not claim global replay resistance;
- make caller-owned persistent replay storage a future boundary.

Freshness must be computed from caller-supplied `request_time`, `issued_at`,
`expires_at`, and a bounded freshness window. The verifier must reject missing,
expired, or future-issued responses unless a future spec defines clock-skew
policy.

## Trust-Root Mapping

Accepted responses must disclose every relied-on trust root in the output
envelope. The future implementation must preserve at least these categories:

```text
phala-managed-verifier:<id>
dstack-runtime-format:<id>
provider-disclosed-hardware-root:<id>
expected-compose-hash:<sha256>
expected-image-digest:<sha256>
```

If quote appraisal is delegated to Phala, the trust root must say managed
verifier. It must not say or imply local DCAP verification.

## Hermetic Test Requirements

The future implementation must include tests for:

- accepted fake response maps to `Attested`;
- verifier trust roots are visible;
- provider rejection fails closed;
- stale response fails closed;
- replayed nonce fails closed;
- anchor mismatch fails closed;
- report-data mismatch fails closed;
- compose hash mismatch fails closed;
- runtime measurement mismatch fails closed;
- image digest mismatch fails closed;
- missing trust root fails closed;
- attempted `Proven` output is impossible;
- rejected response leaves Phase 4 registry state unchanged when composed in a
  local test.

Normal workspace tests must use the fake client only. No normal test may require
Phala availability, credentials, network, wall-clock nondeterminism, Docker, or
operator-run infrastructure.

## Operator-Only Live Path

This spec does not authorize an operator live test.

A later phase may define an ignored or feature-gated operator live path only if
it also defines:

- secret handling outside git;
- explicit environment variables;
- non-secret artifact capture rules;
- redaction rules;
- timeout and retry policy;
- audit output shape;
- a statement that live verifier success is `Attested`, not `Proven`.

## Forbidden In This Spec Slice

- Rust implementation code.
- Cargo metadata changes.
- `Cargo.lock` changes.
- Network access in tests or examples.
- Live Phala API calls.
- Operator live tests.
- Phala deployment orchestration.
- Local Intel DCAP quote verification code.
- PCCS or collateral fetch/caching code.
- Generic managed-service signature/JWKS/JWT fetch code.
- TLS or attested-TLS implementation.
- External repo clones or vendored source.
- Secrets, API keys, cookies, bearer tokens, private keys, or credentials.
- Backend execution.
- Benchmark outputs.
- External result import.
- Accepted Evidence Ledger mutation.
- Phase 4 anchor-registry semantic changes.
- Level2+ evidence.
- Claims above `Attested`.

## Acceptance Criteria For This Spec Slice

- This spec names the future code state slice.
- This spec keeps live calls and credentials out of normal tests.
- README navigation links this spec.
- `docs/12-task-list.md` records this as the next managed-attestation
  authorization spec.
- `AGENTS.md` authorizes only this Markdown planning slice.
- Validation confirms no Rust source, Cargo metadata, package runtime, fixture,
  generated artifact, or benchmark output changed.

## Future Implementation Exit Criteria

A later implementation phase may complete only when:

- the trait and fake client are deterministic;
- accepted fake responses produce `Attested` only;
- rejected responses emit no guarantees or trust roots;
- trust roots disclose managed-verifier reliance;
- replay and freshness checks fail closed;
- normal tests pass without network access;
- root Cargo validation passes;
- docs state that hermetic live-verifier preparation is not proof, not local
  DCAP verification, not benchmark evidence, not live provider evidence, and not
  global software-agent uniqueness.
