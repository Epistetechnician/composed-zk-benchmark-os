# Phala Operator Live Runner Boundary Spec

Status: docs-first boundary only.

This phase defines the operator-only runner boundary after the Phase 102
provider-client implementation. It does not by itself perform a live Phala
call, create a generated operator artifact, mutate accepted evidence, submit an
official benchmark, or implement local DCAP/PCCS/JWKS/TLS verification.

## State Slice

This docs-first phase may touch only:

- `docs/104-phala-operator-live-runner-boundary-spec.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`
- `docs/90-whole-codebase-validation-report.md`

No crate source, Cargo metadata, `Cargo.lock`, fixture, generated operator
artifact, benchmark pack, report bundle, audit index, package runtime file,
credential file, accepted Evidence Ledger, score report, or submission artifact
is changed by this boundary slice.

## Purpose

The repository already has:

- redacted `operator-live/*` output-root plumbing;
- a fail-closed invocation orchestrator;
- an allowlisted environment credential provider;
- a feature-gated Phala/dstack HTTP provider client.

The remaining runner gap is the absent operator-facing command path that wires
those existing pieces together without making normal tests depend on network
access or credentials.

## Future Runner Contract

A future implementation phase may add one operator-only runner under
`crates/hsai-attestation-phala/examples/`. The runner must:

- be gated by `operator-live-provider`;
- require explicit operator acknowledgement;
- read a non-secret invocation JSON path from the environment;
- require the operator-declared credential source to match the invocation JSON;
- allow only that credential source for environment credential loading;
- construct `PhalaOperatorLiveProviderClient<UreqPhalaOperatorLiveTransport>`;
- invoke only through `PhalaOperatorLiveInvocation`;
- write only through existing Phase 85/100 artifact plumbing;
- print only non-secret validated metadata.

The runner must not hard-code endpoint paths, credential names, credential
values, response schemas beyond the existing normalized response type, or
provider-specific accepted-evidence semantics.

## Source Refresh

The Phase 102 implementation already rechecked Phala documentation on
2026-06-22 and intentionally kept the endpoint operator-supplied. For this
runner boundary, current Phala documentation still separates application quote
generation from verifier-side checking and documents the managed verifier API
as a provider endpoint selected by the operator. The runner therefore must keep
endpoint and response authority outside the repo and inside the supplied
operator input.

## Required Future Tests

A future implementation phase must include hermetic tests or source-contract
checks proving:

- the runner requires explicit acknowledgement;
- the runner requires a non-secret input JSON path;
- the runner requires an operator-declared credential source;
- the runner has no hard-coded endpoint;
- the runner has no hard-coded credential name or secret;
- the runner does not write raw response bodies;
- the runner uses the existing invocation orchestrator and output writer;
- normal workspace tests remain hermetic and require no credentials.

## Non-Claims

An operator runner is not proof, not local DCAP verification, not PCCS
collateral verification, not managed-service signature/JWKS/JWT verification,
not TLS channel binding, not benchmark evidence, not official benchmark
evidence, not semantic correctness, not global software-agent uniqueness, and
not authorization to mutate an accepted Evidence Ledger.

## Forbidden In This Slice

- Rust source changes.
- Cargo metadata changes.
- `Cargo.lock` changes.
- Running a live Phala API call.
- Operator live tests.
- Real credentials.
- Credential fixtures.
- Generated operator artifacts.
- Local Intel DCAP quote verification.
- PCCS or collateral fetch/caching code.
- Generic JWKS/JWT fetch code.
- TLS or attested-TLS implementation.
- Deployment orchestration.
- Backend execution.
- Benchmark outputs.
- Official benchmark submission.
- Accepted Evidence Ledger mutation.
- Phase 4 registry semantic changes.
- Level2+ evidence.
- Claims above `Attested`.

## Acceptance Criteria For This Slice

- This spec exists and names the future operator-only runner boundary.
- README navigation links this spec.
- `docs/12-task-list.md` records this docs-first boundary.
- `AGENTS.md` authorizes only this Markdown planning slice.
- `docs/90-whole-codebase-validation-report.md` records that an actual
  operator live run and generated operator artifact remain unexecuted.
