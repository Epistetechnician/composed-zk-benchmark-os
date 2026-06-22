# Phala Operator Live Provider Client Boundary Spec

Status: docs-first boundary only.

This phase defines the next provider-client boundary after the local operator
invocation plumbing in
`docs/100-phala-operator-live-invocation-implementation-notes.md`.
It does not authorize Rust implementation code, Cargo metadata changes,
`Cargo.lock` changes, examples, scripts, package runtime files, network access,
live Phala API calls, operator live tests, real credentials, credential
fixtures, generated operator artifacts, local Intel DCAP verification, PCCS
fetching, JWKS fetching, TLS channel binding, benchmark outputs, official
benchmark submission, accepted Evidence Ledger mutation, or claims above
`Attested`.

## State Slice

This docs-first phase may touch only:

- `docs/101-phala-operator-live-provider-client-boundary-spec.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`
- `docs/90-whole-codebase-validation-report.md`

No crate, Cargo metadata, `Cargo.lock`, fixture, example, script, generated
operator artifact, benchmark pack, report bundle, audit index, package runtime
file, credential file, accepted Evidence Ledger, or submission artifact is
changed by this phase.

## Purpose

The current repository can:

- construct operator-live invocation inputs;
- load opaque credentials through a caller-supplied provider boundary;
- call an injected credential-aware client in hermetic tests;
- validate normalized Phala/dstack managed-verifier responses;
- reject replayed nonces;
- materialize redacted digest-bound `operator-live/*` bundles through the
  Phase 85 output-root writer.

The remaining live-provider gap is that no concrete provider client exists.
This boundary defines the future operator-only client contract before any
networked implementation exists. It keeps the future live path explicit,
opt-in, excluded from normal tests, and capped at managed-verifier `Attested`
evidence.

## Provider And Mode

The future provider client may name exactly one provider and one mode:

```text
provider: Phala/dstack
mode: operator-owned live managed-verifier provider client
```

No Azure, Intel Trust Authority, Apple, Darkbloom, zkTLS, onchain, generic TEE,
generic HTTP multiplexer, or multi-provider abstraction is authorized by this
boundary.

## Future Code Touch Surface

A future implementation phase may add only the smallest concrete client surface
needed to implement `PhalaOperatorLiveClient` for Phala/dstack:

- a provider-client configuration type;
- an explicit operator credential source adapter;
- a single Phala/dstack client type implementing `PhalaOperatorLiveClient`;
- a raw-response redactor that emits only a digest plus declared retained
  non-secret fields;
- error mapping from transport/auth/provider/malformed-response failures into
  existing fail-closed invocation errors;
- hermetic tests over fake transport and fake credential sources;
- an ignored or feature-gated operator-only live test path, if separately
  authorized by the implementation phase.

The future implementation must reuse:

- `PhalaOperatorLiveInvocation`;
- `PhalaOperatorLiveInvocationInput`;
- `PhalaOperatorLiveCredentialProvider`;
- `PhalaOperatorLiveClient`;
- `PhalaManagedVerifierRequest`;
- `PhalaManagedVerifierResponse`;
- `write_phala_operator_live_artifact_output_root`.

It must not bypass the Phase 100 orchestrator or write operator artifacts
directly.

## Credential Source Contract

Future credentials must remain outside git and outside normal tests. A future
implementation may accept a credential only through an explicit operator-owned
source such as an environment variable name selected by the operator at runtime.

The future implementation must fail before network access when:

- the operator acknowledgement is absent;
- the credential source name is empty;
- the credential value is unavailable;
- the credential value is empty;
- the credential source is not explicitly allowed by the operator command;
- a normal test or default command would attempt to load a real credential.

Credential values must never be logged, serialized, committed, written to
operator artifacts, included in panic/debug output, copied into generated
digests except through the redacted raw-response digest, or retained in
redaction sidecars.

## Network And Retry Contract

Future provider-client implementation must be fail-closed and bounded:

- no default command may perform network access;
- endpoint must be explicitly supplied;
- timeout must be finite and bounded;
- retry limit must be finite and bounded;
- redirects must be disabled unless a future source-cited phase allows them;
- request body must contain only declared non-secret inputs;
- credential material may be used only in the outbound authorization boundary;
- raw response body must be redacted before any write;
- provider response must normalize into `PhalaManagedVerifierResponse` before
  it reaches the Phase 100 orchestrator;
- malformed responses, auth failures, transport errors, timeout, retry
  exhaustion, stale responses, replayed nonces, missing trust roots, and
  provider rejection must emit diagnostics only.

Diagnostics must not emit guarantees, verifier trust roots, accepted Evidence
Ledger entries, score-axis entries, benchmark claims, or claims above
`Attested`.

## Operator-Only Test And Command Contract

Normal gates must not require network access or credentials:

- `cargo test --workspace`
- `cargo test --workspace --features external-runner`
- `cargo clippy --workspace --all-targets -- -D warnings`
- `cargo doc --workspace --no-deps`

If a future live test exists, it must be ignored, feature gated, or placed
behind an explicit operator-only command that requires all of:

- explicit operator acknowledgement;
- explicit endpoint;
- explicit credential source;
- caller-owned output root;
- bounded timeout;
- bounded retry limit;
- declared expected nonce/report-data/compose/runtime/image/trust-root inputs.

The operator-only path must write only through the existing Phase 85/100
artifact plumbing and must be safe to omit from CI.

## Source Refresh Requirement

Before a future implementation hard-codes endpoint paths, request formats,
authentication header names, response fields, or status-code semantics, that
implementation phase must re-check current upstream Phala/dstack documentation
and record source attribution in `docs/research/zk_external_source_index.md` or
the implementation notes. This boundary intentionally does not freeze a live
API schema.

## Required Future Tests

A future implementation phase must include hermetic tests for:

- missing operator acknowledgement rejected before credential load;
- missing credential source rejected before network access;
- unavailable credential rejected before network access;
- empty endpoint rejected before network access;
- timeout bound rejection;
- retry bound rejection;
- auth failure mapping;
- transport timeout mapping;
- retry exhaustion mapping;
- malformed response mapping;
- provider rejection mapping;
- credential-shaped raw response redaction;
- refusal to write unredacted raw response body;
- refusal to serialize credential values or credential source names into
  artifacts;
- normal workspace tests requiring no network and no real credentials;
- attempted accepted Evidence Ledger mutation rejection;
- attempted claim above `Attested` rejection.

Any live Phala test must be operator-only and excluded from normal gates.

## Non-Claims

A future successful provider-client invocation is not proof, not local DCAP
verification, not PCCS collateral verification, not managed-service
signature/JWKS/JWT verification, not TLS channel binding, not benchmark
evidence, not official benchmark evidence, not semantic correctness, not global
software-agent uniqueness, and not authorization to mutate an accepted Evidence
Ledger.

## Forbidden In This Slice

- Rust source changes.
- Cargo metadata changes.
- `Cargo.lock` changes.
- Examples or scripts.
- Package runtime files.
- Network access.
- Live Phala API calls.
- Operator live tests.
- Credential handling code.
- Real credentials.
- Secret fixtures.
- Generated operator artifacts.
- Local Intel DCAP quote verification.
- PCCS or collateral fetch/caching code.
- Generic JWKS/JWT fetch code.
- TLS or attested-TLS implementation.
- Deployment orchestration.
- External repo clones or vendored source.
- Backend execution.
- Benchmark outputs.
- Official benchmark submission.
- Accepted Evidence Ledger mutation.
- Phase 4 registry semantic changes.
- Level2+ evidence.
- Claims above `Attested`.

## Acceptance Criteria For This Slice

- This spec exists and names the future Phala/dstack provider-client boundary.
- README navigation links this spec.
- `docs/12-task-list.md` records this docs-first boundary.
- `AGENTS.md` authorizes only this Markdown planning slice.
- `docs/90-whole-codebase-validation-report.md` records that the provider
  client remains unimplemented.
- Validation confirms no Rust source, Cargo metadata, fixture, example, script,
  generated artifact, credential path, network path, benchmark output,
  official submission, or accepted Evidence Ledger changed.
