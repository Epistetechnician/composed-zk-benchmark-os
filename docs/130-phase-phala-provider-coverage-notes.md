# Phase 130 Phala Provider Coverage Notes

Status: complete for a bounded local Phala operator-live provider-client
coverage campaign.

## State Slice

This phase touches only local `hsai-attestation-phala` provider-client tests,
documentation navigation, and the whole-codebase validation report.

Code changes are limited to:

- `crates/hsai-attestation-phala/tests/phala_operator_live_provider_client.rs`

## Purpose

Phase 130 continues the local coverage loop after Phase 129 by targeting the
opt-in Phala/dstack operator-live provider-client fail-closed paths. The goal
is higher local line coverage over already-implemented credential, config,
transport, and response-mapping behavior.

This phase does not change production Rust APIs. It does not add runtime
behavior, live Phala calls, operator live tests, network requirements,
credentials, generated operator artifacts, external replay, benchmark outputs,
official submission, accepted Evidence Ledger mutation, score-axis population,
Level2+ evidence, production-readiness claims, semantic-correctness claims, or
100% coverage.

## Added Coverage

The provider-client tests now cover:

- zero-timeout provider config rejection;
- disallowed credential source rejection before transport invocation;
- HTTP `403` authentication failure mapping;
- non-UTF-8 bearer-token rejection by the `ureq` transport before network
  construction; and
- focused preservation of the existing no-raw-response and no-secret artifact
  guarantees.

The added `PanicTransport` regression proves the client rejects an unapproved
credential source before touching transport code.

## Measurement

Before this phase, the Phase 129 all-feature workspace coverage pass reported:

- region coverage: `85.58%`
- function execution: `82.59%`
- line coverage: `83.74%`

After this phase, the all-feature workspace coverage pass reported:

- region coverage: `85.58%`
- function execution: `82.59%`
- line coverage: `83.76%`

The targeted
`hsai-attestation-phala/src/operator_live_provider.rs` line coverage improved
from `68.35%` to `75.54%` in the all-feature workspace coverage pass.

These are local instrumentation metrics only. They are not proof, not live
provider evidence, not official benchmark evidence, not accepted evidence, not
Level2+ evidence, and not 100% coverage.

## Anti-Goals

This phase does not permit production source changes, new public APIs, live
Phala calls, operator live tests, network access, credentials, generated
operator artifacts, committed output bundles, external replay, official
endpoint submission, accepted Evidence Ledger mutation, score-axis population,
ZK backend performance claims, formal evidence, SOTA claims,
production-readiness claims, semantic-correctness claims, or claiming 100%
coverage.

## Validation

Required validation for this phase:

```sh
cargo fmt --all -- --check
git diff --check
cargo test -p hsai-attestation-phala --features operator-live-provider --test phala_operator_live_provider_client
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --all-features
cargo clippy --workspace --all-targets --all-features -- -D warnings
RUSTDOCFLAGS='-D warnings' cargo doc --workspace --all-features --no-deps
cargo llvm-cov --workspace --all-features --summary-only
rg --files -g 'package.json' -g 'pnpm-lock.yaml' || true
```
