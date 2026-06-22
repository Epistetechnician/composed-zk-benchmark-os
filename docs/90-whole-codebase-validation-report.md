# Whole Codebase Validation Report

Status: local validation report only.

This report records the end-to-end local validation run after Phase S
audit-index ergonomics output plumbing and protected-path overlap hardening. It
evaluates the implemented codebase as a local Level 1 Rust foundation by
running the available workspace gates and mapping those gates to the repo's
major behavioral surfaces.

It does not claim per-function formal correctness, line coverage, accepted
Evidence Ledger mutation, official benchmark evidence, ZK backend performance,
Level2+ evidence, live provider evidence, production readiness, semantic
correctness, or global software-agent uniqueness.

## State Slice

This report touches only:

- `docs/90-whole-codebase-validation-report.md`
- `README.md`

It does not change Rust source, tests, Cargo metadata, fixtures, generated
artifacts, accepted Evidence Ledgers, benchmark packs, report bundles,
audit-index outputs, ergonomics outputs, package runtime files, command-line
tools, or UI artifacts.

## Validation Commands

Run from repository root on `master` after merge commit `696702e`.

```sh
cargo fmt --all --check
cargo test --workspace
cargo test --workspace --features external-runner
cargo clippy --workspace --all-targets -- -D warnings
cargo doc --workspace --no-deps
cargo test -p zkbench-core --test repo_hygiene
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo llvm-cov --workspace --summary-only
cargo llvm-cov --workspace --features external-runner --summary-only
git diff --check
```

All commands passed.

No `package.json` or `pnpm-lock.yaml` exists in this repository, so no `pnpm`
gate is available.

`cargo-llvm-cov 0.8.7` was available, but the local Rust installation required
explicit `LLVM_COV` and `LLVM_PROFDATA` environment variables pointing at the
rustup `llvm-tools-preview` binaries. With those variables set, the default
workspace pass and the `external-runner` feature pass reported the same totals:
`79.22%` region coverage, `79.89%` function execution, and `82.55%` line
coverage. Branch coverage was not reported by this run. These coverage
percentages are local test instrumentation only; they are not production
readiness, semantic correctness, official benchmark evidence, accepted Evidence
Ledger mutation, or Level2+ evidence.

## Efficacy Map

The suite exercises the repo as a set of bounded local systems:

- DSL parsing, lowering, oracle evaluation, and generated fixtures.
- Deterministic generation, mutation, local JSON replay, and stress paths.
- Evidence primitives, evidence ledgers, append previews, review ledgers,
  proposal ledgers, and candidate validation.
- Benchmark pack writing/reading, pack-readiness metadata, score reports, and
  local-only claim-boundary checks.
- zk-Harness dry-run planning, inert execution metadata, manual handoff mapping,
  and no-live-execution guards.
- Phase L soak configuration, sharding, resume checkpoints, telemetry, health
  reports, failure corpus, and local campaign aggregation.
- Phase M recursion-envelope metadata and manual handoff mapping.
- Phase N zkML workload manifest metadata.
- Phase O pack-readiness construction and output plumbing.
- Phase P read-only dashboard/reporting metadata.
- Phase Q report-bundle metadata and adjacent output plumbing.
- Phase R local audit-index metadata and adjacent output plumbing.
- Phase S audit-index ergonomics, materialized output plumbing, stale-digest
  rejection, symlink rejection, partial-bundle rejection, non-repair overwrite
  behavior, and protected-path overlap hardening.
- Phase T cross-bundle audit-index in-memory views and materialized output
  plumbing, duplicate/conflict signal preservation, declared-file output,
  digest sidecars, stale-digest rejection, symlink rejection, partial-bundle
  rejection, corrupted-root non-repair, and protected-path overlap hardening.
- Phase U local benchmark artifact manifest validation, deterministic Markdown
  rendering, declared-file output, digest sidecars, stale-digest rejection,
  symlink-resolved protected overlap rejection, symlink rejection,
  partial-bundle rejection, corrupted-root non-repair, accepted Evidence Ledger
  non-mutation, score-axis non-population, and protected-path overlap
  hardening.
- HSAI claim-envelope algebra, agent-case lanes, distinct-agent registry,
  managed attestation, offline managed-JWT verification, Phala fixture and
  captured-artifact validation, hermetic fake-client live-verifier surface,
  operator-live artifact plumbing, Phase 4 anchor registry, economy, membrane,
  economy simulation, and e2e harness invariants.

The strongest local statement supported by this run is:

The implemented local Rust foundation remains internally consistent under the
available unit, integration, doc, lint, formatting, hygiene, and claim-boundary
gates.

## Function-Level Boundary

This validation is function-aware through Rust unit tests, integration tests,
doc tests, clippy, and public API documentation generation. It is not
function-exhaustive proof.

The suite checks behavior through invariants, round trips, adversarial
fixtures, source scans, failure-mode tests, and cross-crate composition tests.
It does not prove that every function is covered by a test, that every branch is
exercised, or that every valid domain input has been sampled.

## Wholeness Boundary

The repo's current wholeness is local and compositional:

- local data models are serialized, deserialized, digested, and validated;
- output plumbing rejects drift instead of repairing corrupted roots;
- source metadata mutation remains forbidden where phases require read-only
  behavior;
- claim boundaries remain capped at their documented levels;
- live provider behavior, network calls, external benchmark execution, and
  official evidence promotion remain blocked unless a later explicit phase
  authorizes them.

This is not production readiness and not benchmark evidence. It is local
regression evidence that the implemented parts still fit together without
claim-boundary escalation.

## Residual Gaps

- No live external backend, live Phala call, DCAP/PCCS/JWKS fetching, or TLS
  channel binding was exercised.
  `docs/97-phala-operator-live-invocation-boundary-spec.md` now defines the
  docs-first invocation boundary, and
  `docs/100-phala-operator-live-invocation-implementation-notes.md` now records
  local invocation plumbing with a hermetic credential-provider boundary,
  injected client boundary, redacted artifact-bundle assembly, replay checks,
  and fail-closed tests. No shipped network client, live Phala call, real
  operator credential source, operator live test, DCAP/PCCS/JWKS/TLS path, or
  generated operator artifact exists.
  `docs/101-phala-operator-live-provider-client-boundary-spec.md` now defines
  the future concrete provider-client boundary behind the Phase 100 seam, but
  no provider-client implementation, network path, real credential source, live
  call, operator live test, or generated operator artifact exists.
- No committed generated benchmark artifact bundle, official benchmark
  submission, or accepted Evidence Ledger entry was created. Phase U now
  implements local artifact-bundle packaging APIs and hermetic temp-root tests,
  but it does not create durable submitted artifacts or promote them.
  `docs/98-phase-v-local-artifact-campaign-boundary-spec.md` now defines the
  future durable local artifact campaign boundary, and
  `docs/99-phase-w-reviewed-evidence-promotion-boundary-spec.md` now defines the
  future reviewed accepted-evidence and official-submission boundary. No durable
  campaign output, official submission package, accepted Evidence Ledger
  mutation, score-axis population, external replay evidence, or Level2+ evidence
  exists.
- No broader Phase S ergonomics surface was authorized or tested beyond the
  implemented single-index local output boundary.

Any next broadening should start with a docs-first boundary and should name the
state slice before mutation.
