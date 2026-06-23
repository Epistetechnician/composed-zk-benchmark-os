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

Status: complete for docs-first boundary, inert in-memory implementation,
docs-first output-plumbing boundary, and adjacent local output plumbing.
See `docs/73-phase-r-local-audit-index-boundary-spec.md` and
`docs/74-phase-r-local-audit-index-implementation-notes.md`, plus
`docs/75-phase-r-audit-index-output-plumbing-spec.md` and
`docs/76-phase-r-audit-index-output-implementation-notes.md`.

Goal: define a read-only local audit-index contract over existing local metadata
outputs before any implementation broadens beyond report-bundle ergonomics.

Implemented: Phase R boundary spec, `LocalAuditIndexManifest` metadata, source
input refs, deterministic manifest digesting, JSON helpers, validation rules,
construction from existing `ReportBundleManifest` metadata, a docs-first
boundary for adjacent local audit-index output plumbing, and writer/reader APIs
for exactly `audit-index/audit-index-manifest.json` and
`audit-index/digests/audit-index-manifest.sha256`.

Dependencies: Phase O pack-readiness metadata, Phase P read-only reporting, and
Phase Q report-bundle metadata/output plumbing.

Validation gate: documentation navigation checks, claim-boundary text checks,
portable source refs, digest validation, failed-readiness visibility, local-only
warning visibility, no source pack/report/report-bundle mutation, output-root
safety, stale-digest rejection, overwrite-drift rejection, unexpected-file and
symlink rejection, no external execution hooks, and no accepted Evidence Ledger
mutation.

Anti-goals: UI dashboard, command-line tools, replay-command execution, external
replay, official benchmark evidence claims, ZK backend performance claims,
Level2+ evidence creation, accepted Evidence Ledger mutation, score-axis
population from local-only evidence, broad leaderboard claims, generated
benchmark artifacts, or package-script/runtime additions.

Exit criteria: Phase R specs exist, navigation points to the implementation and
output-plumbing notes, `AGENTS.md` authorizes the bounded local audit-index
output implementation, focused tests cover validation, output safety, and
source-scan boundaries, and any broader audit-index work remains blocked until a
separate explicit implementation phase.

## Benchmark OS Track: Phase S Audit Index Ergonomics

Status: complete for docs-first boundary, in-memory single-index implementation,
docs-first output-plumbing boundary, and local output-root implementation. See
`docs/86-phase-s-audit-index-ergonomics-boundary-spec.md`,
`docs/87-phase-s-audit-index-ergonomics-implementation-notes.md`, and
`docs/88-phase-s-audit-index-ergonomics-output-plumbing-spec.md`, and
`docs/89-phase-s-audit-index-ergonomics-output-plumbing-implementation-notes.md`.

Goal: define and implement a single-index audit-index ergonomics contract, then
define the future materialized-output boundary before any generated ergonomics
files, command-line surfaces, UI dashboards, or cross-bundle index construction.

Implemented: docs-first boundary for read-only ergonomics over one valid
`LocalAuditIndexManifest`, plus `LocalAuditIndexErgonomicsRequest`, exact typed
filters over manifest fields, grouping and sorting over manifest fields,
selected-view metadata, warning summaries, required limitation labels,
deterministic Markdown rendering, validation helpers, and `Level0DesignNote`
claim limits. The output-plumbing boundary defines the future
`audit-index-ergonomics/` file shape, selected-view JSON, rendered Markdown,
digest sidecars, output-root safety, overwrite-drift rejection, source
immutability, required limitation-label preservation, and `Level0DesignNote`
claim limits. The output-plumbing implementation adds declared-file-only local
materialization for `ergonomics-view.json`, `rendered/ergonomics-view.md`,
`digests/ergonomics-view-json.sha256`, and
`digests/ergonomics-view-markdown.sha256`; deterministic source
manifest/request rederivation; protected path overlap rejection; stale digest
rejection; symlink and unexpected-file rejection; partial-bundle rejection; and
source immutability.

Dependencies: Phase R local audit-index metadata and Phase R adjacent local
audit-index output plumbing.

Validation gate: documentation navigation checks, claim-boundary text checks,
focused Phase S ergonomics tests for implementation slices, Phase R audit-index
regression tests for implementation slices, docs claim-boundary checks, repo
hygiene checks, no generated committed ergonomics files, no package runtime
files, no cross-bundle construction, no command-line tools, no UI dashboards, no
external execution hooks, no score-axis population, and no accepted Evidence
Ledger mutation.

Anti-goals: generated ergonomics files, command-line tools, UI dashboards,
browser apps, JavaScript/TypeScript/package runtime additions, cross-bundle
audit-index construction, replay-command execution, external replay, live backend
execution, external repo clones, external result import, generated benchmark
artifacts, official benchmark evidence, ZK backend performance claims, Level2+
evidence creation, score-axis population from local-only evidence, broad
leaderboard claims, source mutation, audit-index output mutation, or accepted
Evidence Ledger mutation.

Exit criteria: Phase S boundary, implementation notes, output-plumbing boundary,
and output-plumbing implementation notes exist; README and AGENTS point to them;
ergonomics input/output rules are explicit; limitation labels are preserved in
rendered Markdown; invalid filters and invalid source manifests fail closed;
materialized JSON and Markdown bytes are bound to digest sidecars; protected path
overlap, symlinks, unexpected files, partial bundles, stale digests, and drift
fail closed; normal test paths remain hermetic; and all output remains capped at
`Level0DesignNote`. Future broadening beyond this single-index local output
surface requires a separate docs-first boundary.

## Benchmark OS Track: Phase T Cross-Bundle Audit Index

Status: complete for docs-first boundary, in-memory implementation, docs-first
output-plumbing boundary, and local output-root implementation. See
`docs/91-phase-t-cross-bundle-audit-index-boundary-spec.md` and
`docs/92-phase-t-cross-bundle-audit-index-implementation-notes.md`, and
`docs/93-phase-t-cross-bundle-audit-index-output-plumbing-spec.md`, and
`docs/94-phase-t-cross-bundle-audit-index-output-implementation-notes.md`.

Goal: define the future cross-bundle audit-index planning boundary before any
implementation broadens beyond the Phase S single-index local output surface.

Implemented: docs-first boundary for local presentation metadata over two or
more existing valid `LocalAuditIndexManifest` values, plus an in-memory
implementation that validates source manifests, computes deterministic source
summaries, groups, duplicate/conflict signals, warning summaries, required
limitation labels, deterministic Markdown, and JSON round trips. The boundary
also names future protected-path overlap rules across source packs, source
reports, report bundles, audit-index outputs, Phase S ergonomics outputs,
accepted Evidence Ledgers, and future cross-bundle output roots, plus
non-repair behavior for corrupted output roots. The output-plumbing docs-first
boundary narrows the future materialized shape to one canonical cross-bundle
view JSON file, one rendered Markdown file, and two digest sidecars below a
caller-selected `cross-bundle-audit-index/` output root. The local output-root
implementation adds declared-file-only materialization for
`cross-bundle-view.json`, `rendered/cross-bundle-view.md`,
`digests/cross-bundle-view-json.sha256`, and
`digests/cross-bundle-view-markdown.sha256`; deterministic request/view
rederivation; protected path overlap rejection; stale digest rejection; symlink
and unexpected-file rejection; partial-bundle rejection; corrupted-root
non-repair; source immutability; and `Level0DesignNote` claim limits.

Dependencies: Phase R local audit-index metadata, Phase R adjacent local
audit-index output plumbing, Phase S single-index ergonomics, and Phase S local
ergonomics output plumbing.

Validation gate: focused Phase T cross-bundle tests for implementation slices,
documentation navigation checks, claim-boundary text checks, repo hygiene
checks, no committed generated cross-bundle files, no package runtime files, no
command-line tools, no UI dashboards, no external execution hooks, no
score-axis population, and no accepted Evidence Ledger mutation. Output-plumbing
implementation coverage must include protected-path overlap rejection before
writes and corrupted-output-root non-repair.

Anti-goals: generated committed cross-bundle files, command-line tools, UI
dashboards, browser apps,
JavaScript/TypeScript/package runtime additions, source pack mutation, source
report mutation, report-bundle mutation, audit-index output mutation, Phase S
ergonomics output mutation, accepted Evidence Ledger mutation, replay-command
execution, external replay, live backend execution, external repo clones,
external result import, generated benchmark artifacts, official benchmark
evidence, ZK backend performance claims, Level2+ evidence creation, score-axis
population from local-only evidence, broad leaderboard claims, or treating
cross-bundle audit-index metadata as evidence.

Exit criteria: Phase T boundary spec, implementation notes, output-plumbing
spec, and output implementation notes exist; README and AGENTS point to them;
the in-memory and materialized input/output rules are explicit; duplicate and
conflict signals are tested; invalid manifests fail closed; materialized JSON
and Markdown bytes are bound to digest sidecars; protected-path overlap,
symlinks, unexpected files, partial bundles, stale digests, and drift fail
closed; corrupted roots are not repaired; normal test paths remain hermetic; and
all cross-bundle output remains capped at `Level0DesignNote`.

## Benchmark OS Track: Phase U Local Benchmark Artifact Boundary

Status: complete for docs-first boundary and local implementation. See
`docs/95-phase-u-local-benchmark-artifact-boundary-spec.md` and
`docs/96-phase-u-local-benchmark-artifact-implementation-notes.md`.

Goal: define the future local benchmark artifact generation boundary before any
generated local artifact bundle is created.

Implemented: docs-first boundary for future local benchmark artifact bundles
assembled from already-valid local inputs: local benchmark packs,
pack-readiness metadata, report-bundle metadata, audit-index metadata, Phase S
ergonomics metadata, Phase T cross-bundle metadata, and local replay/evidence
artifacts already referenced by valid local packs. The boundary requires
declared-file output shape, digest sidecars, source-input digest summaries,
claim-boundary summaries capped at the weakest local input, required limitation
labels, protected-path overlap rejection, corrupted-root non-repair, accepted
Evidence Ledger non-mutation, and score-axis non-population from local-only
evidence. The local implementation adds `LocalBenchmarkArtifactManifest`,
manifest validation, deterministic JSON serialization, deterministic Markdown
rendering, manifest digesting, declared-file-only output writing and reading,
digest sidecars, protected-path overlap rejection including symlink-resolved
overlap, stale-digest rejection, symlink rejection, unexpected-file rejection,
partial-bundle rejection, and repair-overwrite rejection.

Dependencies: Phase O local reproducible-pack readiness, Phase Q report-bundle
metadata/output plumbing, Phase R audit-index metadata/output plumbing, Phase S
audit-index ergonomics/output plumbing, and Phase T cross-bundle audit-index
metadata/output plumbing.

Validation gate: documentation navigation checks, claim-boundary text checks,
repo hygiene checks, focused Phase U local benchmark artifact tests, no
committed generated benchmark artifact files, no package runtime files, no
command-line tools, no UI dashboards, no external execution hooks, no
score-axis population, and no accepted Evidence Ledger mutation.

Anti-goals: committed generated benchmark artifact files, command-line tools,
UI dashboards, browser apps,
JavaScript/TypeScript/package runtime additions, source pack mutation, source
report mutation, report-bundle mutation, audit-index output mutation, Phase S
ergonomics output mutation, Phase T cross-bundle output mutation, accepted
Evidence Ledger mutation, replay-command execution, external replay, live
backend execution, external repo clones, external result import, official
benchmark evidence, ZK backend performance claims, Level2+ evidence creation,
score-axis population from local-only evidence, broad leaderboard claims, or
treating local generated artifacts as accepted evidence.

Exit criteria: Phase U boundary spec and implementation notes exist; README and
AGENTS point to them; input classes, output shape, protected-path policy,
overwrite policy, required limitation labels, negative tests, and promotion
boundary are explicit; the local writer/reader uses declared files and digest
sidecars only; and the docs preserve that local benchmark artifacts are
packaging only until a separate reviewed promotion phase creates stronger
evidence.

## Benchmark OS Track: Phase W Reviewed Promotion Preflight

Status: complete for inert implementation. See
`docs/99-phase-w-reviewed-evidence-promotion-boundary-spec.md` and
`docs/114-phase-w-promotion-preflight-boundary-spec.md`, plus
`docs/115-phase-w-promotion-preflight-implementation-notes.md`.

Goal: implement a metadata-only preflight layer that makes accepted-evidence
promotion and official-submission prerequisites explicit and fail-closed before
any accepted Evidence Ledger mutation or official submission operation exists.

Implemented: additive Rust metadata, validation, deterministic digesting,
Markdown rendering, serialization helpers, and hermetic tests under
`crates/zkbench-core`, plus implementation notes and navigation updates. The
surface rejects local-only promotion, stale append previews, missing human
review, missing external replay provenance for Level2+ promotion, unresolved
blocking/quarantine markers, forbidden claim text, and official-submission
package construction before accepted evidence ids exist.

Anti-goals: accepted Evidence Ledger mutation, official benchmark submission,
external replay, live backend execution, generated benchmark artifacts, durable
campaign outputs, command-line tools, UI dashboards, package runtime additions,
score-axis population, ZK backend performance claims, Level2+ evidence
creation, or treating preflight metadata as accepted evidence.

Exit criteria: Phase W preflight boundary and implementation notes exist;
README and AGENTS point to them; focused tests cover valid metadata, fail-closed
promotion rejections, official-submission rejection before accepted evidence,
digest determinism, serialization round trips, and source-scan boundaries; and
all Phase W output remains metadata only.

## Benchmark OS Track: Phase W Accepted Ledger Append Boundary

Status: complete for docs-first boundary. See
`docs/116-phase-w-accepted-ledger-append-boundary-spec.md`.

Goal: define the next possible local accepted Evidence Ledger append
transaction contract after Phase W preflight without authorizing the append
implementation or creating accepted evidence.

Scope: Markdown boundary updates only. The future transaction must require a
valid preflight report, exact candidate/review/append-preview alignment, current
ledger-tip agreement, artifact digest bindings, external replay provenance for
Level2+, no unresolved quarantine or blocking review markers, and explicit
non-claim labels.

Anti-goals: Rust source changes, accepted Evidence Ledger mutation, official
benchmark submission, external replay, live backend execution, generated
benchmark artifacts, durable campaign outputs, command-line tools, UI
dashboards, package runtime additions, score-axis population, ZK backend
performance claims, Level2+ evidence creation, or treating this boundary as
accepted evidence.

Exit criteria: Phase 116 boundary spec exists; README, validation report, and
AGENTS point to it; the future append transaction is constrained to explicit
local inputs and append-only behavior; and no accepted ledger entry, official
submission package, external replay evidence, or score-axis population is
created.

## Benchmark OS Track: Phase W Accepted Ledger Append Implementation

Status: complete for guarded local implementation. See
`docs/117-phase-w-accepted-ledger-append-implementation-notes.md`.

Goal: implement the Phase 116 local accepted-ledger append transaction over
explicit caller-supplied inputs without creating official submission, external
replay, score-axis, or Level2+ evidence surfaces.

Implemented: additive Rust transaction request, validation, report, candidate
to `EvidenceRecord` conversion, and fail-closed append application under
`crates/zkbench-core/src/evidence/accepted_append.rs`, plus focused hermetic
tests. The implementation requires valid preflight, candidate/review/preview
alignment, candidate digest agreement, current ledger-tip agreement, source
artifact digests, and Level1-or-below local evidence.

Anti-goals: filesystem persistence, official benchmark submission, external
replay, live backend execution, network access, credentials or secrets,
generated benchmark artifacts, durable campaign outputs, command-line tools, UI
dashboards, package runtime additions, score-axis population, ZK backend
performance claims, Level2+ evidence creation, formal evidence creation, or
broad leaderboard claims.

Exit criteria: accepted append transaction APIs are exported; focused tests
cover valid append, stale-tip rejection, candidate digest mismatch rejection,
official/score/Level2+ rejection, and source-scan boundaries; and full workspace
validation passes.

## Benchmark OS Track: Phase W Accepted Ledger Materialization

Status: complete for local JSON materialization. See
`docs/118-phase-w-accepted-ledger-materialization-boundary-spec.md` and
`docs/119-phase-w-accepted-ledger-materialization-implementation-notes.md`.

Goal: materialize the guarded Phase W accepted-ledger append transaction to one
explicit caller-selected local JSON ledger path without creating official
submission, external replay, score-axis, or Level2+ evidence surfaces.

Implemented: additive Rust materialization request and helper under
`crates/zkbench-core/src/evidence/accepted_append_output.rs`, exports, and
focused hermetic tests. The implementation validates the ledger path, rejects
parent-directory components and symlinks, loads and validates existing ledgers,
requires explicit creation permission for missing ledgers, applies the Phase
117 transaction, and writes through a same-directory temporary JSON file.

Anti-goals: official benchmark submission, external replay, live backend
execution, network access, credentials or secrets, generated benchmark
artifacts, durable campaign outputs, command-line tools, UI dashboards, package
runtime additions, score-axis population, ZK backend performance claims,
Level2+ evidence creation, formal evidence creation, broad leaderboard claims,
or treating local ledger JSON as official benchmark evidence.

Exit criteria: materialized append APIs are exported; focused tests cover
create-if-missing, second append, missing-file rejection, missing-parent
rejection, directory-target rejection, invalid-ledger rejection, stale-tip
rejection, symlink rejection on Unix platforms, path traversal rejection, and
source-scan boundaries; and full workspace validation passes.

## Benchmark OS Track: Phase W Official Submission Package Materialization Boundary

Status: complete for docs-first boundary. See
`docs/120-phase-w-official-submission-package-materialization-boundary-spec.md`.

Goal: define the future local official-submission package output-root contract
after Phase W accepted-ledger materialization without authorizing package
generation, official endpoint submission, score-axis population, or Level2+
evidence creation.

Scope: Markdown boundary updates only. The future materializer must require
valid `OfficialSubmissionPackageMetadata`, a caller-selected valid accepted
ledger JSON file, accepted evidence ids that exist in that ledger, external
replay provenance, artifact digests, required non-claim labels,
`submits_to_official_endpoint == false`, deterministic JSON and Markdown
outputs, digest sidecars, protected-root rejection, symlink rejection,
path-traversal rejection, and source scans proving no network/process/
credential/submission path exists.

Anti-goals: Rust source changes, tests, Cargo metadata changes, generated
package files, committed official-submission package artifacts, official
benchmark submission, external replay execution, live backend execution,
network access, credentials or secrets, command-line tools, UI dashboards,
package runtime additions, score-axis population, ZK backend performance
claims, Level2+ evidence creation, formal evidence creation, broad leaderboard
claims, or treating local package output as an official benchmark submission.

Exit criteria: Phase 120 boundary spec exists; README, validation report, task
list, and AGENTS point to it; the future output shape and required rejections
are explicit; and no Rust source, generated package output, official endpoint
call, score-axis population, or Level2+ evidence is created.

## Benchmark OS Track: Phase W Official Submission Package Materialization Implementation

Status: complete for local output-root implementation. See
`docs/121-phase-w-official-submission-package-materialization-implementation-notes.md`.

Goal: materialize the Phase W official-submission package as digest-bound local
review files after accepted-ledger validation, without creating an official
benchmark submission, committed package artifact, score-axis population, or
Level2+ evidence.

Scope: additive Rust source and focused tests under `crates/zkbench-core`, plus
phase notes and navigation/status updates. The implementation requires valid
`OfficialSubmissionPackageMetadata`, an existing valid accepted ledger JSON
file, accepted-evidence ids present in that ledger, required non-claim labels,
`submits_to_official_endpoint == false`, deterministic JSON and Markdown
outputs, digest sidecars, protected-root rejection, symlink rejection,
path-traversal rejection, stale-digest rejection, unexpected-file rejection,
and overwrite package-drift rejection.

Anti-goals: generated committed package artifacts, official benchmark
submission, external replay execution, live backend execution, network access,
credentials or secrets, command-line tools, UI dashboards, package runtime
additions, score-axis population, ZK backend performance claims, Level2+
evidence creation, formal evidence creation, broad leaderboard claims, or
treating local package output as an official benchmark submission.

Exit criteria: Phase 121 implementation notes exist; the local package writer
and reader are exported from `zkbench-core`; focused tests cover declared files,
accepted-ledger validation, unsafe paths, digest drift, overwrite drift,
external-submission rejection, and no endpoint runtime surface; and no generated
package artifact, official endpoint call, score-axis population, or Level2+
evidence is created.

## Benchmark OS Track: Phase W External Replay Official Submission Boundary

Status: complete for docs-first boundary. See
`docs/122-phase-w-external-replay-official-submission-boundary-spec.md`.

Goal: define the future boundary between local Phase W package materialization
and any external replay or official-submission promotion path, without
authorizing implementation, endpoint access, credentials, generated artifacts,
accepted Evidence Ledger mutation, score-axis population, or Level2+ evidence.

Scope: Markdown boundary updates only. The future path must require valid
accepted ledger JSON, valid Phase 121 package output, expected package digests,
non-secret benchmark target metadata, backend id and version, benchmark-suite
id, external replay provenance, source artifact digests, explicit operator
acknowledgement, an output root outside git, redaction rules, and claim-class
separation across local, external replay, official submission, performance,
formal, and soundness evidence.

Anti-goals: Rust source changes, tests, Cargo metadata changes, generated
output files, committed external replay artifacts, committed
official-submission artifacts, accepted Evidence Ledger mutation, official
benchmark submission, external replay execution, live backend execution,
network access, credentials or secrets, command-line tools, UI dashboards,
package runtime additions, score-axis population, ZK backend performance
claims, Level2+ evidence creation, formal evidence creation, SOTA claims,
broad leaderboard claims, production-readiness claims, or semantic-correctness
claims.

Exit criteria: Phase 122 boundary spec exists; README, validation report, task
list, and AGENTS point to it; the future input contract, validation order,
artifact shape, rejection list, and required tests are explicit; and no Rust
source, generated output, official endpoint call, accepted Evidence Ledger
mutation, score-axis population, or Level2+ evidence is created.

## Benchmark OS Track: Phase W External Replay Submission Preflight Implementation

Status: complete for local preflight metadata. See
`docs/123-phase-w-external-replay-submission-preflight-implementation-notes.md`.

Goal: implement the local Phase W preflight that validates accepted-ledger JSON,
Phase 121 package output, expected digests, operator acknowledgement, future
output-root safety, redaction policy, and claim-class separation before any
future external replay or official-submission operation.

Scope: additive Rust source and focused tests under `crates/zkbench-core`, plus
phase notes and navigation/status updates. The implementation emits local
metadata only and keeps all external replay, endpoint submission,
accepted-ledger mutation, generated-artifact write, and score-axis flags false.

Anti-goals: external replay execution, official endpoint calls, credentials or
secrets, generated output materialization, accepted Evidence Ledger mutation,
official benchmark submission, live backend execution, network access,
command-line tools, UI dashboards, package runtime additions, score-axis
population, ZK backend performance claims, Level2+ evidence creation, formal
evidence creation, SOTA claims, broad leaderboard claims, production-readiness
claims, or semantic-correctness claims.

Exit criteria: Phase 123 implementation notes exist; preflight request/report,
validation, deterministic JSON, Markdown, and digest helpers are exported from
`zkbench-core`; focused tests cover valid local preflight, digest drift,
operator acknowledgement, local-only promotion, score-axis rejection, endpoint
attempt rejection, protected-root rejection, and no live runtime surface; and no
external replay, endpoint call, credential use, generated output, accepted
Evidence Ledger mutation, score-axis population, or Level2+ evidence is
created.

## Benchmark OS Track: Phase W External Replay Preflight Output Boundary

Status: complete for docs-first boundary only. See
`docs/124-phase-w-external-replay-preflight-output-boundary-spec.md`.

Goal: define the future local output-root contract for materializing Phase 123
external replay submission preflight reports as deterministic review metadata,
without authorizing the materializer implementation, external replay, official
submission, credentials, accepted Evidence Ledger mutation, score-axis
population, or Level2+ evidence.

Scope: Markdown boundary and navigation/status updates only. The boundary
defines future explicit inputs, declared output files, digest sidecars,
redaction requirements, protected-root rules, fail-closed rejection cases, and
future hermetic tests.

Anti-goals: Rust implementation in this slice, generated output files,
committed external replay artifacts, committed official-submission artifacts,
accepted Evidence Ledger mutation, official benchmark submission, external
replay execution, live backend execution, network access, credentials or
secrets, command-line tools, UI dashboards, package runtime additions,
score-axis population, ZK backend performance claims, Level2+ evidence
creation, broad leaderboard claims, SOTA claims, production-readiness claims,
or semantic-correctness claims.

Exit criteria: Phase 124 boundary spec exists; README, AGENTS, task list, and
validation report point to it; future local output-root rules are explicit; raw
credential, token, request, response, transcript, and operator-private material
retention is rejected; and no Rust source, generated output, external replay,
endpoint call, credential use, accepted Evidence Ledger mutation, score-axis
population, or Level2+ evidence is created.

## Benchmark OS Track: Phase W External Replay Preflight Output Implementation

Status: complete for local review metadata output plumbing. See
`docs/125-phase-w-external-replay-preflight-output-implementation-notes.md`.

Goal: implement the local output-root materializer for valid Phase 123 external
replay submission preflight request/report pairs, without external replay,
official submission, credential use, accepted Evidence Ledger mutation,
score-axis population, or Level2+ evidence.

Scope: additive Rust source and focused tests under `crates/zkbench-core`, plus
phase notes and navigation/status updates. The implementation writes and reads
only declared `external-replay-submission/*` review metadata files and digest
sidecars under a caller-selected repo-external output root.

Implemented: deterministic input manifest JSON, preflight report JSON,
preflight report Markdown, redaction report JSON, package digest summary JSON,
non-claims Markdown, SHA-256 sidecars, readback validation, protected-root
checks, repository-root rejection, stale/partial/unexpected output rejection,
repair-overwrite rejection, request/report drift rejection, raw-retention
rejection, and no-live-runtime source scans.

Anti-goals: external replay execution, official endpoint calls, credentials or
secrets, committed generated output, accepted Evidence Ledger mutation,
official benchmark submission, live backend execution, network access,
command-line tools, UI dashboards, package runtime additions, score-axis
population, ZK backend performance claims, Level2+ evidence creation, formal
evidence creation, SOTA claims, broad leaderboard claims, production-readiness
claims, or semantic-correctness claims.

Exit criteria: Phase 125 implementation notes exist; output request/manifest,
redaction report, package digest summary, output summary, declared paths,
writer, and reader are exported from `zkbench-core`; focused tests cover valid
materialization, request/report drift, side-effect rejection, protected-root
rejection, overwrite drift, stale digest rejection, unexpected-file rejection,
raw-retention rejection, incomplete redaction policy rejection, and no live
runtime surface; and no external replay, endpoint call, credential use,
accepted Evidence Ledger mutation, score-axis population, or Level2+ evidence
is created.

## Benchmark OS Track: Phase W Coverage Hardening

Status: complete for local Phase W output-plumbing coverage hardening. See
`docs/126-phase-w-coverage-hardening-notes.md`.

Goal: improve local regression coverage over the Phase 125 external replay
preflight output-root implementation without changing production APIs or
authorizing any live provider, external replay, official submission, accepted
Evidence Ledger, score-axis, or Level2+ path.

Scope: focused tests under
`crates/zkbench-core/tests/phase_w_promotion_preflight.rs`, plus phase notes
and navigation/status updates.

Implemented: additional fail-closed tests for existing-file output roots,
repository-root overlap, parent-directory output roots, Unix symlink roots,
digest-consistent malformed JSON, digest-consistent non-UTF-8 materialized
files, digest-consistent report Markdown drift, input-manifest declared-file
drift, submission-package digest-summary drift, and non-claims Markdown drift.

Anti-goals: production source changes, new APIs, generated artifacts, external
replay execution, official endpoint calls, credentials or secrets, accepted
Evidence Ledger mutation, official benchmark submission, live backend
execution, network access, command-line tools, UI dashboards, package runtime
additions, score-axis population, ZK backend performance claims, Level2+
evidence creation, formal evidence creation, SOTA claims, broad leaderboard
claims, production-readiness claims, semantic-correctness claims, or claiming
100% coverage.

Exit criteria: Phase 126 notes exist; README, AGENTS, task list, and validation
report point to them; focused tests cover digest-consistent readback drift and
output-root safety branches; focused Phase W coverage improves for the Phase
125 output module; normal gates remain hermetic; and no live/external evidence
surface is created.

## Managed-Attestation Track: Managed JWT Signature Verification

Status: complete for offline ES256 managed-JWT verification. See
`docs/66-managed-signature-verification-boundary-spec.md` and
`docs/77-managed-jwt-signature-verification-notes.md`.

Goal: implement the first managed-signature verifier behind
`hsai-attestation::AttestationVerifier` without adding live service calls,
network access, DCAP verification, backend execution, benchmark outputs, or
claims above `Attested`.

Implemented: `Token::signed_jwt`, `VerifiedAttestation::verifier_trust_roots`,
`ManagedJwtEs256Key`, `ManagedJwtVerifier`, compact-JWT parsing, offline ES256
signature verification against caller-provided local P-256 public keys, issuer,
algorithm, key-id, freshness, nonce, report-data, measurement, and anchor
mapping checks, plus verifier trust-root disclosure through `AttestationLane`.

Dependencies: HSAI attestation lane, managed-signature boundary spec, and Phase
4 anchor-registry claim boundaries.

Validation gate: focused `hsai-attestation` tests, adversarial JWT tests, trust
root visibility tests, no network/JWKS/DCAP behavior, and root Cargo gates.

Anti-goals: JWKS fetching, Azure/Intel/Phala live calls, local Intel DCAP quote
verification, PCCS or collateral handling, TLS or attested-TLS channel binding,
external rails, backend execution, benchmark outputs, Level2+ evidence, global
software-agent uniqueness claims, semantic correctness claims, or changes to
Phase 4 registry semantics.

Exit criteria: valid local ES256 JWTs close the existing anchor-validity
assumption at `Attested` maturity; invalid signature, algorithm, key id, issuer,
freshness, report-data, measurement, and anchor mappings fail closed; verifier
trust roots are visible; rejected tokens emit no guarantees or roots; docs state
all non-claims.

## Managed-Attestation Track: Phala Live Managed-Verifier Boundary

Status: complete for docs-first boundary only. See
`docs/78-phala-live-managed-verifier-boundary-spec.md`.

Goal: define the exact Phala/dstack live managed-verifier boundary before any
runtime implementation, network-enabled provider client, live API call, local
DCAP path, or Phase 4 registry change exists.

Implemented: provider and mode selection (`Phala/dstack`,
`live-managed-verifier`), source attribution for Phala/dstack docs and repos,
future input and response contracts, verification order, trust-root disclosure,
replay/freshness rules, future negative-test requirements, forbidden runtime
effects, and future code-phase exit criteria.

Dependencies: managed-signature boundary spec, offline managed-JWT verification,
Phala/dstack fixture and captured-artifact validation, accepted HSAI-owned
Phala/dstack artifact fixture, and Phase 4 anchor-registry claim boundaries.

Validation gate: documentation navigation checks, source-index update,
claim-boundary text checks, no Rust source changes, no Cargo metadata changes,
no package runtime files, no fixture changes, no generated artifacts, no network
code, and no accepted Evidence Ledger mutation.

Anti-goals: Rust implementation, live Phala API calls, Phala deployment
orchestration, local Intel DCAP quote verification, PCCS or collateral handling,
generic JWKS/JWT fetch implementation, Azure/Intel provider work, TLS or
attested-TLS channel binding, secrets, backend execution, benchmark outputs,
Level2+ evidence, global uniqueness claims, or claims above `Attested`.

Exit criteria: the boundary names exactly one provider and one verification
mode; README, AGENTS, task list, and source index point to it; and future
implementation remains blocked until a separate explicit code phase.

## Managed-Attestation Track: Phala Hermetic Live-Verifier Implementation Spec

Status: complete for code-phase authorization spec only. See
`docs/79-phala-hermetic-live-verifier-implementation-spec.md`.

Goal: authorize the smallest future hermetic Phala/dstack verifier code surface
before implementation: provider client trait, offline test double, normalized
response type, failure taxonomy, trust-root mapping, replay/freshness checks,
and `Attested`-only envelope mapping.

Implemented: future code state slice, provider boundary, future public surface,
request contract, response normalization contract, failure taxonomy,
verification order, replay/freshness rules, trust-root mapping, hermetic test
requirements, operator-only live-path constraints, forbidden effects, and future
implementation exit criteria.

Dependencies: Phase 78 Phala live managed-verifier boundary, offline
managed-JWT verification, Phala/dstack fixture and captured-artifact validation,
accepted HSAI-owned Phala/dstack artifact fixture, and Phase 4 anchor-registry
claim boundaries.

Validation gate: documentation navigation checks, claim-boundary text checks, no
Rust source changes, no Cargo metadata changes, no package runtime files, no
fixture changes, no generated artifacts, no network code, and no accepted
Evidence Ledger mutation.

Anti-goals: Rust implementation in this spec slice, live Phala API calls, normal
tests requiring network or credentials, Phala deployment orchestration, local
Intel DCAP quote verification, PCCS or collateral handling, generic JWKS/JWT
fetch implementation, Azure/Intel provider work, TLS or attested-TLS channel
binding, secrets, backend execution, benchmark outputs, Level2+ evidence, global
uniqueness claims, or claims above `Attested`.

Exit criteria: README, AGENTS, and task list point to this spec; the future code
surface is bounded to hermetic provider-client abstraction and deterministic
test doubles; and implementation remains blocked until a separate explicit
implementation phase.

## Managed-Attestation Track: Phala Hermetic Live-Verifier Implementation

Status: complete for hermetic local implementation only. See
`docs/80-phala-hermetic-live-verifier-implementation-notes.md`.

Goal: implement the Phase 79 local interface surface in
`hsai-attestation-phala` without live calls, network access, credentials, local
DCAP, Cargo dependency changes, benchmark output, or claims above `Attested`.

Implemented: `PhalaManagedVerifierClient`,
`InMemoryPhalaManagedVerifierClient`, `PhalaManagedVerifierRequest`,
`PhalaManagedVerifierResponse`, `PhalaManagedVerifierVerdict`,
`PhalaManagedVerifierError`, `PhalaReplayGuard`, `PhalaLiveManagedVerifier`,
normalized response validation, replay/freshness checks, trust-root prefix
validation, local expectation trust-root mapping, `AttestationVerifier`
integration, and hermetic tests over accepted and rejected fake responses.

Dependencies: Phase 79 implementation spec, existing `hsai-attestation` seam,
existing `hsai-attestation-phala` fixture/captured-artifact crate, and Phase 4
claim boundaries.

Validation gate: focused Phala tests, no process/network source hooks, no Cargo
metadata changes, no fixture changes, no generated benchmark artifacts, root
Cargo validation, and claim-boundary text checks.

Anti-goals: live Phala API calls, operator live tests, credentials or secret
handling, network access, local Intel DCAP quote verification, PCCS or
collateral handling, generic JWKS/JWT fetching, TLS or attested-TLS channel
binding, deployment orchestration, external repo clones, backend execution,
benchmark outputs, accepted Evidence Ledger mutation, Phase 4 registry semantic
changes, Level2+ evidence, global uniqueness claims, or claims above
`Attested`.

Exit criteria: accepted fake responses produce `Attested` only; rejected fake
responses emit no guarantees or trust roots; managed-verifier trust roots are
visible; replay and freshness checks fail closed; normal tests remain hermetic;
and documentation states the non-claims.

## Managed-Attestation Track: Phala Operator Live Path Boundary

Status: complete for docs-first boundary only. See
`docs/81-phala-operator-live-path-boundary-spec.md`.

Goal: define the future operator-only live Phala/dstack managed-verifier path
before any ignored or feature-gated live run exists, while preserving the
hermetic verifier surface and `Attested`-only claim boundary.

Implemented: docs-first boundary for secret handling outside git, explicit
operator acknowledgement, future environment contract, non-secret request
contract, local output-bundle shape, redaction rules, timeout and retry policy,
audit output schema, future verification order, required future tests, and
forbidden runtime effects.

Dependencies: Phase 78 Phala live managed-verifier boundary, Phase 79 hermetic
implementation spec, Phase 80 hermetic fake-client implementation, existing
challenge-capture runbook, and Phase 4 claim boundaries.

Validation gate: documentation navigation checks, claim-boundary text checks,
no Rust source changes, no Cargo metadata changes, no package runtime files, no
fixture changes, no generated artifacts, no network code, no live Phala calls,
no operator secrets, and no accepted Evidence Ledger mutation.

Anti-goals: Rust implementation, live Phala API calls, operator live tests,
examples or scripts that call Phala, credential handling code, secret fixtures,
network access, local Intel DCAP quote verification, PCCS or collateral
handling, generic JWKS/JWT fetching, TLS or attested-TLS channel binding,
deployment orchestration, external repo clones, backend execution, benchmark
outputs, accepted Evidence Ledger mutation, Phase 4 registry semantic changes,
Level2+ evidence, global uniqueness claims, or claims above `Attested`.

Exit criteria: the future operator-live boundary is named, README and AGENTS
point to it, normal test paths remain hermetic, future live calls require
explicit acknowledgement, future credentials stay outside git, future output
artifacts are redacted and digest-bound, and all successful future responses
remain capped at `Attested`.

## Managed-Attestation Track: Phala Operator Live Artifact Plumbing Boundary

Status: complete for docs-first boundary only. See
`docs/82-phala-operator-live-artifact-plumbing-spec.md`.

Goal: define the future local artifact plumbing contract for an operator-only
Phala/dstack managed-verifier run before any code writes, reads, or validates
operator-live output bundles.

Implemented: docs-first boundary for operator-live output-bundle file roles,
future code touch surface, portable bundle path constraints, digest and schema
rules, redaction-report validation, future deterministic validation behavior,
required hermetic tests, and `Attested`-only claim limits.

Dependencies: Phase 78 Phala live managed-verifier boundary, Phase 79 hermetic
implementation spec, Phase 80 hermetic fake-client implementation, Phase 81
operator-live path boundary, existing challenge-capture runbook, and Phase 4
claim boundaries.

Validation gate: documentation navigation checks, claim-boundary text checks,
no Rust source changes, no Cargo metadata changes, no package runtime files, no
fixture changes, no generated artifacts, no network code, no live Phala calls,
no operator secrets, and no accepted Evidence Ledger mutation.

Anti-goals: Rust implementation, examples or scripts, live Phala API calls,
operator live tests, credential handling code, secret fixtures, generated
operator artifacts, network access, local Intel DCAP quote verification, PCCS
or collateral handling, generic JWKS/JWT fetching, TLS or attested-TLS channel
binding, deployment orchestration, external repo clones, backend execution,
benchmark outputs, accepted Evidence Ledger mutation, Phase 4 registry semantic
changes, Level2+ evidence, global uniqueness claims, or claims above
`Attested`.

Exit criteria: the future artifact-plumbing boundary is named, README and
AGENTS point to it, future bundle files have declared roles, future validation
rules fail closed, future redaction validation is required, normal test paths
remain hermetic, and all successful future responses remain capped at
`Attested`.

## Managed-Attestation Track: Phala Operator Live Artifact Plumbing Implementation

Status: complete for local in-memory implementation only. See
`docs/83-phala-operator-live-artifact-plumbing-implementation-notes.md`.

Goal: implement the Phase 82 local operator-live artifact-plumbing contract in
`hsai-attestation-phala` without provider HTTP, filesystem writes, network
access, credentials, operator live tests, local DCAP, generated operator
artifacts, benchmark output, or claims above `Attested`.

Implemented: in-memory logical file parsing for the declared `operator-live/*`
bundle, portable path checks, required-file and extra-file validation, schema
checks, SHA-256 digest checks, redaction-report validation, provider and mode
consistency checks, trust-root consistency checks, existing hermetic
managed-verifier response validation, validated local artifact metadata, and
focused hermetic tests.

Dependencies: Phase 78 Phala live managed-verifier boundary, Phase 79 hermetic
implementation spec, Phase 80 hermetic fake-client implementation, Phase 81
operator-live path boundary, Phase 82 artifact-plumbing boundary, and Phase 4
claim boundaries.

Validation gate: focused Phala operator-live artifact tests, no process/network
source hooks, no Cargo metadata changes, no fixture changes, no generated
operator artifacts, root Cargo validation, and claim-boundary text checks.

Anti-goals: provider HTTP, filesystem writes, examples or scripts, live Phala
API calls, operator live tests, credential handling code, secret fixtures,
generated operator artifacts, network access, local Intel DCAP quote
verification, PCCS or collateral handling, generic JWKS/JWT fetching, TLS or
attested-TLS channel binding, deployment orchestration, external repo clones,
backend execution, benchmark outputs, accepted Evidence Ledger mutation, Phase
4 registry semantic changes, Level2+ evidence, global uniqueness claims, or
claims above `Attested`.

Exit criteria: valid in-memory bundles round trip; missing, extra, and unsafe
paths fail closed; schema and digest drift fail closed; stale responses and
missing trust roots fail closed; retained secret-shaped values fail closed;
rejected provider verdicts emit no validated artifact; normal test paths remain
hermetic; and successful validation remains capped at `Attested`.

## Managed-Attestation Track: Phala Operator Live Artifact Output Plumbing Boundary

Status: complete for docs-first boundary only. See
`docs/84-phala-operator-live-artifact-output-plumbing-boundary-spec.md`.

Goal: define the future materialized output-root contract for operator-live
artifact bundles before any implementation writes, reads, overwrites, or
validates files on disk.

Implemented: docs-first boundary for caller-selected output roots, declared
`operator-live/*` materialized file shape, write policy, read policy, overwrite
policy, symlink rejection, path-traversal rejection, partial-bundle rejection,
raw-response retention limits, future code touch surface, required hermetic
tests, and `Attested`-only claim limits.

Dependencies: Phase 81 operator-live path boundary, Phase 82 artifact-plumbing
boundary, Phase 83 in-memory artifact-plumbing implementation, and Phase 4
claim boundaries.

Validation gate: documentation navigation checks, claim-boundary text checks,
no Rust source changes, no Cargo metadata changes, no package runtime files, no
fixture changes, no generated artifacts, no filesystem implementation, no
network code, no live Phala calls, no operator secrets, and no accepted
Evidence Ledger mutation.

Anti-goals: Rust implementation, filesystem write/read implementation, examples
or scripts, live Phala API calls, operator live tests, credential handling
code, secret fixtures, generated operator artifacts, raw response body
retention, network access, local Intel DCAP quote verification, PCCS or
collateral handling, generic JWKS/JWT fetching, TLS or attested-TLS channel
binding, deployment orchestration, external repo clones, backend execution,
benchmark outputs, accepted Evidence Ledger mutation, Phase 4 registry semantic
changes, Level2+ evidence, global uniqueness claims, or claims above
`Attested`.

Exit criteria: the future output-plumbing boundary is named, README and AGENTS
point to it, future output-root rules are explicit, future write/read policies
reuse Phase 83 validation, future raw response retention remains forbidden by
default, normal test paths remain hermetic, and all successful future responses
remain capped at `Attested`.

## Managed-Attestation Track: Phala Operator Live Artifact Output Plumbing Implementation

Status: complete for local output-root plumbing. See
`docs/85-phala-operator-live-artifact-output-plumbing-implementation-notes.md`.

Goal: implement the Phase 84 materialized output-root contract for local
operator-live artifact bundles without adding live provider behavior,
credentials, generated operator artifacts, or claims above `Attested`.

Implemented: `PhalaOperatorLiveOutputOverwriteMode`,
`write_phala_operator_live_artifact_output_root`, and
`read_phala_operator_live_artifact_output_root` in `hsai-attestation-phala`.
The writer validates in-memory bundles first, materializes only the six declared
`operator-live/*` files under a caller-owned output root, stages writes before
publishing, requires explicit overwrite for existing bundles, and rereads the
materialized bundle through the Phase 83 validator. The reader rejects undeclared
files, partial bundles, symlinks, stale digests, invalid JSON, invalid UTF-8, and
raw response body retention by default before returning validated metadata.

Dependencies: Phase 81 operator-live path boundary, Phase 82 artifact-plumbing
boundary, Phase 83 in-memory artifact-plumbing implementation, Phase 84
output-plumbing boundary, and Phase 4 claim boundaries.

Validation gate: focused Phala operator-live artifact tests, claim-boundary text
checks, no Cargo metadata changes, no package runtime files, no fixture changes,
no generated operator artifacts, no network code, no live Phala calls, no
operator secrets, and no accepted Evidence Ledger mutation.

Anti-goals: live Phala API calls, operator live tests, credential handling code,
secret fixtures, generated operator artifacts, raw response body retention,
network access, local Intel DCAP quote verification, PCCS or collateral
handling, generic JWKS/JWT fetching, TLS or attested-TLS channel binding,
deployment orchestration, external repo clones, backend execution, benchmark
outputs, accepted Evidence Ledger mutation, Phase 4 registry semantic changes,
Level2+ evidence, global uniqueness claims, semantic-correctness claims, or
claims above `Attested`.

Exit criteria: valid materialized bundles write and read under a temporary
caller-owned root; repository-root, empty-root, symlink-root, symlink-file,
unexpected-file, partial-bundle, stale-digest, raw-response-body, and implicit
overwrite paths fail closed; normal tests remain hermetic; and all successful
validation remains capped at `Attested`.

## Benchmark OS Track: Phase V Local Artifact Campaign Boundary

Status: complete for docs-first boundary only. See
`docs/98-phase-v-local-artifact-campaign-boundary-spec.md`.

Goal: define the future user-approved durable local artifact campaign boundary
after Phase U local artifact packaging, before any campaign execution or durable
generated local artifact root exists.

Implemented: docs-first boundary for future campaign ids, ignored output roots,
valid local input classes, protected-path policy, retention policy, campaign
manifest shape, validation report shape, digest sidecars, required limitation
labels, accepted Evidence Ledger non-mutation, score-axis non-population, and
promotion non-goals.

Dependencies: Phase U local benchmark artifact packaging, Phase T cross-bundle
audit-index outputs, Phase S ergonomics outputs, Phase R audit-index outputs,
Phase Q report bundles, Phase O pack-readiness metadata, and local benchmark
packs.

Validation gate: documentation navigation checks, claim-boundary text checks,
repo hygiene checks, no Rust source changes, no Cargo metadata changes, no
generated campaign files, no package runtime files, no CLI/UI, no external
execution hooks, no official submission, and no accepted Evidence Ledger
mutation.

Anti-goals: Rust implementation in this slice, generated committed artifacts,
durable campaign outputs, external replay, live backend execution, official
benchmark evidence, accepted Evidence Ledger mutation, ZK backend performance
claims, score-axis population, Level2+ evidence creation, broad leaderboard
claims, command-line tools, UI dashboards, package runtime files, credentials,
or secrets.

Exit criteria: Phase V campaign boundary spec exists; README and AGENTS point
to it; source input classes, ignored output-root rules, required limitation
labels, retention rules, validation rules, and promotion boundary are explicit;
and all implementation remains blocked until a separate explicit phase.

## Benchmark OS Track: Phase V Local Artifact Campaign Implementation

Status: complete for local artifact-campaign output plumbing only. See
`docs/103-phase-v-local-artifact-campaign-implementation-notes.md`.

Goal: implement durable local artifact campaign metadata and output-root
plumbing after the Phase V boundary, without creating committed campaign
outputs, official benchmark evidence, accepted evidence, external replay
evidence, score-axis population, or Level2+ evidence.

Implemented: `LocalArtifactCampaignManifest`, campaign input refs, retention
policy, validation report, required limitation labels, deterministic JSON and
Markdown rendering, manifest digesting, exactly six declared campaign output
files, digest sidecars for every campaign-level file, Phase U output-root
validation before campaign input construction, protected-path overlap rejection,
symlink-resolved overlap rejection, stale-digest rejection, partial-campaign
rejection, unexpected-file rejection, symlink rejection, and non-repair
overwrite behavior. `.local-artifact-campaigns/` is ignored as a default
operator-owned local output root.

Dependencies: Phase U local benchmark artifact packaging, Phase V docs-first
boundary, local output-root patterns from Phases Q/R/S/T/U, and Phase W
promotion non-goals.

Validation gate: focused Phase V campaign tests, Phase U artifact tests,
repository claim-boundary checks, repo hygiene checks, workspace tests, clippy,
docs, no Cargo metadata changes, no package runtime files, no generated
committed campaign files, no CLI/UI, no external replay hooks, no network or
credential path, no official submission, and no accepted Evidence Ledger
mutation.

Anti-goals: generated committed campaign outputs, external replay, live backend
execution, official benchmark evidence, accepted Evidence Ledger mutation, ZK
backend performance claims, score-axis population, Level2+ evidence creation,
broad leaderboard claims, command-line tools, UI dashboards, package runtime
files, credentials, or secrets.

Exit criteria: valid campaign manifests serialize, validate, render, write, and
read deterministically; invalid campaign ids, missing Phase U outputs, claim
elevation, unsafe refs, missing limitation labels, stale digests, partial
outputs, unexpected files, protected overlap, symlinks, and repair overwrites
fail closed; normal workspace tests remain hermetic; and campaign outputs remain
local durability metadata only.

## Benchmark OS Track: Phase W Reviewed Evidence Promotion Boundary

Status: complete for docs-first boundary only. See
`docs/99-phase-w-reviewed-evidence-promotion-boundary-spec.md`.

Goal: define the future reviewed accepted-evidence mutation and official
submission boundary before any accepted Evidence Ledger append, official
submission package, score-axis population, or Level2+ promotion exists.

Implemented: docs-first boundary for future promotion preconditions, accepted
Evidence Ledger mutation policy, official submission package preconditions,
evidence class separation, required future tests, required non-claims, and
blocked local-only promotion paths.

Dependencies: Phase J reviewed proposal acceptance metadata, Phase O
pack-readiness, Phase U local artifact packaging, Phase V local artifact
campaign boundary, future external replay authority, future external result
import, and future manual review approval.

Validation gate: documentation navigation checks, claim-boundary text checks,
repo hygiene checks, no Rust source changes, no Cargo metadata changes, no
generated artifacts, no package runtime files, no external replay, no official
submission, no accepted Evidence Ledger mutation, no score report mutation, and
no Level2+ evidence creation.

Anti-goals: implementation in this slice, accepted Evidence Ledger append,
official benchmark submission, external replay, live backend execution, network
access, credentials, external result import, score-axis population, ZK backend
performance claims, formal/soundness claims without scoped evidence, Level2+
evidence creation, broad leaderboard claims, command-line tools, UI dashboards,
or package runtime files.

Exit criteria: Phase W promotion boundary spec exists; README and AGENTS point
to it; accepted-ledger mutation and official-submission preconditions are
explicit; local-only evidence remains blocked from promotion; and all mutation
or submission implementation remains blocked until a separate explicit phase.

## Managed-Attestation Track: Phala Operator Live Invocation Boundary

Status: complete for docs-first boundary only. See
`docs/97-phala-operator-live-invocation-boundary-spec.md`.

Goal: define the future operator-owned live Phala/dstack invocation contract
after local operator artifact output plumbing, before any live provider call,
credential path, network code, or operator live test exists.

Implemented: docs-first boundary for the single allowed provider/mode
(`Phala/dstack`, operator-owned live managed-verifier invocation), future
declared invocation inputs, credential boundary, fail-closed invocation order,
normal-test exclusion, required future hermetic tests, required non-claims, and
explicit blocks for DCAP/PCCS/JWKS/TLS and accepted evidence mutation.

Dependencies: Phase 81 operator-live path boundary, Phase 82 artifact-plumbing
boundary, Phase 83 in-memory artifact-plumbing implementation, Phase 84
output-plumbing boundary, Phase 85 local output-root plumbing implementation,
and Phase 4 claim boundaries.

Validation gate: documentation navigation checks, claim-boundary text checks,
repo hygiene checks, no Rust source changes, no Cargo metadata changes, no
fixtures, no generated operator artifacts, no package runtime files, no
network code, no live Phala calls, no credentials, no operator live tests, no
benchmark outputs, and no accepted Evidence Ledger mutation.

Anti-goals: implementation in this slice, examples or scripts, package runtime
files, network access, live Phala API calls, credentials or secret fixtures,
operator live tests, generated operator artifacts, local Intel DCAP quote
verification, PCCS or collateral fetching, generic JWKS/JWT fetching, TLS or
attested-TLS channel binding, deployment orchestration, external repo clones,
backend execution, benchmark outputs, accepted Evidence Ledger mutation,
Phase 4 registry semantic changes, Level2+ evidence, global uniqueness claims,
or claims above `Attested`.

Exit criteria: Phase 97 invocation boundary spec exists; README and AGENTS
point to it; future live calls remain operator-only and excluded from normal
tests; future credentials stay outside git; future output flows through the
existing redacted digest-bound operator artifact plumbing; and all successful
future invocation output remains capped at `Attested`.

## Managed-Attestation Track: Phala Operator Live Invocation Implementation

Status: complete for local invocation plumbing only. See
`docs/100-phala-operator-live-invocation-implementation-notes.md`.

Goal: implement the smallest operator-owned invocation orchestrator after the
Phase 97 boundary, without shipping a network client, loading real credentials,
running live Phala calls, or raising claims above `Attested`.

Implemented: additive `hsai-attestation-phala` invocation input types, opaque
credential type, credential-provider trait, hermetic in-memory credential
provider, credential-aware injected client trait, invocation orchestrator,
fail-closed acknowledgement/endpoint/credential/timeout/retry validation,
bounded retry exhaustion mapping, normalized response validation, replay
rejection, redacted artifact-bundle assembly, Phase 85 output-root reuse, and
hermetic tests.

Dependencies: Phase 80 hermetic live-verifier response validation, Phase 83
in-memory operator artifact plumbing, Phase 85 output-root plumbing, and Phase
97 invocation boundary.

Validation gate: Phala crate tests, workspace tests, clippy, docs, repository
claim-boundary checks, repo hygiene checks, no Cargo metadata changes, no
examples or scripts, no package runtime files, no network client, no process
environment credential loader, no real credentials, no generated operator
artifacts, no operator live tests, no live Phala calls, no benchmark outputs,
and no accepted Evidence Ledger mutation.

Anti-goals: shipped HTTP client, process environment loading, network access,
live Phala API calls, operator live tests, real operator credentials, secret
fixtures, generated operator artifacts, local Intel DCAP quote verification,
PCCS or collateral fetching, generic JWKS/JWT fetching, TLS or attested-TLS
channel binding, deployment orchestration, external repo clones, backend
execution, benchmark outputs, accepted Evidence Ledger mutation, Phase 4
registry semantic changes, Level2+ evidence, global uniqueness claims, or
claims above `Attested`.

Exit criteria: the invocation orchestrator rejects missing controls before
client invocation, loads credentials only through caller-owned providers, never
serializes credential material to artifacts, validates accepted responses,
fails closed on retry exhaustion/provider rejection/replay, writes only the
declared Phase 85 operator-live artifact files, and normal workspace tests
remain hermetic.

## Managed-Attestation Track: Phala Operator Live Provider Client Boundary

Status: complete for docs-first boundary only. See
`docs/101-phala-operator-live-provider-client-boundary-spec.md`.

Goal: define the future concrete Phala/dstack provider-client boundary behind
the existing Phase 100 injected-client seam before any shipped network client,
real credential source, operator live test, or live Phala call exists.

Implemented: docs-first boundary for the single allowed provider/mode
(`Phala/dstack`, operator-owned live managed-verifier provider client), future
provider-client touch surface, credential source contract, bounded network and
retry contract, operator-only test/command contract, source refresh
requirement, required future hermetic tests, required non-claims, and explicit
blocks for DCAP/PCCS/JWKS/TLS and accepted evidence mutation.

Dependencies: Phase 85 operator-live output-root plumbing, Phase 100 local
operator-live invocation plumbing, current Phala/dstack upstream documentation
re-check before implementation hard-codes endpoint or response semantics, and
Phase 4 claim boundaries.

Validation gate: documentation navigation checks, claim-boundary text checks,
repo hygiene checks, no Rust source changes, no Cargo metadata changes, no
fixtures, no examples or scripts, no generated operator artifacts, no package
runtime files, no network code, no live Phala calls, no credentials, no
operator live tests, no benchmark outputs, and no accepted Evidence Ledger
mutation.

Anti-goals: implementation in this slice, shipped HTTP client, process
environment loading, network access, live Phala API calls, operator live tests,
real operator credentials, secret fixtures, generated operator artifacts, local
Intel DCAP quote verification, PCCS or collateral fetching, generic JWKS/JWT
fetching, TLS or attested-TLS channel binding, deployment orchestration,
external repo clones, backend execution, benchmark outputs, accepted Evidence
Ledger mutation, Phase 4 registry semantic changes, Level2+ evidence, global
uniqueness claims, or claims above `Attested`.

Exit criteria: Phase 101 provider-client boundary spec exists; README and
AGENTS point to it; the future client is constrained to the existing Phase 100
invocation seam; future live calls remain operator-only and excluded from
normal tests; future credentials stay outside git; future output flows through
the existing redacted digest-bound operator artifact plumbing; and all
successful future provider-client output remains capped at `Attested`.

## Managed-Attestation Track: Phala Operator Live Provider Client Implementation

Status: complete for opt-in operator-owned provider-client plumbing only. See
`docs/102-phala-operator-live-provider-client-implementation-notes.md`.

Goal: implement the smallest concrete Phala/dstack provider client behind the
Phase 100 injected-client seam while keeping the HTTP path feature-gated,
operator-owned, excluded from normal tests, and capped at `Attested`.

Implemented: optional `operator-live-provider` feature, provider-client config,
allowlisted environment credential provider, transport seam, ureq-backed HTTP
transport with bounded timeout and redirects disabled, concrete
`PhalaOperatorLiveClient` implementation, raw-response digest replacement,
authentication/status/transport/malformed-response error mapping, and hermetic
fake-transport tests flowing through the existing Phase 100 invocation
orchestrator and Phase 85 redacted output-root plumbing.

Dependencies: Phase 85 operator-live output-root plumbing, Phase 100 local
operator-live invocation plumbing, Phase 101 provider-client boundary, current
Phala/dstack documentation re-check, and Phase 4 claim boundaries.

Validation gate: Phala crate tests with and without
`--features operator-live-provider`, workspace tests, clippy, docs,
repository claim-boundary checks, repo hygiene checks, no examples or scripts,
no package runtime files, no committed credentials, no secret fixtures, no
generated operator artifacts, no operator live tests, no live Phala calls, no
DCAP/PCCS/JWKS/TLS path, no benchmark outputs, and no accepted Evidence Ledger
mutation.

Anti-goals: default network access, normal tests requiring credentials,
operator live tests, committed real credentials, secret fixtures, generated
operator artifacts, hard-coded provider endpoint schemas, local Intel DCAP quote
verification, PCCS or collateral fetching, generic JWKS/JWT fetching, managed
signature verification, TLS or attested-TLS channel binding, deployment
orchestration, external repo clones, vendored source, backend execution,
benchmark outputs, accepted Evidence Ledger mutation, Phase 4 registry semantic
changes, Level2+ evidence, global uniqueness claims, or claims above
`Attested`.

Exit criteria: the feature-gated provider client validates controls before
transport use, loads credentials only from allowlisted operator-declared
environment sources, sends secrets only as outbound bearer material, never
writes raw responses or credential material, normalizes accepted responses
before the Phase 100 orchestrator validates them, and normal workspace tests
remain hermetic.

## Managed-Attestation Track: Phala Operator Live Runner Boundary

Status: complete for docs-first boundary only. See
`docs/104-phala-operator-live-runner-boundary-spec.md`.

Goal: define the future operator-only live runner after Phase 102 provider
client plumbing, before any command wiring, operator live test, generated live
artifact, accepted evidence, official submission, or DCAP/PCCS/JWKS/TLS path
exists.

Implemented: docs-first boundary for a feature-gated example surface, explicit
operator acknowledgement, non-secret invocation JSON path, matching
credential-source declaration, allowlisted environment credential loading,
existing Phase 100 invocation seam, existing Phase 85 output writer, normal
test exclusion, source-contract tests, and `Attested`-only claim limits.

Dependencies: Phase 85 operator-live output-root plumbing, Phase 100
operator-live invocation plumbing, Phase 102 provider-client implementation,
current Phala/dstack documentation re-check, and Phase 4 claim boundaries.

Validation gate: documentation navigation checks, claim-boundary text checks,
repo hygiene checks, no Rust source changes, no Cargo metadata changes, no
fixtures, no generated operator artifacts, no package runtime files, no live
Phala calls, no credentials, no operator live tests, no benchmark outputs, and
no accepted Evidence Ledger mutation.

Anti-goals: implementation in this slice, live Phala calls, operator live
tests, real credentials, credential fixtures, generated operator artifacts,
local Intel DCAP quote verification, PCCS or collateral fetching, generic
JWKS/JWT fetching, TLS or attested-TLS channel binding, deployment
orchestration, backend execution, benchmark outputs, official benchmark
submission, accepted Evidence Ledger mutation, Level2+ evidence, global
uniqueness claims, or claims above `Attested`.

Exit criteria: Phase 104 runner boundary spec exists; README and AGENTS point
to it; the future runner is constrained to the existing Phase 100 invocation
seam and Phase 85 output writer; normal tests remain hermetic; and any future
successful run remains capped at `Attested`.

## Managed-Attestation Track: Phala Operator Live Runner Implementation

Status: complete for operator-only example runner only. See
`docs/105-phala-operator-live-runner-implementation-notes.md`.

Goal: implement the smallest operator-owned runner over the Phase 102 provider
client while keeping the path feature-gated, explicitly acknowledged,
credential-free in git, excluded from normal tests, and capped at `Attested`.

Implemented: `crates/hsai-attestation-phala/examples/operator_live_run.rs`,
which requires `--features operator-live-provider`,
`HSAI_PHALA_OPERATOR_ACK=I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN`,
`HSAI_PHALA_OPERATOR_INPUT_JSON`, and
`HSAI_PHALA_OPERATOR_CREDENTIAL_SOURCE`. The runner reads a non-secret
invocation JSON, requires the declared credential source to match the JSON,
allowlists exactly that credential source, constructs
`PhalaOperatorLiveProviderClient<UreqPhalaOperatorLiveTransport>`, invokes
through `PhalaOperatorLiveInvocation`, writes only the existing redacted
`operator-live/*` bundle, and prints only non-secret validated metadata.

Dependencies: Phase 85 operator-live output-root plumbing, Phase 100
operator-live invocation plumbing, Phase 102 provider-client implementation,
Phase 104 runner boundary, and Phase 4 claim boundaries.

Validation gate: runner contract tests, Phala crate tests with and without
`--features operator-live-provider`, example clippy with
`--features operator-live-provider --examples`, workspace tests, clippy, docs,
no committed credentials, no secret fixtures, no generated committed operator
artifacts, no normal test network access, no DCAP/PCCS/JWKS/TLS path, no
benchmark outputs, and no accepted Evidence Ledger mutation.

Anti-goals: normal tests requiring credentials, committed real credentials,
secret fixtures, generated committed operator artifacts, hard-coded provider
endpoint schemas, local Intel DCAP quote verification, PCCS or collateral
fetching, generic JWKS/JWT fetching, managed-service signature verification,
TLS or attested-TLS channel binding, deployment orchestration, external repo
clones, vendored source, benchmark outputs, official benchmark submission,
accepted Evidence Ledger mutation, Phase 4 registry semantic changes, Level2+
evidence, global uniqueness claims, or claims above `Attested`.

Exit criteria: the runner compiles only as an operator-owned feature-gated path,
requires explicit acknowledgement and matching credential source declaration,
contains no hard-coded endpoint or secret, writes no raw response body, uses
the existing invocation/output plumbing, normal workspace tests remain
hermetic, and this repository still commits no live operator artifact.

## Managed-Attestation Track: Phala Cloud API Live Artifact Materialization

Status: complete for operator-only Phala Cloud API response materialization
only. See `docs/106-phala-cloud-api-live-artifact-implementation-notes.md`.

Goal: bridge an operator-run Phala Cloud `/attestations/verify` response into
the existing redacted `operator-live/*` artifact format without adding network
access to normal tests or committing generated live artifacts.

Implemented:
`crates/hsai-attestation-phala/examples/operator_live_phala_api_artifact.rs`,
which requires
`HSAI_PHALA_OPERATOR_ACK=I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN` and
`HSAI_PHALA_API_ARTIFACT_INPUT_JSON`. The example reads a non-secret input JSON,
loads a repo-external captured artifact bundle and a repo-external raw Phala
verification response, checks `success`, quote `verified`, `TEE_TDX`, and
captured report-data prefix binding, maps the response into the existing
normalized `PhalaManagedVerifierResponse`, hashes but does not retain the raw
response body, writes only the existing redacted `operator-live/*` bundle, and
reads it back through the validator.

Dependencies: Phase 85 operator-live output-root plumbing, Phase 83 in-memory
operator-live artifact validation, Phase 105 runner/output boundary, and a
repo-external operator-run Phala Cloud API response.

Validation gate: source-contract tests, Phala crate tests, workspace tests,
clippy, docs, no committed credentials, no secret fixtures, no generated
committed operator artifacts, no normal test network access, no
DCAP/PCCS/JWKS/TLS path, no benchmark outputs, and no accepted Evidence Ledger
mutation.

Anti-goals: normal tests requiring credentials, committed real credentials,
secret fixtures, generated committed operator artifacts, direct network APIs in
normal source, local Intel DCAP quote verification, PCCS or collateral
fetching, generic JWKS/JWT fetching, managed-service signature verification,
TLS or attested-TLS channel binding, deployment orchestration, external repo
clones, vendored source, benchmark outputs, official benchmark submission,
accepted Evidence Ledger mutation, Phase 4 registry semantic changes, Level2+
evidence, global uniqueness claims, or claims above `Attested`.

Exit criteria: an operator can run Phala Cloud verification outside normal
tests, save the raw response outside git, materialize the local redacted
operator-live artifact outside git, validate it through the existing output-root
reader, and keep the repository free of generated live artifacts.

## Managed-Attestation Track: Phala DCAP/PCCS Collateral Materialization

Status: complete for operator-only Phala Cloud collateral response
materialization only. See
`docs/107-phala-dcap-pccs-collateral-implementation-notes.md`.

Goal: bridge an operator-run Phala Cloud
`/attestations/collateral/<checksum>` response into digest-only local metadata
without adding network access to normal tests, retaining raw collateral in the
materialized output, operating a local PCCS, or claiming local DCAP
verification.

Implemented:
`crates/hsai-attestation-phala/examples/operator_live_dcap_pccs_artifact.rs`,
which requires
`HSAI_PHALA_OPERATOR_ACK=I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN` and
`HSAI_PHALA_DCAP_PCCS_INPUT_JSON`. The example reads a non-secret input JSON,
loads repo-external saved Phala `/attestations/verify` and
`/attestations/collateral/<checksum>` responses, checks `success`, quote
`verified`, `TEE_TDX`, checksum consistency, and required collateral field
presence, hashes the raw responses and each required collateral field, writes
only digest-only `dcap-pccs/*` files outside git, and retains no raw response
body in the materialized output.

Dependencies: Phase 106 operator-run Phala Cloud verification response,
operator-owned collateral fetch outside normal tests, and repo-external ignored
artifact storage.

Validation gate: source-contract tests, Phala crate tests, feature-specific
tests, clippy, docs, no committed credentials, no secret fixtures, no generated
committed operator artifacts, no normal test network access, no local
DCAP/QVL quote-signature verification, no local PCCS operation, no
JWKS/JWT/TLS path, no benchmark outputs, and no accepted Evidence Ledger
mutation.

Anti-goals: normal tests requiring credentials, committed real credentials,
secret fixtures, generated committed operator artifacts, direct network APIs in
normal source, local Intel QVL/DCAP quote-signature verification, local PCCS
service operation, generic JWKS/JWT fetching, managed-service signature
verification beyond consuming the saved provider response, TLS or attested-TLS
channel binding, deployment orchestration, external repo clones, vendored
source, benchmark outputs, official benchmark submission, accepted Evidence
Ledger mutation, Phase 4 registry semantic changes, Level2+ evidence, global
uniqueness claims, or claims above `Attested`.

Exit criteria: an operator can fetch Phala collateral outside normal tests, save
the raw collateral response outside git, materialize local digest-only
`dcap-pccs/*` metadata outside git, validate required collateral fields by
presence and digest, and keep the repository free of generated live artifacts.

## Managed-Attestation Track: Phala Local DCAP/QVL Verification Artifact

Status: complete for operator-only local QVL verification artifact
materialization only. See
`docs/108-phala-local-dcap-qvl-verification-notes.md`.

Goal: bridge a real raw Phala quote and operator-run local `dcap-qvl`
verification output into digest-only local metadata without adding network
access to normal tests, committing raw quote/QVL artifacts, operating a local
PCCS, or claiming proof.

Implemented:
`crates/hsai-attestation-phala/examples/operator_live_dcap_qvl_artifact.rs`,
which requires
`HSAI_PHALA_OPERATOR_ACK=I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN` and
`HSAI_PHALA_DCAP_QVL_INPUT_JSON`. The example reads a non-secret input JSON,
loads repo-external saved Phala `/attestations/verify`, raw quote, decoded
quote, PCK info, and QVL report files, checks `TEE_TDX`, TDX quote version 4,
PCK certificate chain roles, QVL/QE/platform `UpToDate` statuses, empty
advisory IDs, and measurement equality across Phala parsed quote, decoded raw
quote, and QVL report, then writes only digest-only `dcap-qvl/*` files outside
git.

Dependencies: Phase 106 Phala verification response, Phase 107 raw collateral
context, Phala raw quote download, operator-installed `dcap-qvl` 0.5.2, and
repo-external ignored artifact storage.

Validation gate: source-contract tests, Phala crate tests, feature-specific
tests, clippy, docs, no committed credentials, no secret fixtures, no generated
committed raw quote or QVL artifacts, no normal test network access, no
repo-native DCAP verifier implementation, no local PCCS service operation, no
JWKS/JWT/TLS path, no benchmark outputs, and no accepted Evidence Ledger
mutation.

Anti-goals: normal tests requiring credentials, committed real credentials,
secret fixtures, committed raw quote or QVL artifacts, direct network APIs in
normal source, repo-native Intel QVL/DCAP verifier implementation, local PCCS
service operation, generic JWKS/JWT fetching, managed-service signature
verification beyond consuming saved provider/QVL outputs, TLS or attested-TLS
channel binding, deployment orchestration, external repo clones, vendored
source, benchmark outputs, official benchmark submission, accepted Evidence
Ledger mutation, Phase 4 registry semantic changes, Level2+ evidence, global
uniqueness claims, or claims above `Attested`.

Exit criteria: an operator can download the raw quote outside normal tests, run
local `dcap-qvl` verification outside normal tests, materialize digest-only
`dcap-qvl/*` metadata outside git, validate QVL statuses and measurement
binding, and keep the repository free of generated live artifacts.

## Managed-Attestation Track: Managed JWKS Fetch Artifact

Status: complete for operator-only managed OpenID/JWKS fetch artifact
materialization only. See
`docs/109-managed-jwks-fetch-artifact-notes.md`.

Goal: bridge one real public managed-attestation OpenID/JWKS fetch into
digest-only local metadata without adding network access to normal tests,
committing raw OpenID/JWKS responses, accepting tokens, or claiming managed-JWT
signature verification.

Implemented:
`crates/hsai-attestation/examples/operator_live_jwks_artifact.rs`, which
requires
`HSAI_MANAGED_JWKS_OPERATOR_ACK=I_ACKNOWLEDGE_OPERATOR_LIVE_JWKS_FETCH` and
`HSAI_MANAGED_JWKS_INPUT_JSON`. The example reads a non-secret input JSON,
loads repo-external saved OpenID metadata and JWKS responses, checks HTTPS
issuer and endpoint declarations, OpenID issuer and `jwks_uri` consistency,
`id_token` response support, required `iss`/`exp`/`nbf` claims, non-empty
signing algorithms, non-empty RSA JWKS keys, advertised key algorithms, and
unique `kid` plus algorithm pairs, then writes only digest-only
`managed-jwks/*` files outside git.

Dependencies: managed-signature boundary spec, offline managed-JWT verification,
Intel Trust Authority OpenID/JWKS documentation, live public OpenID/JWKS fetch,
and repo-external ignored artifact storage.

Validation gate: source-contract tests, `hsai-attestation` tests, clippy, docs,
no committed credentials, no secret fixtures, no generated committed OpenID or
JWKS responses, no normal test network access, no token acceptance, no
managed-JWT signature verification, no DCAP/PCCS/TLS path, no benchmark outputs,
and no accepted Evidence Ledger mutation.

Anti-goals: normal tests requiring network access or credentials, committed raw
OpenID/JWKS responses, committed real credentials, secret fixtures, token
acceptance, live managed-JWT signature verification, Azure provider
implementation, Phala managed-signature verification, local DCAP quote
verification, local PCCS service operation, TLS or attested-TLS channel binding,
deployment orchestration, external repo clones, vendored source, benchmark
outputs, official benchmark submission, accepted Evidence Ledger mutation,
Phase 4 registry semantic changes, Level2+ evidence, global uniqueness claims,
or claims above `Attested`.

Exit criteria: an operator can fetch public OpenID metadata and JWKS outside
normal tests, materialize digest-only `managed-jwks/*` metadata outside git,
validate metadata/JWKS consistency, and keep the repository free of generated
live artifacts.

## Managed-Attestation Track: Local PCCS-Compatible Service Artifact

Status: complete for operator-only localhost PCCS-compatible replay service
artifact materialization only. See
`docs/110-phala-local-pccs-service-artifact-notes.md`.

Goal: bridge one local PCCS service-operation run into digest-only local
metadata by serving saved Phala collateral from a localhost-only PCCS-shaped
service and running `dcap-qvl verify` with `PCCS_URL` pointed at that service,
without adding network access to normal tests, committing raw local PCCS logs,
or claiming production Intel PCS/PCCS operation.

Implemented:
`crates/hsai-attestation-phala/examples/operator_live_local_pccs_artifact.rs`,
which requires
`HSAI_PHALA_OPERATOR_ACK=I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN` and
`HSAI_PHALA_LOCAL_PCCS_INPUT_JSON`. The example reads a non-secret input JSON,
loads repo-external saved raw quote, PCK info, local-QVL report, local PCCS
access log, and saved local PCCS response bodies, checks localhost-only
`pccs_url`, TDX PCK roles, QVL/QE/platform `UpToDate` status, empty advisory
IDs, expected PCCS routes, response-file names, and response digests, then
writes only digest-only `local-pccs/*` files outside git.

Dependencies: Phase 107 collateral response materialization, Phase 108 local
QVL verification, operator-installed `dcap-qvl` 0.5.2, a localhost-only
PCCS-shaped replay service, and repo-external ignored artifact storage.

Validation gate: source-contract tests, `hsai-attestation-phala` tests, clippy,
docs, no committed credentials, no secret fixtures, no generated committed raw
quote, no generated committed QVL report, no generated committed access log, no
normal test network access, no production Intel PCS/PCCS operation, no
managed-JWT signature verification, no TLS channel binding, no benchmark
outputs, and no accepted Evidence Ledger mutation.

Anti-goals: normal tests requiring network access or credentials, committed raw
local PCCS access logs, committed local PCCS response bodies, committed real
credentials, secret fixtures, production Intel PCS/PCCS operation, fresh
collateral authority claims, repo-native DCAP verifier implementation, token
acceptance, live managed-JWT signature verification, TLS or attested-TLS channel
binding, deployment orchestration, external repo clones, vendored source,
benchmark outputs, official benchmark submission, accepted Evidence Ledger
mutation, Phase 4 registry semantic changes, Level2+ evidence, global
uniqueness claims, or claims above `Attested`.

Exit criteria: an operator can run `dcap-qvl verify` against a localhost
PCCS-compatible replay service outside normal tests, materialize digest-only
`local-pccs/*` metadata outside git, validate local service accesses and QVL
status, and keep the repository free of generated live artifacts.

## Managed-Attestation Track: Direct Intel PCS QVL Artifact

Status: complete for operator-only direct Intel PCS-backed QVL artifact
materialization only. See
`docs/111-phala-intel-pcs-direct-artifact-notes.md`.

Goal: bridge one direct Intel PCS-backed QVL run into digest-only local
metadata by running `dcap-qvl verify` with
`PCCS_URL=https://api.trustedservices.intel.com`, without adding network access
to normal tests, committing raw QVL outputs, or claiming proof.

Implemented:
`crates/hsai-attestation-phala/examples/operator_live_intel_pcs_artifact.rs`,
which requires
`HSAI_PHALA_OPERATOR_ACK=I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN` and
`HSAI_PHALA_INTEL_PCS_INPUT_JSON`. The example reads a non-secret input JSON,
loads repo-external saved raw quote, PCK info, direct Intel PCS QVL report, and
QVL stderr, checks the Intel PCS URL, TDX PCK roles, QVL/QE/platform
`UpToDate` status, and empty advisory IDs, then writes only digest-only
`intel-pcs/*` files outside git.

Dependencies: Phase 108 raw quote capture, operator-installed `dcap-qvl` 0.5.2,
Intel public PCS availability, and repo-external ignored artifact storage.

Validation gate: source-contract tests, `hsai-attestation-phala` tests, clippy,
docs, no committed credentials, no secret fixtures, no generated committed raw
quote, no generated committed QVL report, no normal test network access, no
repo-native DCAP verifier implementation, no managed-JWT signature
verification, no TLS channel binding, no benchmark outputs, and no accepted
Evidence Ledger mutation.

Anti-goals: normal tests requiring network access or credentials, committed raw
QVL outputs, committed real credentials, secret fixtures, repo-native DCAP
verifier implementation, token acceptance, live managed-JWT signature
verification, TLS or attested-TLS channel binding, deployment orchestration,
external repo clones, vendored source, benchmark outputs, official benchmark
submission, accepted Evidence Ledger mutation, Phase 4 registry semantic
changes, Level2+ evidence, global uniqueness claims, or claims above
`Attested`.

Exit criteria: an operator can run direct Intel PCS-backed `dcap-qvl verify`
outside normal tests, materialize digest-only `intel-pcs/*` metadata outside
git, validate QVL status, and keep the repository free of generated live
artifacts.

## Managed-Attestation Track: Phala TLS Channel-Binding Artifact Boundary

Status: docs-first boundary complete. See
`docs/112-phala-tls-channel-binding-artifact-boundary-spec.md`.

Goal: define the smallest future operator-only TLS 1.3 channel-binding artifact
for a Phala verification request before adding TLS code, live transport, or
generated artifacts.

Implemented: a documentation-only contract for one future Phala Cloud
`/api/v1/attestations/verify` connection using Web PKI validation, TLS 1.3,
the RFC 9266 `EXPORTER-Channel-Binding` label, empty context, 32-byte exporter,
same-connection request/response capture, digest-only output, hermetic source
tests, and explicit claim limits.

Dependencies: Phase 106 Phala Cloud API artifact materialization, RFC 9266,
RFC 8446 section 7.5, dstack transport architecture, and the Phase 66
transport-bound attestation separation.

Validation gate: docs links and source attribution, explicit state slice,
normal-test hermeticity requirements, no Rust source, no Cargo changes, no
network access, no live Phala call, no generated artifact, no credential, no
RA-TLS claim, no benchmark output, and no accepted Evidence Ledger mutation.

Anti-goals: implementation in this slice, TLS 1.2, redirects, proxies, custom
trust roots, insecure certificate bypasses, connection reuse, raw exporter or
response retention, attested server certificates, RA-TLS, proof, benchmark
evidence, official submission, accepted Evidence Ledger mutation, Phase 4
registry semantic changes, Level2+ evidence, global uniqueness claims, or
claims above `Attested`.

Exit criteria: this boundary spec exists; README, AGENTS, task ledger, and
source index point to it; the future artifact shape and tests are explicit; and
the docs state that a client-local TLS exporter capture is not independently
verifiable attested TLS.

## Managed-Attestation Track: Phala TLS Channel-Binding Artifact Implementation

Status: complete for operator-only TLS 1.3 connection artifact materialization.
See `docs/113-phala-tls-channel-binding-artifact-implementation-notes.md`.

Goal: capture one RFC 9266 exporter and one accepted Phala verification
response from the same operator-owned TLS 1.3 connection, then retain only
digest-bound local metadata outside git.

Implemented: a disabled-by-default `operator-live-tls-channel` feature and
`operator_live_tls_channel_artifact` example using rustls, Web PKI roots, TLS
1.3 only, fixed Phala host and path, one HTTP/1.1 request with connection close,
bounded transport, RFC 9266 exporter derivation, accepted TDX response checks,
staged five-file output, overwrite validation, and hermetic tests.

Dependencies: Phase 112 boundary, Phase 106 Phala response semantics, rustls
0.23, webpki-roots 0.26, RFC 9266, and the accepted non-secret Phala TDX quote.

Validation gate: feature-enabled example tests and compilation, source-contract
tests, Phala crate tests, workspace tests, clippy, docs, coverage, one explicit
operator live run, no normal-test network, no credential, no committed generated
artifact, no raw exporter/request/response/certificate output, no RA-TLS claim,
no benchmark output, and no accepted Evidence Ledger mutation.

Anti-goals: TLS 1.2, redirects, proxies, custom roots, certificate bypasses,
connection reuse, raw transport retention, attested server certificates,
endpoint-key quote binding, RA-TLS, proof, official benchmark submission,
accepted Evidence Ledger mutation, Phase 4 registry semantic changes, Level2+
evidence, global uniqueness claims, semantic correctness claims, or claims
above `Attested`.

Exit criteria: the operator example compiles only behind its feature, normal
tests remain hermetic, one live run records TLS 1.3 and a 32-byte RFC 9266
exporter with the accepted Phala response on the same connection, exactly five
digest-bound files exist outside git, and all non-claims remain explicit.
