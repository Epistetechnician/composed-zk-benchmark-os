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

Status: complete for bounded local Phase L. See `docs/62-phase-l-local-soak-acceptance-notes.md`.

Goal: Run longer local soak jobs and publish sampled local-only reports after explicit user approval.

Implemented: user-approved bounded local soak campaign, shard output under an ignored artifact directory, smoke/focused/regression/nightly-local profiles, sampled pack retention, aggregate telemetry reports, targetless mutation applicability telemetry, and local-only report publishing under strict claim boundaries.

Dependencies: Phase K.

Validation gate: explicit approval record, ignored artifact root, aggregate report validation, failure corpus validation, no external execution, no official benchmark evidence, and no ZK backend performance claims. The accepted campaign `phase_l_qwable_local_soak_2026_06_17_extended_256` completed 768 local cases with zero failures, zero failure-corpus entries, a valid aggregate report bundle, and `Level0DesignNote` claim boundary.

Anti-goals: live zk-Harness execution, external result import, official benchmark evidence, ZK backend performance claims, dashboards, Level2+ evidence creation.

Exit criteria: long local soak outputs are reproducible, bounded, claim-safe, and organized outside committed source by default.

## Phase M: gnark Recursion Adapter

Status: complete for inert local contract implementation, inert adapter-preparation metadata, and manual handoff mapping. See `docs/63-phase-m-recursion-envelope-stress-spec.md`.

Goal: Add recursion-envelope stress lane after local soak telemetry exists.

Implemented: recursion-envelope stress spec, input artifact contract, candidate metric labels, inert Rust contract types, serialization helpers, validation rules, fixture-backed negative tests, source-scan guardrails, inert adapter-preparation metadata, manual handoff mapping, and claim-boundary restrictions.

Future deliverables after explicit executable-adapter approval: actual recursion adapter execution implementation and result import review.

Dependencies: Phase L and future explicit adapter approval.

Validation gate: docs and claim-boundary scans, local contract validation tests, serialization round-trips, and source scans that keep executable adapter work absent. Scoped recursion replay only after a future phase explicitly authorizes executable adapter work.

Anti-goals: claiming recursion proof as semantic proof.

Exit criteria for inert local contract implementation: Phase M spec exists, local contract types validate claim-boundary non-escalation, recursion metric labels remain metadata only, adapter-preparation metadata remains `Level0DesignNote`, manual handoff mapping emits no result, and live gnark execution remains blocked.

Future exit criteria after explicit implementation approval: recursion outcomes are evidence-capped.

## Phase N: Narrow zkML Adapter

Status: complete for inert manifest-contract implementation. See `docs/64-phase-n-narrow-zkml-adapter-spec.md`.

Goal: Add mixed control-flow and zkML workload metrics.

Implemented: narrow zkML/control-flow adapter spec, input contract, candidate
metric labels, inert `ZkMlWorkloadManifest` data model, local model artifact
metadata references, digest-root validation, JSON serialization helpers,
validation rules, negative tests, and claim-boundary restrictions.

Future deliverables after explicit approval: manual handoff metadata.
Executable zkML adapter work requires a separate explicit phase.

Dependencies: Phase L and future explicit adapter approval.

Validation gate: local contract validation tests, serialization round-trips,
source scans that keep executable adapter work absent, and full workspace
validation.

Anti-goals: becoming a zkML benchmark project.

Exit criteria for inert implementation: Phase N spec exists, manifest metrics
are metadata only, executable zkML metrics remain unpopulated, and all outputs
remain `Level0DesignNote`. Future exit criteria after executable-adapter
approval: zkML metrics are normalized and claim-capped.

## Phase O: Reproducible Benchmark Packs

Status: complete for inert local reproducible-pack readiness contract,
construction-helper implementation, and adjacent output plumbing. See
`docs/65-phase-o-local-reproducible-pack-readiness-spec.md`.

Goal: Produce deterministic benchmark packs.

Implemented: local reproducible-pack readiness spec, inert `PackReadinessReport`
data model, input refs, inert replay-command metadata, readiness checks,
report digest helper, JSON serialization helpers,
`build_pack_readiness_report_from_reader`, validation over existing
`BenchmarkPackReader` / `BenchmarkPackValidation` metadata,
`write_pack_readiness_outputs_for_pack`, adjacent `readiness/` output files
that stay outside `pack.json`, validation rules, future Level2 promotion
preconditions, required negative tests, non-goals, and claim-boundary
restrictions.

Future deliverables after explicit implementation approval: none inside Phase O.
True Level2 promotion requires a separate future reviewed evidence phase.

Dependencies: Phase L and future reviewed external replay.

Validation gate: local pack-readiness validation tests, serialization
round-trips, source scans that keep replay commands inert, and full workspace
validation.

Anti-goals: broad leaderboard claims without reproduction.

Exit criteria for inert implementation: Phase O spec exists, readiness reports
remain `Level0DesignNote`, replay command metadata remains inert,
deterministic local packs can emit adjacent readiness metadata without mutating
`pack.json`, and readiness validation rejects Level2+ evidence, official
benchmark evidence, external replay, and ZK backend performance claims. Future
Level2 exit criteria require a separate reviewed evidence-promotion phase.

## Phase P: Dashboard/Reporting

Status: complete for read-only reporting boundary over Score Reports and
pack-readiness metadata. See
`docs/67-phase-p-read-only-reporting-boundary-notes.md`.

Goal: Visualize Score Reports after the evidence model works.

Implemented: `DashboardPanelKind::PackReadiness`,
`build_dashboard_model_from_pack_readiness`, Markdown rendering through the
existing renderer, and validation that pack-readiness panels remain
`Level0DesignNote`.

Future deliverables after explicit approval: richer report bundles or a UI
dashboard. Any UI dashboard must remain read-only and preserve claim-boundary
labels.

Dependencies: Phase L and reproducible benchmark packs.

Validation gate: report validation, Phase P dashboard/reporting tests, and
claim-boundary tests.

Anti-goals: dashboard-first development, score-axis population from local-only
evidence, official benchmark evidence claims, ZK backend performance claims,
or Level2+ evidence creation.

Exit criteria for read-only reporting boundary: reports show axes, confidence,
pack-readiness status, and claim boundaries without creating or promoting
evidence. Future UI exit criteria require a separate explicit phase.

## Phase Q: Report Bundles

Status: complete for docs-first boundary, inert in-memory metadata
implementation, adjacent output-plumbing boundary, and adjacent local output
implementation, and local ergonomics hardening. See
`docs/68-phase-q-report-bundle-boundary-spec.md`,
`docs/69-phase-q-report-bundle-implementation-notes.md`, and
`docs/70-phase-q-report-bundle-output-plumbing-spec.md`, and
`docs/71-phase-q-report-bundle-output-implementation-notes.md`, and
`docs/72-phase-q-report-bundle-ergonomics-hardening-notes.md`.

Goal: define a richer read-only report-bundle contract before any implementation
or UI work broadens Phase P reporting.

Implemented: Phase Q-A boundary spec covering allowed inputs, bundle contents,
required validation rules, claim labels, non-goals, and future implementation
exit criteria. Phase Q-B adds `ReportBundleManifest`,
`ReportBundleInputRef`, `ReportBundleRenderedReport`,
`ReportBundlePackReadinessInput`, deterministic manifest digesting, JSON
serialization helpers, `build_report_bundle_manifest_from_reports`, and
`validate_report_bundle_manifest`. Phase Q-C defines the docs-first boundary for
future adjacent local output plumbing around Q-B metadata. Phase Q-D adds
`write_report_bundle_outputs`, `read_report_bundle_outputs`,
`ReportBundleRenderedMarkdown`, `ReportBundleOutput`, materialized manifest and
Markdown digest checks, overwrite gating, extra-file rejection, and
source-immutability tests. Phase Q-E adds
`build_report_bundle_rendered_markdown_payloads`, source-drift rejection,
duplicate rendered output path validation, unsafe-root coverage, unexpected
overwrite-file coverage, and symlink rejection coverage.

Dependencies: Phase O pack-readiness metadata and Phase P read-only reporting.

Validation gate: documentation navigation checks, claim-boundary text checks,
focused Phase Q report-bundle tests, digest validation, portable source refs,
failed-readiness visibility, no external execution hooks, and no accepted
Evidence Ledger mutation. Output-plumbing implementation coverage must include
materialized-file digest tests and source-immutability tests. Ergonomics
hardening coverage must include source-drift rejection and output-root
hardening.

Anti-goals: UI dashboard, replay-command execution, external replay, official
benchmark evidence claims, ZK backend performance claims, Level2+ evidence
creation, accepted Evidence Ledger mutation, score-axis population from
local-only evidence, broad leaderboard claims, generated benchmark artifacts, or
package-script/runtime additions.

Exit criteria for inert in-memory metadata: Phase Q-A spec exists, Phase Q-B
metadata validates, rendered Markdown digests are deterministic, failed
pack-readiness remains visible, output stays `Level0DesignNote`, and
`AGENTS.md` forbids report-bundle materialization beyond the current in-memory
surface. Exit criteria for output-plumbing boundary: Phase Q-C spec exists,
navigation points to it, and `AGENTS.md` authorizes only Markdown planning for
adjacent local output plumbing. Exit criteria for adjacent local output
implementation: writer and reader materialize only declared local report-bundle
files, verify manifest and Markdown digests, reject extra rendered files,
preserve source metadata, keep output `Level0DesignNote`, and leave UI, CLI,
external replay, official evidence, ZK backend performance claims, and Level2+
promotion unauthorized. Exit criteria for ergonomics hardening: rendered
Markdown payloads can be derived from known source reports without caller-side
dashboard-id reconstruction, source drift fails closed, duplicate rendered paths
are rejected, unsafe roots and symlinks are rejected, and report bundles remain
local integrity metadata only.

## Phase R: Local Audit Index

Status: complete for docs-first boundary, inert in-memory implementation, and
docs-first output-plumbing boundary.
See `docs/73-phase-r-local-audit-index-boundary-spec.md` and
`docs/74-phase-r-local-audit-index-implementation-notes.md`, plus
`docs/75-phase-r-audit-index-output-plumbing-spec.md`.

Goal: define a read-only local audit-index contract over existing local metadata
outputs before any implementation broadens beyond report-bundle ergonomics.

Implemented: Phase R boundary spec, `LocalAuditIndexManifest` metadata, source
input refs, deterministic manifest digesting, JSON helpers, validation rules,
construction from existing `ReportBundleManifest` metadata, and a docs-first
boundary for adjacent local audit-index output plumbing.

Dependencies: Phase O pack-readiness metadata, Phase P read-only reporting, and
Phase Q report-bundle metadata/output plumbing.

Validation gate: documentation navigation checks, claim-boundary text checks,
portable source refs, digest validation, failed-readiness visibility, local-only
warning visibility, no source pack/report/report-bundle mutation, no external
execution hooks, no audit-index output writer or reader APIs in this docs-first
slice, and no accepted Evidence Ledger mutation.

Anti-goals: UI dashboard, command-line tools, replay-command execution, external
replay, official benchmark evidence claims, ZK backend performance claims,
Level2+ evidence creation, accepted Evidence Ledger mutation, score-axis
population from local-only evidence, broad leaderboard claims, generated
benchmark artifacts, or package-script/runtime additions.

Exit criteria: Phase R specs exist, navigation points to the implementation and
output-plumbing notes, `AGENTS.md` authorizes only docs-first audit-index output
planning beyond inert in-memory metadata, focused tests cover validation and
source-scan boundaries, and future audit-index output implementation remains
blocked until a separate explicit implementation phase.
