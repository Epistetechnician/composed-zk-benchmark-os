# Phala Operator Live Invocation Boundary Spec

Status: docs-first boundary only.

This phase defines the next missing operator-live boundary after the local
operator artifact output plumbing in `docs/85-phala-operator-live-artifact-output-plumbing-implementation-notes.md`.
It does not authorize Rust implementation code, examples, scripts, package
runtime files, network access, live Phala API calls, operator live tests,
credentials, generated operator artifacts, local DCAP verification, PCCS
fetching, JWKS fetching, TLS channel binding, benchmark outputs, accepted
Evidence Ledger mutation, or claims above `Attested`.

## State Slice

This docs-first phase may touch only:

- `docs/97-phala-operator-live-invocation-boundary-spec.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`
- `docs/90-whole-codebase-validation-report.md`

No crate, Cargo metadata, `Cargo.lock`, fixture, generated operator artifact,
benchmark pack, report bundle, audit index, package runtime file, credential
file, accepted Evidence Ledger, or submission artifact is changed by this
phase.

## Purpose

The current repository can validate and materialize non-secret operator-live
artifact bundles locally. The remaining live gap is the absent invocation
contract for a future operator-owned process that may call the Phala/dstack
managed verifier and then feed the redacted normalized response into the
existing local artifact plumbing.

This boundary defines that future invocation contract before any networked
code exists. It keeps the live provider path operator-only, excluded from
normal tests, and capped at managed-verifier `Attested` evidence.

## Provider And Mode

The future invocation path may name exactly one provider and one mode:

```text
provider: Phala/dstack
mode: operator-owned live managed-verifier invocation
```

No Azure, Intel, Apple, Darkbloom, zkTLS, onchain, generic TEE, generic HTTP,
or multi-provider path is authorized by this boundary.

## Future Invocation Inputs

A future implementation phase may define an ignored or feature-gated operator
invocation only if every input is explicit:

- operator run id;
- provider endpoint;
- caller-owned credential source;
- explicit operator acknowledgement;
- bounded timeout;
- bounded retry limit;
- request nonce;
- expected report-data binding;
- expected compose hash;
- expected runtime measurements;
- expected image digest;
- expected managed-verifier trust-root ids;
- caller-owned output root already accepted by the Phase 85 output plumbing.

No default value may trigger a live provider call. Missing acknowledgement,
missing credential source, empty endpoint, unbounded timeout, unbounded retry,
or output-root overlap must fail before network access.

## Credential Boundary

Future credentials must remain outside git and outside normal tests. A future
implementation may only accept credentials through an explicit operator-owned
mechanism such as an environment variable name or caller-provided credential
provider. It must not commit secrets, credential fixtures, raw headers, bearer
tokens, cookies, registry credentials, cloud credentials, deployment
credentials, private keys, or machine identifiers not intended for publication.

Credential values must never be copied into operator artifacts. The redaction
report must prove credential-shaped fields were removed or hashed before any
output file is written.

## Future Invocation Flow

A future implementation must fail closed in this order:

1. require explicit operator acknowledgement;
2. validate timeout and retry bounds;
3. load the credential through the caller-owned boundary;
4. build a non-secret request from declared inputs only;
5. call the Phala/dstack managed verifier once per bounded attempt;
6. redact the raw response before any write;
7. normalize the response into the existing local response model;
8. validate provider, mode, nonce, freshness, report data, compose hash,
   measurements, image digest, verdict, and trust roots;
9. materialize only the declared operator-live files through the Phase 85
   output plumbing;
10. emit at most `Attested` managed-verifier evidence.

Timeouts, transport errors, provider errors, malformed responses, stale
responses, replayed nonces, missing roots, and rejected provider verdicts must
emit diagnostics only. They must not emit guarantees or verifier trust roots.

## Normal Test Exclusion

The future invocation path must remain outside normal gates:

- `cargo test --workspace`
- `cargo test --workspace --features external-runner`
- `cargo clippy --workspace --all-targets -- -D warnings`
- `cargo doc --workspace --no-deps`

If any operator-live test exists, it must be ignored, feature gated, or placed
behind an explicit operator-only command that normal CI and normal local gates
do not execute.

## Required Future Tests

A future implementation phase must include hermetic tests for:

- missing operator acknowledgement;
- missing credential source;
- empty endpoint;
- unbounded timeout rejection;
- unbounded retry rejection;
- credential-shaped response redaction;
- refusal to write unredacted raw response bodies;
- timeout diagnostic mapping;
- retry exhaustion diagnostic mapping;
- provider rejection mapping;
- stale response rejection;
- replayed nonce rejection;
- missing trust-root rejection;
- attempted claim above `Attested`;
- attempted accepted Evidence Ledger mutation;
- normal workspace tests requiring no network and no credentials.

Operator-live tests that actually call Phala must not be normal tests.

## Non-Claims

A future successful invocation is not proof, not local DCAP verification, not
managed-service signature/JWKS/JWT verification, not TLS channel binding, not
benchmark evidence, not official benchmark evidence, not semantic correctness,
not global software-agent uniqueness, and not authorization to mutate an
accepted Evidence Ledger.

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

- This spec exists and names the future operator-live invocation boundary.
- README navigation links this spec.
- `docs/12-task-list.md` records this docs-first boundary.
- `AGENTS.md` authorizes only this Markdown planning slice.
- `docs/90-whole-codebase-validation-report.md` records that invocation remains
  unimplemented.
- Validation confirms no Rust source, Cargo metadata, fixture, generated
  artifact, credential path, network path, benchmark output, official
  submission, or accepted Evidence Ledger changed.
