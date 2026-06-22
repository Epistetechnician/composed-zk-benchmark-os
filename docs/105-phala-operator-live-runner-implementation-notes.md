# Phala Operator Live Runner Implementation Notes

Status: implemented as an operator-only example runner.

This phase implements the smallest operator-facing runner authorized by
`docs/104-phala-operator-live-runner-boundary-spec.md`. The runner wires
existing Phase 85 output-root plumbing, Phase 100 invocation orchestration, and
Phase 102 provider-client transport together behind the disabled-by-default
`operator-live-provider` feature.

This is not a live Phala run by itself. No normal test calls a provider
endpoint, no credential value is committed, no generated operator artifact is
committed, no local Intel DCAP quote verification exists, no PCCS collateral is
fetched, no JWKS is fetched, no managed-service signature is validated, no TLS
channel is bound, no benchmark evidence is created, no official benchmark is
submitted, and no accepted Evidence Ledger is mutated.

## State Slice

This implementation touches:

- `crates/hsai-attestation-phala/examples/operator_live_run.rs`
- `crates/hsai-attestation-phala/tests/phala_operator_live_runner_contract.rs`
- `docs/104-phala-operator-live-runner-boundary-spec.md`
- `docs/105-phala-operator-live-runner-implementation-notes.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `README.md`
- `AGENTS.md`

No Cargo metadata, `Cargo.lock`, committed credentials, credential fixtures,
generated operator artifacts, benchmark packs, accepted Evidence Ledgers,
official submission artifacts, package runtime files, or Phase 4 registry
semantics are changed by this slice.

## Runner Contract

The runner is `operator_live_run` and requires:

```text
HSAI_PHALA_OPERATOR_ACK=I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN
HSAI_PHALA_OPERATOR_INPUT_JSON=/path/to/non-secret-invocation.json
HSAI_PHALA_OPERATOR_CREDENTIAL_SOURCE=env:NAME_THAT_MATCHES_JSON
NAME_THAT_MATCHES_JSON=<operator secret outside git>
```

The non-secret invocation JSON maps into `PhalaOperatorLiveInvocationInput`
fields and includes output root, endpoint, nonce, expected report-data binding,
compose hash, runtime measurements, image digest, request time, timeout, retry
limit, and credential source. The credential source must match the explicit
environment declaration before the runner constructs the provider client.

The runner:

- requires explicit acknowledgement before reading input;
- reads only a caller-supplied JSON file;
- allowlists exactly one credential source;
- constructs `PhalaOperatorLiveProviderClient<UreqPhalaOperatorLiveTransport>`;
- invokes through `PhalaOperatorLiveInvocation`;
- writes only the declared redacted `operator-live/*` files;
- prints only non-secret validated metadata.

## Tests

`crates/hsai-attestation-phala/tests/phala_operator_live_runner_contract.rs`
is hermetic. It checks the runner source for the explicit acknowledgement,
input JSON, credential source, provider client, credential provider, transport,
and invocation wiring. It also rejects hard-coded endpoints, hard-coded
credential names, test secret shapes, raw response body output, and process
spawning/forced exit hooks.

The feature-specific gate compiles the example with:

```text
cargo clippy -p hsai-attestation-phala --features operator-live-provider --examples -- -D warnings
```

Normal workspace tests do not call Phala and do not require credentials.

## Claim Boundary

Successful runner output remains capped at `Attested`. It is not proof, not
local DCAP verification, not PCCS collateral verification, not
managed-service signature/JWKS/JWT verification, not TLS channel binding, not
benchmark evidence, not official benchmark evidence, not semantic correctness,
not global software-agent uniqueness, and not authorization to mutate an
accepted Evidence Ledger.

## Explicitly Still Missing

- an actual operator-run live Phala provider call in this environment;
- an operator-generated live artifact from real endpoint and credentials;
- local Intel DCAP quote verification;
- PCCS or collateral fetch/caching;
- JWKS fetching;
- managed-service signature fetch/verification;
- TLS or attested-TLS channel binding;
- official benchmark submission;
- accepted Evidence Ledger mutation.
