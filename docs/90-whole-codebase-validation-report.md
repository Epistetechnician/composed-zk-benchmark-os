# Whole Codebase Validation Report

Status: local validation report only.

This report records the end-to-end local validation run after Phase S
audit-index ergonomics output plumbing, protected-path overlap hardening, the
Phase 102 opt-in Phala provider-client implementation, the Phase 105
operator-only live runner implementation, and the Phase 106 Phala Cloud API
live artifact materialization implementation. It
evaluates the implemented codebase as a local Level 1 Rust foundation by
running the available workspace gates and mapping those gates to the repo's
major behavioral surfaces.

It does not claim per-function formal correctness, line coverage, accepted
Evidence Ledger mutation, official benchmark evidence, ZK backend performance,
Level2+ evidence, live provider evidence, production readiness, semantic
correctness, or global software-agent uniqueness.

## State Slice

This report touches only:

- `crates/hsai-attestation-phala/examples/operator_live_phala_api_artifact.rs`
- `crates/hsai-attestation-phala/tests/phala_operator_live_api_artifact_contract.rs`
- `docs/106-phala-cloud-api-live-artifact-implementation-notes.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `README.md`
- `AGENTS.md`

It does not change Cargo metadata, fixtures, generated artifacts, accepted
Evidence Ledgers, benchmark packs, report bundles, audit-index outputs,
ergonomics outputs, package runtime files, command-line tools outside the
operator-only example, or UI artifacts.

## Validation Commands

Run from repository root during Phase 106 validation.

```sh
cargo fmt --all --check
cargo test -p hsai-attestation-phala
cargo test -p hsai-attestation-phala --features operator-live-provider
cargo test -p hsai-attestation-phala --test phala_operator_live_runner_contract
cargo test -p hsai-attestation-phala --test phala_operator_live_api_artifact_contract
cargo test -p hsai-e2e-harness --test claim_boundary_source_scan
cargo test --workspace
cargo test --workspace --features external-runner
cargo clippy --workspace --all-targets -- -D warnings
cargo clippy -p hsai-attestation-phala --all-targets --features operator-live-provider -- -D warnings
cargo clippy -p hsai-attestation-phala --features operator-live-provider --examples -- -D warnings
cargo doc --workspace --no-deps
cargo doc -p hsai-attestation-phala --features operator-live-provider --no-deps
cargo test -p zkbench-core --test repo_hygiene
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo llvm-cov --workspace --summary-only
git diff --check
```

All commands passed.

No `package.json` or `pnpm-lock.yaml` exists in this repository, so no `pnpm`
gate is available.

`cargo-llvm-cov 0.8.7` was available. The default workspace coverage pass
reported `84.49%` region coverage, `80.65%` function execution, and `82.53%`
line coverage. Branch coverage was not reported by this run. The optional
`operator-live-provider` feature was validated by feature-specific test, clippy,
and doc gates above; it is not included in the default workspace coverage
summary unless coverage is run again with that feature enabled.

These coverage percentages are local test instrumentation only; they are not
100% coverage, production readiness, semantic correctness, official benchmark
evidence, accepted Evidence Ledger mutation, or Level2+ evidence.

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
- Phase V local artifact campaign manifest validation, Phase U output-root
  validation before campaign input construction, deterministic validation
  reports and Markdown rendering, declared-file output, digest sidecars,
  stale-digest rejection, symlink-resolved protected overlap rejection, symlink
  rejection, partial-campaign rejection, corrupted-root non-repair, accepted
  Evidence Ledger non-mutation, score-axis non-population, and protected-path
  overlap hardening.
- HSAI claim-envelope algebra, agent-case lanes, distinct-agent registry,
  managed attestation, offline managed-JWT verification, Phala fixture and
  captured-artifact validation, hermetic fake-client live-verifier surface,
  operator-live artifact plumbing, opt-in Phala provider-client plumbing,
  operator-live runner source-contract checks, Phase 4 anchor registry,
  economy, membrane, economy simulation, and e2e harness invariants.

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
  the future concrete provider-client boundary behind the Phase 100 seam.
  `docs/102-phala-operator-live-provider-client-implementation-notes.md` now
  records an opt-in feature-gated provider-client implementation with a
  transport seam, allowlisted environment credential provider, ureq-backed HTTP
  transport, raw-response digest replacement, and hermetic fake-transport
  tests. `docs/104-phala-operator-live-runner-boundary-spec.md` defines the
  operator-only runner boundary, and
  `docs/105-phala-operator-live-runner-implementation-notes.md` records the
  feature-gated `operator_live_run` example that requires explicit
  acknowledgement, non-secret invocation JSON, matching credential-source
  declaration, and an operator-owned credential environment.
  `docs/106-phala-cloud-api-live-artifact-implementation-notes.md` records the
  Phala Cloud API response materialization path. During Phase 106, an
  operator-run Phala Cloud `/attestations/verify` call accepted the submitted
  TDX quote with checksum
  `5c99c72274ed0745f7788cdf272cc359099c07629833306d1a13f1b8e34596bd`, and a
  local redacted `operator-live/*` artifact was generated outside git. No
  generated operator artifact is committed, and no local DCAP/PCCS/JWKS/TLS
  path, accepted Evidence Ledger mutation, official benchmark submission, or
  claim above `Attested` exists.
- No committed generated benchmark artifact bundle, official benchmark
  submission, or accepted Evidence Ledger entry was created. Phase U now
  implements local artifact-bundle packaging APIs and hermetic temp-root tests,
  but it does not create durable submitted artifacts or promote them.
  `docs/98-phase-v-local-artifact-campaign-boundary-spec.md` defines the
  durable local artifact campaign boundary, and
  `docs/103-phase-v-local-artifact-campaign-implementation-notes.md` records
  local campaign output-plumbing APIs and hermetic tests. No committed durable
  campaign output, official submission package, accepted Evidence Ledger
  mutation, score-axis population, external replay evidence, or Level2+
  evidence exists.
  `docs/99-phase-w-reviewed-evidence-promotion-boundary-spec.md` now defines the
  future reviewed accepted-evidence and official-submission boundary. No durable
  submitted artifact, official submission package, accepted Evidence Ledger
  mutation, score-axis population, external replay evidence, or Level2+ evidence
  exists.
- No broader Phase S ergonomics surface was authorized or tested beyond the
  implemented single-index local output boundary.

Any next broadening should start with a docs-first boundary and should name the
state slice before mutation.
