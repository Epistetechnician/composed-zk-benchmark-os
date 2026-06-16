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
- Reviewed proposal acceptance policy, manual review decisions, evidence-record candidates, append previews, Level2 eligibility reports, review ledgers, and small JSON fixtures under `crates/zkbench-core` and `docs/`.
- Local soak run configuration, deterministic shard planning, resumable shard checkpoints, local soak runner APIs, internal benchmark OS telemetry, local health reports, failure corpus extraction, report bundle schemas, tests, and docs under `crates/zkbench-core` and `docs/`.

Explicit HSAI claim-envelope phase now allowed: standalone Rust source, tests, and crate metadata under `crates/hsai-claim-envelope`, workspace membership for that crate, and phase notes under `docs/`. This phase is limited to the Level 1 local claim-envelope data model, deterministic provenance hashing, `top()`, `conjoin()`, and acceptance-policy algebra from `docs/23-claim-envelope-implementation-spec.md`; it does not permit identity, economy, evidence lanes, external rails, backend execution, benchmark outputs, or conflating HSAI code with `zkbench-core`.

Explicit HSAI agent-case phase now allowed: standalone Rust source, tests, and crate metadata under `crates/hsai-agent-case`, workspace membership for that crate, and phase notes under `docs/`. This phase is limited to local `AgentCase` data, the `CaseSource` and `EvidenceLane` interfaces, and the honest `DeclaredLane` and `LocalMemoryLane` reference lanes from `docs/26-agent-case-evidence-lane-spec.md`; it does not permit distinct-agent identity, economy, real ZK or TEE lanes, network access, external rails, backend execution, benchmark outputs, or changes to `zkbench-core` or `hsai-claim-envelope`.

Explicit HSAI distinct-agent phase now allowed: standalone Rust source, tests, and crate metadata under `crates/hsai-distinct-agent`, workspace membership for that crate, and phase notes under `docs/`. This phase is limited to anchor data, conditional `DistinctAgentLane` envelope emission, and the minimal deterministic `IdentityRegistry` from `docs/29-distinct-agent-lane-spec.md`; it does not verify attestations, stakes, or credentials, does not permit economy, harness, interop, network access, real ZK or TEE verification lanes, backend execution, benchmark outputs, or changes to existing crates.

Explicit HSAI economy phase now allowed: standalone Rust source, tests, and crate metadata under `crates/hsai-economy`, workspace membership for that crate, and phase notes under `docs/`. This phase is limited to signed in-memory credits, admitted-work reward records, the floor-plus-demand peg stub, demurrage and mutual-credit pool policies, and a deterministic `Economy` ledger gated on the L2 `IdentityRegistry` from `docs/32-economy-stub-spec.md`; it does not permit regenerative-economy claims, external rails, membrane conversion, real settlement, real demand verification, full corrigibility, backend execution, benchmark outputs, or changes to existing crates.

Explicit HSAI membrane phase now allowed: standalone Rust source, tests, and crate metadata under `crates/hsai-membrane`, workspace membership for that crate, phase notes under `docs/`, and exactly two authorized `hsai-economy` methods, `Economy::debit_external` and `Economy::credit_external`, with focused tests. This phase is limited to bounded in-memory conversion between internal `Credits` and opaque `ExternalAmount` units with L2 registration gating, freeze gating, and per-window autonomy-scaled caps from `docs/35-membrane-spec.md`; it does not permit real rails, settlement, fees, external resource control, full corrigibility, backend execution, benchmark outputs, or other changes to existing crates.

Explicit HSAI economy-simulation phase now allowed: standalone Rust source, tests, and crate metadata under `crates/hsai-economy-sim`, workspace membership for that crate, phase notes under `docs/`, and a measured A5 update under `docs/research/assumption-ledger.md`. This phase is limited to a deterministic integer simulation harness over the shipped HSAI economy from `docs/38-economy-simulation-spec.md`; it does not permit new protocol primitives, empirical economic claims, pool-demurrage economy changes, external rails, backend execution, benchmark outputs, or changes to existing crates.

Explicit HSAI funding-rule sweep phase now allowed: backward-compatible Rust source and tests under `crates/hsai-economy-sim`, phase notes under `docs/`, and an append-only A5 refinement under `docs/research/assumption-ledger.md`. This phase is limited to adding `FundingRule`, `run_with_funding`, `SweepCell`, and `sweep` from `docs/41-funding-rule-sweep-spec.md`; it does not permit changes to any other crate, empirical economic claims, new funding mechanisms beyond the three probes, pool-demurrage economy changes, external rails, backend execution, or benchmark outputs.

Explicit HSAI attestation-verification phase now allowed: standalone Rust source, tests, and crate metadata under `crates/hsai-attestation`, workspace membership for that crate, and phase notes under `docs/`. This phase is limited to the interface-level attestation lane from `docs/44-attestation-verification-lane-spec.md`: the `Token`/`VerifiedAttestation`/`VerifyError` types, the `AttestationVerifier` trait, the reference `ManagedTokenVerifier` (which checks anchor id, nonce, measurements, and freshness but does NOT verify the managed service signature), and `AttestationLane` emitting an `Attested` (never `Proven`) anchor-validity `ClaimEnvelope` that discharges the distinct-agent open assumption. It does not permit real managed-service signature verification, JWKS/JWT or vendor-quote validation, network access, real ZK or TEE verification, GPU attestation formats, onchain verification, backend execution, benchmark outputs, or changes to existing crates. A verified attestation is not a proof: it establishes hardware-bounded distinctness only, under the assumption that the managed service signed the token honestly — the signature check is the deferred real step where the stack leaves pure-data.

Explicit HSAI Phala/dstack attestation phase now allowed: standalone Rust source, tests, and crate metadata under `crates/hsai-attestation-phala`, workspace membership for that crate, small non-secret captured fixtures under `crates/hsai-attestation-phala/tests/fixtures/`, and phase notes under `docs/`. This phase is limited to parsing and validating a real captured Phala/dstack Trust Center artifact: raw TDX quote hex, report data, app compose hash, RTMR/event-log data, Docker image digests when present, observed timestamp, anchor id, agent public key, nonce, case hash, and explicit managed-verifier trust roots. It may validate report-data equality, compose-file SHA-256 hash, RTMR3 event-log replay against the quoted RTMR3, freshness, anchor id, and required Docker digests. The selected verification mode is managed Phala Trust Center/dstack verifier response, so Phala Trust Center, Intel Trust Authority, dstack OS image metadata, and the captured compose hash must remain visible trust roots. This phase does not permit local Intel DCAP quote verification, JWKS/JWT validation, network access during tests, real ZK or TEE proof elevation, backend execution, benchmark outputs, Phase 4 anchor registry work, or changes to existing crates beyond workspace metadata. Output remains `Attested`, never `Proven`; Phase 4 stays blocked until a real hardware-backed captured artifact passes this path.

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
- Evidence-record candidates are not accepted evidence.
- Append previews are not accepted evidence and must not mutate the accepted Evidence Ledger.
- Level2 eligibility reports are not Level2 evidence.
- Review ledgers are review artifacts only and must not mutate the accepted Evidence Ledger.
- Proposal ledgers are review ledgers only and must not mutate the accepted Evidence Ledger.
- Future agents must not treat synthetic metric candidates as performance evidence.
- Local soak telemetry is not official benchmark evidence.
- Internal timing telemetry is not ZK backend performance.
- Failure corpus entries are reproduction aids, not accepted evidence.
- Future agents must not use soak timing as prover/verifier timing.
- Future agents must not commit large soak outputs unless explicitly requested.
- Future agents must run long soak jobs only with explicit user approval and outside normal tests.
- Future agents must preserve shard resumability and claim-boundary checks.

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
grep -R "Evidence-record candidates are not accepted evidence" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "Level2 eligibility reports are not Level2 evidence" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "Local soak telemetry is not official benchmark evidence" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "Internal timing telemetry is not ZK backend performance" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "Failure corpus entries are reproduction aids" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "std::process::Command" "$ROOT/crates/zkbench-core/src" || true
grep -R "Command::new" "$ROOT/crates/zkbench-core/src" || true
grep -R "prover_time\|verifier_time\|proof_size\|zk_harness_time\|memory_usage\|constraint_count" "$ROOT/crates/zkbench-core/tests/fixtures" || true
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

The Rust foundation now includes the DSL/core schema, deterministic local generation, the first mutation engine classes, local JSON replay, evidence ledger persistence, deterministic artifact digests, benchmark pack skeletons, zk-Harness dry-run adapter preparation, the reviewed external-runner boundary schema, a local/synthetic result import prototype, reviewed proposal acceptance primitives, a deterministic local soak runner, internal benchmark OS telemetry, local health reports, and failure corpus extraction. The next slice should run longer local soak execution and sampled local report generation only with explicit user approval. Do not run external benchmarks, claim official evidence, add dashboards, or broaden recursion/zkML support before local soak telemetry proves the internal review/candidate/preview flow remains deterministic.

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
