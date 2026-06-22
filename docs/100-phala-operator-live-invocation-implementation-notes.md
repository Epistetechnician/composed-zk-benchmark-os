# Phala Operator Live Invocation Implementation Notes

Status: implemented as local operator invocation plumbing only.

This slice implements the smallest code surface following
`docs/97-phala-operator-live-invocation-boundary-spec.md`. It adds a
fail-closed operator invocation orchestrator that accepts caller-supplied
clients and caller-supplied credential providers, validates all required
operator controls before invocation, and materializes only the existing
redacted `operator-live/*` artifact bundle through the Phase 85 output-root
writer.

This is not a live Phala run. The crate still does not ship an HTTP client,
load process environment variables, call a provider endpoint, implement local
Intel DCAP quote verification, fetch PCCS collateral, fetch JWKS, validate
managed-service signatures, bind TLS channels, create benchmark evidence,
submit an official benchmark, or mutate an accepted Evidence Ledger.

## State Slice

This implementation touches:

- `crates/hsai-attestation-phala/src/lib.rs`
- `crates/hsai-attestation-phala/tests/phala_operator_live_invocation.rs`
- `docs/100-phala-operator-live-invocation-implementation-notes.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `README.md`
- `AGENTS.md`

No Cargo metadata, `Cargo.lock`, examples, scripts, package runtime files,
fixtures, generated operator artifacts, benchmark packs, accepted Evidence
Ledgers, official submission artifacts, or Phase 4 registry semantics are
changed by this slice.

## Implemented Surface

The crate now provides:

- `PhalaOperatorLiveInvocationInput`, the explicit non-secret invocation
  contract;
- `PhalaOperatorLiveCredential`, an opaque credential value whose debug output
  redacts the secret;
- `PhalaOperatorLiveCredentialProvider`, the caller-owned credential-loading
  boundary;
- `InMemoryPhalaOperatorLiveCredentialProvider`, a hermetic test provider;
- `PhalaOperatorLiveClient`, a credential-aware client boundary;
- `PhalaOperatorLiveInvocation`, the orchestrator that validates controls,
  loads credentials, invokes a caller-supplied client with bounded retries,
  validates the normalized managed-verifier response, applies replay protection,
  builds a redacted artifact bundle, and writes through
  `write_phala_operator_live_artifact_output_root`;
- `PhalaOperatorLiveInvocationError`, the fail-closed error taxonomy.

The orchestrator requires:

- explicit operator acknowledgement;
- non-empty credential source;
- non-empty provider endpoint;
- bounded timeout;
- bounded retry limit;
- matching credential source;
- normalized Phala/dstack managed-verifier acceptance;
- fresh non-replayed nonce;
- required trust roots;
- existing Phase 85 output-root validation.

## Tests

`crates/hsai-attestation-phala/tests/phala_operator_live_invocation.rs`
exercises:

- valid invocation writing a declared operator-live bundle;
- refusal to retain raw response bodies;
- refusal to leak credential secret material or credential source names into
  artifacts;
- missing acknowledgement rejection;
- missing credential source rejection;
- empty endpoint rejection;
- timeout bound rejection;
- retry bound rejection;
- unavailable credential rejection;
- mismatched credential source rejection;
- retry exhaustion mapping;
- provider rejection mapping;
- replayed nonce rejection before a second write.

All tests are hermetic. They use in-memory clients and credentials, require no
network, require no real operator credentials, and perform no live Phala call.

## Claim Boundary

Successful invocation output remains capped at `Attested`. It is not proof, not
local DCAP verification, not managed-service signature/JWKS/JWT verification,
not TLS channel binding, not benchmark evidence, not official benchmark
evidence, not semantic correctness, not global software-agent uniqueness, and
not authorization to mutate an accepted Evidence Ledger.

## Explicitly Still Missing

- live external backend execution;
- live Phala provider call;
- real operator credential source outside test memory;
- operator live test that calls Phala;
- local Intel DCAP quote verification;
- PCCS or collateral fetch/caching;
- JWKS fetching;
- managed-service signature fetch/verification;
- TLS or attested-TLS channel binding;
- official benchmark submission;
- accepted Evidence Ledger mutation.
