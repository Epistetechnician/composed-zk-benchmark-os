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
git diff --check
```

All commands passed.

No `package.json` or `pnpm-lock.yaml` exists in this repository, so no `pnpm`
gate is available.

`cargo llvm-cov` is not installed in this environment, so this report does not
claim line, branch, or per-function coverage percentages.

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

- No coverage tool was available in this environment.
- No live external backend, live Phala call, DCAP/PCCS/JWKS fetching, TLS
  channel binding, or operator-live credential path was exercised.
- No generated benchmark artifacts, official benchmark submissions, or accepted
  Evidence Ledger entries were created.
- No cross-bundle audit-index construction or broader Phase S ergonomics surface
  was authorized or tested beyond the implemented single-index local output
  boundary.

Any next broadening should start with a docs-first boundary and should name the
state slice before mutation.
