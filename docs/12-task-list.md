# Task List

Each phase names goal, deliverables, dependencies, validation gate, anti-goals, and exit criteria.

## Phase A: Documentation Scaffold

Status: complete.

Goal: Create Level 0 design foundation.

Deliverables: README, AGENTS, project brief, source inventory, integration map, architecture, decisions, adapter roadmap, DSL schema, Rust module layout, benchmark taxonomy, mutation engine, scoring rubric, validation gates, semantic/oracle spine, integration docs, research index.

Dependencies: User-provided goalone spec.

Validation gate: docs-only validation in `docs/11-validation-gates.md`.

Anti-goals: runtime code, package files, external clones, fake results.

Exit criteria: exact scaffold exists, non-empty docs, README links all files, no forbidden files.

## Phase B: Rust DSL/Core Schema

Status: complete for the Level 1 local foundation.

Goal: Implement Surface DSL, Parsed AST, Semantic IR, and schema validation.

Deliverables: Rust types for spec, AST, Semantic IR, oracle declarations, witness policy, mutation declarations.

Implemented: `zkbench-core` parses YAML fixtures, validates Surface DSL, lowers Parsed AST into canonical Semantic IR, and defines evidence, replay, adapter-trait, generator, mutation, and scoring primitives.

Dependencies: Phase A.

Validation gate: `test:focused`, `verify:contracts`, future `pnpm run lint`.

Anti-goals: adapters, dashboard, benchmark claims.

Exit criteria: valid and invalid sample specs parse and lower deterministically.

## Phase C: Semantic IR And Oracle Evaluator

Status: partially complete for the v0 executable subset.

Goal: Evaluate trace validity, transition relation, invariant satisfaction, witness policy, and expected verdicts.

Deliverables: OracleEvaluator, TraceSpec validation, result classification.

Implemented: v0 local oracle for simple guards/actions, trace evaluation, and result classification. Remaining: broader invariant scopes, witness-policy evaluation, public/private boundary semantic checks, and richer executable semantics.

Dependencies: Phase B.

Validation gate: focused oracle tests and contract checks.

Anti-goals: backend execution.

Exit criteria: examples from `06-dsl-schema.md` produce expected verdicts.

## Phase D: Generator

Status: complete for local v0 deterministic generation.

Goal: Expand seed specs into Benchmark Families and Benchmark Instances.

Deliverables: deterministic FamilyGenerator with tunables.

Implemented: `GeneratorConfig`, `GeneratorSeed`, `GeneratorProfile`, `GeneratorTunables`, `GeneratorLimits`, `DeterministicGenerator`, `GeneratedBenchmarkFamily`, `GeneratedBenchmarkInstance`, `InstanceParams`, `GenerationProvenance`, `FamilyTemplate`, and `FamilyKind`. Local v0 generators exist for BaselineFsm, BranchingFsm, and BoundedCounterLoop.

Dependencies: Phase C.

Validation gate: deterministic generation tests.

Anti-goals: random uncontrolled generation.

Exit criteria: generated instances bind seed, tunables, and semantic equivalence class.

## Phase E: Mutation Engine

Status: complete for the v0 mutation classes; broader taxonomy remains future.

Goal: Produce valid, near-valid, malicious, and invalid Mutation Variants.

Deliverables: mutation taxonomy implementation and provenance.

Implemented: `MutationEngine`, `MutationPass`, `MutationPlan`, `MutationApplication`, `MutationProvenance`, `MutationInput`, `MutationOutput`, `MutatedBenchmarkInstance`, `MutationExpectedVerdict`, and `MutationSafetyClass`. Local v0 passes exist for MissingConstraints, CorruptedGuards, and BadCounters. Remaining mutation classes are future work.

Dependencies: Phase C and D.

Validation gate: mutation contract tests.

Anti-goals: mutations without expected verdicts.

Exit criteria: each required mutation class has a tested example.

## Phase F: Mock/Local JSON Adapter

Status: complete for local-only Phase F.

Goal: Exercise evidence normalization without external dependencies.

Deliverables: `LocalJsonAdapter`, `ReplayManifest`, `ReplayResult`, deterministic replay serialization, deterministic artifact digesting, persistent `EvidenceLedger`, `BenchmarkPackWriter`, `BenchmarkPackReader`, conservative `ScoreReport` emission, and local reproducibility tests.

Dependencies: Phase E.

Validation gate: `cargo test --workspace`, replay JSON round-trip tests, evidence ledger digest-chain tests, benchmark pack digest validation tests.

Anti-goals: external adapters.

Exit criteria: local JSON adapter reports accepted/rejected/capability_gap/inconclusive outcomes, emits Level1LocalReplay evidence records, writes local packs with relative paths and digest validation, and does not invoke external commands.

## Phase G: zk-Harness Dry-Run Adapter Preparation

Status: complete for dry-run adapter preparation.

Goal: Prepare the zk-Harness adapter contract without live benchmark execution.

Deliverables: `ZkHarnessAdapterManifest`, dry-run plan types, inert planned command descriptions, external execution policy disabled by default, local pack mapping, candidate family/mutation labels, metric mapping schema, evidence policy, claim-boundary policy, and validation tests.

Dependencies: Phase F.

Validation gate: zk-Harness manifest round-trip tests, dry-run plan round-trip tests, pack mapping tests, inertness tests, claim-boundary tests, and source scans for process execution APIs.

Anti-goals: modifying zk-Harness internals, running live zk-Harness benchmarks, official performance numbers, or Level2+ evidence claims.

Exit criteria: reviewed dry-run adapter contract with no external execution and no benchmark evidence claims.

## Phase H: Reviewed External-Runner Boundary

Status: complete for boundary/schema implementation.

Goal: Define an opt-in boundary for future external zk-Harness execution without benchmark claims.

Deliverables: explicit opt-in external execution feature flag, manual handoff bundle schema, dry-run-to-manual-handoff mapping, artifact capture contract, provenance contract, result import validation schema, quarantine schema, and reviewed disabled-by-default policy.

Implemented: `ExternalRunnerPolicy`, `ExternalExecutionMode`, `ExternalExecutionGate`, manual handoff bundle types, artifact capture contract types, provenance contract types, external result import schema and candidate validation, quarantine manifest types, zk-Harness dry-run plan to manual handoff mapping, JSON round-trip helpers, and claim-boundary tests.

Dependencies: Phase G.

Validation gate: external-runner policy tests, manual handoff bundle tests, artifact capture contract tests, result import validation tests, quarantine tests, zk-Harness manual handoff tests, claim-boundary tests, and source scans for process execution APIs.

Anti-goals: default external execution, automatic zk-Harness cloning, official performance claims, Level2+ evidence without reproducible artifacts.

Exit criteria: future external execution cannot occur without explicit opt-in, artifact capture, provenance, result validation, quarantine, and claim-boundary review.

## Phase I: Synthetic Result Import Prototype

Status: complete for local/synthetic Phase I.

Goal: Prototype local/synthetic result import without real external execution.

Deliverables: import synthetic external result candidates from JSON, validate artifact digests and provenance fields, quarantine invalid candidates, normalize valid candidates into pending-review drafts, create evidence append proposals only, persist proposal ledgers separately from the accepted Evidence Ledger, and preserve Level0/Level1 claim boundaries.

Implemented: `SyntheticResultImporter`, `SyntheticResultImportBundle`, `ResultCandidateArtifactResolver`, artifact digest validation, provenance validation, metric candidate validation, official/formal/soundness claim detection, synthetic quarantine, `NormalizedExternalResultDraft`, `EvidenceAppendProposal`, review-state primitives, and `EvidenceAppendProposalLedger`.

Dependencies: Phase H.

Validation gate: synthetic candidate import tests, artifact digest validation tests, provenance validation tests, metric validation tests, quarantine tests, evidence append proposal tests, proposal ledger tests, and claim-boundary tests.

Anti-goals: real zk-Harness execution, official performance claims, Level2+ evidence promotion, proof-system soundness claims.

Exit criteria: safe synthetic import and review workflow exists without creating accepted external evidence.

## Phase J: Reviewed Proposal Acceptance Policy

Status: complete for local metadata-only Phase J.

Goal: Define reviewed proposal acceptance policy without live external execution or automatic EvidenceLedger append.

Deliverables: proposal state transitions, review decisions, blocking issue handling, supersession, audit reasons, future append eligibility, and evidence-ledger non-mutation tests.

Implemented: `EvidenceReviewDecision`, `EvidenceReviewChecklist`, `EvidenceAcceptancePolicy`, `ClaimBoundaryEscalationGuard`, `EvidenceRecordCandidate`, `EvidenceAppendPreview`, `Level2EligibilityChecker`, and `EvidenceReviewLedger`.

Dependencies: Phase I.

Validation gate: proposal review tests, acceptance policy tests, candidate tests, append preview tests, Level2 eligibility tests, review ledger tests, claim-boundary tests, and source scans for live execution APIs.

Anti-goals: live zk-Harness execution, accepted external evidence, automatic Level2 promotion, fake performance metrics, single opaque aggregate.

Exit criteria: reviewed proposals can be approved only for candidate/preview metadata and cannot become accepted evidence in the same step.

## Phase K: Local Soak Runner And Internal Telemetry

Status: complete for local-only Phase K.

Goal: Repeatedly exercise local-only generation, mutation, local replay, optional sampled local packs, internal benchmark OS telemetry, local health reports, and failure corpus extraction to catch nondeterminism and internal regressions.

Implemented: `SoakRunConfig`, `SoakLimits`, `SoakOutputPolicy`, `SoakShardPlanner`, `SoakShardPlan`, `SoakShardManifest`, `SoakShardCheckpoint`, `LocalSoakRunner`, `SoakTelemetryReport`, `SoakHealthReport`, `FailureCorpusIndex`, `FailureReproductionManifest`, `SoakArtifactLayout`, and `SoakReportBundle`.

Dependencies: Phase J.

Validation gate: soak config tests, sharding tests, runner smoke tests, resume tests, telemetry JSON round-trips, health report tests, failure corpus tests, no external execution source scans, no ZK backend performance labels, and no Level2+ actual evidence tests.

Anti-goals: live zk-Harness execution, external result import, dashboards, fake performance numbers, Level2+ evidence creation.

Exit criteria: small local-only runs produce deterministic shard plans, resumable checkpoints, internal telemetry, local health reports, and failure corpus indexes while preserving claim boundaries.

## Phase L: Long Local Soak Execution And Sampled Reports

Status: future.

Goal: Run longer local soak jobs and publish sampled local-only reports after explicit user approval.

Deliverables: user-approved long-running local jobs, shard output outside the repo or under an ignored artifact directory, smoke/focused/regression/nightly-local profiles, sampled pack retention, failure-pack retention, aggregate telemetry reports, regression corpus curation, and local-only report publishing under strict claim boundaries.

Dependencies: Phase K.

Validation gate: explicit approval record, ignored or external artifact root, aggregate report validation, failure corpus validation, no external execution, no official benchmark evidence, and no ZK backend performance claims.

Anti-goals: live zk-Harness execution, external result import, official benchmark evidence, ZK backend performance claims, dashboards, Level2+ evidence creation.

Exit criteria: long local soak outputs are reproducible, bounded, claim-safe, and organized outside committed source by default.

## Phase M: gnark Recursion Adapter

Status: future.

Goal: Add recursion-envelope stress lane after local soak telemetry exists.

Deliverables: recursion adapter and evidence mapping.

Dependencies: Phase L and future explicit adapter approval.

Validation gate: scoped recursion replay.

Anti-goals: claiming recursion proof as semantic proof.

Exit criteria: recursion outcomes are evidence-capped.

## Phase N: Narrow zkML Adapter

Goal: Add mixed control-flow and zkML workload metrics.

Deliverables: manifest shape and narrow adapter.

Dependencies: Phase L and future explicit adapter approval.

Validation gate: manifest validation and one workload replay.

Anti-goals: becoming a zkML benchmark project.

Exit criteria: zkML metrics are normalized and claim-capped.

## Phase O: Reproducible Benchmark Packs

Goal: Produce deterministic benchmark packs.

Deliverables: pack manifests, artifact hashes, replay commands.

Dependencies: Phase L and future reviewed external replay.

Validation gate: `verify:full`.

Anti-goals: broad leaderboard claims without reproduction.

Exit criteria: Level 2 evidence for scoped packs.

## Phase P: Dashboard/Reporting

Goal: Visualize Score Reports after the evidence model works.

Deliverables: report renderer or dashboard.

Dependencies: Phase L and reproducible benchmark packs.

Validation gate: report validation and UI tests if applicable.

Anti-goals: dashboard-first development.

Exit criteria: dashboard shows axes, confidence, and claim boundaries.
