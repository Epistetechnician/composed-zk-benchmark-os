# Agent Rules

## Scope

This repository has been explicitly promoted from the documentation-only Level 0 scaffold to a Level 1 local Rust foundation. Future agents must treat every mutation as a named state slice. Do not infer mutation scope from imports, file names, or convenience.

Allowed in the current Level 1 state:

- Markdown documentation.
- Architecture, schemas, pseudo-types, and pseudo-traits.
- Source inventories and adapter plans.
- Validation checks over the documentation tree.
- Cargo workspace metadata.
- Rust source under `crates/zkbench-core/src/`.
- Rust integration tests and small YAML fixtures under `crates/zkbench-core/tests/`.
- Local JSON replay manifests, local replay results, local evidence ledgers, and benchmark pack skeleton code under `crates/zkbench-core`.
- zk-Harness dry-run adapter preparation types, tests, and docs under `crates/zkbench-core` and `docs/`.
- External-runner boundary, manual handoff bundle, artifact capture contract, provenance contract, result import validation schema, and quarantine types under `crates/zkbench-core` and `docs/`.
- Synthetic result import, normalization, quarantine flow, evidence append proposal, review-state, proposal ledger, and small JSON fixtures under `crates/zkbench-core` and `docs/`.

Forbidden in the current Level 1 state:

- `package.json`, `pnpm-lock.yaml`, `yarn.lock`, `package-lock.json`, `node_modules`, JavaScript or TypeScript runtime files, `Makefile`, CI files, generated benchmark artifacts, or benchmark outputs.
- External repo clones or vendored source.
- Fabricated benchmark results.
- Claims that any backend is formally verified unless a future evidence ledger proves the scoped claim.

## Claim Boundaries

Use these statements as hard boundaries:

- A benchmark pass is not a proof.
- A local replay is not official benchmark evidence.
- A formal proof about one layer is not a formal proof about the full system.
- A recursion proof is not semantic proof.
- A backend rejection is not automatically semantic correctness.
- A timeout is not automatically a soundness failure.
- A successful proof is not automatically evidence that the source spec was meaningful.
- A single aggregate score must not hide weak soundness evidence.
- Local replay artifacts are not official benchmark evidence.
- Evidence ledgers are local integrity records, not tamper-proof proof systems.
- Phase F benchmark packs are local packs only.
- Future agents must not reinterpret local oracle results as ZK backend results.
- zk-Harness dry-run plans are inert design artifacts.
- zk-Harness dry-run plans are not benchmark results.
- External execution is disabled by default.
- Future agents must not enable external execution without an explicit new phase.
- Future agents must not reinterpret dry-run plans as benchmark results.
- Future agents must not import external zk-Harness data without provenance and validation.
- Future agents must not elevate claim boundaries from local packs.
- External execution is disabled unless a future explicit phase enables it.
- Manual handoff bundles are not benchmark results.
- Result import candidates are quarantined or pending review until validated.
- Future agents must not convert imported data into Level2 evidence without artifact and provenance validation.
- Future agents must not reinterpret handoff bundles as zk-Harness execution.
- Synthetic result candidates are not benchmark results.
- Evidence append proposals are not accepted evidence.
- Proposal ledgers are review ledgers only and must not mutate the accepted Evidence Ledger.
- Future agents must not treat synthetic metric candidates as performance evidence.

The architecture docs remain Level 0 design notes. The Rust core crate is Level 1 local implementation foundation only.

## Validation Instructions

For the current Level 1 Rust foundation, validate:

```sh
ROOT="/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os"
find "$ROOT" -type f | sort
find "$ROOT" -type f | sort | sed "s#^$ROOT/##"
find "$ROOT" -type f \( -name "package.json" -o -name "pnpm-lock.yaml" -o -name "yarn.lock" -o -name "package-lock.json" -o -path "*/node_modules/*" \)
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo test --workspace --features external-runner
cargo doc --workspace --no-deps
find "$ROOT" -type f -empty
grep -R "benchmark pass is not proof" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "recursion proof is not semantic proof" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "local replay is not official benchmark evidence" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "Manual handoff bundles are not benchmark results" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "Synthetic result candidates are not benchmark results" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "Evidence append proposals are not accepted evidence" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "std::process::Command" "$ROOT/crates/zkbench-core/src" || true
grep -R "Command::new" "$ROOT/crates/zkbench-core/src" || true
grep -R "prover_time\|verifier_time\|proof_size\|memory_usage\|constraint_count" "$ROOT/crates/zkbench-core/tests/fixtures" || true
```

If package scripts are introduced in a later phase, preserve `pnpm run lint` as the heavy gate and split fast gates into `lint:fast`, `test:focused`, `verify:contracts`, and `verify:full`.

## Updating Docs

Every doc edit must preserve terminology:

- Surface DSL
- Parsed AST
- Semantic IR
- Benchmark Family
- Benchmark Instance
- Mutation Variant
- Oracle
- Expected Verdict
- Backend Outcome
- Evidence Record
- Claim Boundary
- Score Report

When changing behavior, document public utilities under `docs/` before claiming completion.

## Future Rust Work

The Rust foundation now includes the DSL/core schema, deterministic local generation, the first mutation engine classes, local JSON replay, evidence ledger persistence, deterministic artifact digests, benchmark pack skeletons, zk-Harness dry-run adapter preparation, the reviewed external-runner boundary schema, and a local/synthetic result import prototype. The next slice may define reviewed proposal acceptance policy only. Do not run external benchmarks, claim official evidence, add dashboards, or broaden recursion/zkML support before proposal review, supersession, and future append eligibility are implemented and tested.

## External Repos

Default to wrap or reference, not fork. Fork only for upstream contribution or when an adapter cannot be implemented without changing upstream. Curated lists are discovery-only. Existing benchmark/formal/zkML/recursion repos are evidence sources and adapter targets, not feature sets to copy.

## Evidence Classification

Classify evidence before using it:

- Level 0: design note only.
- Level 1: local replay evidence.
- Level 2: reproducible benchmark artifact.
- Level 3: cross-backend replay evidence.
- Level 4: formal property statement.
- Level 5: machine-checked proof for a scoped property.
- Level 6: independently reproduced evidence.

Do not claim Level 2+ without artifacts. Do not claim Level 5 without a scoped machine-checked proof.

## Preserving The SOTA Wedge

The novelty is semantic benchmark generation with formal hooks and adversarial mutation scoring. Avoid adapter sprawl, dashboard-first work, and broad cloning. The core must stay centered on Semantic IR, Oracle, Expected Verdict, Backend Outcome, Evidence Record, Claim Boundary, and Score Report.
