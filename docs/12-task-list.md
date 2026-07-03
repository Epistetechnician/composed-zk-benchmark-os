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

## Benchmark OS Track: Phase 127 DSL Coverage Campaign

Status: complete for local DSL/oracle coverage hardening. See
`docs/127-phase-dsl-coverage-campaign-notes.md`.

Goal: improve local line coverage over the hermetic DSL/oracle/validation
surface without production API changes, runtime execution broadening, live
provider work, external replay, official submission, accepted Evidence Ledger
mutation, score-axis population, Level2+ evidence, or 100% coverage claims.

Scope: focused tests under `crates/zkbench-core/tests/oracle_eval.rs` and
`crates/zkbench-core/tests/lowering.rs`, plus phase notes and
navigation/status updates.

Implemented: guard/action combinator tests, expression helper reference/raw
text tests, oracle rejection tests for trace drift/final expectations/arithmetic
failures/missing initial values, and validation rejection tests for ids, states,
fields, trace references, duplicate ids, and actual Level2 boundary overclaims.

Anti-goals: production source changes, new APIs, generated artifacts, external
replay execution, official endpoint calls, credentials or secrets, accepted
Evidence Ledger mutation, official benchmark submission, live backend
execution, network access, command-line tools, UI dashboards, package runtime
additions, score-axis population, ZK backend performance claims, Level2+
evidence creation, formal evidence creation, SOTA claims, broad leaderboard
claims, production-readiness claims, semantic-correctness claims, or claiming
100% coverage.

Exit criteria: Phase 127 notes exist; README, AGENTS, task list, and
validation report point to them; focused DSL/oracle tests pass; all-feature
workspace coverage improves from Phase 126; normal gates remain hermetic; and
no live/external evidence surface is created.

## Benchmark OS Track: Phase 128 Soak Serialization Coverage

Status: complete for local soak serialization coverage hardening. See
`docs/128-phase-soak-serialization-coverage-notes.md`.

Goal: improve local line coverage over the hermetic soak JSON serialization
surface without production API changes, runtime execution broadening, live
provider work, external replay, official submission, accepted Evidence Ledger
mutation, score-axis population, Level2+ evidence, or 100% coverage claims.

Scope: focused tests under `crates/zkbench-core/tests/soak_serialization.rs`,
plus phase notes and navigation/status updates.

Implemented: successful pretty-JSON round-trip tests for soak run configs,
shard plans, shard manifests, shard checkpoints, telemetry reports, health
reports, failure corpus indexes, failure reproduction manifests, artifact
manifests, and report bundles; malformed JSON tests for every corresponding
soak deserializer wrapper path.

Anti-goals: production source changes, new APIs, generated artifacts, external
replay execution, official endpoint calls, credentials or secrets, accepted
Evidence Ledger mutation, official benchmark submission, live backend
execution, network access, command-line tools, UI dashboards, package runtime
additions, score-axis population, ZK backend performance claims, Level2+
evidence creation, formal evidence creation, SOTA claims, broad leaderboard
claims, production-readiness claims, semantic-correctness claims, or claiming
100% coverage.

Exit criteria: Phase 128 notes exist; README, AGENTS, task list, and
validation report point to them; focused soak serialization tests pass;
all-feature workspace coverage improves from Phase 127; normal gates remain
hermetic; and no live/external evidence surface is created.

## Benchmark OS Track: Phase 129 Proposal Validation Coverage

Status: complete for local evidence append proposal validation coverage
hardening. See `docs/129-phase-proposal-validation-coverage-notes.md`.

Goal: improve local line coverage over the hermetic evidence append proposal
validation surface without production API changes, runtime execution
broadening, live provider work, external replay, official submission, accepted
Evidence Ledger mutation, score-axis population, Level2+ evidence, or 100%
coverage claims.

Scope: focused tests under
`crates/zkbench-core/tests/evidence_append_proposal.rs`, plus phase notes and
navigation/status updates.

Implemented: rejection-path coverage for empty proposal identifiers, non-design
evidence class, Level2 claim boundary, accepted-evidence flag assertion, empty
artifact reference, unresolved blocking import issues, blocked claim-boundary
issue kinds, forbidden official-evidence text, forbidden formal-proof text,
and forbidden soundness-proof wording across proposal notes, provenance
summaries, review requirement notes, and review findings.

Anti-goals: production source changes, new APIs, generated artifacts, external
replay execution, official endpoint calls, credentials or secrets, accepted
Evidence Ledger mutation, official benchmark submission, live backend
execution, network access, command-line tools, UI dashboards, package runtime
additions, score-axis population, ZK backend performance claims, Level2+
evidence creation, formal evidence creation, SOTA claims, broad leaderboard
claims, production-readiness claims, semantic-correctness claims, or claiming
100% coverage.

Exit criteria: Phase 129 notes exist; README, AGENTS, task list, and
validation report point to them; focused evidence append proposal tests pass;
all-feature workspace coverage improves from Phase 128; normal gates remain
hermetic; and no live/external evidence surface is created.

## Benchmark OS Track: Phase 130 Phala Provider Coverage

Status: complete for local Phala operator-live provider-client coverage
hardening. See `docs/130-phase-phala-provider-coverage-notes.md`.

Goal: improve local line coverage over the opt-in Phala/dstack provider-client
fail-closed surface without production API changes, live Phala calls, operator
live tests, network requirements, credentials, generated operator artifacts,
official submission, accepted Evidence Ledger mutation, score-axis population,
Level2+ evidence, or 100% coverage claims.

Scope: focused tests under
`crates/hsai-attestation-phala/tests/phala_operator_live_provider_client.rs`,
plus phase notes and navigation/status updates.

Implemented: zero-timeout config rejection, unapproved credential-source
rejection before transport, HTTP `403` auth mapping, and non-UTF-8 bearer-token
rejection before network construction.

Anti-goals: production source changes, new APIs, live Phala calls, operator
live tests, network access, credentials or secrets, generated operator
artifacts, external replay execution, official endpoint calls, accepted
Evidence Ledger mutation, official benchmark submission, command-line tools,
UI dashboards, package runtime additions, score-axis population, ZK backend
performance claims, Level2+ evidence creation, formal evidence creation, SOTA
claims, broad leaderboard claims, production-readiness claims,
semantic-correctness claims, or claiming 100% coverage.

Exit criteria: Phase 130 notes exist; README, AGENTS, task list, and
validation report point to them; focused Phala provider-client tests pass;
all-feature workspace coverage improves from Phase 129; normal gates remain
hermetic; and no live/external evidence surface is created.

## Benchmark OS Track: Phase 131 Phala Artifact Coverage

Status: complete for local Phala captured-artifact validation coverage
hardening. See `docs/131-phase-phala-artifact-coverage-notes.md`.

Goal: improve local line coverage over the existing captured-artifact parser
and validator without production API changes, live Phala calls, operator live
tests, network requirements, credentials, generated operator artifacts,
official submission, accepted Evidence Ledger mutation, score-axis population,
Level2+ evidence, or 100% coverage claims.

Scope: focused tests under
`crates/hsai-attestation-phala/tests/phala_artifact.rs`, plus phase notes and
navigation/status updates.

Implemented: invalid JSON rejection, malformed quote hex rejection, invalid
case-hash length rejection, future observation rejection, untrusted
managed-verifier kind/status rejection, missing required event-log entry
rejection, mismatched event payload rejection, invalid Docker digest rejection,
and wrong RTMR event-index rejection.

Anti-goals: production source changes, new APIs, live Phala calls, operator
live tests, network access, credentials or secrets, generated operator
artifacts, external replay execution, official endpoint calls, accepted
Evidence Ledger mutation, official benchmark submission, command-line tools,
UI dashboards, package runtime additions, score-axis population, ZK backend
performance claims, Level2+ evidence creation, formal evidence creation, SOTA
claims, broad leaderboard claims, production-readiness claims,
semantic-correctness claims, or claiming 100% coverage.

Exit criteria: Phase 131 notes exist; README, AGENTS, task list, and
validation report point to them; focused Phala artifact validation tests pass;
all-feature workspace coverage improves from Phase 130; normal gates remain
hermetic; and no live/external evidence surface is created.

## Benchmark OS Track: Phase 132 Local JSON Adapter Coverage

Status: complete for local JSON adapter coverage hardening. See
`docs/132-phase-local-json-adapter-coverage-notes.md`.

Goal: improve local line coverage over the existing local JSON adapter without
production API changes, live external backend execution, external replay
execution, generated benchmark artifacts, official submission, accepted
Evidence Ledger mutation, score-axis population, Level2+ evidence, or 100%
coverage claims.

Scope: focused tests under `crates/zkbench-core/tests/local_json_adapter.rs`,
plus phase notes and navigation/status updates.

Implemented: claim-boundary rejection, adapter-id mismatch rejection, missing
generated subject payload rejection, missing mutated subject payload rejection,
selected-trace drift rejection, mock replay mode without a mock command
rejection, mock capability-gap and inconclusive status mapping, legacy
`BackendAdapter::prepare_replay` manifest behavior, and
`BackendAdapter::normalize_result` empty-evidence rejection.

Anti-goals: production source changes, new APIs, live external backend
execution, external replay execution, network access, credentials or secrets,
generated benchmark artifacts, official endpoint calls, accepted Evidence
Ledger mutation, official benchmark submission, command-line tools,
UI dashboards, package runtime additions, score-axis population, ZK backend
performance claims, Level2+ evidence creation, formal evidence creation, SOTA
claims, broad leaderboard claims, production-readiness claims,
semantic-correctness claims, or claiming 100% coverage.

Exit criteria: Phase 132 notes exist; README, AGENTS, task list, and
validation report point to them; focused local JSON adapter tests pass;
all-feature workspace coverage improves from Phase 131; normal gates remain
hermetic; and no live/external evidence surface is created.

## Benchmark OS Track: Phase 133 zk-Harness Export Coverage

Status: complete for local zk-Harness export helper coverage hardening. See
`docs/133-phase-zk-harness-export-coverage-notes.md`.

Goal: improve local line coverage over the existing zk-Harness dry-run export
helper surface without production API changes, zk-Harness execution, live
external backend execution, external replay execution, generated benchmark
artifacts, official submission, accepted Evidence Ledger mutation, score-axis
population, Level2+ evidence, or 100% coverage claims.

Scope: focused tests under
`crates/zkbench-core/tests/zk_harness_pack_mapping.rs`, plus phase notes and
navigation/status updates.

Implemented: direct pack export helper coverage, dry-run plan JSON
serialization/deserialization round-trip coverage, adapter manifest JSON
serialization/deserialization round-trip coverage, and malformed JSON
deserialization rejection for both helper families.

Anti-goals: production source changes, new APIs, zk-Harness execution, live
external backend execution, external replay execution, network access,
credentials or secrets, generated benchmark artifacts, official endpoint
calls, accepted Evidence Ledger mutation, official benchmark submission,
command-line tools, UI dashboards, package runtime additions, score-axis
population, ZK backend performance claims, Level2+ evidence creation, formal
evidence creation, SOTA claims, broad leaderboard claims, production-readiness
claims, semantic-correctness claims, or claiming 100% coverage.

Exit criteria: Phase 133 notes exist; README, AGENTS, task list, and
validation report point to them; focused zk-Harness pack mapping/export tests
pass; all-feature workspace coverage improves from Phase 132; normal gates
remain hermetic; and no live/external evidence surface is created.

## HSAI Track: Phase 134 PCSM-Governed Agent Admission Boundary

Status: complete for docs-first PCSM-governed agent-output admission boundary.
See `docs/134-pcsm-governed-agent-admission-boundary-spec.md`.

Goal: map the recoverable-ghost-states PCSM handoff into this repository as an
admission-governance boundary for Hyper Sacred AI without importing artifacts,
claiming PCSM evidence, changing Rust code, mutating accepted Evidence Ledgers,
or authorizing implementation.

Scope: Markdown boundary and navigation/status updates only. The boundary
defines the future pattern:

```text
untrusted agent/provider output
-> strict typed candidate
-> deterministic admission or rejection
-> accepted state mutation or rejected audit record
-> append-only admission journal
-> source digest binding
-> explicit nonclaims
```

Implemented: a docs-first boundary that maps PCSM admission governance across
HSAI L0 through L5, names the relationship to existing Phase W append rules,
defines future local hermetic surfaces, and records rejection behavior for
direct provider authority, stale tips, replayed candidates, claim-boundary
elevation, missing source digests, missing nonclaims, accepted-ledger bypass,
local-only Level2+ claims, and score-axis population.

Anti-goals: Rust source changes, tests, Cargo metadata changes, `Cargo.lock`
changes, PCSM runtime import or vendoring, recoverable-ghost artifact import,
accepted Evidence Ledger mutation, official benchmark submission, external
replay execution, live backend execution, network access, credentials or
secrets, generated benchmark artifacts, operator-live Phala calls, DCAP/PCCS/
JWKS/JWT/TLS implementation changes, command-line tools, UI dashboards,
package runtime additions, score-axis population, ZK backend performance
claims, Level2+ evidence creation, formal evidence creation, production
readiness claims, semantic-correctness claims, or global software-agent
uniqueness claims.

Exit criteria: Phase 134 boundary exists; README, AGENTS, task list,
assumption ledger, and validation report point to it; repo claim-boundary and
hygiene docs tests pass; normal gates remain hermetic; and no live/external
evidence surface is created.

## Benchmark OS Track: Phase 135 zk-Harness Validation Coverage

Status: complete for local zk-Harness dry-run validation coverage hardening.
See `docs/135-phase-zk-harness-validation-coverage-notes.md`.

Goal: improve local line coverage over the existing zk-Harness dry-run
validation surface without production API changes, zk-Harness execution, live
external backend execution, external replay execution, generated benchmark
artifacts, official submission, accepted Evidence Ledger mutation, score-axis
population, Level2+ evidence, or 100% coverage claims.

Scope: focused tests under
`crates/zkbench-core/tests/zk_harness_dry_run_plan.rs`, plus phase notes and
navigation/status updates.

Implemented: exact fail-closed validation issue-path assertions for empty plan
identifiers, unsupported-feature warnings, planned-only and observed metric
drift, dry-run/inert command drift, relative-path and shell-payload rejection,
artifact local-only and digest drift, family label drift, trace local-only
drift, and forbidden benchmark-evidence language.

Anti-goals: production source changes, new APIs, zk-Harness execution, live
external backend execution, external replay execution, network access,
credentials or secrets, generated benchmark artifacts, official endpoint
calls, accepted Evidence Ledger mutation, official benchmark submission,
command-line tools, UI dashboards, package runtime additions, score-axis
population, ZK backend performance claims, Level2+ evidence creation, formal
evidence creation, SOTA claims, broad leaderboard claims, production-readiness
claims, semantic-correctness claims, or claiming 100% coverage.

Exit criteria: Phase 135 notes exist; README, AGENTS, task list, and
validation report point to them; focused zk-Harness dry-run validation tests
pass; all-feature workspace coverage improves from Phase 134; normal gates
remain hermetic; and no live/external evidence surface is created.

## HSAI Track: Phase 136 Agent Admission Core

Status: complete for local PCSM-governed HSAI agent admission core. See
`docs/136-phase-hsai-agent-admission-core-notes.md`.

Goal: implement the smallest local Rust core that starts leveraging the Phase
134 PCSM-governed admission boundary: strict typed candidates, deterministic
policy admission or rejection, append-only audit journaling, source digest
binding, required nonclaims, and accepted claim-envelope handoff.

Scope: new standalone `crates/hsai-agent-admission` crate, workspace
membership, phase notes, and navigation/status updates only.

Implemented: `AgentAdmissionCandidate`, `AgentAdmissionPolicy`,
`AgentAdmissionDecision`, `AgentAdmissionJournalEntry`,
`AgentAdmissionJournal`, `evaluate_admission`, and
`accepted_claim_envelope`. The crate rejects raw untyped provider output,
provider direct-authority requests, claim-boundary elevation, missing source
digests, missing required nonclaims, accepted-ledger mutation requests,
score-axis population requests, and external/formal evidence claims in the
local path. The journal validates sequence numbers, previous-entry digests,
candidate digests, decision digests, and replayed candidate digests.

Anti-goals: recoverable-ghost runtime import or vendoring, recoverable-ghost
artifact import, provider calls, network access, credentials or secrets,
operator-live Phala calls, external replay execution, accepted Evidence Ledger
mutation, official benchmark submission, generated artifact writes,
score-axis population, DCAP/PCCS/JWKS/JWT/TLS implementation changes,
command-line tools, UI dashboards, package runtime additions, ZK backend
performance claims, Level2+ evidence creation, formal evidence creation,
production-readiness claims, semantic-correctness claims, proof claims,
benchmark-evidence claims, or global software-agent uniqueness claims.

Exit criteria: Phase 136 notes exist; README, AGENTS, task list, and
validation report point to them; `cargo test -p hsai-agent-admission` passes;
HSAI source scans pass; repo claim-boundary and hygiene docs tests pass; full
workspace tests pass; normal gates remain hermetic; and no live/external
evidence surface is created.

## HSAI Track: Phase 137 Admission E2E Harness

Status: complete for local admission-gated HSAI e2e harness coverage. See
`docs/137-phase-hsai-admission-e2e-harness-notes.md`.

Goal: start leveraging the Phase 136 admission core inside the existing
pure-data HSAI e2e harness before downstream registry, economy, or membrane
state is used.

Scope: `crates/hsai-e2e-harness` dependency wiring, focused harness tests,
phase notes, and navigation/status updates only.

Implemented: `hsai-e2e-harness` now depends on `hsai-agent-admission`. The
harness covers a closed attested claim-envelope proposal that passes local
admission and then reaches Phase 4 anchor registration, a rejected candidate
that appends auditable journal metadata but exports no accepted envelope, and a
raw provider-shaped candidate that is quarantined before registry or economy
use.

Anti-goals: recoverable-ghost runtime import or vendoring, recoverable-ghost
artifact import, provider calls, network access, credentials or secrets,
operator-live Phala calls, external replay execution, accepted Evidence Ledger
mutation, official benchmark submission, generated artifact writes,
score-axis population, DCAP/PCCS/JWKS/JWT/TLS implementation changes,
command-line tools, UI dashboards, package runtime additions, ZK backend
performance claims, Level2+ evidence creation, formal evidence creation,
production-readiness claims, semantic-correctness claims, proof claims,
benchmark-evidence claims, or global software-agent uniqueness claims.

Exit criteria: Phase 137 notes exist; README, AGENTS, task list, and
validation report point to them; `cargo test -p hsai-e2e-harness` passes;
`cargo test -p hsai-agent-admission` passes; HSAI source scans pass; repo
claim-boundary and hygiene docs tests pass; full workspace tests pass; normal
gates remain hermetic; and no live/external evidence surface is created.

## HSAI Track: Phase 138 Admission Journal Materialization Boundary

Status: complete for docs-first local admission-journal materialization
boundary. See
`docs/138-phase-hsai-admission-journal-materialization-boundary-spec.md`.

Goal: define the future local JSON output-root contract for a reviewable HSAI
admission journal bundle without promoting that trace into accepted evidence.

Scope: Markdown boundary, README, AGENTS, task list, and validation report
updates only.

Defined: declared `admission-journal/*` files, digest sidecars, manifest
fields, serialized journal validation rules, decision JSONL review-index
rules, source-digest disclosure, required non-claims, output-root safety,
replay and stale-tip checks, redaction-report requirements, rejected and
quarantined audit retention, and future implementation exit criteria.

Anti-goals: Rust source changes, tests, Cargo metadata changes, `Cargo.lock`
changes, filesystem materialization code, generated output files, committed
admission journal bundles, package runtime additions, command-line tools,
provider calls, network access, credentials or secrets, accepted Evidence
Ledger mutation, official benchmark submission, external replay execution,
live backend execution, score-axis population, DCAP/PCCS/JWKS/JWT/TLS
implementation changes, recoverable-ghost runtime import or vendoring, ZK
backend performance claims, Level2+ evidence creation, formal evidence
creation, production-readiness claims, semantic-correctness claims, proof
claims, benchmark-evidence claims, or global software-agent uniqueness claims.

Exit criteria: Phase 138 boundary spec exists; README, AGENTS, task list, and
validation report point to it; repo claim-boundary and hygiene docs tests pass;
normal workspace tests remain hermetic; and no live/external evidence surface
is created.

## HSAI Track: Phase 139 PCSM Bounded-Proof Handoff Intake Boundary

Status: complete for docs-first PCSM CL12 bounded-proof handoff intake
boundary. See
`docs/139-phase-pcsm-bounded-proof-handoff-intake-boundary-spec.md`.

Goal: define how a future phase may intake a committed, digest-stable
recoverable-ghost-states PCSM CL12 bounded-proof handoff as local admission
metadata without importing PCSM code, replaying PCSM runtime behavior, or
promoting the handoff into accepted benchmark evidence.

Scope: Markdown boundary, README, AGENTS, task list, and validation report
updates only.

Defined: required source repo identity, committed source revision, source
handoff path, handoff SHA-256 digest, verifier-status fields, bounded-proof
fields, blocked-preflight preservation, `threshold_admitted=false`
preservation, digest-only source artifact references, required nonclaims,
future HSAI admission mapping limits, rejection rules, and future
implementation exit criteria.

Anti-goals: Rust source changes, tests, Cargo metadata changes, `Cargo.lock`
changes, PCSM runtime import or vendoring, recoverable-ghost artifact import,
dirty or staged-only source snapshot intake, generated output files, committed
intake bundles, admission-journal materialization, package runtime additions,
command-line tools, provider calls, network access, credentials or secrets,
accepted Evidence Ledger mutation, official benchmark submission, external
replay execution, source repo command execution in normal gates, live backend
execution, score-axis population, DCAP/PCCS/JWKS/JWT/TLS implementation
changes, ZK backend performance claims, Level2+ evidence creation, formal
evidence creation, full breakthrough-threshold admission claims,
production-readiness claims, semantic-correctness claims, proof claims,
benchmark-evidence claims, or global software-agent uniqueness claims.

Exit criteria: Phase 139 boundary spec exists; README, AGENTS, task list, and
validation report point to it; repo claim-boundary and hygiene docs tests pass;
normal workspace tests remain hermetic; no PCSM code or recoverable-ghost
artifact is imported; and no live/external evidence surface is created.

## HSAI Track: Phase 140 PCSM Bounded-Proof Handoff Intake Metadata

Status: complete for local structured PCSM bounded-proof handoff intake
metadata validation. See
`docs/140-phase-pcsm-bounded-proof-handoff-intake-metadata-notes.md`.

Goal: implement the smallest local metadata validator authorized by Phase 139
without reading recoverable-ghost files, importing PCSM code, running source
repo commands, or promoting the handoff into accepted benchmark evidence.

Scope: `crates/hsai-agent-admission/src/lib.rs`, phase notes, and
navigation/status updates only.

Implemented: `PcsmBoundedProofHandoffIntake`, source repo status and verifier
status types, `PcsmHandoffIntakeError`, required nonclaim helpers, fail-closed
validation for committed clean source identity and bounded-proof fields, and
`pcsm_bounded_proof_handoff_candidate` mapping to
`AdmissionSourceKind::PcsmBoundedProofHandoff` with `LocalOnly` claim boundary
and no accepted claim envelope.

Anti-goals: filesystem parsing, source repo inspection, source repo command
execution, PCSM runtime import or vendoring, recoverable-ghost artifact import,
dirty or staged-only source snapshot intake, generated output files, committed
intake bundles, admission-journal materialization, package runtime additions,
command-line tools, provider calls, network access, credentials or secrets,
accepted Evidence Ledger mutation, official benchmark submission, external
replay execution, live backend execution, score-axis population,
DCAP/PCCS/JWKS/JWT/TLS implementation changes, ZK backend performance claims,
Level2+ evidence creation, formal evidence creation,
full breakthrough-threshold admission claims, production-readiness claims,
semantic-correctness claims, proof claims, benchmark-evidence claims, or global
software-agent uniqueness claims.

Exit criteria: Phase 140 notes exist; README, AGENTS, task list, and
validation report point to them; `cargo test -p hsai-agent-admission` passes;
HSAI source scans pass; repo claim-boundary and hygiene docs tests pass; full
workspace tests pass; normal gates remain hermetic; no PCSM code or
recoverable-ghost artifact is imported; and no live/external evidence surface
is created.

## HSAI Track: Phase 141 Admission Journal Materialization Implementation

Status: complete for local admission-journal output-root materialization. See
`docs/141-phase-hsai-admission-journal-materialization-implementation-notes.md`.

Goal: implement the Phase 138 local review-bundle contract so admitted,
rejected, and quarantined decisions can be materialized as digest-bound local
admission metadata without becoming accepted evidence.

Scope: `crates/hsai-agent-admission/src/lib.rs`, phase notes, and
navigation/status updates only.

Implemented: `AdmissionJournalMaterializationRequest`,
`AdmissionJournalBundleManifest`, review-row, source-digest, redaction-report,
validation-report, and materialization error types; required nonclaim helper;
`materialize_admission_journal_bundle`; and `read_admission_journal_bundle`.
The implementation writes only declared `admission-journal/*` files with
SHA-256 sidecars, validates readback, preserves rejected/quarantined decisions
as audit metadata, and rejects stale tips, invalid journals, protected roots,
symlink roots, undeclared files, stale digests, and missing nonclaims.

Anti-goals: PCSM runtime import or vendoring, recoverable-ghost artifact
import, recoverable-ghost file parsing, source repo command execution, provider
calls, network access, credentials or secrets, committed generated bundles,
package runtime additions, command-line tools, accepted Evidence Ledger
mutation, official benchmark submission, external replay execution, live
backend execution, score-axis population, DCAP/PCCS/JWKS/JWT/TLS
implementation changes, ZK backend performance claims, Level2+ evidence
creation, formal evidence creation, full breakthrough-threshold admission
claims, production-readiness claims, semantic-correctness claims, proof claims,
benchmark-evidence claims, or global software-agent uniqueness claims.

Exit criteria: Phase 141 notes exist; README, AGENTS, task list, and
validation report point to them; `cargo test -p hsai-agent-admission` passes;
HSAI source scans pass; repo claim-boundary and hygiene docs tests pass; full
workspace tests pass; normal gates remain hermetic; no committed generated
bundle is added; and no live/external evidence surface is created.

## HSAI Track: Phase 142 Admission Journal Semantic Readback Boundary

Status: complete for the docs-first local admission-journal semantic readback
boundary. See
`docs/142-phase-hsai-admission-journal-semantic-readback-boundary-spec.md`.

Goal: define the next local correctness boundary for independently parsing and
cross-validating every Phase 141 admission-journal bundle file so recomputed
sidecars cannot conceal semantic inconsistency.

Scope: Markdown boundary, README, AGENTS, task list, and validation report
updates only.

Defined: manifest, journal, decision-index, source-digest, nonclaim, redaction,
validation-report, and filesystem cross-checks; explicit semantic error
surfaces; sidecar-symlink rejection; digest-consistent tampering tests; one
future PCSM-intake-through-semantic-readback test; local-only claim limits;
source-checkout recheck; and future implementation exit criteria.

Current blocker: on 2026-06-23, the recoverable-ghost-states handoff remained
staged in a dirty checkout. Phase 142 therefore admits no current source commit
or handoff digest and authorizes no actual cross-repo intake.

Anti-goals: Rust source changes, tests, Cargo metadata changes, `Cargo.lock`
changes, recoverable-ghost file parsing or git inspection, source repo command
execution, PCSM runtime import or vendoring, recoverable-ghost artifact import,
provider calls, network access, credentials or secrets, committed generated
bundles, package runtime additions, command-line tools, accepted Evidence
Ledger mutation, official benchmark submission, external replay execution,
live backend execution, score-axis population, DCAP/PCCS/JWKS/JWT/TLS
implementation changes, ZK backend performance claims, Level2+ evidence
creation, formal evidence creation, full breakthrough-threshold admission
claims, production-readiness claims, semantic-correctness claims, proof claims,
benchmark-evidence claims, or global software-agent uniqueness claims.

Exit criteria: Phase 142 boundary exists; README, AGENTS, task list, and
validation report point to it; repo claim-boundary and hygiene docs tests pass;
normal workspace tests remain hermetic; no source checkout is parsed or
mutated; no generated bundle is committed; and no live/external evidence
surface is created.

## HSAI Track: Phase 143 Admission Journal Semantic Readback Implementation

Status: complete for local admission-journal semantic readback hardening. See
`docs/143-phase-hsai-admission-journal-semantic-readback-implementation-notes.md`.

Goal: close the Phase 142 integrity gap so recomputed sidecars cannot conceal
cross-file semantic inconsistency in a Phase 141 bundle.

Scope: `crates/hsai-agent-admission/src/lib.rs`, phase notes, and
navigation/status updates only.

Implemented: regular-file and sidecar-symlink checks; parsing of every declared
file; serialized journal validation; manifest count, tip, policy, declaration,
and content-digest recomputation; exact decision-row and source-index
recomputation; conflicting artifact-id rejection; canonical nonclaim matching;
strict redaction report validation; validation-report recomputation; and
explicit semantic-readback errors.

Regression coverage includes digest-consistent drift across the manifest,
journal, decisions, source digests, nonclaims, redaction report, and validation
report, plus sidecar symlinks and one complete hermetic PCSM metadata path
through semantic bundle readback.

Anti-goals: recoverable-ghost file parsing or git inspection, source repo
command execution, PCSM runtime import or vendoring, recoverable-ghost artifact
import, provider calls, network access, credentials or secrets, committed
generated bundles, package runtime additions, command-line tools, accepted
Evidence Ledger mutation, official benchmark submission, external replay
execution, live backend execution, score-axis population,
DCAP/PCCS/JWKS/JWT/TLS implementation changes, ZK backend performance claims,
Level2+ evidence creation, formal evidence creation, full
breakthrough-threshold admission claims, production-readiness claims,
semantic-correctness claims, proof claims, benchmark-evidence claims, or global
software-agent uniqueness claims.

Exit criteria: Phase 143 notes exist; README, AGENTS, task list, and validation
report point to them; focused admission tests pass; HSAI source scans pass;
repo claim-boundary and hygiene tests pass; full workspace tests, clippy, and
rustdoc pass; no source checkout is parsed; no generated bundle is committed;
and no live/external evidence surface is created.

## HSAI Track: Phase 144 Admission Journal Adversarial Invariant Boundary

Status: complete for the docs-first admission-decision and journal-readback
adversarial invariant boundary. See
`docs/144-phase-hsai-admission-journal-adversarial-invariant-boundary-spec.md`.

Goal: define fail-closed behavior for three remaining local gaps: envelopes
retained under rejected or quarantined verdicts, unknown JSON fields silently
discarded during readback, and symlinked output roots or bundle directories.

Scope: Markdown boundary, README, AGENTS, task list, and validation report
updates only.

Defined: the verdict-envelope invariant, strict recursive declared-file schema
requirements, root and bundle-directory symlink rejection, required future
errors and adversarial tests, compatible test-only coverage hardening, claim
limits, source-checkout recheck, and future implementation exit criteria.

Anti-goals: Rust source or test changes, Cargo metadata changes, generated
artifacts, recoverable-ghost file parsing or git inspection, source repo
commands, PCSM runtime import, provider calls, network access, credentials,
accepted Evidence Ledger mutation, official submission, external replay,
score-axis population, Level2+ evidence, proof, semantic correctness,
production readiness, global software-agent uniqueness, or 100% coverage.

Exit criteria: Phase 144 boundary exists; README, AGENTS, task list, and
validation report point to it; docs contract and hygiene gates pass; normal
tests remain hermetic; no source checkout is parsed; no generated bundle is
committed; and no stronger claim is created.

## HSAI Track: Phase 145 Admission Journal Adversarial Invariant Implementation

Status: complete for fail-closed admission-decision and journal-readback
hardening. See
`docs/145-phase-hsai-admission-journal-adversarial-invariant-implementation-notes.md`.

Goal: implement the Phase 144 verdict-envelope, strict JSON, and root-symlink
invariants while closing missing fail-closed test branches.

Scope: `crates/hsai-agent-admission/src/lib.rs`, phase notes, and
navigation/status updates only.

Implemented: verdict-aware envelope access; journal rejection for envelopes
under rejected or quarantined verdicts; pre-materialization rejection of
invalid journals; typed JSON value round-trip checks that reject recursively
unknown fields; output-root and bundle-directory type and symlink checks; and
expanded hermetic failure coverage.

Measured focused coverage: `96.80%` regions, `94.92%` functions, and `97.45%`
lines. These values are local coverage measurements, not 100% coverage.

Anti-goals: committed-source parsing, recoverable-ghost inspection or command
execution, PCSM runtime import, provider calls, network access, credentials,
committed generated bundles, package runtime additions, accepted Evidence
Ledger mutation, official submission, external replay, score-axis population,
Level2+ evidence, proof, semantic correctness, production readiness, global
software-agent uniqueness, or 100% coverage.

Exit criteria: Phase 145 notes exist; README, AGENTS, task list, and validation
report point to them; 27 focused tests pass; source scans, claim-boundary, and
hygiene tests pass; full workspace tests, clippy, rustdoc, and focused coverage
pass; no source checkout is parsed; no generated bundle is committed; and no
stronger claim is created.

## HSAI Track: Phase 146 Admission Provenance And Transaction Integrity Boundary

Status: complete for the docs-first admission provenance and output-root
transaction integrity boundary. See
`docs/146-phase-hsai-admission-provenance-transaction-integrity-boundary-spec.md`.

Goal: define fail-closed behavior for caller-forgeable decisions, unbound PCSM
intake metadata, and overwrite roots that are ancestors of protected paths.

Scope: Markdown boundary, README, AGENTS, task list, and validation report
updates only.

Defined: stored candidate and policy snapshots, deterministic decision
recomputation, explicit policy append inputs, reserved PCSM intake digest
binding, symmetric protected-root overlap rejection, required future tests,
deferred medium findings, source-checkout recheck, claim limits, and future
implementation exit criteria.

Anti-goals: Rust source or test changes, Cargo metadata changes, generated
artifacts, committed-source parsing, recoverable-ghost inspection or commands,
PCSM runtime import, provider calls, network access, credentials, accepted
Evidence Ledger mutation, official submission, external replay, score-axis
population, Level2+ evidence, proof, semantic correctness, production
readiness, global software-agent uniqueness, or 100% coverage.

Exit criteria: Phase 146 boundary exists; README, AGENTS, task list, and
validation report point to it; docs contract and hygiene gates pass; no source
checkout is parsed; no generated bundle is committed; and no stronger claim is
created.

## HSAI Track: Phase 147 Admission Provenance And Transaction Integrity Implementation

Status: complete for deterministic admission provenance and symmetric
protected-root safety. See
`docs/147-phase-hsai-admission-provenance-transaction-integrity-implementation-notes.md`.

Goal: implement the Phase 146 decision-recomputation, PCSM intake-binding, and
protected-root overlap invariants.

Scope: `crates/hsai-agent-admission/src/lib.rs`,
`crates/hsai-e2e-harness/src/lib.rs`, phase notes, and navigation/status updates
only.

Implemented: typed candidate and policy snapshots in journal entries;
policy-explicit append; exact deterministic decision recomputation during
append and journal validation; candidate, policy, source-digest, and decision
snapshot checks; reserved PCSM intake digest binding and collision rejection;
and symmetric protected-root overlap rejection before mutation.

Focused admission tests increased from 27 to 30. HSAI harness callers now
provide the evaluated policy explicitly.

Measured focused coverage: `97.19%` regions, `95.97%` functions, and `97.75%`
lines. These values are local coverage measurements, not 100% coverage.

Anti-goals: committed-source parsing, recoverable-ghost inspection or commands,
source-kind shape validation, general artifact validation, PCSM count/verifier
hardening, duplicate JSON key detection, failure-atomic overwrite, no-follow
descriptor access, PCSM runtime import, provider calls, network access,
credentials, committed generated bundles, accepted Evidence Ledger mutation,
official submission, external replay, score-axis population, Level2+ evidence,
proof, semantic correctness, production readiness, or global uniqueness.

Exit criteria: Phase 147 notes exist; README, AGENTS, task list, and validation
report point to them; 30 admission tests and 24 HSAI harness tests pass;
source-scan, claim-boundary, and hygiene tests pass; full workspace tests,
clippy, rustdoc, and focused coverage pass; no source checkout is parsed; no
generated bundle is committed; and no stronger claim is created.

## HSAI Track: Phase 148 Admission Input Semantic Integrity Boundary

Status: complete for docs-first authorization only. See
`docs/148-phase-hsai-admission-input-semantic-integrity-boundary-spec.md`.

Goal: define the next fail-closed local semantic validation contract for
admission candidate source shape, artifact identity, and PCSM intake
consistency.

Scope: Phase 148 boundary, README, AGENTS, task-list, and validation-report
navigation only.

Required future behavior: exact source-kind payload shapes; raw provider
non-admissibility; AgentCase subject agreement; portable nonempty artifact
IDs; nonzero SHA-256 values; one digest per logical ID; checked PCSM count
conservation; journal-entry count equality; and an exact duplicate-free
required verifier set whose outcomes all pass.

Anti-goals: Rust implementation in this phase, duplicate JSON key detection,
failure-atomic overwrite, descriptor-relative no-follow access, randomized
staging, committed-source parsing, recoverable-ghost inspection or commands,
PCSM runtime import, provider calls, network access, credentials, generated
bundles, accepted Evidence Ledger mutation, official submission, external
replay, score-axis population, Level2+ evidence, proof, semantic correctness,
production readiness, or global uniqueness.

Exit criteria: Phase 148 boundary exists; README, AGENTS, task list, and
validation report point to it; docs contract and hygiene gates pass; no Rust,
Cargo, fixture, package-runtime, generated-output, or source-checkout surface
changes; and no stronger claim is created.

## HSAI Track: Phase 149 Admission Input Semantic Integrity Implementation

Status: complete for deterministic local candidate and PCSM intake semantic
validation. See
`docs/149-phase-hsai-admission-input-semantic-integrity-implementation-notes.md`.

Goal: implement the Phase 148 source-shape, artifact, count, and verifier-set
invariants.

Scope: `crates/hsai-agent-admission/src/lib.rs`, Phase 149 notes, and
navigation/status updates only.

Implemented: exact source-kind case/envelope shape checks; AgentCase subject
agreement; raw provider non-admissibility; portable nonempty artifact IDs;
nonzero SHA-256 values; one digest per logical artifact ID; checked PCSM count
conservation; journal-entry count equality; and exact required verifier-name
validation with duplicate, unknown, missing, and failing status rejection.

Focused admission tests increased from 30 to 34. Measured focused coverage:
`97.20%` regions, `95.45%` functions, and `97.90%` lines. These values are
local coverage measurements, not 100% coverage.

Anti-goals: candidate identity broadening, exact claim-boundary coupling,
duplicate JSON or raw-array detection, failure-atomic overwrite,
descriptor-relative no-follow access, randomized staging, committed-source
parsing, recoverable-ghost inspection or commands, PCSM runtime import,
provider calls, network access, credentials, generated bundles, accepted
Evidence Ledger mutation, official submission, external replay, score-axis
population, Level2+ evidence, proof, semantic correctness, production
readiness, or global uniqueness.

Exit criteria: Phase 149 notes exist; README, AGENTS, task list, and validation
report point to them; 34 admission tests and 24 HSAI harness tests pass;
source-scan, claim-boundary, and hygiene tests pass; full workspace tests,
clippy, rustdoc, and focused coverage pass; no source checkout is parsed; no
generated bundle is committed; and no stronger claim is created.

## HSAI Track: Phase 150 Admission Candidate Semantic Closure Boundary

Status: complete for docs-first authorization only. See
`docs/150-phase-hsai-admission-candidate-semantic-closure-boundary-spec.md`.

Goal: define the final local candidate-model semantic checks before admission
journal parser or filesystem hardening.

Scope: Phase 150 boundary, README, AGENTS, task-list, and validation-report
navigation only.

Required future behavior: portable nonempty candidate IDs; nonempty trimmed
subjects; exact source-kind claim boundaries; envelope export only from
accepted `ClaimEnvelopeProposal` candidates; mandatory reserved PCSM intake
digest on PCSM candidates; and reserved-ID rejection on every non-PCSM source.

Anti-goals: Rust implementation in this phase, duplicate JSON or raw-array
detection, failure-atomic overwrite, descriptor-relative no-follow access,
randomized staging, committed-source parsing, recoverable-ghost inspection or
commands, PCSM runtime import, provider calls, network access, credentials,
generated bundles, accepted Evidence Ledger mutation, official submission,
external replay, score-axis population, Level2+ evidence, proof, semantic
correctness, production readiness, or global uniqueness.

Exit criteria: Phase 150 boundary exists; README, AGENTS, task list, and
validation report point to it; docs contract and hygiene gates pass; no Rust,
Cargo, fixture, package-runtime, generated-output, or source-checkout surface
changes; and no stronger claim is created.

## HSAI Track: Phase 151 Admission Candidate Semantic Closure Implementation

Status: complete for deterministic local candidate identity, source-boundary,
envelope-export, and reserved-digest validation. See
`docs/151-phase-hsai-admission-candidate-semantic-closure-implementation-notes.md`.

Goal: implement the Phase 150 candidate semantic closure.

Scope: `crates/hsai-agent-admission/src/lib.rs`,
`crates/hsai-e2e-harness/src/lib.rs`, Phase 150 corrections, Phase 151 notes,
and navigation/status updates only.

Implemented: portable nonempty candidate IDs; nonempty trimmed subjects; exact
source-kind claim boundaries; envelope creation only for accepted envelope
proposals; candidate-policy-decision authenticated envelope export; mandatory
reserved PCSM intake digest placement on PCSM candidates; and reserved-ID
rejection on non-PCSM candidates.

Focused admission tests increased from 34 to 36. Measured focused coverage:
`97.49%` regions, `95.62%` functions, and `98.09%` lines. These values are
local coverage measurements, not 100% coverage.

Anti-goals: arbitrary PCSM digest authentication, duplicate JSON or raw-array
detection, failure-atomic overwrite, descriptor-relative no-follow access,
randomized staging, committed-source parsing, recoverable-ghost inspection or
commands, PCSM runtime import, provider calls, network access, credentials,
generated bundles, accepted Evidence Ledger mutation, official submission,
external replay, score-axis population, Level2+ evidence, proof, semantic
correctness, production readiness, or global uniqueness.

Exit criteria: Phase 151 notes exist; README, AGENTS, task list, and validation
report point to them; 36 admission tests and 24 HSAI harness tests pass;
source-scan, claim-boundary, and hygiene tests pass; full workspace tests,
clippy, rustdoc, and focused coverage pass; no source checkout is parsed; no
generated bundle is committed; and no stronger claim is created.

## HSAI Track: Phase 152 Admission Journal Duplicate JSON Boundary

Status: complete for docs-first authorization only. See
`docs/152-phase-hsai-admission-journal-duplicate-json-boundary-spec.md`.

Goal: define recursive duplicate JSON object-key rejection before existing
typed canonical admission-journal readback.

Scope: Phase 152 boundary, README, AGENTS, task-list, and validation-report
navigation only.

Required future behavior: one complete JSON value; recursive duplicate
object-key rejection; nested array/object coverage; trailing-data rejection;
normal `serde_json::Value` preservation; integration before typed
deserialization; and existing malformed-file error mapping for every declared
JSON file and decision JSONL row.

Anti-goals: Rust implementation in this phase, repeated array-element
rejection, raw PCSM array parsing, failure-atomic overwrite,
descriptor-relative no-follow access, randomized staging, committed-source
parsing, recoverable-ghost inspection or commands, PCSM runtime import,
provider calls, network access, credentials, generated bundles, accepted
Evidence Ledger mutation, official submission, external replay, score-axis
population, Level2+ evidence, proof, semantic correctness, production
readiness, or global uniqueness.

Exit criteria: Phase 152 boundary exists; README, AGENTS, task list, and
validation report point to it; docs contract and hygiene gates pass; no Rust,
Cargo, fixture, package-runtime, generated-output, or source-checkout surface
changes; and no stronger claim is created.

## HSAI Track: Phase 153 Admission Journal Duplicate JSON Implementation

Status: complete. See
`docs/153-phase-hsai-admission-journal-duplicate-json-implementation-notes.md`.

Goal: reject recursive duplicate JSON object keys before typed canonical
admission-journal readback.

Scope: `hsai-agent-admission` parser hardening, adversarial tests, and
navigation/status docs only.

Implemented: `parse_json_value_rejecting_duplicate_keys`, integration inside
`parse_strict_json_bytes`, trailing-data rejection, existing malformed-file
error mapping, and adversarial coverage across every declared admission-journal
JSON document and decision JSONL row.

Anti-goals: Cargo metadata changes, dependencies, repeated array-element
rejection, raw PCSM array parsing, failure-atomic overwrite,
descriptor-relative no-follow access, randomized staging, committed-source
parsing, recoverable-ghost inspection or commands, PCSM runtime import,
provider calls, network access, credentials, generated bundles, accepted
Evidence Ledger mutation, official submission, external replay, score-axis
population, Level2+ evidence, proof, semantic correctness, production
readiness, or global uniqueness.

Exit criteria: duplicate keys fail closed before typed deserialization; valid
generated bundles still read successfully; 39 admission tests pass; docs and
hygiene gates pass; no committed bundle or stronger claim is created.

## Benchmark Track: Phase 154 New Benchmark Families

Status: complete. See
`docs/154-phase-new-benchmark-families-implementation-notes.md`.

Goal: unblock two future benchmark families (`NestedLoop` and
`GuardHeavyMachine`) as deterministic local generators over the existing
Surface DSL, Semantic IR, Oracle, and `Level1LocalReplay` claim boundary.

Scope: additive Rust source and tests under `crates/zkbench-core` plus
navigation/status docs only. State slice listed in
`docs/154-phase-new-benchmark-families-boundary-spec.md`.

Implemented: `build_nested_loop` (two stacked bounded loops, inner/outer
counters, two `LoopSpec` entries, one invariant, accepted/rejected traces),
`build_guard_heavy_machine` (acquire/release/advance/finish transitions
exercising `GuardExpr::And`/`GuardExpr::Or`, one `LoopSpec`, one invariant,
accepted/rejected traces), `FamilyKind::is_implemented` extension, family
template registry update, `GeneratorConfig::nested_loop` and
`GeneratorConfig::guard_heavy_machine` constructors, generator dispatch,
zk-Harness inert `candidate_family_label` extension, soak runner dispatch for
explicitly selected new families, and 10 Phase 154 tests covering generation,
oracle evaluation, registry state, determinism, local JSON replay, zk-Harness
dry-run labels, mutation applicability, and soak campaign behavior.

Anti-goals: Cargo metadata changes, dependencies, new DSL types, new mutation
passes, live zk-Harness execution, external repo clones, vendored source,
external result import, external replay, backend execution, benchmark outputs,
official submission, accepted Evidence Ledger mutation, score-axis population,
ZK backend performance claims, Level2+ evidence, formal evidence, proof,
semantic correctness, production readiness, global uniqueness, 100% coverage
claims, or implementation of `RecursiveEnvelope`, `MemoryHeavyStateMachine`,
`PublicPrivateBoundaryStress`, or `ZkMlControlFlowMixed`.

Exit criteria: both families generate, validate, lower, and evaluate with
matching oracle outcomes; `Level1LocalReplay` and local-fixture nonclaims are
preserved; zk-Harness labels are inert and surfaced through the dry-run plan;
soak campaigns stay `Level0DesignNote`; no stronger claim is created.

## Benchmark Track: Phase 155 Operator Soak Campaign Runner

Status: complete. See
`docs/155-phase-operator-soak-campaign-runner-implementation-notes.md`.

Goal: unblock the soak campaign runner by adding a single operator-facing
example binary that wraps the existing shipped `plan_soak_shards` and
`run_soak_campaign` library surface, so an operator can run an approved,
repo-external local soak campaign without writing Rust.

Scope: additive example and hermetic source-contract test under
`crates/zkbench-core/examples/` and `crates/zkbench-core/tests/` plus
navigation/status docs only. State slice listed in
`docs/155-phase-operator-soak-campaign-runner-boundary-spec.md`.

Implemented: `operator_soak_campaign` example reading a fixed authorized set
of environment variables (`ZKBENCH_SOAK_ACK`, `ZKBENCH_SOAK_CAMPAIGN_ID`,
`ZKBENCH_SOAK_ARTIFACT_ROOT`, `ZKBENCH_SOAK_APPROVED_BY`,
`ZKBENCH_SOAK_APPROVAL_STATEMENT`, and optional `ZKBENCH_SOAK_PROFILE`,
`ZKBENCH_SOAK_FAMILIES`, `ZKBENCH_SOAK_SEED_START`, `ZKBENCH_SOAK_SEED_END`,
`ZKBENCH_SOAK_SHARD_COUNT`); fixed acknowledgement gate; fail-closed input
validation; existing `SoakRunConfig::validate` and
`validate_soak_campaign_config` reuse; `plan_soak_shards` and
`run_soak_campaign` invocation; `Level0DesignNote` cap enforcement; non-secret
summary JSON output; and 9 hermetic source-contract tests over the example
bytes.

Anti-goals: Cargo metadata changes, `Cargo.lock` changes, dependencies, CLI
argument parsing, `std::env::args` inspection, `clap`, `structopt`, a shipped
`[[bin]]` target, installable command, package runtime file, new library API,
new soak profile, new claim boundary, change to existing soak semantics,
change to existing artifact layouts, change to existing validation, network
access, credential path, secret fixture, generated committed artifact,
accepted Evidence Ledger mutation, official benchmark submission, external
replay execution, live backend execution, score-axis population, ZK backend
performance claim, Level2+ evidence, formal evidence, proof, semantic
correctness, production readiness, global software-agent uniqueness, or 100%
coverage claim.

Exit criteria: example builds and runs end-to-end; fail-closed paths reject
bad ack, missing required inputs, non-absolute root, bad profile, and unknown
family; hermetic source-contract tests pass; no authorized surface is
exceeded; `Level0DesignNote` cap and required nonclaims are preserved; no
stronger claim is created.

## Benchmark Track: Phase 156 Mutation Engine Depth

Status: complete. See
`docs/156-phase-mutation-engine-depth-implementation-notes.md`.

Goal: advance the "adversarial mutation scoring" SOTA wedge by widening the
runnable mutation surface from 3 of 14 declared `MutationClass` variants to
8 of 14.

Scope: additive Rust source and tests under
`crates/zkbench-core/src/mutation/` and `crates/zkbench-core/tests/` plus
navigation/status docs only. State slice listed in
`docs/156-phase-mutation-engine-depth-boundary-spec.md`.

Implemented: five new deterministic `MutationPass` impls
(`InvariantWeakeningPass`, `InvariantStrengtheningPass`, `StaleStateReadsPass`,
`InvalidUnrollBoundsPass`, `ObservationOmissionPass`); five shared `pub(crate)`
helpers in `apply.rs` (`select_primary_trace`, `invariant_mut`, `loop_mut`,
`guard_read_fields`, `action_write_fields`, `guard_is_executable_expr`);
re-exports from `mutation/mod.rs`, `prelude.rs`, and `lib.rs`; preserved
`apply_default_mutations` (strict engine contract retained, new passes
individually runnable via `apply_mutation_pass` and composable via
`MutationEngine::with_pass`); and 11 focused tests in
`crates/zkbench-core/tests/phase_156_mutation_depth.rs` covering each new
pass's applies path, the no-eligible-target path, custom-engine determinism,
and a `MutationClass` scope guard.

Anti-goals: new `MutationClass`/`MutationKind`/`MutationSafetyClass`/
`ExpectedVerdict` variants, changes to `MutationPass`/`MutationBuild`/DSL/
oracle/scoring/evidence ledgers/accepted append/promotion preflight/
official-submission package/external replay preflight/zk-Harness mapping
beyond the existing future-class `None` branch, Cargo metadata changes,
`Cargo.lock` changes, dependencies, external execution, external repo clones,
vendored source, network access, credentials, command-line tools, UI
dashboards, browser apps, JavaScript or TypeScript runtime files, package
runtime files, committed generated benchmark artifact files, the remaining
six inert mutation classes, Level2+ evidence, formal evidence, accepted
Evidence Ledger mutation, official benchmark submission, score-axis
population, ZK backend performance claims, SOTA claims, broad leaderboard
claims, production readiness, semantic correctness, proof, benchmark evidence,
global software-agent uniqueness, or 100% coverage claims.

Exit criteria: all five new passes apply to eligible generated instances with
the documented `expected_verdict`, `safety_class`, non-empty affected ids, and
`ClaimBoundary::Level1LocalReplay`; no-eligible-target paths return
descriptive `ZkBenchError::mutation` errors; a custom engine composition over
the new passes is deterministic; `MutationClass` still has exactly 14
variants with no duplicates; workspace tests pass on default and
`external-runner` feature configurations.

## Benchmark Track: Phase 157 Mutation Distinguishability Scoring

Status: complete. See
`docs/157-phase-mutation-distinguishability-scoring-implementation-notes.md`.

Goal: advance the "adversarial mutation scoring" SOTA wedge by adding an
analytical lens over the widened mutation surface: a local distinguishability
matrix composing each mutation's declared `ExpectedVerdict` with each
`BackendOutcome` variant via the existing `classify_result`.

Scope: additive Rust source and tests under
`crates/zkbench-core/src/scoring/` and `crates/zkbench-core/tests/` plus
navigation/status docs only. State slice listed in
`docs/157-phase-mutation-distinguishability-scoring-boundary-spec.md`.

Implemented: `MutationDistinguishabilityAxis` (`TruePositive`,
`DetectedRejection`, `UnsoundAcceptanceCandidate`, `FalseRejectionCandidate`,
`Inconclusive`) with `axis_severity`; `MutationDistinguishabilityCell`;
`MutationDistinguishabilityMatrix`; `MutationDistinguishabilitySummary`;
`classify_mutation_distinguishability` (one cell per `BackendOutcome`
variant, deterministic and complete); `summarize_mutation_distinguishability`;
`mandatory_distinguishability_nonclaims`;
`DISTINGUISHABILITY_CLAIM_BOUNDARY` pinned at `Level1LocalReplay`; re-exports
from `scoring/mod.rs`, `prelude.rs`, and `lib.rs`; 11 focused tests in
`crates/zkbench-core/tests/phase_157_distinguishability.rs` covering every
verdict × outcome pairing, matrix completeness per mutation class, the four
interesting axis mappings, summary aggregation, mandatory nonclaims,
severity monotonicity, determinism, and an `ExpectedVerdict`/
`BackendOutcome`/`ResultClassification` scope guard.

Anti-goals: changes to `ExpectedVerdict`/`BackendOutcome`/
`ResultClassification`/`classify_result`/`ScoreReport`/
`LocalMutationEvidenceSummary`/any scoring constructor, changes to any
`MutationClass`/mutation pass/`MutationPass`/DSL/oracle, score-axis
population on `ScoreReport`, Cargo metadata changes, `Cargo.lock` changes,
dependencies, external execution, external repo clones, vendored source,
network access, credentials, command-line tools, UI dashboards, browser apps,
JavaScript or TypeScript runtime files, package runtime files, committed
generated benchmark artifact files, Level2+ evidence, formal evidence,
accepted Evidence Ledger mutation, official benchmark submission, ZK backend
performance claims, SOTA claims, broad leaderboard claims, production
readiness, semantic correctness, proof, benchmark evidence, global
software-agent uniqueness, or 100% coverage claims.

Exit criteria: matrix is complete and deterministic for every mutation
class; `UnsoundAcceptanceCandidate`/`DetectedRejection`/
`FalseRejectionCandidate`/`TruePositive` axes are reachable and correctly
derived from `classify_result`; summary aggregates counts correctly and
carries mandatory nonclaims; `axis_severity` is monotonic; workspace tests
pass.

## Benchmark Track: Phase 158 Oracle Completeness Audit

Status: complete. See
`docs/158-phase-oracle-completeness-audit-implementation-notes.md`.

Goal: advance the SOTA wedge by making the v0 oracle's completeness over the
generated surface auditable, so downstream mutation and formal phases can
reason about gaps honestly.

Scope: additive Rust source and tests under
`crates/zkbench-core/src/dsl/` and `crates/zkbench-core/tests/` plus
navigation/status docs only. State slice listed in
`docs/158-phase-oracle-completeness-audit-boundary-spec.md`.

Implemented: `OracleCompletenessLabel` (`Executable`,
`RawTextCapabilityGap`, `NonExecutableOperandCapabilityGap`,
`StructurallyIncapable`); `OracleCompletenessConstructKind`;
`OracleCompletenessConstruct`; `OracleCompletenessAudit`;
`audit_oracle_completeness` walking every transition guard, transition
action, invariant guard, and loop bound in declaration order and classifying
each via the existing `contains_raw_text` helpers plus a local integer-operand
check; re-exports from `dsl/mod.rs`, `prelude.rs`, and `lib.rs`; 6 focused
integration tests in `crates/zkbench-core/tests/phase_158_oracle_completeness.rs`
plus inline unit tests verifying shipped families are fully executable, count
consistency, determinism, and absence of structurally incapable constructs.

Anti-goals: changes to `evaluate_trace`/`OracleOutcome`/oracle logic/any
guard-action expression type/any DSL type, Cargo metadata changes,
`Cargo.lock` changes, dependencies, external execution, external repo clones,
vendored source, network access, credentials, command-line tools, UI
dashboards, browser apps, JavaScript or TypeScript runtime files, package
runtime files, committed generated benchmark artifact files, Level2+
evidence, formal evidence, accepted Evidence Ledger mutation, official
benchmark submission, score-axis population, ZK backend performance claims,
SOTA claims, broad leaderboard claims, production readiness, semantic
correctness, proof, benchmark evidence, global software-agent uniqueness, or
100% coverage claims.

Exit criteria: every shipped family audits as fully executable with zero
capability gaps; raw-text guards/actions and non-integer comparison operands
are flagged correctly; counts are self-consistent; audit is deterministic;
no shipped family produces a structurally incapable construct; workspace
tests pass.

## Benchmark Track: Phase 159 Formal Lane Interface Stub

Status: complete. See
`docs/159-phase-formal-lane-interface-stub-implementation-notes.md`.

Goal: advance the "formal hooks" half of the SOTA wedge by introducing the
inert formal-lane interface seam — a trait, a reference verifier that always
returns "declared only", and a `FormalLane` wrapper — without claiming
anything is proven.

Scope: additive Rust source under a new `crates/zkbench-core/src/formal/`
module and tests under `crates/zkbench-core/tests/` plus navigation/status
docs only. State slice listed in
`docs/159-phase-formal-lane-interface-stub-boundary-spec.md`.

Implemented: `FormalPropertyScope`; `FormalPropertyAssertion` with
`mandatory_nonclaims`; `FormalLaneProofStatus` with `claim_boundary` mapping;
`FormalLaneProof`; `FormalLaneError`; `FormalVerifier` trait mirroring
`hsai-attestation::AttestationVerifier`; `NoopFormalVerifier` always returning
`DeclaredOnly` and `Level0DesignNote`; `FormalLane<V>` wrapper with
`evaluate`; `FormalLaneOutcome`; `mandatory_lane_outcome_nonclaims`; module
declaration and re-exports from `lib.rs` and `prelude.rs`; 6 focused
integration tests in `crates/zkbench-core/tests/phase_159_formal_lane.rs`
plus inline unit tests verifying noop behavior, no escalation, malformed
input rejection, mandatory nonclaims, and scope-guard variant counts, plus a
source-scan test proving the module contains no forbidden formal-tool or
network/filesystem integrations.

Anti-goals: new Cargo dependencies, `Cargo.toml` changes, `Cargo.lock`
changes, integration with any real formal tool (clean, zkLean, Garden, Coq,
Lean, Rocq, F*, Dafny, etc.), reading or writing any formal proof artifact
file, a new crate, `hsai-formal`, any change to any HSAI crate, changes to
`ClaimEnvelope`/`EvidenceLane`/`AttestationVerifier`/`ScoreReport`/
`EvidenceRecord`/`EvidenceLedger`/accepted-ledger append/promotion preflight/
official-submission package/external replay preflight/any evidence
classification, Level2+ evidence, accepted Evidence Ledger mutation, official
benchmark submission, score-axis population, ZK backend performance claims,
SOTA claims, broad leaderboard claims, production readiness, semantic
correctness, proof, benchmark evidence, global software-agent uniqueness, or
100% coverage claims.

Exit criteria: `NoopFormalVerifier` returns `DeclaredOnly` and
`Level0DesignNote` for every scope and never escalates above `Level0`;
`FormalLane::evaluate` carries mandatory nonclaims; malformed assertions are
rejected; source-scan proves no forbidden integration exists; workspace
tests pass.

## Benchmark Track: Phase 160 Mutation × Formal Cross-Product Mapping

Status: complete. See
`docs/160-phase-mutation-formal-cross-product-implementation-notes.md`.

Goal: advance the SOTA wedge by connecting the mutation and formal halves —
mapping each of the 14 declared `MutationClass` variants to the
`FormalPropertyScope` it most directly stress-tests and deriving a
`FormalPropertyAssertion` template from an existing `SurfaceSpec`.

Scope: additive Rust source under `crates/zkbench-core/src/formal/cross_product.rs`
and tests under `crates/zkbench-core/tests/` plus navigation/status docs only.
State slice listed in
`docs/160-phase-mutation-formal-cross-product-boundary-spec.md`.

Implemented: `FormalPropertyScopeKind` (`TransitionGuard`, `Invariant`,
`LoopBound`, `Machine`, `NotApplicable`); `MutationFormalStressProfile`;
`mutation_class_formal_stress` returning a deterministic profile for each of
the 14 declared `MutationClass` variants; `derive_formal_property_assertion_template`
returning `Option<FormalPropertyAssertion>` over an existing `SurfaceSpec`;
`mandatory_cross_product_nonclaims`; `CROSS_PRODUCT_CLAIM_BOUNDARY` pinned at
`Level0DesignNote`; re-exports from `formal/mod.rs`, `lib.rs`, and
`prelude.rs`; 12 focused integration tests in
`crates/zkbench-core/tests/phase_160_cross_product.rs` plus inline unit tests
verifying profile coverage, scope mapping correctness, nonclaim presence,
template derivation `Some`/`None` paths, determinism, and scope-guard variant
counts.

Anti-goals: changes to `MutationClass`/`FormalPropertyAssertion`/
`FormalPropertyScope`/`FormalLaneProof`/`FormalLaneProofStatus`/
`FormalVerifier`/`NoopFormalVerifier`/`FormalLane`/`FormalLaneOutcome`/any
mutation pass/DSL/oracle/scoring outside the new formal-module additions,
Cargo metadata changes, `Cargo.lock` changes, dependencies, calling any real
formal tool, external execution, external repo clones, vendored source,
network access, credentials, command-line tools, UI dashboards, browser apps,
JavaScript or TypeScript runtime files, package runtime files, committed
generated benchmark artifact files, Level2+ evidence, accepted Evidence
Ledger mutation, official benchmark submission, score-axis population, ZK
backend performance claims, SOTA claims, broad leaderboard claims, production
readiness, semantic correctness, proof, benchmark evidence, global
software-agent uniqueness, or 100% coverage claims.

Exit criteria: every mutation class has a non-`NotApplicable` profile;
implemented classes map to the documented scopes; template derivation
returns `Some` when a matching construct exists and `None` otherwise;
profiles and templates carry "not proof" nonclaims; mapping is deterministic;
workspace tests pass.

## Benchmark Track: Phase 161 Mutation Engine Completion

Status: complete. See
`docs/161-phase-mutation-engine-completion-implementation-notes.md`.

Goal: complete the local mutation-engine dispatch surface for all 14 declared
`MutationClass` variants without changing the default three-pass engine.

Implemented: six additional deterministic `MutationPass` impls,
`apply_mutation_for_class`, soak-runner dispatch through that helper, and
focused tests covering each new pass plus all 14 dispatcher outputs.

Anti-goals: new mutation variants, default-engine broadening, score-axis
population, external execution, accepted Evidence Ledger mutation, official
benchmark submission, Level2+ evidence, proof, or backend-performance claims.

Exit criteria: every declared mutation class dispatches to a concrete pass
returning the same class on a known-applicable local fixture; every mutated
instance remains `Level1LocalReplay`; workspace tests pass.

## Benchmark Track: Phase 162 Distinguishability Soak Telemetry

Status: complete. See
`docs/162-phase-distinguishability-soak-telemetry-implementation-notes.md`.

Goal: carry internal distinguishability counters through soak telemetry without
populating official score axes.

Implemented: `observed_distinguishability_axis`, serde-default telemetry
counters, `record_distinguishability_axis`, soak-runner recording after
successful mutation replay, and focused counter/merge tests.

Anti-goals: `ScoreReport` axis population, benchmark evidence, external
execution, Level2+ evidence, production-readiness claims, or 100% coverage
claims.

Exit criteria: telemetry records expected accept/reject × backend outcome
axes, merge behavior remains deterministic, and telemetry stays internal-only.

## Benchmark Track: Phase 163 Formal Lane Pipeline Wiring

Status: complete. See
`docs/163-phase-formal-lane-pipeline-implementation-notes.md`.

Goal: run the declared-only formal-lane pipeline from local soak mutation
processing without invoking any real formal tool.

Implemented: `evaluate_formal_lane_pipeline`, `FormalLanePipelineOutcome`,
`pipeline_outcome_is_declared_only`, soak-runner invocation, and formal-lane
telemetry counters.

Anti-goals: real formal-tool integration, machine-checked proof claims,
accepted evidence, benchmark evidence, score-axis population, external
execution, Level2+ evidence, or claims above `Level0DesignNote` for the formal
pipeline.

Exit criteria: pipeline outputs remain declared-only, soak telemetry records
derived/evaluated/declared-only counts, and workspace tests pass.

## Benchmark Track: Phase 164 Remaining Benchmark Families

Status: complete. See
`docs/164-phase-remaining-benchmark-families-implementation-notes.md`.

Goal: implement the four remaining deterministic local generator families over
the existing Surface DSL while preserving `Level1LocalReplay`.

Implemented: `RecursiveEnvelope`, `MemoryHeavyStateMachine`,
`PublicPrivateBoundaryStress`, and `ZkMlControlFlowMixed` generators; registry,
template, config, soak, zk-Harness label, and full-pipeline updates; focused
tests for all nine implemented local families and derived resource-limit
validation.

Anti-goals: zkML execution, live ZK backend execution, new DSL types,
dependencies, score-axis population, accepted Evidence Ledger mutation,
official benchmark submission, Level2+ evidence, proof, semantic-correctness
claims, or 100% coverage claims.

Exit criteria: all nine families are implemented, generate/evaluate locally,
respect configured resource limits, carry `Level1LocalReplay`, and pass full
workspace validation.

## Benchmark Track: Phase 165 Formal Pipeline Observability Hardening

Status: complete. See
`docs/165-phase-formal-pipeline-observability-hardening-notes.md`.

Goal: make the declared-only formal-lane pipeline explainable in local soak
telemetry without changing claim strength.

Implemented: formal pipeline outcomes now carry `MutationClass`,
`FormalPropertyScopeKind`, optional `FormalLaneProofStatus`, no-template
reasons, and mandatory nonclaims; soak telemetry records no-template,
scope-count, and proof-status metrics; validation rejects impossible
formal-lane counter relationships and classification drift.

Anti-goals: real formal-tool integration, machine-checked proof claims, formal
evidence, accepted evidence, benchmark evidence, score-axis population,
external execution, Level2+ evidence, semantic-correctness claims, production
readiness, or 100% coverage claims.

Exit criteria: formal pipeline outcomes explain both derived and no-template
paths, telemetry remains internal-only, impossible formal-lane counters fail
closed, and focused workspace tests pass.

## Benchmark Track: Phase 166 Mutation Coverage First Tranche

Status: complete. See
`docs/166-phase-mutation-coverage-first-tranche-notes.md`.

Goal: start the path toward higher end-to-end coverage by hardening one bounded
local mutation module without changing runtime behavior or claim strength.

Implemented: focused regression tests for
`PublicPrivateBoundaryMismatchPass`, covering the class reporter,
public-input witness-policy movement, public-field reclassification,
observed-field reclassification, no-public-target failure, and no-declared
trace failure.

Coverage result: `public_private_boundary_mismatch.rs` moved from `50.00%`
line / `20.00%` function coverage to `100.00%` line / `100.00%` function
coverage, with one LLVM region still uncovered.

Anti-goals: runtime behavior changes, mutation semantics changes, evidence
promotion, benchmark evidence, external execution, Level2+ evidence,
semantic-correctness claims, production readiness, or whole-workspace 100%
coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches
complete line/function coverage, and root validation remains green.

## Benchmark Track: Phase 167 Mutation Coverage Second Tranche

Status: complete. See
`docs/167-phase-mutation-coverage-second-tranche-notes.md`.

Goal: continue the path toward higher end-to-end coverage by hardening the next
bounded local mutation module without changing runtime behavior or claim
strength.

Implemented: focused regression tests for `TraceOrderingCorruptionPass`,
covering the class reporter, deterministic first-two-step swapping, provenance
metadata, no-accepted-trace failure, and single-step-trace failure.

Coverage result: `trace_ordering_corruption.rs` moved from `69.44%` line /
`33.33%` function / `83.33%` region coverage to `100.00%` line / `100.00%`
function / `100.00%` region coverage.

Anti-goals: runtime behavior changes, mutation semantics changes, evidence
promotion, benchmark evidence, external execution, Level2+ evidence,
semantic-correctness claims, production readiness, or whole-workspace 100%
coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches
complete region/line/function coverage, and root validation remains green.

## Benchmark Track: Phase 168 Mutation Coverage Third Tranche

Status: complete. See
`docs/168-phase-mutation-coverage-third-tranche-notes.md`.

Goal: continue the path toward higher end-to-end coverage by hardening the next
bounded local mutation module without changing runtime behavior or claim
strength.

Implemented: focused regression tests for `WitnessAliasingPass`, covering the
class reporter, existing private-witness aliasing path, fallback field-derived
witness path, provenance metadata, no-declared-trace failure, and no-target
failure.

Coverage result: `witness_aliasing.rs` moved from `78.18%` line / `33.33%`
function / `81.25%` region coverage to `100.00%` line / `100.00%` function /
`100.00%` region coverage.

Anti-goals: runtime behavior changes, mutation semantics changes, evidence
promotion, benchmark evidence, external execution, Level2+ evidence,
semantic-correctness claims, production readiness, or whole-workspace 100%
coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches
complete region/line/function coverage, and root validation remains green.

## Benchmark Track: Phase 169 Mutation Coverage Fourth Tranche

Status: complete. See
`docs/169-phase-mutation-coverage-fourth-tranche-notes.md`.

Goal: continue the path toward higher end-to-end coverage by hardening the next
bounded local mutation module without changing runtime behavior or claim
strength.

Implemented: focused regression tests for
`NondeterministicTransitionInjectionPass`, covering the class reporter, injected
unconditional bypass transition shape, provenance metadata, no-declared-trace
failure, no-transition failure, and no-distinct-bypass-target failure.

Coverage result: `nondeterministic_transition_injection.rs` moved from
`76.92%` line / `42.86%` function / `78.87%` region coverage to `100.00%`
line / `100.00%` function / `100.00%` region coverage.

Anti-goals: runtime behavior changes, mutation semantics changes, evidence
promotion, benchmark evidence, external execution, Level2+ evidence,
semantic-correctness claims, production readiness, or whole-workspace 100%
coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches
complete region/line/function coverage, and root validation remains green.

## Benchmark Track: Phase 170 Mutation Coverage Fifth Tranche

Status: complete for local mutation coverage fifth tranche. See
`docs/170-phase-mutation-coverage-fifth-tranche-notes.md`.

Goal: continue the path toward higher end-to-end coverage by hardening the next
bounded low-coverage mutation module while preserving local claim boundaries.

Implemented: focused regression tests for `SemanticNoOpDriftPass`, covering
the class reporter, existing-noop replacement after an earlier non-noop action,
inserted drift assignment when no noop exists, no-declared-trace failure,
no-true-guarded-transition failure, and no-integer-field failure. The pass also
now carries the selected transition index through target selection to remove an
impossible fallible re-lookup edge without changing emitted provenance or
mutation semantics.

Coverage result: `semantic_no_op_drift.rs` moved from `73.56%` line /
`57.14%` function / `76.42%` region coverage to `100.00%` line / `100.00%`
function / `100.00%` region coverage.

Anti-goals: mutation semantics changes, evidence promotion, benchmark evidence,
external execution, Level2+ evidence, semantic-correctness claims, production
readiness, or whole-workspace 100% coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches
complete region/line/function coverage, and root validation remains green.

## Benchmark Track: Phase 171 Mutation Coverage Sixth Tranche

Status: complete for local mutation coverage sixth tranche. See
`docs/171-phase-mutation-coverage-sixth-tranche-notes.md`.

Goal: continue the path toward higher end-to-end coverage by hardening the next
bounded low-coverage mutation module while preserving local claim boundaries.

Implemented: focused regression tests for `CorruptedGuardsPass`, covering the
class reporter, guard-provenance metadata, no-accepted-trace failure, missing
trace-step transition skip behavior, and no-corruptible-guard failure. The pass
also now carries the selected transition index through target selection to
remove an impossible fallible re-lookup edge without changing emitted
provenance or mutation semantics.

Coverage result: `corrupted_guards.rs` moved from `80.39%` line / `33.33%`
function / `85.33%` region coverage to `100.00%` line / `100.00%` function /
`100.00%` region coverage.

Anti-goals: mutation semantics changes, evidence promotion, benchmark evidence,
external execution, Level2+ evidence, semantic-correctness claims, production
readiness, or whole-workspace 100% coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches
complete region/line/function coverage, and root validation remains green.

## Benchmark Track: Phase 172 External Handoff Coverage Seventh Tranche

Status: complete for local external handoff coverage seventh tranche. See
`docs/172-phase-external-handoff-coverage-seventh-tranche-notes.md`.

Goal: continue the path toward higher end-to-end coverage by hardening the
next bounded low-coverage local external-runner module while preserving manual
handoff claim boundaries.

Implemented: focused regression tests for the manual handoff validator,
covering bundle and subject shape rejection, step instruction drift rejection,
export shape rejection, nested provenance-contract and result-import-schema
issue forwarding, and false branches for manual-only step checks. The validator
also now uses the existing `ExternalExecutionMode::is_phase_h_allowed()`
predicate directly, removing a redundant live-mode disjunction without
changing manual handoff validation behavior.

Coverage result: `handoff.rs` moved from `65.64%` line / `100.00%` function /
`75.69%` region coverage to `100.00%` line / `100.00%` function / `100.00%`
region coverage.

Anti-goals: manual handoff semantics changes, evidence promotion, benchmark
evidence, external execution, Level2+ evidence, semantic-correctness claims,
production readiness, or whole-workspace 100% coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches
complete region/line/function coverage, and root validation remains green.

## Benchmark Track: Phase 173 External Quarantine Coverage Eighth Tranche

Status: complete for local external quarantine coverage eighth tranche. See
`docs/173-phase-external-quarantine-coverage-eighth-tranche-notes.md`.

Goal: continue the path toward higher end-to-end coverage by hardening the
next bounded low-coverage local external-runner quarantine module while
preserving claim boundaries.

Implemented: focused regression tests for external quarantine reason selection
and manifest validation, covering Level2+ boundary, official benchmark, formal
evidence, proof-system soundness, absolute-path, unsupported-metric,
unknown-source, and pending-review reason paths, plus manifest id, entry id,
source-artifact reference, and valid status-summary validation. The quarantine
reason selector now checks absolute-path issues before the generic
artifact-ref/unit bucket, returning `AbsolutePathRejected` for those failures.

Coverage result: `quarantine.rs` moved from `68.32%` line / `66.67%` function /
`72.48%` region coverage to `100.00%` line / `100.00%` function / `100.00%`
region coverage.

Anti-goals: quarantine semantics escalation, evidence promotion, benchmark
evidence, external execution, Level2+ evidence, semantic-correctness claims,
production readiness, or whole-workspace 100% coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches
complete region/line/function coverage, and root validation remains green.

## Benchmark Track: Phase 174 External Synthetic Coverage Ninth Tranche

Status: complete for local external synthetic coverage ninth tranche. See
`docs/174-phase-external-synthetic-coverage-ninth-tranche-notes.md`.

Goal: continue the path toward higher end-to-end coverage by hardening the
next bounded low-coverage local external-runner synthetic quarantine helper
while preserving claim boundaries.

Implemented: focused regression tests for synthetic quarantine reason
selection, covering claim-boundary, official benchmark, formal evidence,
proof-system soundness, digest mismatch, invalid digest, provenance, metric,
pending-review fallback, and multiple-issue priority paths. No production code
changed in this tranche.

Coverage result: `synthetic.rs` moved from `69.05%` line / `72.73%` function /
`69.88%` region coverage to `100.00%` line / `100.00%` function / `100.00%`
region coverage.

Anti-goals: synthetic quarantine semantics changes, evidence promotion,
benchmark evidence, external execution, Level2+ evidence, semantic-correctness
claims, production readiness, or whole-workspace 100% coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches
complete region/line/function coverage, and root validation remains green.

## Benchmark Track: Phase 175 Acceptance Policy Coverage Tenth Tranche

Status: complete for local evidence acceptance policy coverage tenth tranche.
See `docs/175-phase-acceptance-policy-coverage-tenth-tranche-notes.md`.

Goal: continue the path toward higher end-to-end coverage by hardening the
next bounded low-coverage local evidence policy module while preserving claim
boundaries.

Implemented: focused regression tests for policy JSON round trip, malformed
JSON error mapping, the default policy path, static policy rejection, proposal
mode rule-result rejection, source proposal rejection paths, changes-requested
review state, invalid review decisions, automated review rejection, and
official/formal/soundness text rejection. No production code changed in this
tranche.

Coverage result: `acceptance_policy.rs` moved from `69.23%` line / `73.68%`
function / `73.61%` region coverage to `98.82%` line / `94.74%` function /
`98.26%` region coverage. The remaining uncovered target-file branch is the
impossible `serde_json::to_string_pretty` serialization-error closure for a
structurally serializable policy type.

Anti-goals: policy semantics changes, evidence promotion, benchmark evidence,
external execution, Level2+ evidence, semantic-correctness claims, production
readiness, unsafe coverage forcing, coverage suppression, or whole-workspace
100% coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Benchmark Track: Phase 176 Evidence Candidate Coverage Eleventh Tranche

Status: complete for local evidence-record candidate coverage eleventh tranche.
See `docs/176-phase-evidence-candidate-coverage-eleventh-tranche-notes.md`.

Goal: continue the path toward higher end-to-end coverage by hardening the
next bounded low-coverage local evidence candidate module while preserving
claim boundaries.

Implemented: focused regression tests for candidate-only design-note creation,
invalid policy rejection, non-candidate policy mode rejection, rejected and
superseded candidate status behavior, malformed candidate JSON error mapping,
acceptance-validation failure, Level2+ boundary rejection, individual claim
flags, disallowed evidence classes, missing local metadata, missing artifact
digest, invalid acceptance validation, forbidden claim text, and missing
provenance. No production code changed in this tranche.

Coverage result: `candidate.rs` moved from `69.92%` line / `78.57%` function /
`76.33%` region coverage to `93.50%` line / `92.86%` function / `96.14%`
region coverage. The remaining uncovered target-file spans are defensive or
unreachable through the public constructor and validator.

Anti-goals: candidate semantics changes, evidence promotion, benchmark
evidence, external execution, Level2+ evidence, semantic-correctness claims,
production readiness, unsafe coverage forcing, coverage suppression, or
whole-workspace 100% coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Benchmark Track: Phase 177 Promotion Preflight Coverage Twelfth Tranche

Status: complete for local reviewed promotion preflight coverage twelfth
tranche. See
`docs/177-phase-promotion-preflight-coverage-twelfth-tranche-notes.md`.

Goal: continue the path toward higher end-to-end coverage by hardening the
next bounded low-coverage local promotion preflight module while preserving
claim boundaries.

Implemented: focused regression tests for reviewed-promotion preflight shape,
candidate, append-preview, review-decision, digest, marker, nonclaim,
score-axis, forbidden-text, Markdown, and malformed-JSON rejection paths, plus
official-submission package shape, digest, nonclaim, forbidden-text, Markdown,
and malformed-JSON rejection paths. No production code changed in this tranche.

Coverage result: `promotion_preflight.rs` moved from `70.49%` line / `88.57%`
function / `81.35%` region coverage to `98.62%` line / `94.29%` function /
`98.05%` region coverage. The remaining uncovered target-file spans are
serialization-error closures for structurally serializable metadata structs and
a narrow already-covered external-provenance scanner loop edge.

Anti-goals: promotion semantics changes, evidence promotion, benchmark
evidence, external execution, Level2+ evidence, semantic-correctness claims,
production readiness, unsafe coverage forcing, coverage suppression, or
whole-workspace 100% coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Benchmark Track: Phase 178 Proposal Ledger Coverage Thirteenth Tranche

Status: complete for local evidence append proposal ledger coverage thirteenth
tranche. See
`docs/178-phase-proposal-ledger-coverage-thirteenth-tranche-notes.md`.

Goal: continue the path toward higher end-to-end coverage by hardening the
next bounded low-coverage local proposal ledger module while preserving claim
boundaries.

Implemented: focused regression tests for default construction, multi-entry
append chaining, previous-digest linkage, sequence drift, previous-digest drift,
stored-entry proposal-validation forwarding, future-append proposal state
mismatch, entry-digest mismatch, save-to-directory failure, missing-file load
failure, and malformed JSON load failure. No production code changed in this
tranche.

Coverage result: `proposal_ledger.rs` moved from `71.50%` line / `62.50%`
function / `76.50%` region coverage to `92.27%` line / `93.75%` function /
`93.59%` region coverage. The remaining uncovered target-file spans are
defensive or unreachable through normal public construction.

Anti-goals: proposal-ledger semantics changes, evidence promotion, benchmark
evidence, external execution, Level2+ evidence, semantic-correctness claims,
production readiness, unsafe coverage forcing, coverage suppression, or
whole-workspace 100% coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Benchmark Track: Phase 179 zkML Coverage Fourteenth Tranche

Status: complete for local inert zkML workload manifest coverage fourteenth
tranche. See `docs/179-phase-zkml-coverage-fourteenth-tranche-notes.md`.

Goal: continue the path toward higher end-to-end coverage by hardening the next
bounded low-coverage local `zkml.rs` validation module while preserving claim
boundaries.

Implemented: focused regression tests for default manifest version, metric
executable-adapter classification, top-level shape rejection, input/model
artifact identity/ref/digest/boundary rejection paths, output and metric
boundary rejection paths, executable-adapter authorization rejection, missing
limitation rejection, and malformed JSON error context. No production code
changed in this tranche.

Coverage result: `zkml.rs` moved from `71.68%` line / `87.50%` function /
`82.42%` region coverage to `98.53%` line / `93.75%` function / `97.80%`
region coverage. The remaining counted target-file spans are defensive
digest-root compute and serialization-error branches that are not reachable
through ordinary valid public construction without changing semantics.

Anti-goals: zkML execution, zkML adapter implementation, zkML semantics changes,
evidence promotion, benchmark evidence, external execution, Level2+ evidence,
semantic-correctness claims, production readiness, unsafe coverage forcing,
coverage suppression, or whole-workspace 100% coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Benchmark Track: Phase 180 External Submission Preflight Coverage Fifteenth Tranche

Status: complete for local external submission preflight coverage fifteenth
tranche. See
`docs/180-phase-external-submission-preflight-coverage-fifteenth-tranche-notes.md`.

Goal: continue the path toward higher end-to-end coverage by hardening the next
bounded low-coverage local external replay / official-submission preflight
validation module while preserving claim boundaries.

Implemented: focused regression tests for aggregate request-shape rejection,
accepted-ledger path rejection, future output-root safety rejection,
digest-consistent package validation-report drift, malformed report JSON error
context, and Markdown nonclaim fail-closed behavior. No production code changed
in this tranche.

Coverage result: `external_submission_preflight.rs` moved from `72.63%` line /
`85.00%` function / `76.70%` region coverage to `89.02%` line / `90.00%`
function / `88.50%` region coverage. The next package coverage floor is
`soak/shard.rs` at `73.55%` line coverage.

Anti-goals: preflight semantics changes, production source changes, external
execution, endpoint calls, credential handling, official submission, generated
artifact materialization, accepted Evidence Ledger mutation, benchmark
evidence, score-axis population, Level2+ evidence, semantic-correctness claims,
production readiness, unsafe coverage forcing, coverage suppression, or
whole-workspace 100% coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Benchmark Track: Phase 181 Soak Shard Coverage Sixteenth Tranche

Status: complete for local soak shard coverage sixteenth tranche. See
`docs/181-phase-soak-shard-coverage-sixteenth-tranche-notes.md`.

Goal: continue the path toward higher end-to-end coverage by hardening the next
bounded low-coverage local soak shard planning and validation module while
preserving claim boundaries.

Implemented: focused regression tests for public shard progress/id/resume-token
and planner helpers, max-cases-per-shard overflow, shard-plan drift,
shard-manifest shape/boundary/path rejection, and shard-summary
boundary/progress/status validation. No production code changed in this
tranche.

Coverage result: `soak/shard.rs` moved from `73.55%` line / `75.00%` function /
`84.88%` region coverage to `98.91%` line / `100.00%` function / `97.94%`
region coverage. The next package coverage floor is `evidence/eligibility.rs`
at `73.75%` line coverage.

Anti-goals: soak semantics changes, production source changes, external
execution, generated artifact materialization, accepted Evidence Ledger
mutation, benchmark evidence, score-axis population, Level2+ evidence,
semantic-correctness claims, production readiness, unsafe coverage forcing,
coverage suppression, or whole-workspace 100% coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Benchmark Track: Phase 182 Evidence Eligibility Coverage Seventeenth Tranche

Status: complete for local evidence eligibility coverage seventeenth tranche.
See `docs/182-phase-evidence-eligibility-coverage-seventeenth-tranche-notes.md`.

Goal: continue the path toward higher end-to-end coverage by hardening the next
bounded low-coverage local Level2 eligibility review-metadata checker while
preserving claim boundaries.

Implemented: focused regression tests for required external-artifact-capture
and replay-manifest marker paths, invalid candidate blocking and finding
metadata, missing artifact/provenance reasons, forbidden official/formal/
soundness claim flags, Level2 boundary blocking, malformed eligibility report
JSON context, and no-evidence-creation checks. No production code changed in
this tranche.

Coverage result: `evidence/eligibility.rs` moved from `73.75%` line / `78.57%`
function / `72.94%` region coverage to `96.25%` line / `92.86%` function /
`95.88%` region coverage. The next package coverage floor is
`local_benchmark_artifact.rs` at `74.42%` line coverage.

Anti-goals: eligibility semantics changes, production source changes, external
execution, generated artifact materialization, accepted Evidence Ledger
mutation, benchmark evidence, score-axis population, Level2+ evidence,
semantic-correctness claims, production readiness, unsafe coverage forcing,
coverage suppression, or whole-workspace 100% coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Benchmark Track: Phase 183 Local Benchmark Artifact Coverage Eighteenth Tranche

Status: complete for local benchmark artifact coverage eighteenth tranche. See
`docs/183-phase-local-benchmark-artifact-coverage-eighteenth-tranche-notes.md`.

Goal: continue the path toward higher end-to-end coverage by hardening the
next bounded low-coverage Phase U local benchmark artifact packaging surface
while preserving claim boundaries.

Implemented: focused regression tests for manifest identity and duplicate
rejection, missing input and benchmark-pack requirements, invalid digest and
claim-boundary rejection, portable artifact URI rejection, invalid
render/deserialize paths, output-root file rejection, matching overwrite
idempotence, digest sidecar UTF-8 rejection, digest drift, and non-UTF-8
Markdown rejection. No production code changed in this tranche.

Coverage result: `local_benchmark_artifact.rs` moved from `74.42%` line /
`62.00%` function / `76.62%` region coverage to `90.08%` line / `70.00%`
function / `84.20%` region coverage. The next package coverage floor is
`evidence/accepted_append_output.rs` at `74.55%` line coverage.

Anti-goals: artifact semantics changes, production source changes, external
execution, generated artifact materialization, accepted Evidence Ledger
mutation, benchmark evidence, score-axis population, Level2+ evidence,
semantic-correctness claims, production readiness, unsafe coverage forcing,
coverage suppression, or whole-workspace 100% coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Benchmark Track: Phase 184 Accepted Append Output Coverage Nineteenth Tranche

Status: complete for accepted append output coverage nineteenth tranche. See
`docs/184-phase-accepted-append-output-coverage-nineteenth-tranche-notes.md`.

Goal: continue the path toward higher end-to-end coverage by hardening the
next bounded low-coverage Phase W materialized accepted-ledger append output
surface while preserving claim boundaries.

Implemented: focused regression tests for empty materialized ledger path
rejection, bare relative ledger path rejection before repository-root writes,
parseable invalid existing ledger rejection without repair, stale temporary
file replacement during atomic JSON write, Unix symlink parent-directory
rejection, and local JSON-only atomic-write source-boundary checks. No
production code changed in this tranche.

Coverage result: `evidence/accepted_append_output.rs` moved from `74.55%` line
/ `57.14%` function / `74.34%` region coverage to `86.36%` line / `57.14%`
function / `78.95%` region coverage. The next package coverage floor is
`replay/serialization.rs` at `75.00%` line coverage.

Anti-goals: accepted-ledger append semantics changes, production source
changes, external execution, generated artifact materialization, accepted
Evidence Ledger policy changes, benchmark evidence, score-axis population,
Level2+ evidence, semantic-correctness claims, production readiness, unsafe
coverage forcing, coverage suppression, or whole-workspace 100% coverage
claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Benchmark Track: Phase 185 Mutation Apply Coverage Twentieth Tranche

Status: complete for mutation apply coverage twentieth tranche. See
`docs/185-phase-mutation-apply-coverage-twentieth-tranche-notes.md`.

Goal: continue the path toward higher end-to-end coverage by hardening the
next reachable low-coverage mutation-application surface while preserving claim
boundaries.

Implemented: focused regression tests for default Phase D/E mutation bundle
execution, public primary-trace evaluation, bad-counter mutation handling for
`add_assign` integer operands other than `1`, and bad-counter mutation handling
for `sub_assign` integer updates. No production code changed in this tranche.

Coverage result: `mutation/apply.rs` moved from `75.37%` line / `82.76%`
function / `76.59%` region coverage to `89.93%` line / `89.66%` function /
`87.29%` region coverage. The package floor remains
`replay/serialization.rs` at `75.00%` line coverage because its remaining
uncovered lines are structurally unreachable `serde_json::to_string_pretty`
error mappings for concrete derived replay structs.

Anti-goals: mutation semantics changes, production source changes, external
execution, generated artifact materialization, accepted Evidence Ledger policy
changes, benchmark evidence, score-axis population, Level2+ evidence,
semantic-correctness claims, production readiness, unsafe coverage forcing,
coverage suppression, structurally unreachable serialization-error forcing, or
whole-workspace 100% coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Benchmark Track: Phase 186 Official Submission Output Coverage Twenty-First Tranche

Status: complete for official submission output coverage twenty-first tranche.
See
`docs/186-phase-official-submission-output-coverage-twenty-first-tranche-notes.md`.

Goal: continue the path toward higher end-to-end coverage by hardening the
next reachable low-coverage official-submission package output surface while
preserving claim boundaries.

Implemented: focused regression tests for output-root shape preconditions,
accepted-ledger path rejection, parseable invalid accepted-ledger rejection,
digest-consistent package Markdown and validation-report drift, non-UTF-8
declared-file rejection, missing declared-file rejection, and symlink rejection.
No production code changed in this tranche.

Coverage result: `evidence/official_submission_output.rs` moved from `76.29%`
line / `61.36%` function / `75.56%` region coverage to `87.45%` line /
`70.45%` function / `82.12%` region coverage. The package floor remains
`replay/serialization.rs` at `75.00%` line coverage because its remaining
uncovered lines are structurally unreachable `serde_json::to_string_pretty`
error mappings for concrete derived replay structs.

Anti-goals: official-submission package semantics changes, production source
changes, external execution, generated artifact materialization, accepted
Evidence Ledger policy changes, benchmark evidence, score-axis population,
Level2+ evidence, semantic-correctness claims, production readiness, unsafe
coverage forcing, coverage suppression, structurally unreachable
serialization-error forcing, or whole-workspace 100% coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Benchmark Track: Phase 187 Scoring Coverage Twenty-Second Tranche

Status: complete for scoring coverage twenty-second tranche. See
`docs/187-phase-scoring-coverage-twenty-second-tranche-notes.md`.

Goal: continue the path toward higher end-to-end coverage by hardening the
next reachable low-coverage score-report validation surface while preserving
claim boundaries.

Implemented: focused regression tests for higher-boundary confidence mapping,
safe higher-boundary axis validation, local populated-axis rejection across all
axes, invalid axis value rejection, forbidden axis-note text rejection, and
`CapabilityGap` risk-penalty text validation. No production code changed in
this tranche.

Coverage result: `scoring/mod.rs` moved from `76.60%` line / `100.00%`
function / `76.86%` region coverage to `100.00%` line / `100.00%` function /
`100.00%` region coverage. The package floor remains `replay/serialization.rs`
at `75.00%` line coverage because its remaining uncovered lines are
structurally unreachable `serde_json::to_string_pretty` error mappings for
concrete derived replay structs.

Anti-goals: scoring semantics changes, production source changes, external
execution, generated artifact materialization, accepted Evidence Ledger policy
changes, benchmark evidence, real score-axis population, Level2+ evidence,
semantic-correctness claims, production readiness, unsafe coverage forcing,
coverage suppression, structurally unreachable serialization-error forcing, or
whole-workspace 100% coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Benchmark Track: Phase 188 Soak Reproduction Coverage Twenty-Third Tranche

Status: complete for soak reproduction coverage twenty-third tranche. See
`docs/188-phase-soak-reproduction-coverage-twenty-third-tranche-notes.md`.

Goal: continue the path toward higher end-to-end coverage by hardening the
next reachable low-coverage soak reproduction-bundle validation surface while
preserving claim boundaries.

Implemented: focused regression tests for reproduction-bundle claim-boundary
elevation rejection, empty entry-id rejection, entry and reproduction-manifest
claim-boundary elevation rejection, post-sidecar pack validation failure
reporting after declared pack-file digest drift, and malformed reproduction
sidecar JSON readback rejection. No production code changed in this tranche.

Coverage result: `soak/reproduction.rs` moved from `76.64%` line / `60.00%`
function / `82.64%` region coverage to `97.20%` line / `80.00%` function /
`89.26%` region coverage. The package floor remains `replay/serialization.rs`
at `75.00%` line coverage because its remaining uncovered lines are
structurally unreachable `serde_json::to_string_pretty` error mappings for
concrete derived replay structs. The next reachable `zkbench-core` floor is
`external_runner/serialization.rs` at `76.65%` line coverage.

Anti-goals: soak reproduction semantics changes, production source changes,
external execution, generated artifact materialization, accepted Evidence
Ledger policy changes, benchmark evidence, real score-axis population, Level2+
evidence, semantic-correctness claims, production readiness, unsafe coverage
forcing, coverage suppression, structurally unreachable serialization-error
forcing, or whole-workspace 100% coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Phase 189 External Runner Importer Coverage Twenty-Fourth Tranche

Status: complete. See
`docs/189-phase-external-runner-importer-coverage-twenty-fourth-tranche-notes.md`.

Goal: continue the bounded local coverage campaign by targeting the next
reachable `zkbench-core` floor after confirming the serializer-wrapper floors
are capped by structurally unreachable `serde_json::to_string_pretty` error
mappings.

Implemented: focused regression tests for relative-file resolver success,
traversal rejection, missing file error mapping, malformed importer JSON
context, explicit config/source quarantine preservation, invalid capture
contract forwarding, resolver digest algorithm rejection, resolver-byte drift,
missing candidate digest rejection, metric parse failure, metric source path
rejection, and nested official/formal/soundness claim-text scans. No production
code changed in this tranche.

Coverage result: `external_runner/importer.rs` moved from `77.00%` line /
`81.82%` function / `77.34%` region coverage to `92.84%` line / `93.18%`
function / `93.11%` region coverage. The package floor remains
`replay/serialization.rs` at `75.00%` line coverage, and the next visible floor
is `external_runner/serialization.rs` at `76.65%` line coverage; both are
serializer-wrapper files capped by structurally unreachable concrete-type
serialization error mappings. The next reachable `zkbench-core` floor is
`generator/instance.rs` at `77.27%` line coverage.

Anti-goals: importer semantics changes, production source changes, external
execution, generated artifact materialization, accepted Evidence Ledger policy
changes, benchmark evidence, real score-axis population, Level2+ evidence,
semantic-correctness claims, production readiness, unsafe coverage forcing,
coverage suppression, structurally unreachable serialization-error forcing, or
whole-workspace 100% coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Phase 190 Generator Instance Coverage Twenty-Fifth Tranche

Status: complete. See
`docs/190-phase-generator-instance-coverage-twenty-fifth-tranche-notes.md`.

Goal: continue the bounded local coverage campaign by targeting the next
reachable `zkbench-core` floor after confirming the serializer-wrapper floors
remain capped by structurally unreachable `serde_json::to_string_pretty` error
mappings.

Implemented: one focused regression test for generated instance fallback
behavior when the semantic oracle has no accepted or rejected traces: fallback
primary-trace identity, empty initial/final fields, empty steps, empty required
capabilities, `ExpectedVerdict::Inconclusive`, empty expected-verdict
collection, custom suffix preservation, and family claim-boundary preservation.
No production code changed in this tranche.

Coverage result: `generator/instance.rs` moved from `77.27%` line / `50.00%`
function / `76.47%` region coverage to `100.00%` line / `100.00%` function /
`100.00%` region coverage. The package floor remains `replay/serialization.rs`
at `75.00%` line coverage, and the next visible floor is
`external_runner/serialization.rs` at `76.65%` line coverage; both are
serializer-wrapper files capped by structurally unreachable concrete-type
serialization error mappings. The next reachable `zkbench-core` floor is
`recursion.rs` at `77.29%` line coverage.

Anti-goals: generator instance semantics changes, production source changes,
external execution, generated artifact materialization, accepted Evidence
Ledger policy changes, benchmark evidence, real score-axis population, Level2+
evidence, semantic-correctness claims, production readiness, unsafe coverage
forcing, coverage suppression, structurally unreachable serialization-error
forcing, or whole-workspace 100% coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Phase 191 Recursion Coverage Twenty-Sixth Tranche

Status: complete. See
`docs/191-phase-recursion-coverage-twenty-sixth-tranche-notes.md`.

Goal: continue the bounded local coverage campaign by targeting the next
reachable `zkbench-core` floor after confirming the serializer-wrapper floors
remain capped by structurally unreachable `serde_json::to_string_pretty` error
mappings.

Implemented: focused regression tests for recursion-envelope empty identity and
missing-input validation, invalid digest algorithm/byte-length/hex-shape
validation, metric claim-boundary escalation, recursion-adapter preparation
empty plan shape, nested source-input and expected-artifact rejection,
manual-handoff wrapper and mapping claim-boundary drift, and malformed JSON
deserialization contexts. No production code changed in this tranche.

Coverage result: `recursion.rs` moved from `77.29%` line / `84.21%` function /
`84.30%` region coverage to `97.05%` line / `92.11%` function / `96.83%`
region coverage. The package floor remains `replay/serialization.rs` at
`75.00%` line coverage, and the next visible floor is
`external_runner/serialization.rs` at `76.65%` line coverage; both are
serializer-wrapper files capped by structurally unreachable concrete-type
serialization error mappings. The next reachable `zkbench-core` floors are
`pack/reader.rs` and `evidence/review.rs`, tied at `77.40%` line coverage.

Anti-goals: recursion-envelope semantics changes, recursion-adapter semantics
changes, production source changes, external execution, generated artifact
materialization, accepted Evidence Ledger policy changes, benchmark evidence,
real score-axis population, Level2+ evidence, semantic-correctness claims,
production readiness, unsafe coverage forcing, coverage suppression,
structurally unreachable serialization-error forcing, or whole-workspace 100%
coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Phase 192 Evidence Review Coverage Twenty-Seventh Tranche

Status: complete. See
`docs/192-phase-evidence-review-coverage-twenty-seventh-tranche-notes.md`.

Goal: continue the bounded local coverage campaign by targeting the next
reachable pure-data `zkbench-core` floor after confirming the serializer-wrapper
floors remain capped by structurally unreachable
`serde_json::to_string_pretty` error mappings.

Implemented: focused regression tests for evidence-review policy defaults,
reviewer-role classification, rejection and changes-requested review decision
builders, future append-preview review routing, candidate-only approval
blocking validation, forbidden claim-language scanning across review text
surfaces, checklist helper behavior, checklist JSON round-trip, and malformed
checklist/decision JSON deserialization contexts. No production code changed in
this tranche.

Coverage result: `evidence/review.rs` moved from `77.40%` line / `76.67%`
function / `73.60%` region coverage to `95.36%` line / `93.33%` function /
`95.03%` region coverage. The package floor remains `replay/serialization.rs`
at `75.00%` line coverage, and the next visible floor is
`external_runner/serialization.rs` at `76.65%` line coverage; both are
serializer-wrapper files capped by structurally unreachable concrete-type
serialization error mappings. The next reachable `zkbench-core` floor is
`pack/reader.rs` at `77.40%` line coverage.

Anti-goals: manual-review semantics changes, evidence-review policy semantics
changes, production source changes, external execution, generated artifact
materialization, accepted Evidence Ledger policy changes, benchmark evidence,
real score-axis population, Level2+ evidence, semantic-correctness claims,
production readiness, unsafe coverage forcing, coverage suppression,
structurally unreachable serialization-error forcing, or whole-workspace 100%
coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Phase 193 Pack Reader Coverage Twenty-Eighth Tranche

Status: complete. See
`docs/193-phase-pack-reader-coverage-twenty-eighth-tranche-notes.md`.

Goal: continue the bounded local coverage campaign by targeting the next
reachable pure-data `zkbench-core` floor after confirming the serializer-wrapper
floors remain capped by structurally unreachable
`serde_json::to_string_pretty` error mappings.

Implemented: focused regression tests for missing and malformed `pack.json`,
invalid pack paths, invalid direct evidence-ledger and score-report paths,
optional versus required missing files, missing and malformed evidence-ledger
readback, missing and malformed score-report readback, claim-boundary
elevation, remaining summary/id drift checks, and explicit safe nonclaim note
exemptions. No production code changed in this tranche.

Coverage result: `pack/reader.rs` moved from `77.40%` line / `75.00%`
function / `75.44%` region coverage to `97.95%` line / `100.00%` function /
`97.97%` region coverage. The package floor remains `replay/serialization.rs`
at `75.00%` line coverage, and the next visible floor is
`external_runner/serialization.rs` at `76.65%` line coverage; both are
serializer-wrapper files capped by structurally unreachable concrete-type
serialization error mappings. The next reachable `zkbench-core` floor is
`local_artifact_campaign.rs` at `77.69%` line coverage.

Anti-goals: benchmark-pack reader semantics changes, benchmark-pack manifest
semantics changes, production source changes, external execution, generated
artifact materialization, accepted Evidence Ledger policy changes, benchmark
evidence, real score-axis population, Level2+ evidence, semantic-correctness
claims, production readiness, unsafe coverage forcing, coverage suppression,
structurally unreachable serialization-error forcing, or whole-workspace 100%
coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Phase 194 Local Artifact Campaign Coverage Twenty-Ninth Tranche

Status: complete. See
`docs/194-phase-local-artifact-campaign-coverage-twenty-ninth-tranche-notes.md`.

Goal: continue the bounded local coverage campaign by targeting the next
reachable pure-data `zkbench-core` floor after confirming the serializer-wrapper
floors remain capped by structurally unreachable
`serde_json::to_string_pretty` error mappings.

Implemented: focused regression tests for empty campaign identity, invalid
campaign id, duplicate artifact URI, invalid digest, weaker-input boundary
validation, missing inputs, invalid artifact-ref schemes, invalid render
preconditions, empty/file output-root rejection, digest-consistent
manifest/validation/Markdown drift, non-UTF8 declared file readback, and
non-UTF8 digest sidecar readback. No production code changed in this tranche.

Coverage result: `local_artifact_campaign.rs` moved from `77.69%` line /
`62.71%` function / `78.42%` region coverage to `90.53%` line / `72.88%`
function / `85.30%` region coverage. The package floor remains
`replay/serialization.rs` at `75.00%` line coverage, and the next visible floor
is `external_runner/serialization.rs` at `76.65%` line coverage; both are
serializer-wrapper files capped by structurally unreachable concrete-type
serialization error mappings. The next reachable `zkbench-core` floor is
`evidence/digest.rs` at `77.78%` line coverage.

Anti-goals: local artifact campaign semantics changes, output-root semantics
changes, production source changes, external execution, generated artifact
materialization, accepted Evidence Ledger policy changes, benchmark evidence,
real score-axis population, Level2+ evidence, semantic-correctness claims,
production readiness, unsafe coverage forcing, coverage suppression,
structurally unreachable serialization-error forcing, or whole-workspace 100%
coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Phase 195 Evidence Digest Coverage Thirtieth Tranche

Status: complete. See
`docs/195-phase-evidence-digest-coverage-thirtieth-tranche-notes.md`.

Goal: continue the bounded local coverage campaign by targeting the next
reachable pure-data `zkbench-core` floor after confirming the serializer-wrapper
floors remain capped by structurally unreachable
`serde_json::to_string_pretty` error mappings.

Implemented: focused regression tests for deterministic `canonical_json_bytes`,
exact-byte parity between struct and raw digest helpers, raw byte digest
metadata, pretty-versus-compact JSON byte distinction, metadata-only kind/role
differences, empty raw payload SHA-256 behavior, and real serialization-error
propagation through both `canonical_json_bytes` and `compute_artifact_digest`.
No production code changed in this tranche.

Coverage result: `evidence/digest.rs` moved from `77.78%` line / `60.00%`
function / `74.36%` region coverage to `100.00%` line / `100.00%` function /
`97.44%` region coverage. The package floor remains
`replay/serialization.rs` at `75.00%` line coverage, and the next visible floor
is `external_runner/serialization.rs` at `76.65%` line coverage; both are
serializer-wrapper files capped by structurally unreachable concrete-type
serialization error mappings. The next reachable `zkbench-core` floor is
`soak/config.rs` at `78.21%` line coverage.

Anti-goals: digest semantics changes, serialization policy changes, production
source changes, external execution, generated artifact materialization,
accepted Evidence Ledger policy changes, benchmark evidence, real score-axis
population, Level2+ evidence, semantic-correctness claims, production
readiness, unsafe coverage forcing, coverage suppression, structurally
unreachable serialization-error forcing, or whole-workspace 100% coverage
claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Phase 196 Soak Config Coverage Thirty-First Tranche

Status: complete. See
`docs/196-phase-soak-config-coverage-thirty-first-tranche-notes.md`.

Goal: continue the bounded local coverage campaign by targeting the next
reachable pure-data `zkbench-core` floor after confirming the serializer-wrapper
floors remain capped by structurally unreachable
`serde_json::to_string_pretty` error mappings.

Implemented: focused regression tests for seed-range helpers, family and
mutation selection normalization, planned case and mutation counts,
output-policy pack-write accounting, smoke/regression/focused/custom/nightly
profile validation, config version and local-only note preservation, boundary
and empty-scope rejection paths, unimplemented mutation rejection, and
family/instance/mutation/shard/pack limit rejection. No production code changed
in this tranche.

Coverage result: `soak/config.rs` moved from `78.21%` line / `90.24%`
function / `86.35%` region coverage to `98.88%` line / `100.00%` function /
`99.26%` region coverage. The package floor remains
`replay/serialization.rs` at `75.00%` line coverage, and the next visible floor
is `external_runner/serialization.rs` at `76.65%` line coverage; both are
serializer-wrapper files capped by structurally unreachable concrete-type
serialization error mappings. The next reachable `zkbench-core` floor is
`adapters/zk_harness/export.rs` at `78.26%` line coverage.

Anti-goals: local soak configuration semantics changes, limit changes, profile
policy changes, production source changes, external execution, generated
artifact materialization, accepted Evidence Ledger policy changes, benchmark
evidence, real score-axis population, Level2+ evidence, semantic-correctness
claims, production readiness, unsafe coverage forcing, coverage suppression,
structurally unreachable serialization-error forcing, or whole-workspace 100%
coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Phase 197 zk-Harness Export Coverage Thirty-Second Tranche

Status: complete. See
`docs/197-phase-zk-harness-export-coverage-thirty-second-tranche-notes.md`.

Goal: continue the bounded local coverage campaign by targeting the next
reachable pure-data `zkbench-core` floor after confirming the serializer-wrapper
floors remain capped by structurally unreachable
`serde_json::to_string_pretty` error mappings.

Implemented: focused regression tests for public helper delegation to direct
export, source-pack id preservation, dry-run plan id binding into the export
manifest, export-time rejection of a locally valid source pack whose id is
unsafe for inert planned-command argument text, and preservation of validation
context/path/message on fail-closed export. No production code changed in this
tranche.

Coverage result: `adapters/zk_harness/export.rs` moved from `78.26%` line /
`80.00%` function / `79.37%` region coverage to `86.96%` line / `80.00%`
function / `80.95%` region coverage. The package floor remains
`replay/serialization.rs` at `75.00%` line coverage, and the next visible floor
is `external_runner/serialization.rs` at `76.65%` line coverage; both are
serializer-wrapper files capped by structurally unreachable concrete-type
serialization error mappings. The next reachable `zkbench-core` floor is
`soak/runner.rs` at `78.41%` line coverage.

Anti-goals: zk-Harness export semantics changes, validation semantics changes,
pack semantics changes, production source changes, external execution,
zk-Harness execution, generated artifact materialization, accepted Evidence
Ledger policy changes, benchmark evidence, real score-axis population, Level2+
evidence, semantic-correctness claims, production readiness, unsafe coverage
forcing, coverage suppression, structurally unreachable serialization-error
forcing, or whole-workspace 100% coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Phase 198 Soak Runner Coverage Thirty-Third Tranche

Status: complete. See
`docs/198-phase-soak-runner-coverage-thirty-third-tranche-notes.md`.

Goal: continue the bounded local coverage campaign by targeting the next
reachable pure-data `zkbench-core` floor after confirming the serializer-wrapper
floors remain capped by structurally unreachable
`serde_json::to_string_pretty` error mappings.

Implemented: focused regression tests for public shard wrapper run/resume
behavior, checkpoint-backed skipped-by-resume status, stop-on-first-failure
replay-failure recording, failure-pack-only output and telemetry,
failure-corpus extraction, and overwrite-enabled sampled-pack output over a
stale directory. No production code changed in this tranche.

Coverage result: `soak/runner.rs` moved from `78.41%` line / `83.67%`
function / `78.48%` region coverage to `89.42%` line / `95.92%` function /
`90.08%` region coverage. The package floor remains
`replay/serialization.rs` at `75.00%` line coverage, and the next visible floor
is `external_runner/serialization.rs` at `76.65%` line coverage; both are
serializer-wrapper files capped by structurally unreachable concrete-type
serialization error mappings. The next reachable `zkbench-core` floor is
`soak/resume.rs` at `78.61%` line coverage.

Anti-goals: local soak runner semantics changes, resume semantics changes,
output-pack semantics changes, failure-corpus semantics changes, telemetry
semantics changes, production source changes, external execution, generated
artifact materialization, accepted Evidence Ledger policy changes, benchmark
evidence, real score-axis population, Level2+ evidence, semantic-correctness
claims, production readiness, unsafe coverage forcing, coverage suppression,
structurally unreachable serialization-error forcing, or whole-workspace 100%
coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Phase 199 Soak Resume Coverage Thirty-Fourth Tranche

Status: complete. See
`docs/199-phase-soak-resume-coverage-thirty-fourth-tranche-notes.md`.

Goal: continue the bounded local coverage campaign by targeting the next
reachable pure-data `zkbench-core` floor after confirming the serializer-wrapper
floors remain capped by structurally unreachable
`serde_json::to_string_pretty` error mappings.

Implemented: focused regression tests for elevated-boundary, empty-shard,
resume-token, case-overlap, artifact-reference, empty failed-case id,
parent-directory creation, readback, missing-file, and malformed-JSON checkpoint
paths. No production code changed in this tranche.

Coverage result: `soak/resume.rs` moved from `78.61%` line / `66.67%`
function / `78.10%` region coverage to `93.58%` line / `77.78%` function /
`88.10%` region coverage. The package floor remains
`replay/serialization.rs` at `75.00%` line coverage, and the next visible floor
is `external_runner/serialization.rs` at `76.65%` line coverage; both are
serializer-wrapper files capped by structurally unreachable concrete-type
serialization error mappings. The next reachable `zkbench-core` floor is
`mutation/invalid_unroll_bounds.rs` at `78.87%` line coverage.

Anti-goals: local soak checkpoint semantics changes, resume semantics changes,
artifact-reference semantics changes, checkpoint persistence semantics changes,
production source changes, external execution, generated artifact
materialization, accepted Evidence Ledger policy changes, benchmark evidence,
real score-axis population, Level2+ evidence, semantic-correctness claims,
production readiness, unsafe coverage forcing, coverage suppression,
structurally unreachable serialization-error forcing, or whole-workspace 100%
coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Phase 200 Mutation Invalid Unroll Bounds Coverage Thirty-Fifth Tranche

Status: complete. See
`docs/200-phase-mutation-invalid-unroll-bounds-coverage-thirty-fifth-tranche-notes.md`.

Goal: continue the bounded local coverage campaign by targeting the next
reachable pure-data `zkbench-core` floor after confirming the serializer-wrapper
floors remain capped by structurally unreachable
`serde_json::to_string_pretty` error mappings.

Implemented: focused regression tests for `InvalidUnrollBoundsPass` mutation
class reporting, no-primary-trace fail-closed behavior, primary-trace and
claim-boundary preservation, and affected-guard-id binding for an eligible
bounded-counter-loop instance. No production code changed in this tranche.

Coverage result: `mutation/invalid_unroll_bounds.rs` moved from `78.87%`
line / `57.14%` function / `81.18%` region coverage to `88.73%` line /
`85.71%` function / `89.41%` region coverage. The package floor remains
`replay/serialization.rs` at `75.00%` line coverage, and the next visible floor
is `external_runner/serialization.rs` at `76.65%` line coverage; both are
serializer-wrapper files capped by structurally unreachable concrete-type
serialization error mappings. The remaining uncovered lines in
`mutation/invalid_unroll_bounds.rs` are structurally unreachable per the
selector contract (`target.bound.is_none()` and the `negate_bound` `Bool` and
`RawText` arms). After the two known serializer-wrapper caps, the next visible
non-serializer `zkbench-core` floor requiring audit is
`evidence/accepted_append.rs` at `78.99%` line coverage.

Anti-goals: mutation pass semantics changes, selector semantics changes,
`negate_bound` semantics changes, DSL types, oracle semantics, scoring
semantics, production source changes, external execution, generated artifact
materialization, accepted Evidence Ledger policy changes, benchmark evidence,
real score-axis population, Level2+ evidence, semantic-correctness claims,
production readiness, unsafe coverage forcing, coverage suppression,
structurally unreachable serialization-error forcing, or whole-workspace 100%
coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Phase 201 Evidence Accepted Append Coverage Thirty-Sixth Tranche

Status: complete. See
`docs/201-phase-evidence-accepted-append-coverage-thirty-sixth-tranche-notes.md`.

Goal: continue the bounded local coverage campaign by targeting the next
visible non-serializer `zkbench-core` floor after confirming the two serializer
wrapper floors remain capped by structurally unreachable concrete-type
serialization error mappings.

Implemented: focused regression tests for accepted-ledger append validation
around empty identities, invalid ledgers, tampered preflight reports, current
tip drift, append-preview candidate/entry metadata drift, missing source
digests, forbidden transaction notes, and post-append ledger validation of
forbidden transaction-id text. No production code changed in this tranche.

Coverage result: `evidence/accepted_append.rs` moved from `79.77%` line /
`84.62%` function coverage to `98.29%` line / `92.31%` function coverage. The
`zkbench-core` package moved from `90.00%` region / `85.65%` function /
`90.82%` line coverage to `90.13%` region / `85.71%` function / `91.11%` line
coverage. The remaining uncovered lines in `evidence/accepted_append.rs` are
the defensive empty-ledger-after-success guard and the concrete candidate digest
serialization error mapping. The next package floor is `soak/health.rs` at
`79.00%` line coverage.

Anti-goals: accepted-append semantics changes, preflight semantics changes,
evidence-ledger semantics changes, candidate digest semantics changes,
production source changes, external execution, generated artifact
materialization, accepted Evidence Ledger policy changes, benchmark evidence,
real score-axis population, Level2+ evidence, semantic-correctness claims,
production readiness, unsafe coverage forcing, coverage suppression,
structurally unreachable serialization-error forcing, defensive
post-append-empty-ledger guard forcing, or whole-workspace 100% coverage claims.

Exit criteria: the focused test suite passes, the targeted module reaches the
highest honest public-API coverage without semantic changes, and root
validation remains green.

## Phase 202 HSAI Gateway SOTA Bridge Boundary

Status: complete for docs-first boundary. See
`docs/202-phase-hsai-gateway-sota-bridge-boundary-spec.md`.

Goal: define the smallest credible bridge from the local HSAI admission stack
to a marketable SOTA-level Agent Approval Gateway proof path, using
hardware-respectful local open-weight model adversarial generation first and a
rented open-weight adversarial lane only when it adds measurable coverage.

Implemented: the boundary names the observed local Apple M4 Max / 36 GB memory
baseline, separates local 1B-14B open-weight model use from rented GPU
adversarial generation, keeps all model outputs proposal-only, requires strict
typed candidate intake before admission, defines adversarial corpus labels,
defines local/rented provenance fields, lists gateway metrics, and orders the
evidence ladder from local corpus replay through future independent
reproduction.

Anti-goals: Rust implementation, package runtime files, CLI/server/UI,
dashboard, model downloads, committed prompts, committed generated corpora,
output bundles, secrets, credential handling, external replay execution,
signer/wallet/exchange/custody/ACP/MCP integration code, accepted Evidence
Ledger mutation, score-axis population, benchmark output, Level2+ evidence,
production-readiness claims, semantic-correctness claims, global
software-agent uniqueness claims, or claims above `Attested`.

Exit criteria: README navigation, task list, validation report, and AGENTS
scope rules point to the boundary; local and rented model lanes are separated;
trust-native rules are explicit; adversarial corpus shape is explicit; and the
spec authorizes no runtime surface.

## Phase 203 HSAI Agent Approval Gateway PRD

Status: complete for long-form PRD. See
`docs/203-hsai-agent-approval-gateway-prd.md`.

Goal: turn the Phase 202 bridge boundary and current product strategy into a
durable product requirements document for an HSAI Agent Approval Gateway.

Implemented: the PRD defines the problem statement, product solution, extensive
user stories, implementation decisions, deep modules, trust model, cost and
pricing decisions, product tiers, baselines to beat, testing decisions, success
metrics, out-of-scope boundaries, rollout plan, and source references. It frames
HSAI as an evidence-aware authorization layer between autonomous-agent proposals
and downstream authority, not as a wallet, custodian, model host, checkout
provider, or proof system.

Anti-goals: implementation code, Cargo metadata changes, dependencies, package
runtime files, CLI/server/UI/dashboard work, model execution, generated corpora,
generated output bundles, secrets, credentials, external replay execution,
signer/wallet/exchange/custody/ACP/MCP integration code, accepted Evidence
Ledger mutation, score-axis population, benchmark output, Level2+ evidence,
production-readiness claims, semantic-correctness claims, global
software-agent uniqueness claims, "fully secure" claims, or claims above
`Attested`.

Exit criteria: README navigation, task list, validation report, and AGENTS scope
rules point to the PRD; the PRD preserves Phase 202 trust-native rules; and
documentation validation passes.

## Phase 204 HSAI Agent Approval Gateway Local MVP

Status: complete for local hermetic implementation. See
`docs/204-hsai-agent-approval-gateway-local-mvp-notes.md`.

Goal: implement the first local Agent Approval Gateway surface over the existing
HSAI admission journal without model execution, external integrations, or
authority-bearing runtime paths.

Implemented: `GatewayActionProposal`, gateway action kinds, threat labels,
model-lane provenance, gateway policy, gateway policy violations, accepted
handoff metadata, corpus cases, local metrics, gateway candidate mapping,
action evaluation, accepted handoff extraction, corpus evaluation, and metrics.
The implementation maps typed proposals into
`AdmissionSourceKind::GatewayActionProposal`, turns gateway violations into
deterministic admission reasons, reuses `AgentAdmissionJournal`, and exposes
handoff metadata only after accepted local admission.

Anti-goals: Cargo metadata changes, dependencies, package runtime files,
CLI/server/UI/dashboard work, model execution/download, generated corpora,
generated output bundles, secrets, credentials, external replay execution,
signer/wallet/exchange/custody/ACP/MCP integration code, accepted Evidence
Ledger mutation, score-axis population, benchmark output, Level2+ evidence,
production-readiness claims, semantic-correctness claims, global
software-agent uniqueness claims, "fully secure" claims, or claims above
`Attested`.

Exit criteria: focused gateway admission tests pass, README navigation, task
list, validation report, and AGENTS scope rules point to the implementation
notes; accepted actions expose handoff metadata; rejected and quarantined cases
remain auditable; metrics remain local and non-benchmark.

## Phase 205 HSAI Gateway Report Artifact

Status: complete for local hermetic implementation. See
`docs/205-hsai-gateway-report-artifact-notes.md`.

Goal: add a deterministic local report artifact surface over
`GatewayCorpusReport` without filesystem materialization, package runtime code,
model execution, external integrations, or benchmark evidence.

Implemented: `GatewayReportValidationIssue`, `GatewayReportArtifactError`,
`GatewayReportArtifactManifest`, `GatewayReportArtifact`,
`gateway_report_required_nonclaims`, `validate_gateway_corpus_report`,
`gateway_report_artifact`, and `render_gateway_report_markdown`. The report
artifact binds deterministic JSON bytes, deterministic Markdown bytes, the
policy id, report digest, journal tip digest, local metrics, SHA-256 sidecars,
and required nonclaims.

Anti-goals: Cargo metadata changes, dependencies, package runtime files,
filesystem materialization, CLI/server/UI/dashboard work, model
execution/download, generated corpora/output bundles, secrets, credentials,
external replay execution, signer/wallet/exchange/custody/ACP/MCP integration
code, accepted Evidence Ledger mutation, score-axis population, benchmark
output, Level2+ evidence, production-readiness claims, semantic-correctness
claims, global software-agent uniqueness claims, "fully secure" claims, or
claims above `Attested`.

Exit criteria: focused gateway report tests pass, deterministic JSON and
Markdown hashes are bound in the manifest, stale metrics fail closed before
rendering, README navigation, validation report, and AGENTS scope rules point to
the notes, and metrics remain local and non-benchmark.

## Phase 206 HSAI Gateway Report Output Plumbing

Status: complete for local hermetic implementation. See
`docs/206-hsai-gateway-report-output-plumbing-notes.md`.

Goal: materialize Phase 205 gateway report artifacts under a caller-selected
local output root with declared files, SHA-256 sidecars, and strict readback
validation, without package runtime code, model execution, external
integrations, committed generated bundles, or benchmark evidence.

Implemented: `GatewayReportMaterializationRequest`,
`GatewayReportOutputManifest`, `GatewayReportOutputValidationReport`,
`GatewayReportMaterializationError`, `materialize_gateway_report_bundle`, and
`read_gateway_report_bundle`. The output bundle writes declared
`gateway-report/*` files and sidecars, rejects protected roots and unsafe output
roots, rejects undeclared files, and validates report, manifest, nonclaim, and
validation-report semantics on readback.

Anti-goals: Cargo metadata changes, dependencies, package runtime files,
CLI/server/UI/dashboard work, model execution/download, committed generated
gateway report bundles, generated corpora/output bundles, secrets, credentials,
external replay execution, signer/wallet/exchange/custody/ACP/MCP integration
code, accepted Evidence Ledger mutation, score-axis population, benchmark
output, Level2+ evidence, production-readiness claims, semantic-correctness
claims, global software-agent uniqueness claims, "fully secure" claims, or
claims above `Attested`.

Exit criteria: focused gateway output tests pass; declared files and sidecars
materialize; readback equals the written manifest; protected roots, undeclared
files, and digest-consistent tampered reports fail closed; README navigation,
validation report, and AGENTS scope rules point to the notes.

## Phase 207 HSAI Gateway Corpus Output Run

Status: complete for local hermetic implementation. See
`docs/207-hsai-gateway-corpus-output-run-notes.md`.

Goal: provide a single local API that evaluates typed gateway corpus cases and
materializes the validated Phase 206 report bundle only after successful
evaluation and report validation.

Implemented: `GatewayCorpusOutputRun`, `GatewayCorpusOutputRunError`, and
`materialize_gateway_corpus_output_run`. The helper composes the existing
gateway corpus evaluator, report artifact validation, and output writer without
adding model execution, external replay, signer/tool integration, or package
runtime code.

Anti-goals: Cargo metadata changes, dependencies, package runtime files,
CLI/server/UI/dashboard work, model execution/download, committed generated
gateway report bundles, generated corpora/output bundles, secrets, credentials,
external replay execution, signer/wallet/exchange/custody/ACP/MCP integration
code, accepted Evidence Ledger mutation, score-axis population, benchmark
output, Level2+ evidence, production-readiness claims, semantic-correctness
claims, global software-agent uniqueness claims, "fully secure" claims, or
claims above `Attested`.

Exit criteria: focused gateway output-run tests pass; replayed candidates fail
before output creation; protected roots fail through the existing output safety
path; README navigation, validation report, and AGENTS scope rules point to the
notes.

## Phase 208 HSAI Gateway Cost Router

Status: complete for local hermetic implementation. See
`docs/208-hsai-gateway-cost-router-notes.md`.

Goal: implement the first deterministic local cost-router surface for the HSAI
Agent Approval Gateway so review effort can be routed by typed risk, value, and
budget without giving raw model output authority.

Implemented: `GatewayCostRoute`, `GatewayCostRouteReason`,
`GatewayCostRouterPolicy`, `GatewayCostRouteDecision`,
`gateway_cost_router_default_policy`, and `route_gateway_action_cost`. The
router maps deterministic policy violations to zero-cost deterministic handling,
moderate clean actions to local open-weight review, threat-labeled actions to a
verifier mixture route, high-value actions to premium escalation only inside the
configured budget, and deployment or over-ceiling actions to operator review.
Every route preserves `authority_granted = false`.

Anti-goals: Cargo metadata changes, dependencies, package runtime files,
CLI/server/UI/dashboard work, model execution/download, verifier-agent runtime,
hosted model calls, generated corpora/output bundles, secrets, credentials,
external replay execution, signer/wallet/exchange/custody/ACP/MCP integration
code, accepted Evidence Ledger mutation, score-axis population, benchmark
output, Level2+ evidence, production-readiness claims, semantic-correctness
claims, global software-agent uniqueness claims, "fully secure" claims, or
claims above `Attested`.

Exit criteria: focused cost-router tests pass; deterministic rejects avoid
model-review cost; threat-labeled cases route to verifier mixture; premium
budget exhaustion fails closed to operator review; operator-only deployments
require operator review; README navigation, validation report, and AGENTS scope
rules point to the notes.

## Phase 209 HSAI Gateway Model Lane Registry

Status: complete for local hermetic implementation. See
`docs/209-hsai-gateway-model-lane-registry-notes.md`.

Goal: implement the first deterministic local model-lane registry surface so
local, rented, hosted, and premium model provenance can be validated before it
is treated as proposal metadata in the gateway proof path.

Implemented: `GatewayModelLaneRegistryEntry`, `GatewayModelLaneRegistry`,
`GatewayModelLaneRegistryIssue`, and `validate_gateway_model_lane_registry`.
The validator rejects invalid or duplicate lane ids, missing model family /
artifact ids, missing prompt-template digests, missing non-secret statements,
stale output-bundle digests, and unbounded rented, hosted-small, or
premium-escalation lane metadata.

Anti-goals: Cargo metadata changes, dependencies, package runtime files,
CLI/server/UI/dashboard work, model execution/download, provider calls,
verifier-agent runtime, generated corpora/output bundles, secrets,
credentials, external replay execution, signer/wallet/exchange/custody/ACP/MCP
integration code, accepted Evidence Ledger mutation, score-axis population,
benchmark output, Level2+ evidence, production-readiness claims,
semantic-correctness claims, global software-agent uniqueness claims, "fully
secure" claims, or claims above `Attested`.

Exit criteria: focused model-lane registry tests pass; missing model ids,
prompt digests, non-secret statements, stale output digests, duplicate lane
ids, and unbounded rented metadata fail closed; README navigation, validation
report, and AGENTS scope rules point to the notes.

## Phase 210 HSAI Gateway Adversarial Corpus Validation

Status: complete for local hermetic implementation. See
`docs/210-hsai-gateway-adversarial-corpus-notes.md`.

Goal: implement the first deterministic local adversarial-corpus validation
surface so typed gateway corpora can be checked before local replay or report
generation.

Implemented: `GatewayAdversarialCorpus`, `GatewayAdversarialCorpusIssue`,
`gateway_required_adversarial_threat_labels`, and
`validate_gateway_adversarial_corpus`. The validator rejects invalid corpus
ids, empty corpora, duplicate case ids, missing required threat labels, missing
accepted benign controls, adversarial cases that expect acceptance, unknown
model-lane provenance, and invalid model-lane registries.

Anti-goals: Cargo metadata changes, dependencies, package runtime files,
CLI/server/UI/dashboard work, corpus generation, model execution/download,
prompt storage, provider calls, verifier-agent runtime, generated
corpora/output bundles, secrets, credentials, external replay execution,
signer/wallet/exchange/custody/ACP/MCP integration code, accepted Evidence
Ledger mutation, score-axis population, benchmark output, Level2+ evidence,
production-readiness claims, semantic-correctness claims, global software-agent
uniqueness claims, "fully secure" claims, or claims above `Attested`.

Exit criteria: focused adversarial-corpus tests pass; full required threat
coverage validates; invalid/empty corpora, duplicate ids, missing threat
labels, unsafe expected acceptance, unknown model lanes, and invalid registries
fail closed; README navigation, validation report, and AGENTS scope rules point
to the notes.

## Phase 211 HSAI Gateway Adversarial Corpus Output Run

Status: complete for local hermetic implementation. See
`docs/211-hsai-gateway-adversarial-corpus-output-run-notes.md`.

Goal: compose adversarial-corpus validation with the existing one-shot gateway
corpus replay and report materialization path.

Implemented: `GatewayCorpusOutputRunError::CorpusValidation` and
`materialize_gateway_adversarial_corpus_output_run`. The helper validates the
typed adversarial corpus and model-lane registry before evaluating cases or
creating output, then reuses the existing Phase 207 output-run and Phase 206
report-bundle materialization path.

Anti-goals: Cargo metadata changes, dependencies, package runtime files,
CLI/server/UI/dashboard work, corpus generation, model execution/download,
prompt storage, provider calls, verifier-agent runtime, generated
corpora/output bundles, secrets, credentials, external replay execution,
signer/wallet/exchange/custody/ACP/MCP integration code, accepted Evidence
Ledger mutation, score-axis population, benchmark output, Level2+ evidence,
production-readiness claims, semantic-correctness claims, global software-agent
uniqueness claims, "fully secure" claims, or claims above `Attested`.

Exit criteria: focused adversarial-corpus output-run tests pass; invalid corpus
metadata stops before output creation; valid corpora materialize the existing
`gateway-report/*` bundle; protected output roots still fail through the
existing materialization safety path; README navigation, validation report, and
AGENTS scope rules point to the notes.

## Phase 212 HSAI Gateway Baseline Comparison

Status: complete for local hermetic implementation. See
`docs/212-hsai-gateway-baseline-comparison-notes.md`.

Goal: implement the first local baseline-comparison surface so validated HSAI
gateway reports can be compared against simple baseline decisions without
making benchmark or production claims.

Implemented: `GatewayBaselineKind`, `GatewayBaselineDecision`,
`GatewayBaselineRun`, `GatewayBaselineComparison`,
`GatewayBaselineComparisonIssue`, `GatewayBaselineComparisonError`,
`gateway_baseline_required_nonclaims`, and `compare_gateway_baseline`. The
comparison validates the HSAI report and baseline shape, requires local
nonclaims, computes unsafe accepted counts and false rejection counts for HSAI
and the baseline, carries audit-bundle completeness, records a local claim
boundary, and preserves `authority_granted = false`.

Anti-goals: Cargo metadata changes, dependencies, package runtime files,
CLI/server/UI/dashboard work, live baseline execution, model execution/download,
LLM judge runtime, provider calls, verifier-agent runtime, generated
corpora/output bundles, secrets, credentials, external replay execution,
signer/wallet/exchange/custody/ACP/MCP integration code, accepted Evidence
Ledger mutation, score-axis population, benchmark output, Level2+ evidence,
production-readiness claims, semantic-correctness claims, global software-agent
uniqueness claims, "fully secure" claims, or claims above `Attested`.

Exit criteria: focused baseline-comparison tests pass; no-approval baseline
unsafe accepts are counted; invalid HSAI reports fail closed; missing nonclaims
fail closed; duplicate, missing, and unknown baseline decisions fail closed;
README navigation, validation report, and AGENTS scope rules point to the
notes.

## Phase 213 HSAI Gateway Effectiveness Metrics

Status: complete for local hermetic implementation. See
`docs/213-hsai-gateway-effectiveness-metrics-notes.md`.

Goal: implement a local effectiveness-summary surface for validated HSAI
gateway corpus reports.

Implemented: `GatewayThreatCoverageRow`, `GatewayEffectivenessSummary`, and
`gateway_effectiveness_summary`. The summary validates the HSAI report, then
computes unsafe case count, benign expected-accept count, unsafe action block
rate, false rejection rate, quarantine rate, decision recomputation agreement
rate, audit-bundle completeness, covered threat labels, per-threat coverage,
local claim-boundary metadata, and `authority_granted = false`.

Anti-goals: Cargo metadata changes, dependencies, package runtime files,
CLI/server/UI/dashboard work, live metrics collection, model execution/download,
LLM judge runtime, provider calls, verifier-agent runtime, generated
corpora/output bundles, secrets, credentials, external replay execution,
signer/wallet/exchange/custody/ACP/MCP integration code, accepted Evidence
Ledger mutation, score-axis population, benchmark output, Level2+ evidence,
production-readiness claims, semantic-correctness claims, global software-agent
uniqueness claims, "fully secure" claims, or claims above `Attested`.

Exit criteria: focused effectiveness-metrics tests pass; full adversarial
corpus rates and per-threat coverage compute; invalid reports fail closed;
zero-denominator local rate handling is deterministic; README navigation,
validation report, and AGENTS scope rules point to the notes.

## Phase 214 HSAI Gateway Public Proof Packet

Status: complete for bounded public proof packaging. See
`docs/214-hsai-gateway-public-proof-packet.md`.

Goal: publish a shareable claim packet for the green public Phase 204-212 HSAI
Gateway state without expanding the technical claim.

Implemented: the packet names public commit
`4dfa3e6dfddd8ab79f558691bc10c48b74f47bf7`, the validated Phase 204-212
surfaces, the exact local verifier commands, reproduction checklist, public
claim text, buyer-facing wording, and explicit nonclaims.

Anti-goals: Rust source changes, tests, Cargo metadata changes, package runtime
files, generated demo bundles, model execution/download, provider calls,
verifier-agent runtime, external replay execution, signer/wallet/exchange/
custody/ACP/MCP/tool integration, accepted Evidence Ledger mutation,
score-axis population, benchmark output, Level2+ evidence,
production-readiness claims, semantic-correctness claims, global software-agent
uniqueness claims, "fully secure" claims, or claims above `Attested`.

Exit criteria: the proof packet names the public commit and verifier commands,
preserves all Phase 204-212 claim boundaries, and README navigation points to
the packet.

## Phase 215 HSAI Gateway Local Demo Runbook

Status: complete for local ignored demo output. See
`docs/215-hsai-gateway-local-demo-runbook.md`.

Goal: add an operator-facing, reproducible local demo path for the existing
`gateway-report/*` output bundle.

Implemented: `.gateway-demo-runs/` is now ignored; `gateway_demo_report` is an
env-driven Cargo example under `hsai-agent-admission`; the example builds a
fixed non-secret local adversarial corpus, validates it against a local
model-lane registry, materializes the existing declared `gateway-report/*`
bundle, reads it back through the existing validator, and prints a summary JSON
with `authority_granted = false`. A source-contract test verifies the env
contract, ignored-root constraint, nonclaim text, and absence of provider or
process runtime surfaces.

Anti-goals: new gateway semantics, package runtime files, dependencies, CLI
argument parsing, server/UI/dashboard work, model execution/download, provider
calls, verifier-agent runtime, hosted model calls, committed generated bundles,
secrets, credentials, external replay execution, signer/wallet/exchange/custody
/ACP/MCP/tool integration, accepted Evidence Ledger mutation, score-axis
population, benchmark output, Level2+ evidence, production-readiness claims,
semantic-correctness claims, global software-agent uniqueness claims, "fully
secure" claims, or claims above `Attested`.

Exit criteria: the example compiles; the source-contract test passes; the
runbook names the exact env contract and generated files; repo hygiene and
claim-boundary checks pass; the generated demo root remains ignored.

## Phase 216 Soak Health Coverage Thirty-Seventh Tranche

Status: complete for focused local coverage hardening. See
`docs/216-phase-soak-health-coverage-thirty-seventh-tranche-notes.md`.

Goal: add focused regression coverage for
`crates/zkbench-core/src/soak/health.rs` without changing production health
semantics.

Implemented: `soak_health_report` tests now cover empty report version, empty
shard id, empty aggregate id, nested finding claim-boundary elevation, unsafe
ZK-backend-performance notes, mutation/local-replay/failure summary drift,
aggregate warning propagation, aggregate status precedence, aggregate regression
signal activation, telemetry replay-failure findings, and telemetry validation
failure findings.

Anti-goals: production source changes, health semantics changes, status
precedence changes, telemetry semantics changes, failure-corpus semantics
changes, Cargo metadata changes, dependencies, external execution, generated
artifact materialization, accepted Evidence Ledger policy changes, formal
evidence, benchmark evidence, score-axis population, Level2+ evidence,
semantic-correctness claims, production-readiness claims, unsafe coverage
forcing, coverage suppression, structurally unreachable branch forcing, or
whole-workspace 100% coverage claims.

Exit criteria: focused `soak_health_report` tests pass; repo hygiene and
claim-boundary checks pass; full workspace tests pass; docs record the claim
boundary and non-goals.

## Phase 217 Replay Serialization Coverage Audit

Status: complete for local coverage-floor audit. See
`docs/217-phase-replay-serialization-coverage-audit-notes.md`.

Goal: audit the current package coverage floor at
`crates/zkbench-core/src/replay/serialization.rs` before adding any coverage
tests.

Implemented: the local package coverage run still reports `zkbench-core` at
`90.28%` region coverage, `85.76%` function execution, and `91.35%` line
coverage. The measured floor remains `replay/serialization.rs` at `75.00%`
line / `75.00%` function / `75.00%` region coverage. Missing-line inspection
shows only the serializer `serde_json::to_string_pretty` error closures remain
uncovered; malformed JSON deserializer branches are already exercised.

Audit decision: no Rust tests were added because reaching those serializer
closures would require fabricated concrete-type serialization failures or
production API changes. The next visible low file is
`external_runner/serialization.rs` at `76.65%` line coverage and should be
audited before any test expansion.

Anti-goals: production source changes, serialization semantics changes, Cargo
metadata changes, dependencies, external execution, generated artifact
materialization, accepted Evidence Ledger policy changes, formal evidence,
benchmark evidence, score-axis population, Level2+ evidence,
semantic-correctness claims, production-readiness claims, unsafe coverage
forcing, coverage suppression, structurally unreachable branch forcing, or
whole-workspace 100% coverage claims.

Exit criteria: missing-line audit identifies the reachable and capped replay
serialization paths; focused replay serialization tests still pass; repo
hygiene and claim-boundary checks pass; full workspace tests pass; docs record
the cap and next audit target.

## Phase 218 External Runner Serialization Coverage Audit

Status: complete for local coverage-floor audit. See
`docs/218-phase-external-runner-serialization-coverage-audit-notes.md`.

Goal: audit the next visible serializer-wrapper floor at
`crates/zkbench-core/src/external_runner/serialization.rs` before adding any
coverage tests.

Implemented: the local package coverage run still reports `zkbench-core` at
`90.28%` region coverage, `85.76%` function execution, and `91.35%` line
coverage. The audited file reports `76.65%` line / `75.00%` function /
`75.00%` region coverage. Missing-line inspection shows only concrete-type
serializer `serde_json::to_string_pretty` error closures remain uncovered;
malformed JSON deserializer branches are already exercised by
`phase_v_coverage_hardening.rs`.

Audit decision: no Rust tests were added because reaching those serializer
closures would require fabricated concrete-type serialization failures or
production API changes. The next coverage slice should move past
serializer-wrapper floors and target a reachable public-API module after a
fresh missing-line audit.

Anti-goals: production source changes, serialization semantics changes, Cargo
metadata changes, dependencies, external execution, generated artifact
materialization, accepted Evidence Ledger policy changes, formal evidence,
benchmark evidence, score-axis population, Level2+ evidence,
semantic-correctness claims, production-readiness claims, unsafe coverage
forcing, coverage suppression, structurally unreachable branch forcing, or
whole-workspace 100% coverage claims.

Exit criteria: missing-line audit identifies the reachable and capped
external-runner serialization paths; focused Phase V coverage hardening tests
still pass; repo hygiene and claim-boundary checks pass; full workspace tests
pass; docs record the cap and next reachable target class.

## Phase 219 External Runner Artifact Capture Coverage

Status: complete for local coverage hardening. See
`docs/219-phase-external-runner-artifact-capture-coverage-notes.md`.

Goal: harden the first reachable non-serializer public API surface after the
Phase 217/218 serializer-wrapper audits:
`crates/zkbench-core/src/external_runner/artifact_capture.rs`.

Implemented: added focused tests in
`crates/zkbench-core/tests/artifact_capture_contract.rs` for the default
artifact matrix and validator branches covering empty contract id,
claim-boundary elevation, empty expected-artifact id, expected-artifact
traversal hints, captured-artifact warning emission, unreviewed captured
artifact warnings, and captured-artifact traversal URI rejection.

Coverage result: the local package coverage run moved `zkbench-core` from
`90.28%` region / `85.76%` function / `91.35%` line coverage to `90.37%`
region / `85.82%` function / `91.48%` line coverage.
`external_runner/artifact_capture.rs` moved from `82.69%` region / `87.50%`
function / `80.84%` line coverage to `98.08%` region / `100.00%` function /
`99.40%` line coverage.

Anti-goals: production source changes, artifact-capture semantics changes,
external-runner semantics changes, Cargo metadata changes, dependencies,
external execution, generated artifact materialization, accepted Evidence
Ledger policy changes, formal evidence, benchmark evidence, score-axis
population, Level2+ evidence, semantic-correctness claims, production-readiness
claims, unsafe coverage forcing, coverage suppression, structurally unreachable
branch forcing, or whole-workspace 100% coverage claims.

Exit criteria: focused artifact-capture tests pass; repo hygiene and
claim-boundary checks pass; full workspace tests pass; package coverage summary
records the local coverage movement and next low non-serializer surfaces.

## Phase 220 Generator Config Coverage

Status: complete for local coverage hardening. See
`docs/220-phase-generator-config-coverage-notes.md`.

Goal: harden the next reachable non-serializer public API surface after Phase
219: `crates/zkbench-core/src/generator/config.rs`.

Implemented: added focused tests in
`crates/zkbench-core/tests/generator_determinism.rs` for explicit
trace-length limit rejection, derived transition-count limit rejection,
baseline FSM state and trace requirements, branching FSM branching-factor
requirements, bounded counter loop bound requirements, and the public
`branching_factor` builder.

Coverage result: the local package coverage run moved `zkbench-core` from
`90.37%` region / `85.82%` function / `91.48%` line coverage to `90.41%`
region / `85.88%` function / `91.62%` line coverage. `generator/config.rs`
moved from `92.68%` region / `94.74%` function / `80.23%` line coverage to
`97.56%` region / `100.00%` function / `90.70%` line coverage.

Audit decision: no production source was changed. Remaining generator-config
misses are capped by the current API and validation order: all current
`FamilyKind` variants are implemented, and generic transition/trace limit
checks fail before duplicate family-specific transition/trace branches.

Anti-goals: production source changes, generator semantics changes, generated
family semantics changes, mutation semantics changes, Cargo metadata changes,
dependencies, external execution, generated artifact materialization, accepted
Evidence Ledger policy changes, formal evidence, benchmark evidence, score-axis
population, Level2+ evidence, semantic-correctness claims, production-readiness
claims, unsafe coverage forcing, coverage suppression, structurally unreachable
branch forcing, or whole-workspace 100% coverage claims.

Exit criteria: focused generator config tests pass; repo hygiene and
claim-boundary checks pass; full workspace tests pass; package coverage summary
records the local coverage movement and next low non-serializer surface.

## Phase 221 Mutation Missing Constraints Coverage

Status: complete for local coverage hardening. See
`docs/221-phase-mutation-missing-constraints-coverage-notes.md`.

Goal: harden the next reachable non-serializer public API surface after Phase
220: `crates/zkbench-core/src/mutation/missing_constraints.rs`.

Implemented: added focused tests in
`crates/zkbench-core/tests/mutation_engine.rs` for
`MissingConstraintsPass::mutation_class`, fail-closed behavior when no
rejected trace provides an eligible target, skip-ahead behavior for empty
rejected traces, and skip-ahead behavior for rejected trace steps that
reference an unknown transition before a later eligible target.

Coverage result: the local package coverage run moved `zkbench-core` from
`90.41%` region / `85.88%` function / `91.62%` line coverage to `90.44%`
region / `85.99%` function / `91.66%` line coverage.
`mutation/missing_constraints.rs` moved from `85.92%` region / `33.33%`
function / `80.43%` line coverage to `98.59%` region / `100.00%` function /
`100.00%` line coverage.

Audit decision: no production source was changed. The remaining uncovered
region is capped by the current API shape because the mutable transition lookup
uses a transition id selected from the same surface spec immediately before the
surface is cloned and edited.

Anti-goals: production source changes, mutation semantics changes, generated
family semantics changes, generator semantics changes, Cargo metadata changes,
dependencies, external execution, generated artifact materialization, accepted
Evidence Ledger policy changes, formal evidence, benchmark evidence, score-axis
population, Level2+ evidence, semantic-correctness claims, production-readiness
claims, unsafe coverage forcing, coverage suppression, structurally unreachable
branch forcing, or whole-workspace 100% coverage claims.

Exit criteria: focused mutation-engine tests pass; repo hygiene and
claim-boundary checks pass; full workspace tests pass; package coverage summary
records the local coverage movement and next low non-serializer surface.

## Phase 222 zk-Harness Mapping Coverage

Status: complete for local coverage hardening. See
`docs/222-phase-zk-harness-mapping-coverage-notes.md`.

Goal: harden the next reachable non-serializer public API surface after Phase
221: `crates/zkbench-core/src/adapters/zk_harness/mapping.rs`.

Implemented: added focused tests in
`crates/zkbench-core/tests/zk_harness_pack_mapping.rs` for current family-label
helper coverage, unsupported mutation-label helper coverage, invalid
source-pack rejection before mapping, malformed generated-instance payload
rejection, malformed mutated-instance payload rejection, missing optional
generated-instance payload rejection, unsupported mutation-class warning and
unsupported-feature recording, and non-default expected-outcome labels for
backend-error, capability-gap, and inconclusive traces.

Coverage result: the local package coverage run moved `zkbench-core` from
`90.44%` region / `85.99%` function / `91.66%` line coverage to `90.56%`
region / `86.10%` function / `91.76%` line coverage.
`adapters/zk_harness/mapping.rs` moved from `81.33%` region / `85.71%`
function / `82.05%` line coverage to `94.67%` region / `100.00%` function /
`94.36%` line coverage.

Audit decision: no production source was changed. Remaining mapping misses are
capped by the current API shape: all current `FamilyKind` variants have
candidate labels, and `compute_artifact_digest` over the concrete pack manifest
is not expected to fail during local mapping.

Anti-goals: production source changes, zk-Harness adapter semantics changes,
pack semantics changes, mutation semantics changes, generator semantics
changes, Cargo metadata changes, dependencies, external execution, generated
artifact materialization, accepted Evidence Ledger policy changes, formal
evidence, benchmark evidence, score-axis population, Level2+ evidence,
semantic-correctness claims, production-readiness claims, unsafe coverage
forcing, coverage suppression, structurally unreachable branch forcing, or
whole-workspace 100% coverage claims.

Exit criteria: focused zk-Harness mapping tests pass; repo hygiene and
claim-boundary checks pass; full workspace tests pass; package coverage summary
records the local coverage movement and next low non-serializer surface.

## Phase 223 External Submission Preflight Output Coverage

Status: complete for local coverage hardening. See
`docs/223-phase-external-submission-preflight-output-coverage-notes.md`.

Goal: harden the next reachable non-serializer public API surface after Phase
222: `crates/zkbench-core/src/evidence/external_submission_preflight_output.rs`.

Implemented: added focused tests in
`crates/zkbench-core/tests/phase_w_promotion_preflight.rs` for non-empty
output-root rejection without explicit overwrite, readback file-root rejection,
matching overwrite with a persisted overwrite-enabled preflight request,
`not retain` redaction-policy wording, invalid tampered preflight reports,
forbidden report side effects, missing report non-claim labels, forbidden
manifest side effects, manifest report-id and request-id drift, raw-retention
markers in rendered Markdown, and non-UTF-8 digest sidecars.

Coverage result: the local package coverage run moved `zkbench-core` from
`90.56%` region / `86.10%` function / `91.76%` line coverage to `90.64%`
region / `86.16%` function / `91.93%` line coverage.
`evidence/external_submission_preflight_output.rs` moved from `79.84%` region
/ `72.58%` function / `82.11%` line coverage to `81.89%` region / `74.19%`
function / `87.03%` line coverage.

Audit decision: no production source was changed. Remaining misses are mostly
filesystem error closures, serde serialization error closures for infallible
in-memory structs, portable-path helper branches not reachable through public
constants, and platform-specific path component branches.

Anti-goals: production source changes, external replay behavior changes,
endpoint submission behavior, credential handling, accepted Evidence Ledger
policy changes, generated artifact materialization, formal evidence, benchmark
evidence, score-axis population, Level2+ evidence, semantic-correctness claims,
production-readiness claims, unsafe coverage forcing, coverage suppression,
structurally unreachable branch forcing, or whole-workspace 100% coverage
claims.

Exit criteria: focused Phase W promotion-preflight tests pass; repo hygiene and
claim-boundary checks pass; full workspace tests pass; package coverage summary
records the local coverage movement and next low non-serializer surface.

## Phase 224 Report Bundle Coverage

Status: complete for local coverage hardening. See
`docs/224-phase-report-bundle-coverage-notes.md`.

Goal: harden the next reachable non-serializer public API surface after Phase
223: `crates/zkbench-core/src/report_bundle.rs`.

Implemented: added focused tests in
`crates/zkbench-core/tests/phase_q_report_bundle.rs` for empty and duplicate
identities, unsupported digest algorithms, zero-length digest metadata, missing
required local limitations, missing source references, missing inputs, missing
rendered reports, shell-like artifact references, empty rendered Markdown
payload identifiers and bodies, duplicate rendered Markdown payloads, extra
rendered Markdown payloads, regular-file output roots, syntactically invalid
output roots, non-UTF-8 manifest digest sidecars, and non-UTF-8 manifest JSON
with matching digest sidecars.

Coverage result: the local package coverage run moved `zkbench-core` from
`90.64%` region / `86.16%` function / `91.93%` line coverage to `90.82%`
region / `86.28%` function / `92.33%` line coverage. `report_bundle.rs` moved
from `86.84%` region / `79.37%` function / `82.30%` line coverage to `91.35%`
region / `82.54%` function / `92.90%` line coverage.

Audit decision: no production source was changed. Remaining misses are mostly
filesystem error closures, serde serialization error closures for infallible
in-memory structs, digest computation error closures, and platform-specific
path component branches.

Anti-goals: production source changes, report-bundle semantics changes,
external replay behavior changes, endpoint submission behavior, credential
handling, accepted Evidence Ledger policy changes, generated artifact
materialization, formal evidence, benchmark evidence, score-axis population,
Level2+ evidence, semantic-correctness claims, production-readiness claims,
unsafe coverage forcing, coverage suppression, structurally unreachable branch
forcing, or whole-workspace 100% coverage claims.

Exit criteria: focused Phase Q report-bundle tests pass; repo hygiene and
claim-boundary checks pass; full workspace tests pass; package coverage summary
records the local coverage movement and next low non-serializer surface.

## Phase 225 Soak Artifact Layout Coverage

Status: complete for local coverage hardening. See
`docs/225-phase-soak-artifact-layout-coverage-notes.md`.

Goal: harden the next reachable non-serializer surface after Phase 224:
`crates/zkbench-core/src/soak/artifact_layout.rs`.

Implemented: added focused tests in
`crates/zkbench-core/tests/phase_l_soak_campaign.rs` for report-bundle
claim-boundary drift, nested shard-plan claim-boundary drift, artifact
relative-path drift, artifact claim-boundary drift, health-report artifact
count drift, failure-corpus-index artifact count drift, file-root write
rejection, non-empty directory write rejection, invalid-bundle write rejection,
successful write/read round trip, missing bundle JSON readback rejection, and
malformed bundle JSON readback rejection.

Coverage result: the local package coverage run moved `zkbench-core` from
`90.82%` region / `86.28%` function / `92.33%` line coverage to `91.03%`
region / `86.56%` function / `92.48%` line coverage.
`soak/artifact_layout.rs` moved from `77.19%` region / `60.71%` function /
`83.81%` line coverage to `88.49%` region / `78.57%` function / `93.73%`
line coverage.

Audit decision: no production source was changed. Remaining misses are mostly
filesystem error closures, serde serialization error closures for infallible
in-memory structs, digest computation error closures, and platform-specific
path component branches.

Anti-goals: production source changes, soak artifact-layout semantics changes,
report-bundle semantics changes, external replay behavior changes, endpoint
submission behavior, credential handling, accepted Evidence Ledger policy
changes, generated artifact materialization, formal evidence, benchmark
evidence, score-axis population, Level2+ evidence, semantic-correctness claims,
production-readiness claims, unsafe coverage forcing, coverage suppression,
structurally unreachable branch forcing, or whole-workspace 100% coverage
claims.

Exit criteria: focused Phase L soak-campaign tests pass; repo hygiene and
claim-boundary checks pass; full workspace tests pass; package coverage summary
records the local coverage movement and next low non-serializer surface.

## Phase 226 Observation Omission Coverage

Status: complete for local coverage hardening. See
`docs/226-phase-observation-omission-coverage-notes.md`.

Goal: harden the next reachable non-serializer surface after Phase 225:
`crates/zkbench-core/src/mutation/observation_omission.rs`.

Implemented: added focused tests in
`crates/zkbench-core/tests/phase_156_mutation_depth.rs` for no-observation
fail-closed rejection, no-trace fail-closed rejection after an observation
target exists, accepted-trace rewrite behavior, rejected-trace fallback rewrite
behavior, observation removal, sentinel final-field mismatch injection, and
diagnostic-note preservation.

Coverage result: the local package coverage run moved `zkbench-core` from
`91.03%` region / `86.56%` function / `92.48%` line coverage to `91.06%`
region / `86.67%` function / `92.51%` line coverage.
`mutation/observation_omission.rs` moved from `87.50%` region / `57.14%`
function / `83.33%` line coverage to `96.59%` region / `85.71%` function /
`95.45%` line coverage.

Audit decision: no production source was changed. Remaining misses are capped
by the current helper shape around in-slice trace replacement and validation
composition.

Anti-goals: production source changes, mutation semantics changes, oracle
semantics changes, generator semantics changes, external replay behavior
changes, endpoint submission behavior, credential handling, accepted Evidence
Ledger policy changes, generated artifact materialization, formal evidence,
benchmark evidence, score-axis population, Level2+ evidence,
semantic-correctness claims, production-readiness claims, unsafe coverage
forcing, coverage suppression, structurally unreachable branch forcing, or
whole-workspace 100% coverage claims.

Exit criteria: focused Phase 156 mutation-depth tests pass; repo hygiene and
claim-boundary checks pass; full workspace tests pass; package coverage summary
records the local coverage movement and next low non-serializer surface.

## Phase 227 Result Import Coverage

Status: complete for local coverage hardening. See
`docs/227-phase-result-import-coverage-notes.md`.

Goal: harden the next reachable non-serializer surface after Phase 226:
`crates/zkbench-core/src/external_runner/result_import.rs`.

Implemented: added focused tests in
`crates/zkbench-core/tests/result_import_validation.rs` for schema drift,
candidate identity/status/path/provenance rejection, metric and note forbidden
claim text, policy-controlled validation toggles, and direct quarantine-record
context.

Coverage result: the local package coverage run moved `zkbench-core` from
`91.06%` region / `86.67%` function / `92.51%` line coverage to `91.15%`
region / `86.73%` function / `92.66%` line coverage.
`external_runner/result_import.rs` moved from `87.39%` region / `88.89%`
function / `83.61%` line coverage to `97.83%` region / `100.00%` function /
`97.95%` line coverage.

Audit decision: no production source was changed. Remaining misses are limited
to currently unforced local branch combinations inside the result-import
validation helpers.

Anti-goals: production source changes, result-import semantics changes,
quarantine semantics changes, external replay behavior changes, endpoint
submission behavior, credential handling, accepted Evidence Ledger policy
changes, generated artifact materialization, formal evidence, benchmark
evidence, score-axis population, Level2+ evidence, semantic-correctness
claims, production-readiness claims, unsafe coverage forcing, coverage
suppression, structurally unreachable branch forcing, or whole-workspace 100%
coverage claims.

Exit criteria: focused result-import validation tests pass; repo hygiene and
claim-boundary checks pass; full workspace tests pass; package coverage summary
records the local coverage movement and next low non-serializer surface.

## Phase 228 Append Preview Coverage

Status: complete for local coverage hardening. See
`docs/228-phase-append-preview-coverage-notes.md`.

Goal: harden the next reachable non-serializer surface after Phase 227:
`crates/zkbench-core/src/evidence/append_preview.rs`.

Implemented: added focused tests in
`crates/zkbench-core/tests/evidence_append_preview.rs` for invalid-candidate
creation rejection, empty preview/source ids, preview and proposed-entry
claim-boundary drift, forbidden claim text in preview and transaction notes,
and malformed preview JSON.

Coverage result: the local package coverage run moved `zkbench-core` from
`91.15%` region / `86.73%` function / `92.66%` line coverage to `91.22%`
region / `86.79%` function / `92.75%` line coverage.
`evidence/append_preview.rs` moved from `88.79%` region / `88.24%` function /
`83.87%` line coverage to `96.41%` region / `94.12%` function / `94.47%`
line coverage.

Audit decision: no production source was changed. Remaining misses are limited
to currently unforced local branch combinations inside append-preview
projection and serialization helpers.

Anti-goals: production source changes, append-preview semantics changes,
candidate semantics changes, external replay behavior changes, endpoint
submission behavior, credential handling, accepted Evidence Ledger policy
changes, generated artifact materialization, formal evidence, benchmark
evidence, score-axis population, Level2+ evidence, semantic-correctness
claims, production-readiness claims, unsafe coverage forcing, coverage
suppression, structurally unreachable branch forcing, or whole-workspace 100%
coverage claims.

Exit criteria: focused append-preview validation tests pass; repo hygiene and
claim-boundary checks pass; full workspace tests pass; package coverage summary
records the local coverage movement and next low non-serializer surface.

## Phase 229 Pack Readiness Coverage

Status: complete for local coverage hardening. See
`docs/229-phase-pack-readiness-coverage-notes.md`.

Goal: harden the next reachable non-serializer surface after Phase 228:
`crates/zkbench-core/src/pack/readiness.rs`.

Implemented: added focused tests in
`crates/zkbench-core/tests/phase_o_pack_readiness.rs` for malformed readiness
JSON, missing and malformed readback files, empty identity fields, invalid
digest and artifact refs, check boundary escalation, and missing inputs.

Coverage result: the local package coverage run moved `zkbench-core` from
`91.22%` region / `86.79%` function / `92.75%` line coverage to `91.38%`
region / `87.02%` function / `92.97%` line coverage.
`pack/readiness.rs` moved from `84.18%` region / `74.47%` function / `86.24%`
line coverage to `90.60%` region / `82.98%` function / `94.19%` line
coverage.

Audit decision: no production source was changed. Remaining misses are limited
to currently unforced local branch combinations inside pack-readiness output
writing, helper mapping, and filesystem error paths.

Anti-goals: production source changes, pack-readiness semantics changes, pack
writer/reader semantics changes, external replay behavior changes, endpoint
submission behavior, credential handling, accepted Evidence Ledger policy
changes, generated artifact materialization, formal evidence, benchmark
evidence, score-axis population, Level2+ evidence, semantic-correctness
claims, production-readiness claims, unsafe coverage forcing, coverage
suppression, structurally unreachable branch forcing, or whole-workspace 100%
coverage claims.

Exit criteria: focused pack-readiness tests pass; repo hygiene and
claim-boundary checks pass; full workspace tests pass; package coverage summary
records the local coverage movement and next low non-serializer surface.

## Phase 230 Audit Index Coverage

Status: complete for local coverage hardening. See
`docs/230-phase-audit-index-coverage-notes.md`.

Goal: harden the next reachable non-serializer surface after Phase 229:
`crates/zkbench-core/src/audit_index.rs`.

Implemented: added focused tests in
`crates/zkbench-core/tests/phase_r_audit_index.rs` for malformed audit-index
JSON, empty identities, duplicate input and artifact refs, missing limitation
labels, missing inputs, file roots, missing readback files, non-UTF-8
sidecars/manifests, and digest-consistent invalid manifests.

Coverage result: the local package coverage run moved `zkbench-core` from
`91.38%` region / `87.02%` function / `92.97%` line coverage to `91.51%`
region / `87.19%` function / `93.20%` line coverage.
`audit_index.rs` moved from `83.71%` line coverage to `85.51%` region /
`74.07%` function / `86.49%` line coverage.

Audit decision: no production source was changed. Remaining misses are
concentrated in Phase S/Phase T materialized-view readback and protected-path
branch combinations, cross-bundle grouping/sorting variants, and filesystem
error paths.

Anti-goals: production source changes, audit-index semantics changes,
audit-index ergonomics semantics changes, cross-bundle audit-index semantics
changes, pack writer/reader semantics changes, external replay behavior
changes, endpoint submission behavior, credential handling, accepted Evidence
Ledger policy changes, generated artifact materialization, formal evidence,
benchmark evidence, score-axis population, Level2+ evidence,
semantic-correctness claims, production-readiness claims, unsafe coverage
forcing, coverage suppression, structurally unreachable branch forcing, or
whole-workspace 100% coverage claims.

Exit criteria: focused audit-index tests pass; repo hygiene and claim-boundary
checks pass; full workspace tests pass; package coverage summary records the
local coverage movement and next low non-serializer surface.

## Phase 231 Accepted Append Output Coverage

Status: complete for local coverage hardening. See
`docs/231-phase-accepted-append-output-coverage-notes.md`.

Goal: harden the next reachable non-serializer surface after Phase 230:
`crates/zkbench-core/src/evidence/accepted_append_output.rs`.

Implemented: added focused root-path rejection coverage in
`crates/zkbench-core/tests/phase_184_accepted_append_output_coverage.rs` for
materialized accepted-ledger append requests.

Coverage result: the local package coverage run moved `zkbench-core` from
`91.51%` region / `87.19%` function / `93.20%` line coverage to `91.53%`
region / `87.24%` function / `93.21%` line coverage.
`evidence/accepted_append_output.rs` moved from `78.95%` region / `57.14%`
function / `86.36%` line coverage to `82.24%` region / `64.29%` function /
`90.00%` line coverage.

Audit decision: no production source was changed. Remaining misses are the
internal `write_ledger_atomically` parent/file-name error closures, which are
unreachable through the public API because `validate_ledger_path` rejects
non-materializable paths before atomic writing starts.

Anti-goals: production source changes, accepted-append semantics changes,
accepted-append output semantics changes, endpoint submission behavior,
credential handling, accepted Evidence Ledger policy changes, generated
artifact materialization, formal evidence, benchmark evidence, score-axis
population, Level2+ evidence, semantic-correctness claims, production-readiness
claims, unsafe coverage forcing, coverage suppression, structurally unreachable
branch forcing, or whole-workspace 100% coverage claims.

Exit criteria: focused accepted-append-output tests pass; repo hygiene and
claim-boundary checks pass; full workspace tests pass; package coverage summary
records the local coverage movement and next low non-serializer surface.

## Phase 232 DSL IR Coverage

Status: complete for local coverage hardening. See
`docs/232-phase-dsl-ir-coverage-notes.md`.

Goal: harden the next reachable non-serializer surface after Phase 231:
`crates/zkbench-core/src/dsl/ir.rs`.

Implemented: added focused present/missing field lookup coverage in
`crates/zkbench-core/tests/lowering.rs` for `SemanticIr::field()`.

Coverage result: the local package coverage run moved `zkbench-core` from
`91.53%` region / `87.24%` function / `93.21%` line coverage to `91.55%`
region / `87.36%` function / `93.23%` line coverage. `dsl/ir.rs` moved from
`84.62%` region / `75.00%` function / `85.19%` line coverage to `100.00%`
region / `100.00%` function / `100.00%` line coverage.

Audit decision: no production source was changed. The missing-line audit showed
that the only uncovered executable path in `dsl/ir.rs` was the public
`SemanticIr::field()` lookup helper.

Anti-goals: production source changes, DSL semantics changes, lowering
semantics changes, oracle semantics changes, endpoint submission behavior,
credential handling, accepted Evidence Ledger policy changes, generated
artifact materialization, formal evidence, benchmark evidence, score-axis
population, Level2+ evidence, semantic-correctness claims, production-readiness
claims, unsafe coverage forcing, coverage suppression, structurally unreachable
branch forcing, or whole-workspace 100% coverage claims.

Exit criteria: focused lowering tests pass; repo hygiene and claim-boundary
checks pass; full workspace tests pass; package coverage summary records the
local coverage movement and next low non-serializer surface.

## Phase 233 Review Ledger Coverage

Status: complete for local coverage hardening. See
`docs/233-phase-review-ledger-coverage-notes.md`.

Goal: harden the next reachable non-serializer surface after Phase 232:
`crates/zkbench-core/src/evidence/review_ledger.rs`.

Implemented: added focused review-ledger coverage in
`crates/zkbench-core/tests/review_ledger.rs` for default construction,
malformed ledger JSON, invalid nested review-decision append rejection, empty
ledger id, entry sequence drift, previous-digest drift, and nested
review-decision/append-preview validation drift.

Coverage result: the local package coverage run moved `zkbench-core` from
`91.55%` region / `87.36%` function / `93.23%` line coverage to `91.65%`
region / `87.47%` function / `93.34%` line coverage.
`evidence/review_ledger.rs` moved from `85.23%` region / `84.21%` function /
`85.27%` line coverage to `94.70%` region / `94.74%` function / `97.32%` line
coverage.

Audit decision: no production source was changed. Remaining misses are the
digest serialization error path and pretty-JSON serialization wrapper path,
which are not forced through the public serializable review-ledger data model.

Anti-goals: production source changes, review-ledger semantics changes,
EvidenceLedger mutation, accepted Evidence Ledger policy changes, endpoint
submission behavior, credential handling, generated artifact materialization,
formal evidence, benchmark evidence, score-axis population, Level2+ evidence,
semantic-correctness claims, production-readiness claims, unsafe coverage
forcing, coverage suppression, structurally unreachable branch forcing, or
whole-workspace 100% coverage claims.

Exit criteria: focused review-ledger tests pass; repo hygiene and
claim-boundary checks pass; full workspace tests pass; package coverage summary
records the local coverage movement and next low non-serializer surface.

## Phase 234 Invariant Weakening Coverage

Status: complete for local coverage hardening. See
`docs/234-phase-invariant-weakening-coverage-notes.md`.

Goal: harden the next reachable non-serializer surface after Phase 233:
`crates/zkbench-core/src/mutation/invariant_weakening.rs`.

Implemented: added focused mutation-depth coverage in
`crates/zkbench-core/tests/phase_156_mutation_depth.rs` for
`InvariantWeakeningPass::mutation_class()` and the eligible-invariant/no-trace
failure path.

Coverage result: the local package coverage run moved `zkbench-core` from
`91.65%` region / `87.47%` function / `93.34%` line coverage to `91.67%`
region / `87.59%` function / `93.37%` line coverage.
`mutation/invariant_weakening.rs` moved from `87.30%` region / `60.00%`
function / `85.71%` line coverage to `98.41%` region / `100.00%` function /
`100.00%` line coverage.

Audit decision: no production source was changed. `invariant_weakening.rs` has
no remaining missed lines in the local coverage report; one region remains
unexecuted without forcing artificial behavior beyond the current public
generated-instance API.

Anti-goals: production source changes, mutation semantics changes, generator
semantics changes, oracle semantics changes, accepted Evidence Ledger mutation,
accepted Evidence Ledger policy changes, endpoint submission behavior,
credential handling, generated artifact materialization, formal evidence,
benchmark evidence, score-axis population, Level2+ evidence,
semantic-correctness claims, production-readiness claims, unsafe coverage
forcing, coverage suppression, structurally unreachable branch forcing, or
whole-workspace 100% coverage claims.

Exit criteria: focused mutation-depth tests pass; repo hygiene and
claim-boundary checks pass; full workspace tests pass; package coverage summary
records the local coverage movement and next low non-serializer surface.

## Phase 235 External Runner Policy Coverage

Status: complete for local coverage hardening. See
`docs/235-phase-external-runner-policy-coverage-notes.md`.

Goal: harden the next reachable non-serializer surface after Phase 234:
`crates/zkbench-core/src/external_runner/policy.rs`.

Implemented: added focused external-runner policy coverage in
`crates/zkbench-core/tests/external_runner_policy.rs` for the Phase H default
and manual-handoff policy helpers, empty policy id validation, elevated policy
claim-boundary validation, claim-boundary-policy mismatch validation, missing
manual-review gate validation, and absolute-path flag validation.

Coverage result: the local package coverage run moved `zkbench-core` from
`91.67%` region / `87.59%` function / `93.37%` line coverage to `91.72%`
region / `87.64%` function / `93.47%` line coverage.
`external_runner/policy.rs` moved from `91.18%` region / `93.75%` function /
`85.78%` line coverage to `98.82%` region / `100.00%` function / `97.63%`
line coverage.

Audit decision: no production source was changed. The remaining missed lines
are the explicit Level2+ actual-claim rejection branch, which is structurally
capped by the public Phase H claim-boundary guard before validator reachability;
this tranche does not force that branch by weakening the guard or adding
test-only entry points.

Anti-goals: production source changes, external-runner policy semantics
changes, live external execution behavior, endpoint submission behavior,
credential handling, generated artifact materialization, accepted Evidence
Ledger mutation, accepted Evidence Ledger policy changes, formal evidence,
benchmark evidence, score-axis population, Level2+ evidence,
semantic-correctness claims, production-readiness claims, unsafe coverage
forcing, coverage suppression, structurally unreachable branch forcing, or
whole-workspace 100% coverage claims.

Exit criteria: focused external-runner policy tests pass; repo hygiene and
claim-boundary checks pass; full workspace tests pass; package coverage summary
records the local coverage movement and next low non-serializer surface.

## Phase 236 Soak Campaign Coverage

Status: complete for local coverage hardening. See
`docs/236-phase-soak-campaign-coverage-notes.md`.

Goal: harden the next reachable non-serializer surface after Phase 235:
`crates/zkbench-core/src/soak/campaign.rs`.

Implemented: added focused soak-campaign coverage in
`crates/zkbench-core/tests/phase_l_soak_campaign.rs` for empty campaign id
validation, campaign report-bundle write failure propagation, pack-write
failures without retained failure packs, and retained failure-pack reproduction
bundle attachment. Added the bounded public
`run_soak_campaign_with_local_json_adapter` helper so the retained failure-pack
path is testable through a real approved local campaign surface.

Coverage result: the local package coverage run moved `zkbench-core` from
`91.72%` region / `87.64%` function / `93.47%` line coverage to `91.83%`
region / `87.71%` function / `93.56%` line coverage. `soak/campaign.rs` moved
from `85.42%` region / `90.91%` function / `85.79%` line coverage to `96.15%`
region / `100.00%` function / `97.49%` line coverage.

Audit decision: the remaining missed lines are defensive error returns from
internally constructed artifact manifests and the retained-failure-pack-without
matching-corpus-entry guard. This tranche does not weaken campaign id, shard id,
artifact-layout, or runner corpus invariants to force those branches.

Anti-goals: live external execution behavior, non-local adapter execution,
endpoint submission behavior, credential handling, generated benchmark artifact
claims, accepted Evidence Ledger mutation, accepted Evidence Ledger policy
changes, formal evidence, benchmark evidence, score-axis population, Level2+
evidence, semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, unsafe coverage forcing, coverage suppression,
structurally unreachable branch forcing, or whole-workspace 100% coverage
claims.

Exit criteria: focused soak-campaign tests pass; repo hygiene and
claim-boundary checks pass; full workspace tests pass; package coverage summary
records the local coverage movement and next low non-serializer surface.

## Phase 237 Invariant Strengthening Coverage

Status: complete for local coverage hardening. See
`docs/237-phase-invariant-strengthening-coverage-notes.md`.

Goal: harden the next reachable non-serializer surface after Phase 236:
`crates/zkbench-core/src/mutation/invariant_strengthening.rs`.

Implemented: added focused mutation-depth coverage in
`crates/zkbench-core/tests/phase_156_mutation_depth.rs` for
`InvariantStrengtheningPass::mutation_class()` and the
eligible-invariant/no-trace failure path.

Coverage result: the local package coverage run moved `zkbench-core` from
`91.83%` region / `87.71%` function / `93.56%` line coverage to `91.86%`
region / `87.83%` function / `93.59%` line coverage.
`mutation/invariant_strengthening.rs` moved from `87.88%` region / `60.00%`
function / `86.00%` line coverage to `98.48%` region / `100.00%` function /
`100.00%` line coverage.

Audit decision: no production source was changed.
`mutation/invariant_strengthening.rs` has no remaining missed lines in the
local coverage report; one region remains unexecuted without forcing artificial
behavior beyond the current generated-instance API.

Anti-goals: production source changes, mutation semantics changes, generator
semantics changes, oracle semantics changes, accepted Evidence Ledger mutation,
accepted Evidence Ledger policy changes, endpoint submission behavior,
credential handling, generated artifact materialization, formal evidence,
benchmark evidence, score-axis population, Level2+ evidence,
semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, unsafe coverage forcing, coverage suppression,
structurally unreachable branch forcing, or whole-workspace 100% coverage
claims.

Exit criteria: focused mutation-depth tests pass; repo hygiene and
claim-boundary checks pass; full workspace tests pass; package coverage summary
records the local coverage movement and next low non-serializer surface.

## Phase 238 Recursion Envelope Mismatch Coverage

Status: complete for local coverage hardening. See
`docs/238-phase-recursion-envelope-mismatch-coverage-notes.md`.

Goal: harden the next reachable non-serializer surface after Phase 237:
`crates/zkbench-core/src/mutation/recursion_envelope_mismatch.rs`.

Implemented: added focused mutation-completion coverage in
`crates/zkbench-core/tests/phase_161_mutation_completion.rs` for
`RecursionEnvelopeMismatchPass::mutation_class()`, no-declared-trace failure,
no-loop-after-trace-selection failure, and prior-envelope-digest fallback
metadata recording.

Coverage result: the local package coverage run moved `zkbench-core` from
`91.86%` region / `87.83%` function / `93.59%` line coverage to `91.90%`
region / `88.00%` function / `93.62%` line coverage.
`mutation/recursion_envelope_mismatch.rs` moved from `84.00%` region /
`50.00%` function / `86.44%` line coverage to `98.67%` region / `100.00%`
function / `100.00%` line coverage.

Audit decision: no production source was changed.
`mutation/recursion_envelope_mismatch.rs` has no remaining missed lines or
missed functions in the local coverage report; one defensive region remains
unexecuted without corrupting the internal loop-id selection invariant.

Anti-goals: production source changes, mutation semantics changes, generator
semantics changes, oracle semantics changes, accepted Evidence Ledger mutation,
accepted Evidence Ledger policy changes, endpoint submission behavior,
credential handling, generated artifact materialization, formal evidence,
benchmark evidence, score-axis population, Level2+ evidence,
semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, unsafe coverage forcing, coverage suppression,
structurally unreachable branch forcing, or whole-workspace 100% coverage
claims.

Exit criteria: focused mutation-completion tests pass; repo hygiene and
claim-boundary checks pass; full workspace tests pass; package coverage summary
records the local coverage movement and next low non-serializer surface.

## Phase 239 Evidence Ledger Coverage

Status: complete for local coverage hardening. See
`docs/239-phase-evidence-ledger-coverage-notes.md`.

Goal: harden the next reachable non-serializer surface after Phase 238:
`crates/zkbench-core/src/evidence/ledger.rs`.

Implemented: added focused Evidence Ledger coverage in
`crates/zkbench-core/tests/evidence_ledger.rs` for `EvidenceLedger::default()`,
filesystem save/load error wrapping, malformed JSON deserialization,
sequence-number, previous-digest, and cached-summary validation drift, and
explicit nonclaim text handling.

Coverage result: the local package coverage run moved `zkbench-core` from
`91.90%` region / `88.00%` function / `93.62%` line coverage to `91.99%`
region / `88.17%` function / `93.71%` line coverage. `evidence/ledger.rs`
moved from `84.73%` region / `76.19%` function / `86.78%` line coverage to
`94.27%` region / `90.48%` function / `96.04%` line coverage.

Audit decision: no production source was changed. Remaining missed lines are
serialization-error branches inside digest/save helpers and the private docs-
only class marker; this tranche does not introduce fake non-serializable data,
test-only production hooks, or dead-code forcing.

Anti-goals: production source changes, Evidence Ledger policy changes, accepted
Evidence Ledger mutation, accepted evidence state changes, endpoint submission
behavior, credential handling, generated artifact materialization, formal
evidence, benchmark evidence, score-axis population, Level2+ evidence,
semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, unsafe coverage forcing, coverage suppression,
structurally unreachable branch forcing, or whole-workspace 100% coverage
claims.

Exit criteria: focused Evidence Ledger tests pass; repo hygiene and
claim-boundary checks pass; full workspace tests pass; package coverage summary
records the local coverage movement and next low non-serializer surface.

## Phase 240 zk-Harness Export Coverage Audit

Status: complete as an audit-only coverage tranche. See
`docs/240-phase-zk-harness-export-coverage-audit-notes.md`.

Goal: audit the next apparent low non-serializer surface after Phase 239:
`crates/zkbench-core/src/adapters/zk_harness/export.rs`.

Implemented: no Rust source or test changes. The missing-line audit found only
serialization error wrappers for serializable manifest and dry-run plan types.

Coverage state: `adapters/zk_harness/export.rs` remains at `80.95%` region /
`80.00%` function / `86.96%` line coverage. The local `zkbench-core` package
summary after Phase 239 remains `91.99%` region / `88.17%` function / `93.71%`
line coverage.

Audit decision: forcing the remaining serialization-error closures would
require fake non-serializable data, production test hooks, or serializer
indirection. This tranche records the cap and routes to the next candidate
instead.

Anti-goals: production source changes, test-only serializer hooks, fake
non-serializable zk-Harness data, live zk-Harness execution, endpoint submission
behavior, credential handling, generated artifact materialization, formal
evidence, benchmark evidence, score-axis population, Level2+ evidence,
semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, unsafe coverage forcing, coverage suppression,
structurally unreachable branch forcing, or whole-workspace 100% coverage
claims.

Exit criteria: missing-line audit is recorded; repo hygiene and claim-boundary
checks remain green; next low non-serializer surface is routed.

## Phase 241 Audit Index Coverage

Status: complete. See `docs/241-phase-audit-index-coverage-notes.md`.

Goal: harden the next reachable non-serializer surface after Phase 240:
`crates/zkbench-core/src/audit_index.rs`.

Implemented: focused Phase S and Phase T audit-index tests for filter, sort,
group, signal, source-id validation, invalid root, protected-path, file-root,
readback encoding, digest-consistent drift, and materialized Markdown/view
failure paths.

Coverage result: `audit_index.rs` moved from `85.51%` region / `74.07%`
function / `86.49%` line coverage to `91.14%` region / `85.19%` function /
`93.14%` line coverage. The local `zkbench-core` package summary moved from
`91.99%` region / `88.17%` function / `93.71%` line coverage to `92.50%`
region / `89.02%` function / `94.26%` line coverage.

Residual cap: remaining misses are mostly serialization-error wrappers,
overwrite mismatch branches that are not reachable without violating
deterministic readback assumptions, filesystem error edges, and validation
branches that require impossible digest or claim-boundary states under current
public constructors.

Anti-goals: production source changes, audit-index semantics changes, accepted
Evidence Ledger mutation, accepted evidence state changes, endpoint submission
behavior, credential handling, generated artifact materialization, formal
evidence, benchmark evidence, score-axis population, Level2+ evidence,
semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, unsafe coverage forcing, coverage suppression,
structurally unreachable branch forcing, or whole-workspace 100% coverage
claims.

Exit criteria: focused Phase S/T audit-index tests pass; repo hygiene and
claim-boundary checks remain green; full workspace tests pass; package coverage
summary records the local coverage movement and next low non-serializer
surface.

## Phase 242 Failure Corpus Coverage

Status: complete. See `docs/242-phase-failure-corpus-coverage-notes.md`.

Goal: harden the next reachable non-serializer surface after Phase 241:
`crates/zkbench-core/src/soak/failure_corpus.rs`.

Implemented: focused failure-corpus tests for index claim-boundary escalation,
empty entry ids, entry and reproduction-manifest claim-boundary escalation,
valid portable artifact refs, and absolute, parent-directory, and backslash
artifact-ref rejection paths.

Coverage result: `soak/failure_corpus.rs` moved from `93.89%` region /
`100.00%` function / `86.54%` line coverage to `100.00%` region /
`100.00%` function / `100.00%` line coverage. The local `zkbench-core`
package summary moved from `92.50%` region / `89.02%` function / `94.26%`
line coverage to `92.54%` region / `89.02%` function / `94.37%` line
coverage.

Anti-goals: production source changes, soak semantics changes, accepted
Evidence Ledger mutation, accepted evidence state changes, endpoint submission
behavior, credential handling, generated artifact materialization, formal
evidence, benchmark evidence, score-axis population, Level2+ evidence,
semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, unsafe coverage forcing, coverage suppression,
structurally unreachable branch forcing, or whole-workspace 100% coverage
claims.

Exit criteria: focused failure-corpus tests pass; repo hygiene and
claim-boundary checks remain green; full workspace tests pass; package coverage
summary records the local coverage movement and next low non-serializer
surface.

## Phase 243 Pack Writer Coverage

Status: complete. See `docs/243-phase-pack-writer-coverage-notes.md`.

Goal: harden the next reachable non-serializer surface after Phase 242:
`crates/zkbench-core/src/pack/writer.rs`.

Implemented: focused benchmark-pack writer tests for file-root rejection, root
parent conflicts, README path conflicts, dynamic artifact id path drift for
generated instances, mutated instances, replay manifests, and replay results,
plus parent-conflict reporting for generated, mutated, replay, evidence, and
score-report artifact families.

Coverage result: `pack/writer.rs` moved from `82.96%` region / `80.56%`
function / `86.91%` line coverage to `90.86%` region / `88.89%` function /
`92.62%` line coverage. The local `zkbench-core` package summary moved from
`92.54%` region / `89.02%` function / `94.37%` line coverage to `92.66%`
region / `89.19%` function / `94.44%` line coverage.

Residual cap: remaining misses are serialization-error wrappers for currently
serializable pack-manifest and JSON artifact values, plus low-level file-write
or read-dir operating-system error wrappers that would require brittle
permission or filesystem forcing.

Anti-goals: production source changes, pack writer semantics changes, accepted
Evidence Ledger mutation, accepted evidence state changes, endpoint submission
behavior, credential handling, generated artifact materialization beyond temp
test dirs, formal evidence, benchmark evidence, score-axis population, Level2+
evidence, semantic-correctness claims, production-readiness claims, SOTA
claims, breakthrough claims, unsafe coverage forcing, coverage suppression,
structurally unreachable branch forcing, or whole-workspace 100% coverage
claims.

Exit criteria: focused benchmark-pack writer tests pass; repo hygiene and
claim-boundary checks remain green; full workspace tests pass; package coverage
summary records the local coverage movement and next low non-serializer
surface.

## Phase 244 External Submission Preflight Output Coverage

Status: complete. See
`docs/244-phase-external-submission-preflight-output-coverage-notes.md`.

Goal: harden the next reachable non-serializer surface after Phase 243:
`crates/zkbench-core/src/evidence/external_submission_preflight_output.rs`.

Implemented: focused Phase W external replay preflight output tests for each
stale digest sidecar rejection path and malformed redaction-report and
submission-package digest-summary JSON deserialization context.

Coverage result: `evidence/external_submission_preflight_output.rs` moved from
`81.89%` region / `74.19%` function / `87.03%` line coverage to `83.45%`
region / `77.42%` function / `88.60%` line coverage. The local `zkbench-core`
package summary moved from `92.66%` region / `89.19%` function / `94.44%`
line coverage to `92.72%` region / `89.31%` function / `94.50%` line
coverage.

Residual cap: remaining misses are mostly output-root guards, write-side OS
wrappers, serialization-error wrappers for currently serializable local output
data, private relative-path guards over constant paths, directory iteration OS
wrappers, symlink rejection branches, current-directory wrappers, and
path-normalization platform branches.

Anti-goals: production source changes, preflight output semantics changes,
accepted Evidence Ledger mutation, accepted evidence state changes, endpoint
submission behavior, credential handling, generated artifact materialization
beyond temp test dirs, formal evidence, benchmark evidence, score-axis
population, Level2+ evidence, semantic-correctness claims, production-readiness
claims, SOTA claims, breakthrough claims, unsafe coverage forcing, coverage
suppression, structurally unreachable branch forcing, or whole-workspace 100%
coverage claims.

Exit criteria: focused Phase W promotion-preflight tests pass; repo hygiene and
claim-boundary checks remain green; full workspace tests pass; package coverage
summary records the local coverage movement and next low non-serializer
surface.

## Phase 245 Bad Counters Coverage

Status: complete. See `docs/245-phase-bad-counters-coverage-notes.md`.

Goal: harden the next reachable non-serializer surface after Phase 244:
`crates/zkbench-core/src/mutation/bad_counters.rs`.

Implemented: focused mutation-engine tests for `BadCountersPass` class
metadata and skipping an accepted trace step whose transition id is absent
before finding a later eligible counter update target.

Coverage result: `mutation/bad_counters.rs` moved from `90.65%` region /
`50.00%` function / `87.14%` line coverage to `94.39%` region / `75.00%`
function / `92.86%` line coverage. The local `zkbench-core` package summary
moved from `92.72%` region / `89.31%` function / `94.50%` line coverage to
`92.74%` region / `89.36%` function / `94.51%` line coverage.

Residual cap: remaining misses are the defensive action-index drift wrapper and
the fallback affected-field match arm that is unreachable through the current
`bad_counter_action` selector.

Anti-goals: production source changes, mutation semantics changes, accepted
Evidence Ledger mutation, accepted evidence state changes, endpoint submission
behavior, credential handling, generated artifact materialization, formal
evidence, benchmark evidence, score-axis population, Level2+ evidence,
semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, unsafe coverage forcing, coverage suppression,
structurally unreachable branch forcing, test-only hooks, or whole-workspace
100% coverage claims.

Exit criteria: focused mutation-engine tests pass; repo hygiene and
claim-boundary checks remain green; full workspace tests pass; package coverage
summary records the local coverage movement and next low non-serializer
surface.

## Phase 246 HSAI Public Proof Refresh

Status: complete. See `docs/246-hsai-public-proof-refresh.md`.

Goal: convert the current green public state into a bounded public proof
refresh before stronger SOTA-bridge evidence work starts.

Proof target: commit `977d198c3a12f3161580c2c580aa8218e85b900a`, validated
Phases 204-245, and current `origin/master` state.

Implemented: a docs-only public proof refresh naming the exact verifier
commands that passed, the current `zkbench-core` coverage summary, the
validated local gateway and Level 1 Rust surfaces, reproduction steps,
buyer-facing wording, nonclaims, and the next evidence bridge:
Phase 247 local gateway demo bundle, Phase 248 first real external evidence
lane, Phase 249 accepted evidence promotion, and Phase 250 public baseline
comparison.

Nonclaims: no production readiness, semantic correctness, SOTA status,
breakthrough status, model execution, hosted model behavior, live provider
evidence, verifier-agent runtime behavior, external replay, accepted Evidence
Ledger mutation, score-axis population, official benchmark evidence, Level2+
evidence, live baseline execution, deployment safety, global software-agent
uniqueness, full security, or claim above `Attested`.

Exit criteria: the current green head is named; exact verifier commands are
listed; reproduction steps are bounded; buyer-facing wording remains honest;
claim-boundary checks remain green.

## Phase 247 HSAI Gateway Local Demo Bundle Run

Status: complete. See `docs/247-hsai-gateway-local-demo-bundle-run.md`.

Goal: produce and record a concrete local gateway demo bundle under the ignored
`.gateway-demo-runs/` root without committing generated bundle contents or
inflating the public claim.

Implemented: ran the existing Phase 215 `gateway_demo_report` example with
fixed acknowledgement, fixed bundle id `phase-247-gateway-demo`, fixed
timestamp `0`, and ignored output root
`.gateway-demo-runs/phase-247-gateway-demo`; verified the declared
`gateway-report/*` files, ignored status, primary file digests, summary metrics,
and `authority_granted=false`.

Result: the local demo produced 14 cases, 1 accepted benign control, 13
rejected unsafe cases, 0 quarantined cases, 13 unsafe actions blocked, 0 false
rejections, 14 recomputation agreements, and a complete audit bundle.

Nonclaims: no production readiness, semantic correctness, SOTA status,
breakthrough status, model execution, hosted model behavior, live provider
evidence, verifier-agent runtime behavior, external replay, accepted Evidence
Ledger mutation, score-axis population, official benchmark evidence, Level2+
evidence, live baseline execution, deployment safety, global software-agent
uniqueness, full security, or claim above `Attested`.

Exit criteria: ignored demo bundle exists locally; generated files are not
committed; exact run command and digests are recorded; claim-boundary checks
remain green.

## Phase 248 HSAI First Real External Evidence Lane

Status: complete. See
`docs/248-hsai-first-real-external-evidence-lane.md`.

Goal: connect the local HSAI Gateway demo/report stack to the already-existing
real/operator external-evidence surfaces without promoting the claim beyond the
evidence.

Implemented: a bounded public evidence-lane map naming the Phase 247 gateway
demo surface, the Phase 57 HSAI-owned Phala/dstack real fixture, the Phase 106
operator-only Phala Cloud API materialization path, the Phase 108 local QVL
artifact path, the Phase 109 managed JWKS artifact path, and the Phase 113 TLS
channel artifact path. The artifact states what the gateway can rely on
tangibly, what remains missing before accepted external gateway evidence, exact
reproduction checks, buyer-facing wording, and explicit nonclaims.

Nonclaims: no production readiness, semantic correctness, SOTA status,
breakthrough status, live gateway execution, live model behavior,
verifier-agent runtime behavior, accepted Evidence Ledger mutation,
score-axis population, official benchmark evidence, Level2+ evidence, live
baseline execution, deployment safety, global software-agent uniqueness, full
security, or claim above `Attested`.

Exit criteria: public evidence-lane map exists; current external-evidence
surfaces are named; the gateway-to-attestation binding gap is explicit;
claim-boundary checks remain green.

## Phase 249 HSAI Gateway-To-Attestation Binding

Status: complete. See
`docs/249-hsai-gateway-attestation-binding-notes.md`.

Goal: implement the pure-data bridge from a concrete gateway action proposal to
an attestation challenge input.

Implemented: `hsai-agent-admission` now uses the canonical
`hsai-attestation::report_data_binding` function to derive
`GatewayAttestationChallengeBinding` from `GatewayActionProposal::digest()`, an
anchor id, agent public key, nonce, validity window, and admission policy id.
Validation rejects schema drift, proposal drift, policy drift, challenge-window
errors, report-data drift, challenge-id drift, missing nonclaims, and any
authority grant.

Dependencies: Phase 248 evidence-lane map and the existing HSAI attestation
report-data binding.

Validation gate: focused `gateway_attestation` unit tests,
`hsai-agent-admission` library tests, repo hygiene, claim-boundary docs, and the
full workspace test suite.

Anti-goals: provider calls, live attestation capture, generated operator
artifacts, model execution, signer/tool integration, accepted Evidence Ledger
mutation, score-axis population, official benchmark evidence, Level2+
evidence, production-readiness claims, semantic-correctness claims, SOTA
claims, breakthrough claims, full-security claims, or claims above `Attested`.

Exit criteria: gateway action proposals can deterministically produce and
validate attestation challenge input metadata while preserving
`authority_granted=false` and explicit nonclaims.

## Phase 250 HSAI Gateway Operator Bridge Bundle

Status: complete. See
`docs/250-hsai-gateway-operator-bridge-bundle-notes.md`.

Goal: materialize a reproducible local bridge bundle that joins one gateway
report digest, one gateway attestation challenge binding, and one repo-external
operator-live artifact reference.

Implemented: `hsai-agent-admission` now provides the `GatewayOperatorBridge`
bundle model, operator artifact reference model, declared `gateway-bridge/*`
output files, digest sidecars, materialization/readback helpers, validation
reports, and focused drift/escalation tests. The operator-facing
`gateway_operator_bridge_bundle` example writes a gateway report output and a
gateway bridge output under `.gateway-demo-runs/phase-250-gateway-bridge`.

Validation gate: focused `gateway_operator_bridge` unit tests,
`gateway_operator_bridge_bundle_contract`, example compilation, ignored demo
run, repo hygiene, claim-boundary docs, and full workspace tests.

Anti-goals: raw provider artifact retention, credential handling, provider
calls, live attestation capture, model execution, signer/tool integration,
accepted Evidence Ledger mutation, score-axis population, official benchmark
evidence, Level2+ evidence, production-readiness claims, semantic-correctness
claims, SOTA claims, breakthrough claims, full-security claims, or claims above
`Attested`.

Exit criteria: ignored bridge bundle exists locally; generated files are not
committed; exact run command and digests are recorded; claim-boundary checks
remain green.

## Phase 251 HSAI Gateway Bridge Promotion Preflight

Status: complete. See
`docs/251-hsai-gateway-bridge-promotion-preflight-notes.md`.

Goal: add a reviewed local preflight report for the Phase 250 bridge bundle
that validates bridge metadata and repo-external operator artifact reference
digests without promoting accepted evidence.

Implemented: `hsai-agent-admission` now provides the
`GatewayOperatorBridgePromotionPreflightRequest`,
`GatewayOperatorBridgePromotionPreflightReport`, review-decision, validation,
issue, nonclaim, claim-boundary, report-builder, and request-validation
surfaces. The preflight requires `ApprovedMetadataOnly`, matching
bundle/manifest digests, repo-external operator artifact reference, false
raw-artifact and credential flags, false accepted-ledger mutation, false
Level2+ evidence, false score-axis population, and no stronger claim text.

Validation gate: focused promotion-preflight unit tests, bridge regression
tests, repo hygiene, claim-boundary docs, and full workspace tests.

Anti-goals: bridge promotion, accepted Evidence Ledger mutation, raw provider
artifact retention, credential handling, provider calls, live attestation
capture, score-axis population, official benchmark evidence, Level2+ evidence,
production-readiness claims, semantic-correctness claims, SOTA claims,
breakthrough claims, full-security claims, or claims above `Attested`.

Exit criteria: valid preflight report remains local metadata only; escalation
flags and forbidden claim text fail closed; no generated output is committed.

## Phase 252 HSAI Gateway Bridge Acceptance Preview

Status: complete. See
`docs/252-hsai-gateway-bridge-acceptance-preview-notes.md`.

Goal: add a candidate-only local acceptance preview for the Phase 251 bridge
promotion preflight report without mutating accepted evidence.

Implemented: `hsai-agent-admission` now provides
`GatewayOperatorBridgeAcceptancePreviewRequest`,
`GatewayOperatorBridgeAcceptancePreviewReport`, preview decision, validation,
issue, nonclaim, schema-version, claim-boundary, report-builder, and
request-validation surfaces. The preview requires `ApproveCandidateOnly`, a
valid non-escalating source preflight report, exact preflight digest binding,
`candidate_only=true`, false accepted-ledger mutation, false Level2+ evidence,
false score-axis population, false authority grant, false raw-artifact and
credential retention, and no stronger claim text.

Validation gate: focused acceptance-preview unit tests, promotion-preflight
regression tests, repo hygiene, claim-boundary docs, and full workspace tests.

Anti-goals: final bridge acceptance, accepted Evidence Ledger mutation, ledger
append, raw provider artifact retention, credential handling, provider calls,
live attestation capture, score-axis population, official benchmark evidence,
Level2+ evidence, production-readiness claims, semantic-correctness claims,
SOTA claims, breakthrough claims, full-security claims, or claims above
`Attested`.

Exit criteria: valid preview report remains candidate-only metadata; digest
drift, invalid source preflight, escalation flags, and forbidden claim text fail
closed; no generated output is committed.

## Phase 253 HSAI Gateway Bridge Acceptance Preview Bundle

Status: complete. See
`docs/253-hsai-gateway-bridge-acceptance-preview-bundle-notes.md`.

Goal: materialize a reproducible ignored output bundle for the Phase 252
candidate-only acceptance preview report.

Implemented: `hsai-agent-admission` now provides the acceptance-preview
materialization request, output manifest, output validation report,
materialization error surface, declared `gateway-acceptance-preview/*` files,
digest sidecars, materialization/readback helpers, focused drift/escalation
tests, source-contract tests, and the `gateway_acceptance_preview_bundle`
operator-facing example. The ignored demo writes gateway report, bridge, and
acceptance-preview output sub-bundles under
`.gateway-demo-runs/phase-253-gateway-acceptance-preview`.

Validation gate: focused acceptance-preview bundle unit tests, source-contract
tests, example compilation, ignored demo run, repo hygiene, claim-boundary docs,
and full workspace tests.

Anti-goals: final bridge acceptance, accepted Evidence Ledger mutation, ledger
append, committed generated output, raw provider artifact retention, credential
handling, provider calls, live attestation capture, score-axis population,
official benchmark evidence, Level2+ evidence, production-readiness claims,
semantic-correctness claims, SOTA claims, breakthrough claims, full-security
claims, or claims above `Attested`.

Exit criteria: ignored preview bundle exists locally; generated files are not
committed; exact run command and digests are recorded; readback and
claim-boundary checks remain green.

## Phase 254 HSAI Gateway Bridge Public Claim Packet

Status: complete. See
`docs/254-hsai-gateway-bridge-public-claim-packet.md`.

Goal: package Phases 249-253 into one bounded public claim artifact that says
exactly what is locally proven, how to reproduce it, and what is explicitly not
claimed.

Implemented: added a docs-only public claim packet for the local
gateway-to-attestation-to-preview bridge. The packet names commit
`edbae44ea2f47f067683e28d2c6d5cb8af4362e8`, covered phases, public claim,
passed commands, ignored run evidence, reproduction checklist, explicit
nonclaims, buyer-facing wording, and the next defensible evidence step.

Validation gate: repo hygiene, claim-boundary docs, Markdown presence checks,
and full workspace tests.

Anti-goals: code changes, generated output, accepted Evidence Ledger mutation,
final bridge acceptance, Level2+ evidence, live provider evidence, live
attestation capture, benchmark evidence, score-axis population,
production-readiness claims, semantic-correctness claims, SOTA claims,
breakthrough claims, full-security claims, or claims above `Attested`.

Exit criteria: the public packet is shareable without inflating the claim and
the repo validation gates remain green.

## Phase 255 HSAI Gateway Claim-Packet Reproduction Checker

Status: complete. See
`docs/255-hsai-gateway-claim-packet-reproduction-checker-notes.md`.

Goal: add a local hermetic checker that keeps the Phase 254 public claim packet
aligned with committed repository state.

Implemented: added `gateway_claim_packet_reproduction`, a `zkbench-core`
integration test that reads the Phase 254 packet, `.gitignore`, README, task
list, validation report, and AGENTS boundary. It verifies the packet's pinned
commit string, covered surfaces, exact commands, ignored demo-root boundary,
declared output files, candidate-only and non-mutating flags, explicit
nonclaims, buyer-facing wording, "do not use" phrases, and navigation
references.

Validation gate: focused reproduction-checker test, repo hygiene,
claim-boundary docs, formatting, diff hygiene, and full workspace tests.

Anti-goals: provider calls, generated artifacts, ignored demo execution,
credential handling, accepted Evidence Ledger mutation, final bridge
acceptance, Level2+ evidence, live provider evidence, live attestation capture,
benchmark evidence, score-axis population, production-readiness claims,
semantic-correctness claims, SOTA claims, breakthrough claims, full-security
claims, or claims above `Attested`.

Exit criteria: the Phase 254 public packet has a committed local reproduction
checker and the repo validation gates remain green.

## Phase 256 HSAI Gateway Structured Claim-Packet Manifest

Status: complete. See
`docs/256-hsai-gateway-structured-claim-packet-manifest-notes.md`.

Goal: make the Phase 254 public claim packet more machine-checkable without
strengthening the public claim.

Implemented: added a fenced `claim-packet-manifest-v1` block to
`docs/254-hsai-gateway-bridge-public-claim-packet.md` and upgraded
`gateway_claim_packet_reproduction` to parse the block. The parser validates
singleton fields and repeated values for packet identity, commit metadata,
covered phases, claim level, ignored demo boundary, declared output files,
summary flags, commands, nonclaims, and forbidden public phrases.

Validation gate: focused parser-backed reproduction-checker test, repo hygiene,
claim-boundary docs, formatting, diff hygiene, and full workspace tests.

Anti-goals: provider calls, generated artifacts, ignored demo execution,
credential handling, accepted Evidence Ledger mutation, final bridge
acceptance, Level2+ evidence, live provider evidence, live attestation capture,
benchmark evidence, score-axis population, production-readiness claims,
semantic-correctness claims, SOTA claims, breakthrough claims, full-security
claims, or claims above `Attested`.

Exit criteria: the Phase 254 packet carries a structured local manifest and the
repo validation gates remain green.

## Phase 257 HSAI Gateway Claim-Packet Manifest Drift Coverage

Status: complete. See
`docs/257-hsai-gateway-claim-packet-manifest-drift-coverage-notes.md`.

Goal: harden the Phase 256 structured manifest checker with local malformed
packet examples.

Implemented: changed the manifest parser to return structured errors, added a
reusable local manifest contract validator, and added negative coverage for
missing fences, unterminated fences, non-`key=value` lines, empty keys, empty
values, maximum-maturity drift, missing focused checker command, and explicit
nonclaim drift.

Validation gate: focused manifest drift checker test, repo hygiene,
claim-boundary docs, formatting, diff hygiene, and full workspace tests.

Anti-goals: fixture files, generated artifacts, ignored demo execution,
provider calls, credential handling, accepted Evidence Ledger mutation, final
bridge acceptance, Level2+ evidence, live provider evidence, live attestation
capture, benchmark evidence, score-axis population, production-readiness
claims, semantic-correctness claims, SOTA claims, breakthrough claims,
full-security claims, or claims above `Attested`.

Exit criteria: malformed local packet examples are rejected without creating
artifacts and the repo validation gates remain green.

## Phase 258 HSAI Gateway Structured Manifest Digest Binding

Status: complete. See
`docs/258-hsai-gateway-structured-manifest-digest-binding-notes.md`.

Goal: bind the structured Phase 254 claim-packet manifest to a deterministic
local digest without strengthening the public claim.

Implemented: added `manifest_digest_sha256` to the structured manifest and
upgraded `gateway_claim_packet_reproduction` to recompute the canonical digest
over sorted `key=value` lines excluding the digest line. The checker validates
64-character lowercase hex formatting, digest self-consistency, digest-field
drift, digest-content drift, and recomputed-digest semantic drift examples.

Validation gate: focused manifest digest checker test, repo hygiene,
claim-boundary docs, formatting, diff hygiene, and full workspace tests.

Anti-goals: fixture files, generated artifacts, ignored demo execution,
provider calls, credential handling, accepted Evidence Ledger mutation, final
bridge acceptance, Level2+ evidence, live provider evidence, live attestation
capture, benchmark evidence, score-axis population, production-readiness
claims, semantic-correctness claims, SOTA claims, breakthrough claims,
full-security claims, or claims above `Attested`.

Exit criteria: the Phase 254 structured manifest is digest-bound and the repo
validation gates remain green.

## Phase 259 HSAI Gateway Digest-Bound Manifest Reproduction Note

Status: complete. See
`docs/259-hsai-gateway-digest-bound-manifest-reproduction-note.md`.

Goal: provide bounded external-share wording for the Phase 254 digest-bound
structured manifest without strengthening the public claim.

Implemented: added a docs-only reproduction note that names the Phase 254 packet
path, `manifest_digest_sha256`, digest rule, focused checker command,
shareable wording, short wording, reproduction checklist, and explicit
nonclaims.

Validation gate: docs hygiene, claim-boundary docs, formatting, diff hygiene,
and full workspace tests.

Anti-goals: Rust/source changes, fixture files, generated artifacts, ignored
demo execution, provider calls, credential handling, accepted Evidence Ledger
mutation, final bridge acceptance, Level2+ evidence, live provider evidence,
live attestation capture, benchmark evidence, score-axis population,
production-readiness claims, semantic-correctness claims, SOTA claims,
breakthrough claims, full-security claims, or claims above `Attested`.

Exit criteria: the digest-bound manifest has a short shareable reproduction note
and the repo validation gates remain green.

## Phase 260 HSAI Gateway Public Packet Index

Status: complete. See `docs/260-hsai-gateway-public-packet-index.md`.

Goal: provide one local index for the latest shareable gateway packet, digest,
checker command, and nonclaims without strengthening the public claim.

Implemented: added a docs-only public packet index pinned to commit
`85a49f546935e5c237ff01811ea94fba38d5d0b5`. The index names the latest
shareable packet, reproduction note, structured manifest digest, digest rule,
checker command, bounded public wording, short wording, reproduction checklist,
explicit nonclaims, and next local index-checker slice.

Validation gate: docs hygiene, claim-boundary docs, formatting, diff hygiene,
and full workspace tests.

Anti-goals: Rust/source changes, fixture files, generated artifacts, ignored
demo execution, provider calls, credential handling, accepted Evidence Ledger
mutation, final bridge acceptance, Level2+ evidence, live provider evidence,
live attestation capture, benchmark evidence, score-axis population,
production-readiness claims, semantic-correctness claims, SOTA claims,
breakthrough claims, full-security claims, or claims above `Attested`.

Exit criteria: the latest packet index is shareable without claim inflation and
the repo validation gates remain green.

## Phase 261 HSAI Gateway Public Packet Index Checker

Status: complete. See
`docs/261-hsai-gateway-public-packet-index-checker-notes.md`.

Goal: make the Phase 260 public packet index locally checkable against the
Phase 254 packet and Phase 259 reproduction note without creating artifacts or
strengthening the public claim.

Implemented: extended
`crates/zkbench-core/tests/gateway_claim_packet_reproduction.rs` to validate the
Phase 260 index path, indexed commit, packet path, reproduction-note path,
structured manifest digest, digest rule, focused checker command, bounded
wording, reproduction checklist hygiene, explicit nonclaims, and absence of
forbidden public phrases in the public-facing index and reproduction note. The
test also rejects in-memory drift examples for indexed commit, packet path,
digest, checker command, and nonclaim drift.

Validation gate: focused gateway packet checker, docs hygiene, claim-boundary
docs, formatting, diff hygiene, and full workspace tests.

Anti-goals: fixture files, generated artifacts, ignored demo execution,
provider calls, credential handling, accepted Evidence Ledger mutation, final
bridge acceptance, Level2+ evidence, live provider evidence, live attestation
capture, benchmark evidence, score-axis population, production-readiness
claims, semantic-correctness claims, SOTA claims, breakthrough claims,
full-security claims, or claims above `Attested`.

Exit criteria: the Phase 260 index is guarded by a local hermetic checker and
the repo validation gates remain green.

## Phase 262 Official Submission Output Coverage

Status: complete. See
`docs/262-phase-official-submission-output-coverage-notes.md`.

Goal: return to the `zkbench-core` coverage lane and harden the next reachable
non-serializer surface after the gateway public-packet work:
`crates/zkbench-core/src/evidence/official_submission_output.rs`.

Implemented: extended
`crates/zkbench-core/tests/phase_186_official_submission_output_coverage.rs`
with tests for matching explicit overwrite, digest-preserving rewrite,
non-UTF-8 digest sidecar rejection, invalid validation-report JSON rejection
with a matching digest sidecar, and unexpected declared-root child rejection.

Coverage result: `evidence/official_submission_output.rs` moved from `82.12%`
region / `70.45%` function / `87.45%` line coverage to `84.22%` region /
`75.00%` function / `90.04%` line coverage. The local `zkbench-core` package
summary moved from `92.74%` region / `89.36%` function / `94.51%` line
coverage to `92.80%` region / `89.48%` function / `94.57%` line coverage.

Residual cap: remaining misses are low-level filesystem error wrappers,
private relative-path validation branches reached only by fixed internal
constants, unreachable parent-component fallback arms after public
prevalidation, and concrete serializer-error wrappers.

Anti-goals: production source behavior changes, official submission behavior,
endpoint submission behavior, credential handling, generated artifact
materialization outside test tempdirs, accepted Evidence Ledger mutation,
benchmark evidence, score-axis population, Level2+ evidence, semantic
correctness claims, production-readiness claims, SOTA claims, breakthrough
claims, unsafe coverage forcing, coverage suppression, test-only hooks, or
whole-workspace 100% coverage claims.

Exit criteria: focused official-submission output tests pass; repo hygiene and
claim-boundary checks remain green; full workspace tests pass; package coverage
summary records the local coverage movement and next low non-serializer
surface.

## Phase 263 External Runner Validation Coverage

Status: complete. See
`docs/263-phase-external-runner-validation-coverage-notes.md`.

Goal: harden the next reachable non-serializer coverage target after Phase 262:
`crates/zkbench-core/src/external_runner/validation.rs`.

Implemented: added
`crates/zkbench-core/tests/phase_263_external_runner_validation_coverage.rs`
with tests for `ExternalValidationIssue::warning` preserving path, message, and
warning severity, plus Windows absolute-path detection for slash and backslash
forms and negative checks for non-drive prefixes, drive-relative paths, short
drive strings, and portable relative paths.

Coverage result: `external_runner/validation.rs` moved from `89.36%` region /
`90.91%` function / `88.16%` line coverage to `100.00%` region / `100.00%`
function / `100.00%` line coverage. The local `zkbench-core` package summary
moved from `92.80%` region / `89.48%` function / `94.57%` line coverage to
`92.83%` region / `89.53%` function / `94.60%` line coverage.

Residual cap: no residual missed lines remain in
`external_runner/validation.rs` under the local coverage run.

Anti-goals: production source behavior changes, external-runner behavior
changes, external execution, endpoint submission behavior, credential handling,
generated artifact materialization, accepted Evidence Ledger mutation,
benchmark evidence, score-axis population, Level2+ evidence, semantic
correctness claims, production-readiness claims, SOTA claims, breakthrough
claims, unsafe coverage forcing, coverage suppression, test-only hooks, or
whole-workspace 100% coverage claims.

Exit criteria: focused external-runner validation tests pass; repo hygiene and
claim-boundary checks remain green; full workspace tests pass; package coverage
summary records the local coverage movement and next low non-serializer
surface.

## Phase 264 HSAI Gateway External Evidence Acceptance Boundary

Status: complete. See
`docs/264-hsai-gateway-external-evidence-acceptance-boundary.md`.

Goal: define the docs-first boundary for the first gateway-bound external
evidence accepted-ledger mutation before implementation touches accepted
evidence.

Implemented: added a bounded acceptance-boundary spec that names the existing
gateway bridge inputs, existing `zkbench-core` accepted append APIs, future
request shape, redaction rules, evidence-class and claim-boundary caps,
verification order, output-root shape, required review decision, required tests,
verifier commands, buyer-facing wording, explicit nonclaims, and next
implementation slice.

Validation gate: docs hygiene, claim-boundary docs, repo hygiene, formatting,
diff hygiene, and full workspace tests.

Anti-goals: Rust/source changes, accepted Evidence Ledger mutation, final
bridge acceptance, generated artifacts, raw provider payload retention,
credential handling, live provider calls, live attestation capture, benchmark
evidence, official benchmark submission, score-axis population, Level2+
evidence, production-readiness claims, semantic-correctness claims, SOTA
claims, breakthrough claims, full-security claims, global software-agent
uniqueness claims, or claims above `Attested`.

Exit criteria: the future accepted-evidence implementation path is explicit,
bounded, and nonclaim-safe before code mutation.

## Phase 265 HSAI Formal Verification Evidence Architecture Boundary

Status: complete. See
`docs/265-hsai-formal-verification-evidence-architecture-boundary.md`.

Goal: define the docs-first boundary for the next HSAI
formal-verification evidence architecture before implementation touches formal
tools, external repositories, proof artifacts, accepted evidence, or public
SOTA wording.

Implemented: added a bounded architecture spec that ranks COBALT, Aeneas,
Verified-zkEVM rust-lean, VeriSoftBench, Federated Formal Verification,
cycle-consistent certificate explanation, and related research repos by their
future HSAI role. It defines the target pipeline, first tiny gateway-property
targets, future formal evidence shape, verification order, source verification
rule, explicit nonclaims, and next implementation slice.

Validation gate: docs hygiene, source-index hygiene, claim-boundary docs, repo
hygiene, formatting, diff hygiene, and full workspace tests.

Anti-goals: Rust/source changes, Cargo metadata changes, package runtime files,
external repo clones, vendored source, proof assistant setup files, Lean, Coq,
TLA+, SMT, Z3, CBMC, or model-checker execution, generated proof artifacts,
accepted Evidence Ledger mutation, Level2+ evidence, score-axis population,
benchmark evidence, official benchmark submission, live provider calls,
credential handling, production-readiness claims, semantic-correctness claims,
SOTA claims, breakthrough claims, full-security claims, or global
software-agent uniqueness claims.

Exit criteria: the next formal-verification evidence track is explicit,
bounded, source-indexed, and nonclaim-safe before code mutation.

## Phase 266 HSAI Gateway Formal Evidence Metadata Adapter

Status: complete. See
`docs/266-hsai-gateway-formal-evidence-metadata-adapter-notes.md`.

Goal: implement the first bounded local metadata adapter for one tiny HSAI
gateway formal-evidence candidate without running formal tools or escalating
claims.

Implemented: added typed `hsai-agent-admission` request, report, validation,
local-check, status, property-kind, and issue types for the gateway attestation
challenge binding determinism/input-sensitivity candidate. The adapter rebuilds
the existing challenge binding, checks identical-input determinism, nonce
sensitivity, proposal sensitivity, expected binding digest agreement, portable
source attribution, source digest/commit presence, explicit nonclaims, and
claim-boundary flags.

Validation gate: focused `hsai-agent-admission` formal-evidence tests, repo
hygiene, formatting, diff hygiene, and full workspace tests.

Anti-goals: formal backend execution, proof artifact submission, external repo
clones, vendored source, proof assistant setup files, accepted Evidence Ledger
mutation, Level2+ evidence, score-axis population, benchmark evidence,
official benchmark submission, live provider calls, credential handling,
production-readiness claims, semantic-correctness claims, SOTA claims,
breakthrough claims, full-security claims, global software-agent uniqueness
claims, or authority to execute an action.

Exit criteria: one gateway formal-evidence candidate is represented as bounded
local metadata with explicit nonclaims and fail-closed escalation rejection.

## Phase 267 HSAI Gateway Formal Source Correspondence Boundary

Status: complete. See
`docs/267-hsai-gateway-formal-source-correspondence-boundary.md`.

Goal: define the source-correspondence contract for any future formal
obligation over the Phase 266 gateway binding property before proof tooling or
certificate implementation is allowed.

Implemented: added a docs-first boundary that names the source anchor set for
`GatewayActionProposal`, `GatewayAttestationChallengeBinding`,
`build_gateway_attestation_challenge_binding`,
`validate_gateway_attestation_challenge_binding`,
`gateway_attestation_challenge_id`, the Phase 266 formal-evidence local check,
and the imported `hsai-attestation::report_data_binding` dependency. It splits
the future property into deterministic-constructor, nonce-sensitivity,
proposal-sensitivity, and validation-agreement obligations, then defines
required correspondence-certificate fields and backend-specific rules for
Rust-to-Lean, SMT/COBALT-style, and federated paths.

Validation gate: docs hygiene, source-correspondence claim-boundary review, repo
hygiene, formatting, diff hygiene, and full workspace tests.

Anti-goals: Rust implementation changes, Cargo metadata changes, package
runtime files, proof assistant setup files, external repo clones, vendored
source, Lean, Coq, TLA+, SMT, Z3, CBMC, model-checker execution, generated proof
artifacts, accepted Evidence Ledger mutation, Level2+ evidence, score-axis
population, benchmark evidence, official benchmark submission, live provider
calls, credential handling, production-readiness claims, semantic-correctness
claims, SOTA claims, breakthrough claims, full-security claims, global
software-agent uniqueness claims, or authority to execute an action.

Exit criteria: the future proof target is source-anchored and nonclaim-safe
before any prover or correspondence-certificate implementation begins.

## Phase 268 HSAI Gateway Formal Correspondence Certificate Metadata

Status: complete. See
`docs/268-hsai-gateway-formal-correspondence-certificate-notes.md`.

Goal: implement the local pure-data correspondence-certificate type for the
Phase 267 source mapping without running a prover or creating proof evidence.

Implemented: added typed `hsai-agent-admission` certificate, validation, issue,
source-file digest, source-anchor, tool-status, proof-obligation, backend-kind,
tool-execution-status, proof-status, and review-decision surfaces. Validation
requires both source files, all Phase 267 anchors, all four P267 obligations,
source commit metadata, nonzero source digests, tool metadata, trusted
assumptions, modeled replacements, an input/output schema digest,
metadata-only review, explicit nonclaims, and the correspondence-only claim
boundary.

Validation gate: focused `hsai-agent-admission` correspondence-certificate
tests, repo hygiene, formatting, diff hygiene, and full workspace tests.

Anti-goals: formal backend execution, proof artifact submission, proof-status
escalation, external repo clones, vendored source, proof assistant setup files,
accepted Evidence Ledger mutation, Level2+ evidence, score-axis population,
benchmark evidence, official benchmark submission, live provider calls,
credential handling, production-readiness claims, semantic-correctness claims,
SOTA claims, breakthrough claims, full-security claims, global software-agent
uniqueness claims, or authority to execute an action.

Exit criteria: the Phase 267 source mapping is represented as local
correspondence metadata with fail-closed source, tool, assumption, review, and
claim-boundary validation.

## Phase 269 HSAI Gateway Formal Correspondence Output Bundle Boundary

Status: complete. See
`docs/269-hsai-gateway-formal-correspondence-output-bundle-boundary.md`.

Goal: define the docs-first output-bundle boundary for future materialization
of the Phase 268 correspondence certificate before filesystem code is allowed.

Implemented: added a bounded bundle spec that names the future
`gateway-formal-correspondence/*` declared files, SHA-256 sidecars, manifest
fields, validation-report fields, redaction-report fields, readback semantics,
future tests, anti-goals, explicit nonclaims, and next implementation slice. The
bundle contract requires local consistency checks over certificate, manifest,
sidecars, validation report, redaction report, and nonclaims.

Validation gate: docs hygiene, output-bundle claim-boundary review, repo
hygiene, formatting, diff hygiene, and full workspace tests.

Anti-goals: Rust implementation changes, Cargo metadata changes, package
runtime files, filesystem output implementation, generated output bundles, proof
assistant setup files, external repo clones, vendored source, Lean, Coq, TLA+,
SMT, Z3, CBMC, model-checker execution, generated proof artifacts, proof
artifact submission, raw prover or solver logs, accepted Evidence Ledger
mutation, Level2+ evidence, score-axis population, benchmark evidence, official
benchmark submission, live provider calls, credential handling,
production-readiness claims, semantic-correctness claims, SOTA claims,
breakthrough claims, full-security claims, global software-agent uniqueness
claims, or authority to execute an action.

Exit criteria: future correspondence-certificate output materialization is
declared, digest-bound, readback-bound, and nonclaim-safe before code mutation.

## Phase 270 HSAI Gateway Formal Correspondence Output Bundle Implementation

Status: complete. See
`docs/270-hsai-gateway-formal-correspondence-output-bundle-notes.md`.

Goal: implement the Phase 269 local output-bundle materialization and readback
contract for Phase 268 correspondence certificates.

Implemented: added local `hsai-agent-admission` output request, manifest,
validation report, redaction report, output error, materialization, and readback
surfaces for `gateway-formal-correspondence/*` bundles. The implementation
stages writes, emits SHA-256 sidecars, recomputes manifest and validation
content on readback, rejects undeclared files and symlinks, and preserves the
metadata-only claim boundary.

Validation gate: focused bundle materialization/readback tests, docs hygiene,
repo hygiene, formatting, diff hygiene, and full workspace tests.

Anti-goals: formal backend execution, proof assistant setup files, external
repo clones, vendored source, Lean, Coq, TLA+, SMT, Z3, CBMC, model-checker
execution, generated proof artifacts, proof artifact submission, raw prover or
solver logs, accepted Evidence Ledger mutation, Level2+ evidence, score-axis
population, benchmark evidence, official benchmark submission, live provider
calls, credential handling, production-readiness claims, semantic-correctness
claims, SOTA claims, breakthrough claims, full-security claims, global
software-agent uniqueness claims, or authority to execute an action.

Exit criteria: Phase 268 correspondence certificates can be materialized into a
local declared-file bundle and read back with fail-closed local consistency
checks, without becoming proof evidence or accepted evidence.

## Phase 271 HSAI Gateway Formal Correspondence Output Bundle Drift Coverage

Status: complete. See
`docs/271-hsai-gateway-formal-correspondence-output-bundle-drift-coverage-notes.md`.

Goal: expand audit-first negative coverage for the Phase 270 local output
bundle before any backend-specific proof adapter boundary.

Implemented: added focused `hsai-agent-admission` tests for existing output
roots without overwrite, file output roots, protected output roots, symlink
output roots, symlink bundle directories, symlink declared files, symlink
sidecars, missing sidecars, stale sidecars, malformed manifest JSON,
validation-report semantic drift, and manifest claim-boundary escalation.

Validation gate: focused bundle drift coverage tests, docs hygiene, repo
hygiene, formatting, diff hygiene, and full workspace tests.

Anti-goals: production source format changes, formal backend execution, proof
assistant setup files, external repo clones, vendored source, Lean, Coq, TLA+,
SMT, Z3, CBMC, model-checker execution, generated proof artifacts, proof
artifact submission, raw prover or solver logs, accepted Evidence Ledger
mutation, Level2+ evidence, score-axis population, benchmark evidence, official
benchmark submission, live provider calls, credential handling,
production-readiness claims, semantic-correctness claims, SOTA claims,
breakthrough claims, full-security claims, global software-agent uniqueness
claims, or authority to execute an action.

Exit criteria: Phase 270 output-bundle readback has focused failure coverage for
root safety, declared-file safety, sidecar integrity, semantic drift, and claim
boundary escalation.

## Phase 272 HSAI Gateway Formal Backend Adapter Boundary

Status: complete. See
`docs/272-hsai-gateway-formal-backend-adapter-boundary.md`.

Goal: define the docs-first boundary for the first future backend-specific proof
adapter before any proof tool setup or execution is allowed.

Implemented: added a backend ranking that puts a Rust-to-Lean
source-correspondence lane first for the gateway binding property, limits the
SMT/COBALT-style lane to boolean claim-boundary and small arithmetic
containment invariants, defers federated dispatch and benchmark evaluation until
candidate backend runs exist, and treats certificate explanation as audit/debug
support only. The boundary defines future adapter inputs, outputs, verification
order, maturity labels, required tests, anti-goals, and next implementation
slice.

Validation gate: docs hygiene, backend-boundary claim review, repo hygiene,
formatting, diff hygiene, and full workspace tests.

Anti-goals: Rust implementation changes, Cargo metadata changes, package
runtime files, proof assistant setup files, external repo clones, vendored
source, Lean, Coq, TLA+, SMT, Z3, CBMC, model-checker, Aeneas, Hax, rust-lean,
or COBALT execution, generated proof artifacts, generated checker transcripts,
accepted Evidence Ledger mutation, Level2+ evidence, score-axis population,
benchmark evidence, official benchmark submission, live provider calls,
credential handling, production-readiness claims, semantic-correctness claims,
SOTA claims, breakthrough claims, full-security claims, global software-agent
uniqueness claims, or authority to execute an action.

Exit criteria: the first backend-specific adapter is bounded as future
candidate metadata only, with explicit correspondence, toolchain, proof
artifact, checker transcript, and claim-boundary requirements.

## Phase 273 HSAI Gateway Formal Backend Adapter Inert Metadata

Status: complete. See
`docs/273-hsai-gateway-formal-backend-adapter-inert-metadata-notes.md`.

Goal: implement the inert request/report metadata surface for the first future
backend-specific adapter without running any backend.

Implemented: added local `hsai-agent-admission` request, report, validation,
issue, status, maturity, claim-boundary, required-nonclaim, validation, and
report-construction surfaces for the future `RustToLean` gateway formal lane.
Validation binds the Phase 268 correspondence certificate digest, Phase 270
output manifest digest, source commit, source files, source anchors, proof
obligations, tool metadata, model assumptions, modeled replacements,
unsupported Rust features, input/output schema digest, expected future proof
artifact format, expected checker transcript format, `NotRun` maturity, and
explicit nonclaims.

Validation gate: focused backend-adapter metadata tests, docs hygiene, repo
hygiene, formatting, diff hygiene, and full workspace tests.

Anti-goals: backend execution, proof assistant setup files, external repo
clones, vendored source, Lean, Coq, TLA+, SMT, Z3, CBMC, model-checker, Aeneas,
Hax, rust-lean, or COBALT execution, generated proof artifacts, generated
checker transcripts, accepted Evidence Ledger mutation, Level2+ evidence,
score-axis population, benchmark evidence, official benchmark submission, live
provider calls, credential handling, production-readiness claims,
semantic-correctness claims, SOTA claims, breakthrough claims, full-security
claims, global software-agent uniqueness claims, or authority to execute an
action.

Exit criteria: the future backend adapter now has local candidate metadata that
fails closed on digest drift, source drift, tool drift, proof/checker artifact
submission, maturity escalation, and public-claim escalation.

## Phase 274 HSAI Gateway Formal Backend Adapter Drift Coverage

Status: complete. See
`docs/274-hsai-gateway-formal-backend-adapter-drift-coverage-notes.md`.

Goal: add audit-first negative coverage for the Phase 273 inert backend-adapter
metadata before any backend-run artifact boundary.

Implemented: added focused `hsai-agent-admission` tests for output-manifest
digest drift, output-manifest certificate-digest drift, output-manifest
claim-boundary drift, invalid nested correspondence certificates,
schema-version drift, unsafe adapter ids, state-slice drift, and requested
claim-boundary drift.

Validation gate: focused backend-adapter metadata tests, docs hygiene, repo
hygiene, formatting, diff hygiene, and full workspace tests.

Anti-goals: production source format changes, backend execution, proof
assistant setup files, external repo clones, vendored source, Lean, Coq, TLA+,
SMT, Z3, CBMC, model-checker, Aeneas, Hax, rust-lean, or COBALT execution,
generated proof artifacts, generated checker transcripts, accepted Evidence
Ledger mutation, Level2+ evidence, score-axis population, benchmark evidence,
official benchmark submission, live provider calls, credential handling,
production-readiness claims, semantic-correctness claims, SOTA claims,
breakthrough claims, full-security claims, global software-agent uniqueness
claims, or authority to execute an action.

Exit criteria: Phase 273 adapter metadata has focused failure coverage for
manifest identity, nested certificate validity, request identity, and claim
boundary drift.

## Phase 275 HSAI Gateway Formal Backend Run Artifact Boundary

Status: complete. See
`docs/275-hsai-gateway-formal-backend-run-artifact-boundary.md`.

Goal: define the docs-first artifact boundary for a future hermetic backend run
before any proof tool setup or execution is allowed.

Implemented: added a backend-run artifact boundary that defines the future
`gateway-formal-backend-run/*` declared file layout, SHA-256 sidecars, optional
candidate proof/checker references, run-summary contract, execution-mode
contract, review gate, benchmark hooks, required future tests, anti-goals, and
next implementation slice. The boundary keeps any future run candidate-only and
forbids accepted-evidence promotion inside this slice.

Validation gate: docs hygiene, backend-run boundary claim review, repo hygiene,
formatting, diff hygiene, and full workspace tests.

Anti-goals: Rust implementation changes, Cargo metadata changes, package
runtime files, proof assistant setup files, external repo clones, vendored
source, Lean, Coq, TLA+, SMT, Z3, CBMC, model-checker, Aeneas, Hax, rust-lean,
or COBALT execution, generated proof artifacts, generated checker transcripts,
raw prover logs, raw checker logs, accepted Evidence Ledger mutation, Level2+
evidence, score-axis population, benchmark evidence, official benchmark
submission, live provider calls, credential handling, production-readiness
claims, semantic-correctness claims, SOTA claims, breakthrough claims,
full-security claims, global software-agent uniqueness claims, or authority to
execute an action.

Exit criteria: the future backend-run artifact surface is declared,
candidate-only, digest-bound, redaction-bound, review-gated, benchmark-hooked
only as metadata, and nonpromotion-safe before code mutation.

## Phase 276 HSAI Gateway Formal Backend Run Inert Artifact Metadata

Status: complete. See
`docs/276-hsai-gateway-formal-backend-run-inert-artifact-metadata-notes.md`.

Goal: implement local inert backend-run artifact metadata that binds the future
run summary to the Phase 273 adapter chain without running a backend.

Implemented: added schema/state/claim-boundary constants, backend-run execution,
exit, checker, artifact-reference, metadata, issue, and validation types;
required nonclaims; digest helpers for modeled assumptions and unsupported
features; a `NotRun` metadata builder; and fail-closed validation for binding
drift, execution labels, timestamps, proof/checker references, tool-log
summaries, accepted evidence, Level2+ evidence, score axes, authority grants,
forbidden public claim text, and missing nonclaims.

Validation gate: focused `hsai-agent-admission` tests for valid inert metadata,
execution/artifact-reference escalation rejection, and binding drift rejection;
formatting; repo hygiene; full workspace tests.

Anti-goals: materialized backend-run bundle writes, backend execution, proof
assistant setup files, external repo clones, vendored source, Lean, Coq, TLA+,
SMT, Z3, CBMC, model-checker, Aeneas, Hax, rust-lean, or COBALT execution,
generated proof artifacts, generated checker transcripts, raw prover logs, raw
checker logs, accepted Evidence Ledger mutation, Level2+ evidence, score-axis
population, benchmark evidence, official benchmark submission, live provider
calls, credential handling, semantic-correctness claims, production-readiness
claims, SOTA claims, breakthrough claims, full-security claims, global
software-agent uniqueness claims, or authority to execute an action.

Exit criteria: the backend-run artifact has a local, digest-bound `NotRun`
metadata representation with negative coverage for execution and claim
escalation, while remaining below backend execution and accepted evidence.

## Phase 277 HSAI Gateway Formal Backend Run Materialized Bundle Boundary

Status: complete. See
`docs/277-hsai-gateway-formal-backend-run-materialized-bundle-boundary.md`.

Goal: define the docs-first filesystem contract for a future materialized
`gateway-formal-backend-run/*` bundle before implementation code writes or reads
those files.

Implemented: added a materialized bundle boundary that defines output-root
rules, protected-root and symlink rejection, exact declared files, required
SHA-256 sidecars, manifest fields, bounded file semantics, redaction-report
rules, optional proof/checker/tool-log attachment rejection, readback drift
checks, required future tests, anti-goals, and next implementation slice.

Validation gate: docs hygiene, boundary claim review, repo hygiene, formatting,
diff hygiene, and workspace tests.

Anti-goals: Rust implementation changes, Cargo metadata changes, package
runtime files, filesystem bundle materialization code, proof assistant setup
files, external repo clones, vendored source, Lean, Coq, TLA+, SMT, Z3, CBMC,
model-checker, Aeneas, Hax, rust-lean, or COBALT execution, generated proof
artifacts, generated checker transcripts, raw prover logs, raw checker logs,
accepted Evidence Ledger mutation, Level2+ evidence, score-axis population,
benchmark evidence, official benchmark submission, live provider calls,
credential handling, semantic-correctness claims, production-readiness claims,
SOTA claims, breakthrough claims, full-security claims, global software-agent
uniqueness claims, or authority to execute an action.

Exit criteria: the future backend-run bundle has an explicit materialized-file
contract with fail-closed readback requirements and no authorization to execute
a backend or promote evidence.

## Phase 278 HSAI Gateway Formal Backend Run Inert Bundle Materialization

Status: complete. See
`docs/278-hsai-gateway-formal-backend-run-inert-bundle-materialization-notes.md`.

Goal: implement local inert materialization and readback for the Phase 277
`gateway-formal-backend-run/*` bundle without running a backend or promoting
evidence.

Implemented: added backend-run output request, toolchain-lock, redaction-report,
manifest, and error types; declared file and sidecar constants; deterministic
bundle construction; staged writes; output-root validation; sidecar generation;
readback; undeclared-file rejection; sidecar digest checks; manifest semantic
validation; redaction-report checking; nonclaim checking; optional attachment
rejection; and focused tests for valid readback, escalated metadata rejection,
optional proof attachment rejection, and digest-consistent semantic drift.

Validation gate: focused backend-run tests, formatting, docs hygiene, repo
hygiene, diff hygiene, and full workspace tests.

Anti-goals: backend execution, proof assistant setup files, external repo
clones, vendored source, Lean, Coq, TLA+, SMT, Z3, CBMC, model-checker, Aeneas,
Hax, rust-lean, or COBALT execution, generated proof artifacts, generated
checker transcripts, raw prover logs, raw checker logs, raw solver traces,
accepted Evidence Ledger mutation, Level2+ evidence, score-axis population,
benchmark evidence, official benchmark submission, live provider calls,
credential handling, semantic-correctness claims, production-readiness claims,
SOTA claims, breakthrough claims, full-security claims, global software-agent
uniqueness claims, or authority to execute an action.

Exit criteria: the backend-run bundle can be materialized and read back as a
local `NotRun` metadata bundle with digest-bound semantics and no evidence
promotion.

## Phase 279 HSAI Gateway Formal Backend Run Bundle Drift Coverage

Status: complete. See
`docs/279-hsai-gateway-formal-backend-run-bundle-drift-coverage-notes.md`.

Goal: add audit-first negative coverage for the Phase 278 backend-run bundle
reader without changing the bundle format or running a backend.

Implemented: added tests for protected output-root rejection, file output-root
rejection, symlink output-root rejection, stale run-summary sidecar rejection,
manifest nonpromotion-flag drift rejection, malformed run-summary JSON
rejection, redaction-report drift rejection, nonclaim Markdown drift rejection,
and symlink declared-file rejection.

Validation gate: focused backend-run tests, formatting, docs hygiene, repo
hygiene, diff hygiene, and full workspace tests.

Anti-goals: production bundle semantic changes, backend execution, proof
assistant setup files, external repo clones, vendored source, Lean, Coq, TLA+,
SMT, Z3, CBMC, model-checker, Aeneas, Hax, rust-lean, or COBALT execution,
generated proof artifacts, generated checker transcripts, raw prover logs, raw
checker logs, raw solver traces, accepted Evidence Ledger mutation, Level2+
evidence, score-axis population, benchmark evidence, official benchmark
submission, live provider calls, credential handling, semantic-correctness
claims, production-readiness claims, SOTA claims, breakthrough claims,
full-security claims, global software-agent uniqueness claims, or authority to
execute an action.

Exit criteria: the Phase 278 reader now has focused failure coverage for
root/file/symlink drift, sidecar drift, manifest drift, redaction drift,
nonclaim drift, malformed run-summary JSON, and symlinked declared files.

## Phase 280 HSAI Gateway Formal Backend Execution Preflight Boundary

Status: complete. See
`docs/280-hsai-gateway-formal-backend-execution-preflight-boundary.md`.

Goal: define the docs-first preflight boundary that must exist before any
future Lean, SMT, COBALT, Rust-to-Lean, Aeneas, Hax, Z3, CBMC, Coq, TLA+, or
model-checker command can run.

Implemented: added a backend execution preflight boundary defining required
future inputs, inert argv-only command descriptors, allowed future backend
modes, environment rules, artifact-root rules, operator acknowledgement,
preflight output shape, required future tests, anti-goals, and next
implementation slice.

Validation gate: docs hygiene, boundary claim review, repo hygiene, formatting,
diff hygiene, and full workspace tests.

Anti-goals: Rust implementation changes, Cargo metadata changes, package
runtime files, command execution, process spawning, proof assistant setup files,
external repo clones, vendored source, Lean, Coq, TLA+, SMT, Z3, CBMC,
model-checker, Aeneas, Hax, rust-lean, or COBALT execution, generated proof
artifacts, generated checker transcripts, raw prover logs, raw checker logs,
raw solver traces, accepted Evidence Ledger mutation, Level2+ evidence,
score-axis population, benchmark evidence, official benchmark submission, live
provider calls, credential handling, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, global software-agent uniqueness claims, or authority to execute an
action.

Exit criteria: the future backend execution lane now has an explicit preflight
contract for command, environment, artifact-root, operator acknowledgement,
no-network, no-secret, and nonpromotion rules before code mutation.

## Phase 281 HSAI Gateway Formal Backend Execution Preflight Inert Metadata

Status: complete. See
`docs/281-hsai-gateway-formal-backend-execution-preflight-inert-metadata-notes.md`.

Goal: implement the Phase 280 backend execution preflight boundary as pure
metadata and validation in `hsai-agent-admission`, without running any command.

Implemented: added preflight request/report types, backend preflight modes,
argv-only command descriptors, environment descriptors, artifact-root
descriptors, operator acknowledgement metadata, redaction-policy metadata,
digest helpers, fail-closed validation, and focused tests for candidate-only
acceptance and drift rejection.

Validation gate: focused `hsai-agent-admission` tests, formatting, diff hygiene,
repo hygiene, and full workspace tests.

Anti-goals: command execution, process spawning, backend runner implementation,
filesystem materialization for preflight output bundles, Cargo metadata changes,
package runtime files, proof assistant setup files, external repo clones,
vendored source, Lean, Coq, TLA+, SMT, Z3, CBMC, model-checker, Aeneas, Hax,
rust-lean, or COBALT execution, generated proof artifacts, generated checker
transcripts, raw prover logs, raw checker logs, raw solver traces, accepted
Evidence Ledger mutation, Level2+ evidence, score-axis population, benchmark
evidence, official benchmark submission, live provider calls, credential
handling, semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, full-security claims, global software-agent uniqueness
claims, or authority to execute an action.

Exit criteria: Phase 281 can now decide whether a future backend execution
command descriptor is preflight-ready as local metadata only. It still cannot
execute the command or create proof/checker artifacts.

## Phase 282 HSAI Gateway Formal Backend Preflight Output-Bundle Boundary

Status: complete. See
`docs/282-hsai-gateway-formal-backend-preflight-output-bundle-boundary.md`.

Goal: define the docs-first filesystem output-bundle contract for future
materialization of Phase 281 preflight metadata.

Implemented: added a boundary spec for
`gateway-formal-backend-preflight/*` declared files, SHA-256 sidecars,
output-root rules, manifest fields, readback drift checks, required future
tests, anti-goals, and next implementation slice.

Validation gate: docs hygiene, boundary claim review, formatting, diff hygiene,
repo hygiene, and full workspace tests.

Anti-goals: Rust implementation changes, Cargo metadata changes, package
runtime files, filesystem bundle materialization code, command execution,
process spawning, backend runner implementation, proof assistant setup files,
external repo clones, vendored source, Lean, Coq, TLA+, SMT, Z3, CBMC,
model-checker, Aeneas, Hax, rust-lean, or COBALT execution, generated proof
artifacts, generated checker transcripts, raw prover logs, raw checker logs,
raw solver traces, accepted Evidence Ledger mutation, Level2+ evidence,
score-axis population, benchmark evidence, official benchmark submission, live
provider calls, credential handling, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, global software-agent uniqueness claims, or authority to execute an
action.

Exit criteria: the future preflight materialization lane now has an explicit
declared-file, sidecar, manifest, output-root, and readback contract before any
Rust implementation is authorized.

## Phase 283 HSAI Gateway Formal Backend Preflight Output-Bundle Implementation

Status: complete. See
`docs/283-hsai-gateway-formal-backend-preflight-output-bundle-implementation-notes.md`.

Goal: implement the Phase 282 preflight output-bundle contract as local
filesystem materialization and readback in `hsai-agent-admission`.

Implemented: added preflight output request, manifest, error type, declared
files, SHA-256 sidecars, staged writes, readback validation, manifest
recomputation, semantic drift rejection, and focused tests.

Validation gate: focused `hsai-agent-admission` tests, formatting, diff
hygiene, repo hygiene, and full workspace tests.

Anti-goals: command execution, process spawning, backend runner implementation,
proof assistant setup files, external repo clones, vendored source, Lean, Coq,
TLA+, SMT, Z3, CBMC, model-checker, Aeneas, Hax, rust-lean, or COBALT
execution, generated proof artifacts, generated checker transcripts, raw prover
logs, raw checker logs, raw solver traces, accepted Evidence Ledger mutation,
Level2+ evidence, score-axis population, benchmark evidence, official benchmark
submission, live provider calls, credential handling, semantic-correctness
claims, production-readiness claims, SOTA claims, breakthrough claims,
full-security claims, global software-agent uniqueness claims, or authority to
execute an action.

Exit criteria: Phase 281 preflight metadata can now be materialized and read
back as a bounded local metadata bundle. It still cannot execute any backend or
create proof/checker artifacts.

## Phase 284 HSAI Gateway Formal Backend Execution Transcript Boundary

Status: complete. See
`docs/284-hsai-gateway-formal-backend-execution-transcript-boundary.md`.

Goal: define the docs-first boundary for future backend execution transcript
references and checker-output admission rules.

Implemented: added a boundary spec for future transcript metadata, proof and
checker reference rules, checker-output admission requirements, required future
tests, anti-goals, and next implementation slice.

Validation gate: docs hygiene, boundary claim review, formatting, diff hygiene,
repo hygiene, and full workspace tests.

Anti-goals: Rust implementation changes, Cargo metadata changes, package
runtime files, filesystem transcript bundle materialization code, command
execution, process spawning, backend runner implementation, proof assistant
setup files, external repo clones, vendored source, Lean, Coq, TLA+, SMT, Z3,
CBMC, model-checker, Aeneas, Hax, rust-lean, or COBALT execution, generated
proof artifacts, generated checker transcripts, raw prover logs, raw checker
logs, raw solver traces, accepted Evidence Ledger mutation, Level2+ evidence,
score-axis population, benchmark evidence, official benchmark submission, live
provider calls, credential handling, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, global software-agent uniqueness claims, or authority to execute an
action.

Exit criteria: the future transcript lane now has an explicit reference,
redaction, checker-output, and nonpromotion boundary before any Rust
implementation is authorized.

## Phase 285 HSAI Gateway Formal Backend Execution Transcript Inert Metadata

Status: complete. See
`docs/285-hsai-gateway-formal-backend-execution-transcript-inert-metadata-notes.md`.

Goal: implement local transcript metadata and validation for a future backend
execution transcript candidate without running a backend or materializing
transcript files.

Implemented: added transcript schema/state/claim-boundary constants, execution
and checker status labels, transcript reference metadata, redaction report
metadata, `GatewayFormalBackendExecutionTranscriptMetadata`, validation issue
labels, deterministic digesting, a Phase 283 preflight-bound metadata builder,
and fail-closed validation for preflight binding, command/toolchain binding,
transcript references, redaction retention, proof-obligation submission,
trust-root submission, nonpromotion flags, forbidden public claim text, and
required nonclaims.

Validation gate: `cargo fmt --all -- --check`,
`cargo test -p hsai-agent-admission gateway_formal_backend_transcript`, full
workspace tests, diff hygiene, repo hygiene, and package-script detection.

Anti-goals: Cargo metadata changes, package runtime files, filesystem
transcript bundle materialization code, command execution, process spawning,
backend runner implementation, proof assistant setup files, external repo
clones, vendored source, Lean, Coq, TLA+, SMT, Z3, CBMC, model-checker, Aeneas,
Hax, rust-lean, or COBALT execution, generated proof artifacts, generated
checker transcripts, raw prover logs, raw checker logs, raw solver traces,
accepted Evidence Ledger mutation, Level2+ evidence, score-axis population,
benchmark evidence, official benchmark submission, live provider calls,
credential handling, semantic-correctness claims, production-readiness claims,
SOTA claims, breakthrough claims, full-security claims, global software-agent
uniqueness claims, or authority to execute an action.

Exit criteria: HSAI gateway formal backend transcript metadata can be built and
validated as an inert candidate bound to a Phase 283 preflight bundle. It still
cannot execute a backend, create proof/checker artifacts, create accepted
evidence, populate score axes, or support SOTA/full-security/semantic
correctness/production-readiness claims.

## Phase 286 HSAI Gateway Formal Backend Transcript Output-Bundle Boundary

Status: complete. See
`docs/286-hsai-gateway-formal-backend-transcript-output-bundle-boundary.md`.

Goal: define the docs-first filesystem contract for future transcript metadata
materialization and readback.

Implemented: added a boundary spec for declared
`gateway-formal-backend-transcript/*` files, SHA-256 sidecars, output-root
rules, manifest fields, file semantics, readback drift checks, required future
tests, anti-goals, explicit nonclaims, and next implementation slice.

Validation gate: docs hygiene, boundary claim review, formatting, diff hygiene,
repo hygiene, and full workspace tests.

Anti-goals: Rust implementation changes, Cargo metadata changes, package
runtime files, filesystem bundle materialization code, command execution,
process spawning, backend runner implementation, proof assistant setup files,
external repo clones, vendored source, Lean, Coq, TLA+, SMT, Z3, CBMC,
model-checker, Aeneas, Hax, rust-lean, or COBALT execution, generated proof
artifacts, generated checker transcripts, raw prover logs, raw checker logs,
raw solver traces, accepted Evidence Ledger mutation, Level2+ evidence,
score-axis population, benchmark evidence, official benchmark submission, live
provider calls, credential handling, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, global software-agent uniqueness claims, or authority to execute an
action.

Exit criteria: the future transcript metadata output bundle now has an explicit
declared-file, sidecar, manifest, readback, redaction, and nonpromotion boundary
before any Rust implementation is authorized.

## Phase 287 HSAI Gateway Formal Backend Transcript Output-Bundle Implementation

Status: complete. See
`docs/287-hsai-gateway-formal-backend-transcript-output-bundle-implementation-notes.md`.

Goal: implement local materialization and readback for inert Phase 285
transcript metadata.

Implemented: added transcript output request, manifest, component records,
error types, declared `gateway-formal-backend-transcript/*` files, SHA-256
sidecars, staged writes, output-root validation, invalid transcript rejection
before write, exact metadata-builder drift rejection before write, readback
validation, manifest recomputation, preflight-binding checks, toolchain-binding
checks, execution-status checks, checker-status checks, redaction-report checks,
proof-obligation checks, nonclaim Markdown checks, and undeclared-file
rejection.

Validation gate: `cargo fmt --all -- --check`,
`cargo test -p hsai-agent-admission gateway_formal_backend_transcript_output_bundle`,
full workspace tests, diff hygiene, repo hygiene, and package-script detection.

Anti-goals: Cargo metadata changes, package runtime files, command execution,
process spawning, backend runner implementation, proof assistant setup files,
external repo clones, vendored source, Lean, Coq, TLA+, SMT, Z3, CBMC,
model-checker, Aeneas, Hax, rust-lean, or COBALT execution, generated proof
artifacts, generated checker transcripts, raw prover logs, raw checker logs,
raw solver traces, accepted Evidence Ledger mutation, Level2+ evidence,
score-axis population, benchmark evidence, official benchmark submission, live
provider calls, credential handling, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, global software-agent uniqueness claims, or authority to execute an
action.

Exit criteria: HSAI gateway formal backend transcript metadata can now be
materialized and read back as a bounded local metadata bundle. It still cannot
execute a backend, create proof/checker artifacts, create accepted evidence,
populate score axes, or support SOTA/full-security/semantic
correctness/production-readiness claims.

## Phase 288 HSAI Gateway Formal Backend Transcript Output-Bundle Drift Coverage

Status: complete. See
`docs/288-hsai-gateway-formal-backend-transcript-output-bundle-drift-coverage-notes.md`.

Goal: broaden negative readback coverage for Phase 287 transcript output
bundles without broadening the execution or claim boundary.

Implemented: added tests for stale transcript metadata sidecars, missing
manifest sidecars, malformed transcript metadata JSON, nonclaim Markdown drift,
proof-obligation drift, preflight-binding drift, checker-status drift,
protected output-root rejection, declared-file symlink rejection, and
declared-sidecar symlink rejection.

Validation gate: `cargo fmt --all -- --check`,
`cargo test -p hsai-agent-admission gateway_formal_backend_transcript_output_bundle`,
full workspace tests, diff hygiene, repo hygiene, and package-script detection.

Anti-goals: Cargo metadata changes, package runtime files, command execution,
process spawning, backend runner implementation, proof assistant setup files,
external repo clones, vendored source, Lean, Coq, TLA+, SMT, Z3, CBMC,
model-checker, Aeneas, Hax, rust-lean, or COBALT execution, generated proof
artifacts, generated checker transcripts, raw prover logs, raw checker logs,
raw solver traces, accepted Evidence Ledger mutation, Level2+ evidence,
score-axis population, benchmark evidence, official benchmark submission, live
provider calls, credential handling, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, global software-agent uniqueness claims, or authority to execute an
action.

Exit criteria: Phase 287 transcript output bundles now reject broader
filesystem, sidecar, malformed JSON, semantic drift, symlink, and protected-root
failure modes while remaining local metadata only.

## Phase 289 HSAI Gateway Formal Backend Execution Authorization Boundary

Status: complete. See
`docs/289-hsai-gateway-formal-backend-execution-authorization-boundary.md`.

Goal: define the docs-first authorization boundary for a future
operator-approved local formal backend execution experiment.

Implemented: added a boundary spec for future authorization metadata,
execution preconditions, output quarantine rules, transcript admission rules,
required future tests, anti-goals, explicit nonclaims, and next implementation
slice.

Validation gate: docs hygiene, boundary claim review, formatting, diff hygiene,
repo hygiene, and full workspace tests.

Anti-goals: Rust implementation changes, Cargo metadata changes, package
runtime files, command execution, process spawning, backend runner
implementation, proof assistant setup files, external repo clones, vendored
source, Lean, Coq, TLA+, SMT, Z3, CBMC, model-checker, Aeneas, Hax, rust-lean,
or COBALT execution, generated proof artifacts, generated checker transcripts,
raw prover logs, raw checker logs, raw solver traces, accepted Evidence Ledger
mutation, Level2+ evidence, score-axis population, benchmark evidence,
official benchmark submission, live provider calls, credential handling,
semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, full-security claims, global software-agent uniqueness
claims, or authority to execute an action.

Exit criteria: the future backend execution lane now has an explicit
authorization, quarantine, transcript-admission, and nonpromotion boundary
before any Rust implementation or command execution is authorized.

## Phase 290 HSAI Gateway Formal Backend Execution Authorization Inert Metadata

Status: complete. See
`docs/290-hsai-gateway-formal-backend-execution-authorization-inert-metadata-notes.md`.

Goal: implement local inert authorization metadata for a future
operator-approved formal backend execution experiment.

Implemented: added execution-authorization schema/state/claim-boundary
constants, quarantine descriptor metadata, operator acknowledgement metadata,
authorization request metadata, deterministic digest helpers, required
nonclaims, builder helpers, validation issue labels, and fail-closed validation
for Phase 283 preflight bundle binding, Phase 287 transcript output-bundle
binding, command/argv/toolchain drift, timeout and output-retention drift,
environment and network/secret policy drift, quarantine-root drift,
operator-acknowledgement drift, proof-obligation submission, nonpromotion
flags, forbidden public-claim text, and required nonclaims.

Validation gate: `cargo fmt --all -- --check`, focused
`hsai-agent-admission` authorization tests, full workspace tests, diff hygiene,
empty-file hygiene, and package-root lint check.

Anti-goals: Cargo metadata changes, package runtime files, filesystem
authorization bundle materialization, command execution, process spawning,
backend runner implementation, proof assistant setup files, external repo
clones, vendored source, Lean, Coq, TLA+, SMT, Z3, CBMC, model-checker, Aeneas,
Hax, rust-lean, or COBALT execution, generated proof artifacts, generated
checker transcripts, raw prover logs, raw checker logs, raw solver traces,
accepted Evidence Ledger mutation, Level2+ evidence, score-axis population,
benchmark evidence, official benchmark submission, live provider calls,
credential handling, semantic-correctness claims, production-readiness claims,
SOTA claims, breakthrough claims, full-security claims, global software-agent
uniqueness claims, or authority to execute an action.

Exit criteria: HSAI now has a local metadata-only authorization record for the
future backend execution lane, with digest binding and fail-closed policy
validation, while still creating no execution, proof artifact, checker
transcript, accepted evidence, Level2+ evidence, score axes, or stronger public
claim.

## Phase 291 HSAI Gateway Formal Backend Execution Authorization Output-Bundle Boundary

Status: complete. See
`docs/291-hsai-gateway-formal-backend-execution-authorization-output-bundle-boundary.md`.

Goal: define the docs-first filesystem boundary for a future local output bundle
over Phase 290 inert execution-authorization metadata.

Implemented: added the boundary spec for future
`gateway-formal-backend-authorization/*` declared files, SHA-256 sidecars,
manifest fields, authorization/preflight/transcript/command/environment/
quarantine/operator binding rules, readback rejection rules, required future
tests, anti-goals, explicit nonclaims, and next implementation slice.

Validation gate: docs hygiene, boundary claim review, formatting, diff hygiene,
empty-file hygiene, package-root lint check, and full workspace tests.

Anti-goals: Rust implementation changes, Cargo metadata changes, package
runtime files, filesystem authorization bundle materialization, command
execution, process spawning, backend runner implementation, proof assistant
setup files, external repo clones, vendored source, Lean, Coq, TLA+, SMT, Z3,
CBMC, model-checker, Aeneas, Hax, rust-lean, or COBALT execution, generated
proof artifacts, generated checker transcripts, raw prover logs, raw checker
logs, raw solver traces, accepted Evidence Ledger mutation, Level2+ evidence,
score-axis population, benchmark evidence, official benchmark submission, live
provider calls, credential handling, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, global software-agent uniqueness claims, or authority to execute an
action.

Exit criteria: the future authorization output-bundle lane now has an explicit
declared-file, sidecar, manifest, readback, quarantine, nonpromotion, and
claim-boundary contract before any Rust materializer or backend execution is
authorized.

## Phase 292 HSAI Gateway Formal Backend Execution Authorization Output-Bundle Implementation

Status: complete. See
`docs/292-hsai-gateway-formal-backend-execution-authorization-output-bundle-implementation-notes.md`.

Goal: implement local filesystem materialization and readback for Phase 290
inert execution-authorization metadata.

Implemented: added authorization output-bundle state/claim constants, output
schema and declared file constants, output request and manifest types,
component binding records, output error labels, staged writes, SHA-256
sidecars, output-root validation, invalid authorization rejection before write,
readback validation, manifest recomputation, component binding checks,
nonclaim Markdown checks, undeclared-file rejection, and focused hermetic tests.

Validation gate: `cargo fmt --all -- --check`, focused
`hsai-agent-admission` authorization output-bundle tests, full workspace tests,
diff hygiene, empty-file hygiene, and package-root lint check.

Anti-goals: Cargo metadata changes, package runtime files, command execution,
process spawning, backend runner implementation, proof assistant setup files,
external repo clones, vendored source, Lean, Coq, TLA+, SMT, Z3, CBMC,
model-checker, Aeneas, Hax, rust-lean, or COBALT execution, generated proof
artifacts, generated checker transcripts, raw prover logs, raw checker logs,
raw solver traces, accepted Evidence Ledger mutation, Level2+ evidence,
score-axis population, benchmark evidence, official benchmark submission, live
provider calls, credential handling, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, global software-agent uniqueness claims, or authority to execute an
action.

Exit criteria: Phase 290 authorization metadata can now be materialized and
read back as a local, declared-file, digest-bound output bundle while still
creating no command execution, proof artifact, checker transcript, accepted
evidence, Level2+ evidence, score axes, or stronger public claim.

## Phase 293 HSAI Gateway Formal Backend Execution Quarantine Artifact Boundary

Status: complete. See
`docs/293-hsai-gateway-formal-backend-execution-quarantine-artifact-boundary.md`.

Goal: define the docs-first quarantine artifact boundary that must exist before
any future formal backend runner can record process results.

Implemented: added a boundary spec for future quarantine artifact metadata,
authorization/preflight/transcript binding requirements, bounded retained
summary rules, disallowed raw logs and proof/checker artifacts, required
rejection paths, required future tests, anti-goals, explicit nonclaims, and the
next implementation slice.

Validation gate: docs hygiene, boundary claim review, formatting, diff hygiene,
empty-file hygiene, package-root lint check, and full workspace tests.

Anti-goals: Rust implementation changes, Cargo metadata changes, package
runtime files, command execution, process spawning, backend runner
implementation, proof assistant setup files, external repo clones, vendored
source, Lean, Coq, TLA+, SMT, Z3, CBMC, model-checker, Aeneas, Hax, rust-lean,
or COBALT execution, generated proof artifacts, generated checker transcripts,
raw prover logs, raw checker logs, raw solver traces, accepted Evidence Ledger
mutation, Level2+ evidence, score-axis population, benchmark evidence,
official benchmark submission, live provider calls, credential handling,
semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, full-security claims, global software-agent uniqueness
claims, or authority to execute an action.

Exit criteria: the future execution quarantine lane now has an explicit
bounded-retention, write-path, proof/checker nonpromotion, and public-claim
boundary before any Rust quarantine metadata or backend runner implementation is
authorized.

## Phase 294 HSAI Gateway Formal Backend Execution Quarantine Artifact Inert Metadata

Status: complete. See
`docs/294-hsai-gateway-formal-backend-execution-quarantine-artifact-inert-metadata-notes.md`.

Goal: add inert local quarantine artifact metadata for bounded, redacted
operator-supplied process-result summaries without executing a command.

Implemented: added quarantine artifact schema/state/claim constants, output
summary metadata, output file references, redaction reports, proof/checker
nonpromotion reports, quarantine artifact metadata, issue labels, validation
results, required nonclaims, a deterministic builder, and fail-closed validation
against the Phase 292 authorization output manifest.

Validation gate: focused Phase 294 tests, formatting, diff hygiene,
empty-file hygiene, package-root lint check, and full workspace tests.

Anti-goals: command execution, process spawning, backend runner implementation,
filesystem quarantine bundle materialization, proof assistant setup files,
external repo clones, vendored source, Lean, Coq, TLA+, SMT, Z3, CBMC,
model-checker, Aeneas, Hax, rust-lean, or COBALT execution, generated proof
artifact promotion, generated checker transcript promotion, raw prover log
retention, raw checker log retention, raw solver trace retention, accepted
Evidence Ledger mutation, Level2+ evidence, score-axis population, benchmark
evidence, official benchmark submission, live provider calls, credential
handling, semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, full-security claims, global software-agent uniqueness
claims, or authority to execute an action.

Exit criteria: HSAI can now validate a local, authorization-bound,
process-result quarantine artifact as scoped metadata while preserving explicit
nonclaims that process success, checker success, and proof/checker artifacts are
not accepted evidence, semantic correctness, production readiness, SOTA, full
security, or execution authority.

## Phase 295 HSAI Gateway Formal Backend Quarantine Output-Bundle Boundary

Status: complete. See
`docs/295-hsai-gateway-formal-backend-quarantine-output-bundle-boundary.md`.

Goal: define the docs-first filesystem output-bundle contract for future
materialization of Phase 294 quarantine artifact metadata.

Implemented: added a boundary spec for the future
`gateway-formal-backend-quarantine/*` bundle namespace, declared files,
SHA-256 sidecars, manifest fields, readback rules, required rejection paths,
required future tests, anti-goals, explicit nonclaims, and next implementation
slice.

Validation gate: docs hygiene, boundary claim review, formatting, diff hygiene,
empty-file hygiene, package-root lint check, and full workspace tests.

Anti-goals: Rust implementation changes, Cargo metadata changes, package
runtime files, filesystem quarantine bundle materialization, command execution,
process spawning, backend runner implementation, proof assistant setup files,
external repo clones, vendored source, Lean, Coq, TLA+, SMT, Z3, CBMC,
model-checker, Aeneas, Hax, rust-lean, or COBALT execution, generated proof
artifact promotion, generated checker transcript promotion, raw prover log
retention, raw checker log retention, raw solver trace retention, accepted
Evidence Ledger mutation, Level2+ evidence, score-axis population, benchmark
evidence, official benchmark submission, live provider calls, credential
handling, semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, full-security claims, global software-agent uniqueness
claims, or authority to execute an action.

Exit criteria: the future quarantine output-bundle lane now has an explicit
declared-file, sidecar, manifest, readback, drift-rejection, nonpromotion, and
public-claim boundary before any Rust filesystem materialization is authorized.

## Phase 296 HSAI Gateway Formal Backend Quarantine Output-Bundle Implementation

Status: complete. See
`docs/296-hsai-gateway-formal-backend-quarantine-output-bundle-implementation-notes.md`.

Goal: implement local filesystem materialization and readback for the declared
Phase 295 quarantine output bundle.

Implemented: added quarantine output-bundle state/claim constants, declared
file and sidecar lists, output request and manifest types, authorization
binding and process-status records, output error labels, staged writes,
SHA-256 sidecars, output-root validation, invalid quarantine artifact rejection
before write, readback validation, manifest recomputation, component binding
checks, nonclaim Markdown checks, undeclared-file rejection, and focused
hermetic tests.

Validation gate: focused Phase 296 tests, formatting, diff hygiene,
empty-file hygiene, package-root lint check, and full workspace tests.

Anti-goals: command execution, process spawning, backend runner implementation,
proof assistant setup files, external repo clones, vendored source, Lean, Coq,
TLA+, SMT, Z3, CBMC, model-checker, Aeneas, Hax, rust-lean, or COBALT
execution, generated proof artifact promotion, generated checker transcript
promotion, raw prover log retention, raw checker log retention, raw solver
trace retention, accepted Evidence Ledger mutation, Level2+ evidence,
score-axis population, benchmark evidence, official benchmark submission, live
provider calls, credential handling, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, global software-agent uniqueness claims, or authority to execute an
action.

Exit criteria: Phase 294 quarantine metadata can now be materialized and read
back as a local, declared-file, digest-bound output bundle while still creating
no command execution, proof artifact promotion, checker transcript promotion,
accepted evidence, Level2+ evidence, score axes, or stronger public claim.

## Phase 297 HSAI Gateway Formal Backend Quarantine Output-Bundle Drift Coverage Boundary

Status: complete. See
`docs/297-hsai-gateway-formal-backend-quarantine-output-bundle-drift-coverage-boundary.md`.

Goal: define the next focused negative-test slice for Phase 296 quarantine
output-bundle readback drift.

Implemented: added a docs-first boundary naming the future drift coverage for
protected roots, missing sidecars, malformed JSON, authorization binding drift,
process-status drift, stderr drift, redaction drift, inventory drift,
proof/checker nonpromotion drift, symlink rejection, undeclared raw logs,
undeclared proof/checker artifacts, undeclared accepted Evidence Ledger paths,
undeclared benchmark outputs, and undeclared earlier formal-bundle paths.

Validation gate: docs hygiene, boundary claim review, formatting, diff hygiene,
empty-file hygiene, package-root lint check, and full workspace tests.

Anti-goals: Rust implementation changes, Cargo metadata changes, package
runtime files, new bundle materialization behavior, command execution, process
spawning, backend runner implementation, proof assistant setup files, external
repo clones, vendored source, Lean, Coq, TLA+, SMT, Z3, CBMC, model-checker,
Aeneas, Hax, rust-lean, or COBALT execution, generated proof artifact
promotion, generated checker transcript promotion, raw prover log retention,
raw checker log retention, raw solver trace retention, accepted Evidence Ledger
mutation, Level2+ evidence, score-axis population, benchmark evidence,
official benchmark submission, live provider calls, credential handling,
semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, full-security claims, global software-agent uniqueness
claims, or authority to execute an action.

Exit criteria: the next quarantine output-bundle test slice is now explicitly
bounded to negative readback coverage and cannot be interpreted as backend
execution, proof/checker promotion, accepted evidence, Level2+ evidence, score
axes, or stronger public claims.

## Phase 298 HSAI Gateway Formal Backend Quarantine Output-Bundle Drift Coverage Implementation

Status: complete. See
`docs/298-hsai-gateway-formal-backend-quarantine-output-bundle-drift-coverage-implementation-notes.md`.

Goal: implement the Phase 297 focused drift-coverage test slice for the Phase
296 quarantine output-bundle readback path.

Implemented: added local tests for protected output roots, overwrite rejection,
missing sidecars, malformed declared JSON, authorization binding drift,
process-status drift, stderr summary drift, redaction report drift, output
inventory drift, proof/checker nonpromotion report drift, undeclared raw logs,
undeclared proof/checker artifacts, undeclared accepted Evidence Ledger paths,
undeclared benchmark outputs, undeclared earlier formal-bundle paths, and Unix
symlink rejection for output roots, bundle directories, declared files, and
declared sidecars.

Validation gate: focused `hsai-agent-admission` quarantine output-bundle tests,
formatting, diff hygiene, empty-file hygiene, package-root lint check, and full
workspace tests.

Anti-goals: public API changes, Cargo metadata changes, package runtime files,
command execution, process spawning, backend runner implementation, proof
assistant setup files, external repo clones, vendored source, Lean, Coq, TLA+,
SMT, Z3, CBMC, model-checker, Aeneas, Hax, rust-lean, or COBALT execution,
generated proof/checker promotion, accepted evidence, Level2+, score axes,
benchmark evidence, semantic-correctness, production-readiness, SOTA,
breakthrough, full-security, or authority claims.

## Phase 299 HSAI Gateway Formal Backend Quarantine Validation-Summary Boundary

Status: complete. See
`docs/299-hsai-gateway-formal-backend-quarantine-validation-summary-boundary.md`.

Goal: define the docs-first boundary for a future local validation-summary
artifact over the Phase 296 quarantine output-bundle and Phase 298 drift tests.

Implemented: specified the future summary fields, required coverage labels,
required fail-closed validation paths, evidence meaning, nonclaims, anti-goals,
and next implementation scope.

Validation gate: docs hygiene, boundary claim review, formatting, diff hygiene,
empty-file hygiene, package-root lint check, and full workspace tests.

Anti-goals: Rust implementation changes, Cargo metadata changes, package
runtime files, command execution, process spawning, backend runner
implementation, proof assistant setup files, external repo clones, vendored
source, Lean, Coq, TLA+, SMT, Z3, CBMC, model-checker, Aeneas, Hax, rust-lean,
or COBALT execution, generated proof/checker promotion, accepted evidence,
Level2+, score axes, benchmark evidence, semantic-correctness,
production-readiness, SOTA, breakthrough, full-security, or authority claims.

## Phase 300 HSAI Gateway Formal Backend Quarantine Validation-Summary Implementation

Status: complete. See
`docs/300-hsai-gateway-formal-backend-quarantine-validation-summary-implementation-notes.md`.

Goal: implement the Phase 299 pure-data validation-summary surface for the
Phase 296 quarantine output bundle and Phase 298 drift tests.

Implemented: added validation-summary constants, data type, deterministic
digest helper, validation issue labels, validation result type, required
nonclaims, required coverage-label registries, required command-label registry,
summary builder from a quarantine output manifest, fail-closed validation
against that manifest, and focused tests for valid deterministic summaries,
identity/digest/coverage drift, claim escalation, command-label drift, and
missing nonclaims.

Validation gate: focused validation-summary tests, focused quarantine
output-bundle tests, formatting, diff hygiene, empty-file hygiene, package-root
lint check, and full workspace tests.

Anti-goals: filesystem materialization for the summary, public claim changes,
Cargo metadata changes, package runtime files, command execution, process
spawning, backend runner implementation, proof assistant setup files, external
repo clones, vendored source, Lean, Coq, TLA+, SMT, Z3, CBMC, model-checker,
Aeneas, Hax, rust-lean, or COBALT execution, generated proof/checker
promotion, accepted evidence, Level2+, score axes, benchmark evidence,
semantic-correctness, production-readiness, SOTA, breakthrough, full-security,
or authority claims.

## Phase 301 HSAI Gateway Formal Backend Quarantine Validation-Summary Output-Bundle Boundary

Status: complete. See
`docs/301-hsai-gateway-formal-backend-quarantine-validation-summary-output-bundle-boundary.md`.

Goal: define the docs-first filesystem boundary for a future local declared-file
bundle around the Phase 300 validation summary.

Implemented: specified future declared files and sidecars, future manifest
fields, readback rules, validation-report meaning, required future tests,
anti-goals, and next implementation scope.

Validation gate: docs hygiene, boundary claim review, formatting, diff hygiene,
empty-file hygiene, package-root lint check, and full workspace tests.

Anti-goals: Rust implementation changes, Cargo metadata changes, package
runtime files, filesystem materialization behavior, command execution, process
spawning, backend runner implementation, proof assistant setup files, external
repo clones, vendored source, Lean, Coq, TLA+, SMT, Z3, CBMC, model-checker,
Aeneas, Hax, rust-lean, or COBALT execution, generated proof/checker
promotion, accepted evidence, Level2+, score axes, benchmark evidence,
semantic-correctness, production-readiness, SOTA, breakthrough, full-security,
or authority claims.

## Phase 302 HSAI Gateway Formal Backend Quarantine Validation-Summary Output-Bundle Implementation

Status: complete. See
`docs/302-hsai-gateway-formal-backend-quarantine-validation-summary-output-bundle-implementation-notes.md`.

Goal: implement the Phase 301 local declared-file output-bundle surface for the
Phase 300 validation summary.

Implemented: added output-bundle constants, declared file and sidecar
registries, output request type, coverage-labels record, validation-report
record, output manifest and digest helper, error labels, staged
materialization, readback, undeclared-file rejection, stale-sidecar rejection,
semantic readback for summary/source manifest/coverage labels/nonclaims/
validation report/manifest, and focused tests.

Validation gate: focused validation-summary output-bundle tests, focused
validation-summary tests, focused quarantine output-bundle tests, formatting,
diff hygiene, empty-file hygiene, package-root lint check, and full workspace
tests.

Anti-goals: backend command execution, proof artifact reads, checker transcript
promotion, accepted evidence, Level2+, score axes, benchmark evidence,
semantic-correctness, production-readiness, SOTA, breakthrough, full-security,
or authority claims.

## Phase 303 HSAI Gateway Formal Backend Hermetic Execution Boundary

Status: complete. See
`docs/303-hsai-gateway-formal-backend-hermetic-execution-boundary.md`.

Goal: define the first future point where the HSAI gateway formal lane may
cross from inert metadata into hermetic local backend execution.

Implemented: added a docs-first boundary for the
`local_smt_tiny_gateway_invariant` lane, including future input contracts,
future command descriptor rules, future quarantine output contract, future
readback rules, evidence meaning, required future tests, anti-goals, and the
next no-spawn implementation slice.

Validation gate: docs/reference scan, diff hygiene, empty-file hygiene,
package-root lint check, and full workspace tests.

Anti-goals: Rust implementation changes, command execution, process spawning,
backend runner implementation, proof artifact promotion, checker transcript
promotion, accepted evidence, Level2+, score axes, benchmark evidence,
semantic-correctness, production-readiness, SOTA, breakthrough, full-security,
or authority claims.

## Phase 304 HSAI Gateway Formal Backend Hermetic Execution No-Spawn Descriptor Implementation

Status: complete. See
`docs/304-hsai-gateway-formal-backend-hermetic-execution-no-spawn-descriptor-notes.md`.

Goal: implement the Phase 303 hermetic backend execution boundary as pure-data
descriptor metadata and fail-closed validation, still without process spawning.

Implemented: added descriptor/report schema constants, state and claim
boundary constants, lane/command/property enums, descriptor/report/validation
types, required nonclaims, a deterministic `local_smt_tiny_gateway_invariant`
descriptor builder, a fail-closed validator, a report builder, and focused
tests for valid no-spawn metadata, execution/claim escalation rejection,
shell/environment/raw-retention rejection, and digest sensitivity.

Validation gate: focused no-spawn descriptor tests, focused Phase 302
validation-summary output-bundle tests, repo docs/hygiene tests, formatting,
diff hygiene, empty-file hygiene, package-root lint check, and full workspace
tests.

Anti-goals: process spawning, backend execution, SMT/Z3/COBALT/Lean execution,
proof artifact reads or promotion, checker transcript promotion, accepted
evidence, Level2+, score axes, benchmark evidence, semantic-correctness,
production-readiness, SOTA, breakthrough, full-security, or authority claims.

## Phase 305 HSAI Gateway Formal Backend Hermetic Descriptor-Report Output-Bundle Boundary

Status: complete. See
`docs/305-hsai-gateway-formal-backend-hermetic-descriptor-report-output-bundle-boundary.md`.

Goal: define the future declared-file output-bundle boundary for the Phase 304
no-spawn descriptor report.

Implemented: added a docs-first boundary for future descriptor/report
materialization, declared files and SHA-256 sidecars, future manifest fields,
future readback rules, future validation-report meaning, required future tests,
anti-goals, and next implementation scope.

Validation gate: docs/reference scan, diff hygiene, empty-file hygiene,
package-root lint check, repo docs/hygiene tests, and full workspace tests.

Anti-goals: Rust implementation changes, filesystem materialization, process
spawning, backend execution, SMT/Z3/COBALT/Lean execution, proof artifact
promotion, checker transcript promotion, accepted evidence, Level2+, score
axes, benchmark evidence, semantic-correctness, production-readiness, SOTA,
breakthrough, full-security, or authority claims.

## Phase 306 HSAI Gateway Formal Backend Hermetic Descriptor-Report Output-Bundle Implementation

Status: complete. See
`docs/306-hsai-gateway-formal-backend-hermetic-descriptor-report-output-bundle-implementation-notes.md`.

Goal: implement the Phase 305 local declared-file output-bundle surface for the
Phase 304 no-spawn descriptor report.

Implemented: added output-bundle constants, declared file and sidecar
registries, output request type, command-contract record, validation-report
record, output manifest and digest helper, error labels, staged
materialization, readback, undeclared-file rejection, stale-sidecar rejection,
semantic readback for descriptor/report/validation/command-contract/nonclaims/
manifest, and focused tests.

Validation gate: focused descriptor-report output-bundle tests, focused
no-spawn descriptor tests, repo docs/hygiene tests, formatting, diff hygiene,
empty-file hygiene, package-root lint check, and full workspace tests.

Anti-goals: process spawning, backend execution, SMT/Z3/COBALT/Lean execution,
proof artifact reads or promotion, checker transcript promotion, accepted
evidence, Level2+, score axes, benchmark evidence, semantic-correctness,
production-readiness, SOTA, breakthrough, full-security, or authority claims.

## Phase 307 HSAI Gateway Formal Backend Hermetic Execution Result Quarantine Output-Bundle Boundary

Status: complete. See
`docs/307-hsai-gateway-formal-backend-hermetic-execution-result-quarantine-output-bundle-boundary.md`.

Goal: define the future declared-file output-bundle boundary for the first
local hermetic execution result quarantine shape.

Implemented: added a docs-first boundary for
`gateway-formal-backend-hermetic-execution-result-quarantine/*`, future
declared files and SHA-256 sidecars, manifest fields, execution-status meaning,
readback rejection rules, validation-report limits, required future tests, and
anti-goals.

Validation gate: docs/reference scan, diff hygiene, empty-file hygiene,
package-root lint check, repo docs/hygiene tests, and full workspace tests.

Anti-goals: Rust implementation, filesystem materialization, command execution,
process spawning, backend runner implementation, SMT/Z3/COBALT/Lean execution,
proof artifact promotion, checker transcript promotion, solver-certificate
promotion, accepted evidence, Level2+, score axes, benchmark evidence,
semantic-correctness, production-readiness, SOTA, breakthrough, full-security,
or authority claims.

## Phase 308 HSAI Gateway Formal Backend Hermetic Execution Result Quarantine Output-Bundle Implementation

Status: complete. See
`docs/308-hsai-gateway-formal-backend-hermetic-execution-result-quarantine-output-bundle-implementation-notes.md`.

Goal: implement the Phase 307 local declared-file output-bundle surface for a
not-run hermetic execution result quarantine shape.

Implemented: added result-quarantine output-bundle constants, declared file and
sidecar registries, output request type, not-run solver/verdict labels,
input-binding, bounded stdout/stderr summaries, redaction report, output
inventory, invariant-verdict report, nonpromotion report, execution-status
record, validation report, output manifest and digest helpers, staged
materialization, readback, undeclared-file rejection, stale-sidecar rejection,
semantic component validation, and focused tests.

Validation gate: focused result-quarantine output-bundle tests, focused
descriptor-report output-bundle tests, focused no-spawn descriptor tests, repo
docs/hygiene tests, formatting, diff hygiene, empty-file hygiene, package-root
lint check, and full workspace tests.

Anti-goals: process spawning, backend execution, SMT/Z3/COBALT/Lean execution,
proof artifact promotion, checker transcript promotion, solver-certificate
promotion, accepted evidence, Level2+, score axes, benchmark evidence,
semantic-correctness, production-readiness, SOTA, breakthrough, full-security,
or authority claims.

## Phase 309 HSAI Gateway Formal Backend Hermetic Result Quarantine Output-Bundle Drift Coverage Boundary

Status: complete. See
`docs/309-hsai-gateway-formal-backend-hermetic-result-quarantine-output-bundle-drift-coverage-boundary.md`.

Goal: define the focused negative-test coverage required for the Phase 308
result-quarantine output-bundle surface before any process-spawning backend
runner phase.

Implemented: added a docs-first drift-coverage boundary for protected roots,
overwrite rejection, missing sidecars, malformed JSON/Markdown, input-binding
drift, command-contract drift, execution-status drift, bounded-summary drift,
redaction drift, output-inventory drift, invariant-verdict drift,
nonpromotion-report drift, validation-report drift, manifest escalation,
undeclared raw/proof/checker/solver/evidence/benchmark/score artifacts, nested
bundle rejection, and symlink rejection.

Validation gate: docs/reference scan, diff hygiene, empty-file hygiene,
package-root lint check, repo docs/hygiene tests, and full workspace tests.

Anti-goals: Rust implementation, new bundle materialization behavior, command
execution, process spawning, backend runner implementation, SMT/Z3/COBALT/Lean
execution, proof artifact promotion, checker transcript promotion,
solver-certificate promotion, accepted evidence, Level2+, score axes,
benchmark evidence, semantic-correctness, production-readiness, SOTA,
breakthrough, full-security, or authority claims.

## Phase 310 HSAI Gateway Formal Backend Hermetic Result Quarantine Output-Bundle Drift Coverage Implementation

Status: complete. See
`docs/310-hsai-gateway-formal-backend-hermetic-result-quarantine-output-bundle-drift-coverage-implementation-notes.md`.

Goal: implement focused local drift-coverage tests for the Phase 308
result-quarantine output-bundle reader and materializer.

Implemented: added tests for protected-root rejection, existing-root overwrite
rejection, missing sidecar rejection, malformed JSON rejection, nested
descriptor-report bundle rejection, input-binding claim-boundary drift,
command-contract network drift, execution-status process-spawned drift,
redaction credential drift, nonpromotion Level2 drift, and validation
accepted-evidence drift.

Validation gate: focused result-quarantine output-bundle tests, focused
descriptor-report output-bundle tests, focused no-spawn descriptor tests, repo
docs/hygiene tests, formatting, diff hygiene, empty-file hygiene, package-root
lint check, and full workspace tests.

Anti-goals: new materialization behavior, command execution, process spawning,
backend runner implementation, SMT/Z3/COBALT/Lean execution, proof artifact
promotion, checker transcript promotion, solver-certificate promotion,
accepted evidence, Level2+, score axes, benchmark evidence,
semantic-correctness, production-readiness, SOTA, breakthrough, full-security,
or authority claims.

## Phase 311 HSAI Gateway Formal Backend Hermetic Process-Spawn Crossing Boundary

Status: complete. See
`docs/311-hsai-gateway-formal-backend-hermetic-process-spawn-crossing-boundary.md`.

Goal: define the future process-spawn crossing contract for the first tiny
local `local_smt_tiny_gateway_invariant` backend lane.

Implemented: added a docs-first boundary for future direct-process no-shell
execution, fixed executable policy, fixed argv policy, empty or allowlisted
environment, no stdin, no network, timeout handling, bounded stdout/stderr,
redaction, quarantine output, nonpromotion, required tests, anti-goals, and
next no-default-runner interface scope.

Validation gate: docs/reference scan, diff hygiene, empty-file hygiene,
package-root lint check, repo docs/hygiene tests, and full workspace tests.

Anti-goals: Rust implementation, command execution, process spawning, backend
runner implementation, SMT/Z3/COBALT/Lean execution, proof artifact promotion,
checker transcript promotion, solver-certificate promotion, accepted evidence,
Level2+, score axes, benchmark evidence, semantic-correctness,
production-readiness, SOTA, breakthrough, full-security, or authority claims.

## Phase 312 HSAI Gateway Formal Backend Hermetic Process-Spawn No-Default-Runner Interface

Status: complete. See
`docs/312-hsai-gateway-formal-backend-hermetic-process-spawn-no-default-runner-interface-notes.md`.

Goal: implement the local Rust interface and validator for the Phase 311
process-spawn boundary without adding a default runner or executing a backend.

Implemented: added process-spawn interface constants, executable policy
metadata, runtime policy metadata, nonpromotion policy metadata, deterministic
builder, fail-closed validator, digest/source bindings to Phase 304/306/308
artifacts, and focused tests for valid no-default-runner metadata, runner/policy
escalation rejection, and source drift rejection.

Validation gate: formatting, Phase 312 focused tests, Phase 308/306/304
regression tests, repo docs/hygiene tests, diff hygiene, empty-file hygiene,
package-root lint check, and full workspace tests.

Anti-goals: default runner implementation, command execution, process
spawning, backend execution, SMT/Z3/COBALT/Lean execution, proof artifact
promotion, checker transcript promotion, solver-certificate promotion, accepted
evidence, Level2+, score axes, benchmark evidence, semantic-correctness,
production-readiness, SOTA, breakthrough, full-security, or authority claims.

## Phase 313 HSAI Gateway Formal Backend Hermetic Fixture-Runner Crossing

Status: complete. See
`docs/313-hsai-gateway-formal-backend-hermetic-fixture-runner-crossing-notes.md`.

Goal: cross the process-spawn boundary with one fixed local fixture process,
while preserving no-shell execution, empty environment, bounded summaries, and
quarantine-only output.

Implemented: added Phase 313 constants, fixture-runner request/report/output
types, fixture-runner errors, direct-process execution with `env_clear`, null
stdin, piped stdout/stderr, timeout handling, bounded digest/count summaries,
Phase 313 materialization/readback for the quarantine namespace, a narrow
cross-crate source-scan exception for the Phase 313 `Stdio` import and
`Command::new` call, and tests for successful fixture execution, pre-spawn
acknowledgement rejection, invalid interface rejection, and claim-escalation
readback rejection.

Validation gate: formatting, Phase 313 focused tests, Phase 312/308/306/304
regression tests, repo docs/hygiene tests, diff hygiene, empty-file hygiene,
package-root lint check, and full workspace tests.

Anti-goals: Lean/SMT/Z3/COBALT/Aeneas/Hax/rust-lean/Coq/TLA+/CBMC/model-checker
execution as proof authority, proof artifact promotion, checker transcript
promotion, solver-certificate promotion, accepted evidence, Level2+, score
axes, benchmark evidence, semantic-correctness, production-readiness, SOTA,
breakthrough, full-security, or authority claims.

## Phase 314 HSAI Gateway Formal Backend Hermetic Fixture-Runner Hardening Coverage

Status: complete. See
`docs/314-hsai-gateway-formal-backend-hermetic-fixture-runner-hardening-coverage-notes.md`.

Goal: harden the Phase 313 fixture-runner crossing with focused local negative
coverage and one readback guard for the executed-fixture quarantine bundle
directory.

Implemented: added tests for nonzero fixture-process exit classification,
timeout classification, bounded stdout truncation without raw retention, stale
sidecar rejection, declared summary drift rejection through manifest digest
bindings, redaction drift rejection through manifest digest bindings,
undeclared proof-artifact rejection, and bundle-directory symlink rejection.
Added a readback guard that rejects a symlinked or non-directory
`gateway-formal-backend-hermetic-execution-result-quarantine` bundle directory.

Validation gate: formatting, Phase 314/313 focused tests, Phase 312/308/306/304
regression tests, repo docs/hygiene tests, diff hygiene, empty-file hygiene,
package-root lint check, and full workspace tests.

Anti-goals: new process APIs beyond the Phase 313 fixture-runner implementation,
generic backend runners, caller-supplied executable paths, shell execution,
inherited environment, stdin, network access, Lean/SMT/Z3/COBALT/Aeneas/Hax/
rust-lean/Coq/TLA+/CBMC/model-checker execution as proof authority, proof
artifact promotion, checker transcript promotion, solver-certificate promotion,
accepted evidence, Level2+, score axes, benchmark evidence,
semantic-correctness, production-readiness, SOTA, breakthrough, full-security,
or authority claims.

## Phase 315 HSAI Mesh Repo-Patch Admission Backend Compatibility

Status: complete. See
`docs/315-hsai-mesh-repo-patch-admission-backend-compatibility-notes.md`.

Goal: align HSAI's local repo-patch admission backend with the Mesh
`repo_patch_service` / `investigate_and_patch` bridge schemas and golden
allow/deny fixture vocabulary.

Implemented: added Mesh repo-patch bounded claim labels
`patch_applies_cleanly`, `tests_passed`, and `no_protected_paths_modified`;
allowed URI-shaped Mesh policy ids; aligned required nonclaims with the Mesh
golden fixture vocabulary; made any rejection clear accepted claims; preserved
`missing_explicit_nonclaims` as the exact empty-nonclaim denial; added
repo-local non-secret Mesh golden fixtures; and added integration tests for
canonical fixture digests, allow/deny parity, claim rejection, weakening,
backend-run metadata requirements, and decision digest sensitivity.

Validation gate: formatting, Phase 315 Mesh admission integration tests, HSAI
claim-boundary source scan, repo docs/hygiene tests, diff hygiene,
empty-file hygiene, package-root lint check, and full workspace tests.

Anti-goals: Mesh orchestration implementation, Kubernetes rollback authority,
feature-flag action authority, network calls, live Mesh runtime calls,
accepted HSAI evidence, formal proof claims, Level2+ evidence, score axes,
benchmark evidence, global correctness, production certification, full
security, semantic-correctness, production-readiness, SOTA, breakthrough, or
authority to execute a patch.

## Phase 316 HSAI Tiny Hermetic Formal-Backend Adapter Contract Boundary

Status: complete. See
`docs/316-hsai-tiny-hermetic-formal-backend-adapter-contract-boundary.md`.

Goal: define the docs-first contract that must exist before HSAI can move from
the Phase 313 fixture-process crossing toward a real tiny formal-backend
adapter implementation.

Implemented: documented the exact target invariant, source anchors, imported
`report_data_binding` assumption handling, adapter request fields, direct-process
command descriptor constraints, non-secret fixture input shape, checker
transcript metadata contract, quarantine and nonpromotion rejection rules,
accepted-ledger ceiling, and implementation exit criteria for a later Phase 317
data-model/quarantine slice.

Validation gate: formatting, HSAI claim-boundary source scan, repo docs/hygiene
tests, diff hygiene, empty-file hygiene, package-root lint check, and full
workspace tests.

Anti-goals: Rust implementation code, new process APIs, default runners,
caller-supplied executable paths, shell execution, inherited environment, stdin,
network access, external repo clones, vendored source, Lean/SMT/Z3/COBALT/
Aeneas/Hax/rust-lean/Coq/TLA+/CBMC/model-checker execution, proof artifacts,
checker transcript creation, solver certificates, accepted evidence, Level2+,
score axes, benchmark evidence, semantic-correctness, production-readiness,
SOTA, breakthrough, full-security, or authority claims.

## Phase 317 HSAI Tiny Hermetic Formal-Backend Adapter Data Model

Status: complete. See
`docs/317-hsai-tiny-hermetic-formal-backend-adapter-data-model-notes.md`.

Goal: implement the typed not-run adapter data model and declared quarantine
bundle required before a future backend execution readiness boundary.

Implemented: Phase 317 constants, adapter request, fixed non-secret fixture
input, fixed command descriptor metadata, not-run transcript summary,
nonpromotion report, output manifest, output validation report, declared
logical files and SHA-256 sidecars, staged materialization, readback, duplicate
JSON rejection, manifest semantic validation, nonclaim Markdown checks, stale
digest rejection, undeclared proof-artifact rejection, and focused unit tests.

Validation gate: formatting, Phase 317 focused unit tests, HSAI claim-boundary
source scan, repo docs/hygiene tests, diff hygiene, empty-file hygiene,
package-root lint check, and full workspace tests.

Anti-goals: process spawning, backend execution, Lean/SMT/Z3/COBALT/Aeneas/Hax/
rust-lean/Coq/TLA+/CBMC/model-checker execution, proof artifacts, checker
transcripts, solver certificates, accepted evidence, Level2+ evidence, score
axes, benchmark evidence, live provider evidence, semantic-correctness,
production-readiness, SOTA, breakthrough, full-security, or authority claims.

Exit criteria: `hsai-agent-admission` can materialize and read back a typed
not-run tiny hermetic formal-backend adapter quarantine bundle for the selected
gateway attestation challenge-binding invariant, while rejecting command-policy
escalation, stale digests, manifest drift, and undeclared proof artifacts.

## Phase 318 HSAI Tiny Hermetic Formal-Backend Execution Readiness Boundary

Status: complete. See
`docs/318-hsai-tiny-hermetic-formal-backend-execution-readiness-boundary.md`.

Goal: define the readiness contract required before any later code may run the
Phase 317 tiny hermetic formal-backend adapter command.

Implemented: documented the required preconditions for future process spawn,
the fixed command execution contract, transcript metadata contract, quarantine
readback rejection requirements, nonpromotion requirements, exact claim
boundary, anti-goals, validation gate, and Phase 319 implementation ceiling.

Validation gate: formatting, HSAI claim-boundary source scan, repo docs/hygiene
tests, diff hygiene, empty-file hygiene, package-root lint check, and full
workspace tests.

Anti-goals: Rust implementation code, process APIs, process spawning, backend
execution, Lean/SMT/Z3/COBALT/Aeneas/Hax/rust-lean/Coq/TLA+/CBMC/model-checker
execution, solver scripts, checker scripts, package runtime files, external
repo clones, vendored source, network access, credentials, secrets, proof
artifacts, checker transcripts, solver certificates, accepted evidence,
Level2+ evidence, score axes, benchmark evidence, live provider evidence,
semantic-correctness, production-readiness, SOTA, breakthrough, full-security,
or authority claims.

Exit criteria: future execution code has an explicit readiness boundary for
operator acknowledgement, exact command fixture, transcript schema, raw-output
redaction, quarantine readback, and nonpromotion before any new code phase can
cross into a tiny local backend execution experiment.

## Phase 319 HSAI Tiny Hermetic Formal-Backend Local Fixture Execution Readback

Status: complete. See
`docs/319-hsai-tiny-hermetic-formal-backend-local-fixture-execution-readback-notes.md`.

Goal: implement the smallest Phase 318 execution crossing by running one fixed
local fixture process from the Phase 317 command descriptor and materializing a
quarantine-only readback bundle.

Implemented: Phase 319 constants, execution output request, execution
transcript, nonpromotion report, validation report, output manifest, declared
logical files and SHA-256 sidecars, source Phase 317 adapter-manifest
revalidation before spawn, direct-process no-shell fixture execution, cleared
environment, no stdin, bounded stdout/stderr summaries, redaction report,
staged materialization, digest/semantic readback, nonclaim Markdown checks, and
focused tests for successful readback, missing acknowledgement rejection,
source-manifest drift rejection, manifest drift rejection, stale sidecar
rejection, and undeclared proof-artifact rejection.

Validation gate: formatting, Phase 319 focused unit tests, HSAI claim-boundary
source scan, repo docs/hygiene tests, diff hygiene, empty-file hygiene,
package-root lint check, and full workspace tests.

Anti-goals: generic backend runners, caller-supplied executable paths,
caller-supplied argv, shell execution, inherited environment, stdin, network
access, package runtime files, external repo clones, vendored source,
Lean/SMT/Z3/COBALT/Aeneas/Hax/rust-lean/Coq/TLA+/CBMC/model-checker execution
as proof authority, solver scripts, checker scripts, proof artifacts, checker
transcripts, solver certificates, accepted evidence, Level2+ evidence, score
axes, benchmark evidence, live provider evidence, semantic-correctness,
production-readiness, SOTA, breakthrough, full-security, or authority claims.

Exit criteria: `hsai-agent-admission` can execute and read back one fixed local
fixture process for the selected gateway invariant while proving through local
tests that the bundle remains quarantine-only, promotion flags stay false, raw
logs are not retained, and undeclared proof artifacts are rejected.

## Phase 320 HSAI Tiny Hermetic Formal-Backend Execution Readback Hardening

Status: complete. See
`docs/320-hsai-tiny-hermetic-formal-backend-execution-readback-hardening-notes.md`.

Goal: harden the Phase 319 local fixture execution output readback lane before
opening any real Lean/SMT/COBALT command boundary.

Implemented: focused tests for malformed declared JSON, overwrite rejection,
output-root symlink rejection, bundle-directory symlink rejection, declared-file
symlink rejection, declared-sidecar symlink rejection, digest-preserving stdout
summary semantic drift rejection, digest-preserving redaction-report semantic
drift rejection, and digest-preserving nonpromotion-report semantic drift
rejection.

Validation gate: formatting, Phase 319/320 focused unit tests, HSAI
claim-boundary source scan, repo docs/hygiene tests, diff hygiene,
empty-file hygiene, package-root lint check, and full workspace tests.

Anti-goals: generic backend runners, caller-supplied executable paths,
caller-supplied argv, shell execution, inherited environment, stdin, network
access, package runtime files, external repo clones, vendored source,
Lean/SMT/Z3/COBALT/Aeneas/Hax/rust-lean/Coq/TLA+/CBMC/model-checker execution
as proof authority, solver scripts, checker scripts, proof artifacts, checker
transcripts, solver certificates, accepted evidence, Level2+ evidence, score
axes, benchmark evidence, live provider evidence, semantic-correctness,
production-readiness, SOTA, breakthrough, full-security, or authority claims.

Exit criteria: the Phase 319 local fixture execution bundle rejects malformed
declared files, unsafe filesystem shapes, unauthorized overwrite, and
digest-preserving semantic drift in summaries, redaction, and nonpromotion
metadata.

## Phase 321 HSAI Real Formal Command Lane Boundary

Status: complete. See
`docs/321-hsai-real-formal-command-lane-boundary.md`.

Goal: define the docs-first boundary for the first real formal command lane
after the Phase 319/320 local fixture execution readback lane.

Defined: the first real command lane as `local_smt_tiny_gateway_invariant`, the
first backend mode as `smt-lib2-offline-command`, the first property as
`attestation_challenge_binding_deterministic_input_sensitive`, the local
non-secret input contract, fixed direct-process command contract, declared
`gateway-formal-real-command-lane/*` artifact grammar, checker transcript
grammar, solver verdict labels, readback rejection rules, nonclaims,
anti-goals, validation gate, and Phase 322 inert implementation ceiling.

Validation gate: formatting, HSAI claim-boundary source scan, repo docs/hygiene
tests, diff hygiene, empty-file hygiene, package-root lint check, and full
workspace tests.

Anti-goals: Rust implementation code, Cargo metadata changes, package runtime
files, command execution, process spawning, backend runner implementation,
solver scripts, checker scripts, proof assistant setup files, external repo
clones, vendored source, Lean/SMT/Z3/COBALT/Aeneas/Hax/rust-lean/Coq/TLA+/
CBMC/model-checker execution, generated proof artifacts, generated checker
transcripts, generated solver certificates, accepted evidence, Level2+
evidence, score axes, benchmark evidence, live provider evidence,
semantic-correctness, production-readiness, SOTA, breakthrough, full-security,
or authority claims.

Exit criteria: the first real command lane has an explicit docs-first boundary
that chooses one tiny SMT-style lane and blocks Lean/COBALT/proof-authority
execution until separate source/toolchain and artifact boundaries exist.

## Phase 322 HSAI Real Formal Command Lane Inert Data Model

Status: complete. See
`docs/322-hsai-real-formal-command-lane-inert-data-model-notes.md`.

Goal: implement the inert Rust data model and declared output contract for the
Phase 321 real formal command lane without running a solver or materializing a
new command-lane bundle.

Implemented: schema/state/claim-boundary constants, request metadata, fixed
command descriptor metadata, static SMT-LIB2 obligation metadata, obligation
binding metadata, bounded stdout/stderr summary metadata, solver verdict labels,
checker/execution transcript metadata, nonpromotion report, validation report,
output manifest, output contract, exact declared file and sidecar lists, an
in-memory builder, and fail-closed validation.

Validation coverage: valid contract construction from real Phase 317/319 source
manifests, exact declared file and sidecar grammar, missing operator
acknowledgement rejection, unsafe command-policy rejection, source execution
manifest drift rejection, transcript promotion rejection, and nonpromotion of
process execution, solver execution, proof artifacts, checker transcripts,
solver certificates, accepted evidence, Level2+ evidence, score axes,
semantic-correctness, production-readiness, SOTA, breakthrough, full-security,
and authority claims.

Validation gate: formatting, focused Phase 322 tests, HSAI claim-boundary source
scan, repo docs/hygiene tests, diff hygiene, empty-file hygiene, package-root
lint check, and full workspace tests.

Anti-goals: package runtime files, command execution, process spawning,
filesystem materialization for the new lane, backend runner implementation,
solver scripts, checker scripts, proof assistant setup files, external repo
clones, vendored source, Lean/SMT/Z3/COBALT/Aeneas/Hax/rust-lean/Coq/TLA+/
CBMC/model-checker execution, generated proof artifacts, generated checker
transcripts, generated solver certificates, accepted evidence, Level2+
evidence, score axes, benchmark evidence, live provider evidence,
semantic-correctness, production-readiness, SOTA, breakthrough, full-security,
or authority claims.

Exit criteria: the real command lane now has an in-memory Rust contract tied to
Phase 317/319 source manifests and a declared output grammar, with policy and
claim-escalation validation, but still no materialized command-lane readback and
no real solver run.

## Phase 323 HSAI Real Formal Command Lane Materialized Readback

Status: complete. See
`docs/323-hsai-real-formal-command-lane-materialized-readback-notes.md`.

Goal: materialize and read back the Phase 322 real formal command-lane output
contract while preserving the no-execution and no-promotion boundary.

Implemented: local staged writes, exact declared
`gateway-formal-real-command-lane/*` files, SHA-256 sidecars, output-root
validation, protected-root rejection, symlink rejection, undeclared-file
rejection, malformed declared JSON rejection, sidecar digest mismatch rejection,
manifest semantic drift rejection, transcript/checker-transcript consistency
checks, bounded stdout/stderr summary checks, deterministic redaction report
checks, solver verdict checks, nonpromotion report checks, validation report
checks, and nonclaims Markdown checks.

Validation coverage: valid materialization and readback, stale sidecar
rejection, malformed solver-verdict JSON rejection, undeclared proof-artifact
rejection, and manifest Level2+ promotion drift rejection.

Validation gate: formatting, focused Phase 323 tests, HSAI claim-boundary source
scan, repo docs/hygiene tests, diff hygiene, empty-file hygiene, package-root
lint check, and full workspace tests.

Anti-goals: command execution, process spawning, backend runner implementation,
solver scripts, checker scripts, proof assistant setup files, package runtime
files, external repo clones, vendored source, Lean/SMT/Z3/COBALT/Aeneas/Hax/
rust-lean/Coq/TLA+/CBMC/model-checker execution, generated proof artifacts,
accepted evidence, Level2+ evidence, score axes, benchmark evidence, live
provider evidence, semantic-correctness, production-readiness, SOTA,
breakthrough, full-security, or authority claims.

Exit criteria: the real command lane now has a materialized local output bundle
and strict readback path, but still no solver preflight exception and no real
solver run.

## Phase 324 HSAI Real Formal Command Lane Execution Preflight Boundary

Status: complete. See
`docs/324-hsai-real-formal-command-lane-execution-preflight-boundary.md`.

Goal: define the docs-first execution preflight boundary that must exist before
the Phase 321-323 real formal command lane can cross into a fixed local
SMT-LIB2 process invocation.

Defined: the one eligible future lane
`local_smt_tiny_gateway_invariant`, backend mode
`smt-lib2-offline-command`, property
`attestation_challenge_binding_deterministic_input_sensitive`, required future
inputs, fail-closed rejection cases, the single-function future source-scan
exception shape, inert preflight output fields, fixed nonclaims, evidence
meaning, required tests, validation gate, and Phase 325 ceiling.

Validation coverage defined: valid preflight from a read back Phase 323 bundle,
missing operator acknowledgement, missing executable digest, caller executable
path, caller argv, shell fragments, inherited environment, stdin, network
access, protected output roots, Phase 323 manifest drift, command descriptor
drift, obligation digest drift, expected-output grammar digest drift,
accepted-evidence path rejection, Level2+ path rejection, score-axis path
rejection, benchmark-output path rejection, proof-promotion path rejection, and
single-function fixed-command source-scan exception enforcement.

Validation gate: formatting, focused real formal command-lane tests, HSAI
claim-boundary source scan, repo docs/hygiene tests, diff hygiene, empty-file
hygiene, package-root lint check, and full workspace tests.

Anti-goals: Rust implementation code, Cargo metadata changes, package runtime
files, source-scan exception code, process APIs, process spawning, solver
scripts, checker scripts, proof assistant setup files, command execution,
generated proof artifacts, generated checker transcripts, generated solver
certificates, accepted evidence, Level2+ evidence, score axes, benchmark
evidence, live provider evidence, semantic-correctness, production-readiness,
SOTA, breakthrough, full-security, or authority claims.

Exit criteria: the real formal command lane now has a documented execution
preflight boundary for one future fixed local SMT-LIB2 command invocation over
one tiny gateway invariant, but still no source-scan implementation exception,
no process spawn, no solver run, and no accepted formal evidence.

## Phase 325 HSAI Real Formal Command Lane Inert Execution Preflight

Status: complete. See
`docs/325-hsai-real-formal-command-lane-inert-execution-preflight-notes.md`.

Goal: implement the inert execution-preflight metadata and tightly scoped
source-scan exception shape for one future fixed local SMT-LIB2 command
invocation over the Phase 321-323 real formal command lane.

Implemented: preflight input metadata, preflight report metadata, validation
issues, validation result, required nonclaims, digest binding to the read back
Phase 323 manifest, command request, command descriptor, obligation digest,
expected-output grammar digest, executable policy id, executable digest, fixed
executable label, fixed argv digest, timeout/stdout/stderr bounds, blocked
fixed-SMT process-plan stub, and a source-scan exception constrained to one
future direct-process line inside
`run_gateway_formal_real_command_lane_fixed_smt_process`.

Validation coverage: valid preflight from a read back Phase 323 bundle, blocked
process-plan behavior with no spawn, missing readback, missing operator
acknowledgement, missing executable digest, manifest/request/descriptor/
obligation/grammar drift, caller executable path, caller argv, shell fragment,
inherited environment, stdin, network, protected output-root, accepted-evidence
path, Level2+ path, score-axis path, benchmark-output path, proof-promotion
path, promotion flag, and single-function source-scan exception enforcement.

Validation gate: formatting, focused real formal command-lane tests, HSAI
claim-boundary source scan, repo docs/hygiene tests, diff hygiene, empty-file
hygiene, package-root lint check, and full workspace tests.

Anti-goals: real process spawning, SMT/Z3/Lean/COBALT/Rust-to-Lean/Aeneas/Hax/
Coq/TLA+/CBMC/model-checker execution, arbitrary backend runners,
caller-controlled executable paths, caller-controlled argv, shell execution,
inherited environment, stdin, network access, solver scripts, checker scripts,
proof assistant setup files, generated proof artifacts, generated checker
transcripts, generated solver certificates, accepted evidence, Level2+
evidence, score axes, benchmark evidence, live provider evidence,
semantic-correctness, production-readiness, SOTA, breakthrough, full-security,
or authority claims.

Exit criteria: the real formal command lane now has an inert local
execution-preflight lane and source-scan exception shape, but still no process
spawn, no solver run, no proof/checker/solver artifacts, and no accepted formal
evidence.

## Phase 326 HSAI Real Formal Command Lane Quarantined Fixed SMT Execution

Status: complete. See
`docs/326-hsai-real-formal-command-lane-quarantined-fixed-smt-execution-notes.md`.

Goal: cross from inert preflight into one bounded fixed local process execution
for the real formal command lane while preserving quarantine and nonpromotion.

Implemented: fixed executable digest verification, direct process spawn through
`std::process::Command::new(fixed_executable)`, fixed argv from the validated
command descriptor, cleared environment, null stdin, piped stdout/stderr,
timeout handling, bounded redacted stream summaries, solver-like `unsat`,
`sat`, and `unknown` label classification, pre-spawn executable digest mismatch
rejection, and all proof/evidence/score/authority flags held false.

Validation coverage: successful fixed process execution through the Phase 325
preflight, `unsat` classification without proof authority, redacted summary
retention without raw stdout, executable digest mismatch rejection before spawn,
and source-scan confinement of the single allowed process API line.

Validation gate: formatting, focused real formal command-lane tests, HSAI
claim-boundary source scan, repo docs/hygiene tests, diff hygiene, empty-file
hygiene, package-root lint check, and full workspace tests.

Anti-goals: generic backend runners, caller-controlled executable paths,
caller-controlled argv, shell execution, inherited environment, stdin, network
access, solver scripts, checker scripts, proof assistant setup files, generated
proof artifacts, generated checker transcripts, generated solver certificates,
accepted evidence, Level2+ evidence, score axes, benchmark evidence, official
benchmark submission, semantic-correctness, production-readiness, SOTA,
breakthrough, full-security, or authority claims.

Exit criteria: the real formal command lane now has a local quarantined fixed
process execution surface and focused execution coverage, but still no
materialized Phase 326 output bundle, no accepted formal evidence, no Level2+
formal evidence, and no proof-authority claim.

## Phase 327 HSAI Real Formal Command Lane Fixed SMT Execution Output Readback

Status: complete. See
`docs/327-hsai-real-formal-command-lane-fixed-smt-execution-output-readback-notes.md`.

Goal: materialize and read back the Phase 326 quarantined fixed-SMT execution
output as a local bundle while preserving digest binding and nonpromotion.

Implemented: Phase 327 output-bundle schema metadata, fixed declared
`gateway-formal-real-command-lane-fixed-smt-execution/*` files, SHA-256
sidecars, staged materialization, protected-root rejection, symlink rejection,
exact declared-file rejection, duplicate-key/canonical JSON readback checks,
process-output/summary consistency checks, nonclaim Markdown checks, sidecar
digest drift rejection, manifest promotion drift rejection, and undeclared proof
artifact rejection.

Validation coverage: successful materialization/readback of a Phase 326
quarantined fixed-SMT process output, confirmation that process execution is
recorded only as local quarantined output, and rejection of sidecar drift,
promotion drift, and undeclared artifact files.

Validation gate: formatting, focused fixed-SMT execution output tests, HSAI
claim-boundary source scan, repo docs/hygiene tests, diff hygiene, empty-file
hygiene, package-root lint check, and full workspace tests.

Anti-goals: generic backend runners, additional process-spawn APIs,
caller-controlled executable paths, caller-controlled argv, shell execution,
inherited environment, stdin, network access, solver scripts, checker scripts,
proof assistant setup files, generated proof artifacts as evidence, generated
checker transcripts, generated solver certificates, accepted evidence, Level2+
evidence, score axes, benchmark evidence, official benchmark submission,
semantic-correctness, production-readiness, SOTA, breakthrough, full-security,
or authority claims.

Exit criteria: the real formal command lane now has a materialized/readback
bundle for quarantined fixed-SMT execution output, but still no accepted formal
evidence, no Level2+ formal evidence, no score-axis evidence, no proof-authority
claim, and no production/SOTA/security/correctness claim.

## Phase 328 HSAI Formal Evidence Promotion Boundary

Status: complete. See
`docs/328-hsai-formal-evidence-promotion-boundary.md`.

Goal: define the docs-first promotion boundary between a Phase 327
quarantined fixed-SMT output bundle and any future formal-evidence candidate.

Implemented: formal-lane state ladder, candidate input digest requirements,
required rejection cases, evidence meaning limits, SOTA-quality direction, and
future Phase 329 exit criteria. The state ladder is
`quarantined_output -> formal_evidence_candidate -> reviewed_formal_evidence
-> accepted_formal_evidence`, and no state transition may skip a state.

Validation coverage: documentation now separates quarantined backend output
from candidate evidence, reviewed evidence, and accepted evidence. It defines
why a Phase 327 bundle can inform a future evidence candidate without becoming
accepted evidence, Level2+ evidence, score-axis evidence, or proof authority.

Validation gate: formatting, docs/hygiene checks, diff hygiene, empty-file
hygiene, package-root lint check, and full workspace tests.

Anti-goals: Rust implementation code, candidate emission, accepted Evidence
Ledger mutation, Level2+ evidence, score-axis population, proof artifact
generation, checker transcript generation, solver certificate generation,
Lean execution, COBALT execution, Rust-to-Lean extraction, benchmark
submission, production deployment, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, or action authority.

Exit criteria: the repo now has a documented formal-evidence promotion
boundary that moves toward SOTA-quality evidence discipline, but still no
formal-evidence candidate implementation, no reviewed formal evidence, no
accepted formal evidence, no Level2+ evidence, no score axes, no proof-authority
claim, and no production/SOTA/security/correctness claim.

## Phase 329 HSAI Local Formal Evidence Candidate

Status: complete. See
`docs/329-hsai-local-formal-evidence-candidate-notes.md`.

Goal: implement the first local formal-evidence candidate data model for the
real formal command lane while keeping the candidate below reviewed evidence and
accepted evidence.

Implemented: Phase 329 schema/state/claim-boundary constants, candidate input
metadata, candidate record metadata, validation issue taxonomy, validation
report, candidate nonclaim helpers, candidate builder, and fail-closed
candidate-input validation from Phase 323 source manifest, Phase 325 preflight,
and Phase 327 fixed-SMT execution output manifest.

Validation coverage: valid candidate construction from a hermetic Phase
326/327 fixed-SMT output, preservation of the promotion ladder, proof/evidence
/score/claim/authority flags held false, stale preflight digest rejection,
accepted-evidence/SOTA/score-axis promotion rejection, nonclaim drift rejection,
non-eligible solver verdict rejection, raw-log reliance rejection, and
checker-transcript promotion rejection.

Validation gate: formatting, focused Phase 329 candidate tests, HSAI
claim-boundary source scan, repo docs/hygiene tests, diff hygiene, empty-file
hygiene, package-root lint check, and full workspace tests.

Anti-goals: reviewed formal evidence, accepted Evidence Ledger mutation,
Level2+ evidence, score-axis population, proof artifact generation, checker
transcript generation, solver certificate generation, Lean execution, COBALT
execution, Rust-to-Lean extraction, benchmark submission, production deployment,
semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, full-security claims, or action authority.

Exit criteria: HSAI now has a local formal-evidence candidate lane for one
gateway admission invariant with digest-bound replay, nonclaim preservation,
and explicit promotion rejection, but still no reviewed formal evidence, no
accepted formal evidence, no Level2+ evidence, no score axes, no proof-authority
claim, and no production/SOTA/security/correctness claim.

## Phase 330 HSAI Reviewed Formal Evidence Preview Boundary

Status: complete. See
`docs/330-hsai-reviewed-formal-evidence-preview-boundary.md`.

Goal: define the docs-first boundary for a future reviewed-formal-evidence
preview over Phase 329 candidates while preserving a separate reviewed evidence
state and a separate accepted evidence state.

Implemented: review-preview promotion ladder, review input digest
requirements, reviewer decision labels, required rejection cases, evidence
meaning limits, SOTA-quality review discipline, and future Phase 331 preview
metadata exit criteria. The state ladder is now
`quarantined_output -> formal_evidence_candidate ->
reviewed_formal_evidence_preview -> reviewed_formal_evidence ->
accepted_formal_evidence`.

Validation coverage: documentation now separates candidate evidence from review
preview, reviewed formal evidence, and accepted formal evidence. It defines why
a review preview can classify a candidate without becoming reviewed evidence or
accepted evidence.

Validation gate: formatting, docs/hygiene checks, diff hygiene, empty-file
hygiene, package-root lint check, and full workspace tests.

Anti-goals: Rust implementation code, reviewed evidence emission, accepted
Evidence Ledger mutation, Level2+ evidence, score-axis population, proof
artifact generation, checker transcript generation, solver certificate
generation, Lean execution, COBALT execution, Rust-to-Lean extraction,
benchmark submission, production deployment, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, or action authority.

Exit criteria: the repo now has a documented reviewed-formal-evidence preview
boundary that moves review toward typed, digest-bound evidence discipline, but
still no review-preview implementation, no reviewed formal evidence, no
accepted formal evidence, no Level2+ evidence, no score axes, no proof-authority
claim, and no production/SOTA/security/correctness claim.

## Phase 331 HSAI Reviewed Formal Evidence Preview Metadata

Status: complete. See
`docs/331-hsai-reviewed-formal-evidence-preview-metadata-notes.md`.

Goal: implement local review-preview metadata for Phase 329 candidates while
keeping preview metadata below reviewed formal evidence and accepted evidence.

Implemented: Phase 331 schema/state/claim-boundary constants, review-preview
decision labels, review-preview input metadata, review-preview record metadata,
validation issue taxonomy, validation report, canonical replay-readiness and
promotion-rejection checklist helpers, review-preview builder, and fail-closed
review-preview validation from Phase 329 candidates.

Validation coverage: successful preview construction for accept, reject,
needs-replay, and needs-checker-lane decisions; preservation of the promotion
ladder; proof/evidence/score/claim/authority flags held false; candidate digest
drift rejection; policy drift rejection; nonclaim acknowledgement drift
rejection; promotion-rejection checklist drift rejection; review/accepted/SOTA
/score-axis promotion rejection; and promoted-candidate state rejection.

Validation gate: formatting, focused Phase 331 review-preview tests, HSAI
claim-boundary source scan, repo docs/hygiene tests, diff hygiene, empty-file
hygiene, package-root lint check, and full workspace tests.

Anti-goals: reviewed formal evidence, accepted Evidence Ledger mutation,
Level2+ evidence, score-axis population, proof artifact generation, checker
transcript generation, solver certificate generation, Lean execution, COBALT
execution, Rust-to-Lean extraction, benchmark submission, production deployment,
semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, full-security claims, or action authority.

Exit criteria: HSAI now has a local reviewed-formal-evidence preview lane that
can classify one formal-evidence candidate as scoped-acceptable, rejected,
replay-blocked, or checker-lane-blocked without creating reviewed or accepted
evidence. It still has no reviewed formal evidence, no accepted formal
evidence, no Level2+ evidence, no score axes, no proof-authority claim, and no
production/SOTA/security/correctness claim.

## Phase 332 HSAI Reviewed Formal Evidence Record Boundary

Status: complete. See
`docs/332-hsai-reviewed-formal-evidence-record-boundary.md`.

Goal: define the docs-first boundary for a future reviewed-formal-evidence
record over Phase 331 review previews while keeping accepted evidence as a
separate future state.

Implemented: reviewed-record evidence ladder, reviewed-record input digest
requirements, required `ReviewPreviewAcceptCandidateScope` preview state,
required rejection cases, evidence meaning limits, SOTA-quality reviewed-record
discipline, and future Phase 333 reviewed-record metadata exit criteria.

Validation coverage: documentation now separates review preview from reviewed
formal evidence and accepted formal evidence. It defines why a reviewed record
can represent local reviewed evidence without becoming accepted Evidence Ledger
evidence, Level2+ evidence, score-axis evidence, or proof authority.

Validation gate: formatting, docs/hygiene checks, diff hygiene, empty-file
hygiene, package-root lint check, and full workspace tests.

Anti-goals: Rust implementation code, reviewed evidence emission, accepted
Evidence Ledger mutation, Level2+ evidence, score-axis population, proof
artifact generation, checker transcript generation, solver certificate
generation, Lean execution, COBALT execution, Rust-to-Lean extraction,
benchmark submission, production deployment, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, or action authority.

Exit criteria: the repo now has a documented reviewed-formal-evidence record
boundary that moves local reviewed evidence toward typed, digest-bound evidence
discipline, but still no reviewed-record implementation, no accepted formal
evidence, no Level2+ evidence, no score axes, no proof-authority claim, and no
production/SOTA/security/correctness claim.

## Phase 333 HSAI Reviewed Formal Evidence Record Metadata Implementation

Status: complete. See
`docs/333-hsai-reviewed-formal-evidence-record-metadata-notes.md`.

Goal: implement local reviewed formal-evidence record metadata over Phase 331
review previews while keeping accepted formal evidence, Level2+ evidence, and
score axes out of scope.

Implemented: reviewed-record schema/state/claim-boundary constants,
reviewed-record input and record data models, deterministic digesting,
validation issue taxonomy, validation report, accepted-evidence-disabled
acknowledgement helper, reviewed-record builder, and fail-closed validation from
Phase 331 preview metadata.

Validation coverage: focused tests build a reviewed record only from
`ReviewPreviewAcceptCandidateScope` and reject reject, needs-replay, and
needs-checker-lane preview decisions. Additional tests reject preview digest
drift, candidate digest drift, policy drift, nonclaim acknowledgement drift,
accepted-evidence-disabled acknowledgement drift, reviewed-scope claim
escalation, accepted-evidence mutation attempts, Level2+ attempts, score-axis
attempts, SOTA/full-security attempts, and preview state drift.

Validation gate: formatting, focused `hsai-agent-admission` tests,
docs/hygiene checks, diff hygiene, empty-file hygiene, package-root lint check,
claim-boundary source scans, repo docs tests, and full workspace tests.

Anti-goals: accepted Evidence Ledger mutation, Level2+ evidence, score-axis
population, proof artifact generation, checker transcript generation, solver
certificate generation, additional process-spawn APIs, generic backend runners,
solver scripts, checker scripts, proof assistant setup files, Lean execution,
COBALT execution, Rust-to-Lean extraction, benchmark submission, production
deployment, semantic-correctness claims, production-readiness claims, SOTA
claims, breakthrough claims, full-security claims, or action authority.

Exit criteria: HSAI now has local reviewed formal-evidence record metadata for
one scoped gateway admission invariant, bound to Phase 331 preview, Phase 329
candidate, Phase 327 output, Phase 325 preflight, and Phase 323 source digests.
It still has no accepted formal evidence, no Level2+ evidence, no score axes,
no proof-authority claim, and no production/SOTA/security/correctness claim.

## Phase 334 HSAI Accepted Formal Evidence Handoff Boundary

Status: complete. See
`docs/334-hsai-accepted-formal-evidence-handoff-boundary.md`.

Goal: define the docs-first handoff boundary from Phase 333 reviewed-record
metadata toward a future accepted formal-evidence path without bypassing the
existing accepted Evidence Ledger append policy.

Implemented: future handoff input requirements, current evidence ladder,
explicit policy decision required before accepted formal evidence can exist,
forbidden shortcuts, evidence meaning limits, and future Phase 335 handoff
metadata exit criteria.

Validation coverage: documentation now records that the current
`zkbench-core` accepted append transaction rejects formal evidence classes and
claim boundaries above `Level1LocalReplay`. Phase 334 therefore creates no
parallel accepted-evidence path and does not mutate accepted evidence.

Validation gate: formatting, docs/hygiene checks, diff hygiene, empty-file
hygiene, package-root lint check, claim-boundary source scans, repo docs tests,
and full workspace tests.

Anti-goals: Rust implementation code, accepted Evidence Ledger mutation,
accepted formal evidence, Level2+ evidence, score-axis population, proof
artifact generation, checker transcript generation, solver certificate
generation, Lean execution, COBALT execution, Rust-to-Lean extraction,
benchmark submission, production deployment, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, or action authority.

Exit criteria: HSAI now has a documented handoff boundary from local reviewed
formal-evidence metadata to a future accepted formal-evidence path. It still
has no accepted formal evidence, no Level2+ evidence, no score axes, no
proof-authority claim, and no production/SOTA/security/correctness claim.

## Phase 335 HSAI Accepted Formal Evidence Handoff Metadata Implementation

Status: complete. See
`docs/335-hsai-accepted-formal-evidence-handoff-metadata-notes.md`.

Goal: implement local handoff metadata from Phase 333 reviewed-record metadata
toward a future accepted formal-evidence policy decision without mutating the
accepted Evidence Ledger or changing accepted append policy.

Implemented: handoff schema/state/claim-boundary constants, handoff input and
record data models, unresolved formal-evidence acceptance policy decision enum,
accepted-append policy version marker, requested class and claim-boundary
markers, current accepted append blocker helper, required nonclaim helper,
handoff builder, validation issue taxonomy, and fail-closed validation.

Validation coverage: focused tests build handoff metadata from a Phase 333
reviewed record and reject reviewed-record digest drift, policy drift,
requested accepted-evidence class drift, requested claim-boundary drift,
attempted formal-evidence policy approval, current accepted append blocker
drift, promoted reviewed-record state drift, accepted-evidence mutation,
accepted append policy change, Level2+, score-axis, proof/checker/solver
promotion, SOTA, full-security, and authority attempts.

Validation gate: formatting, focused `hsai-agent-admission` tests,
docs/hygiene checks, diff hygiene, empty-file hygiene, package-root lint check,
claim-boundary source scans, repo docs tests, and full workspace tests.

Anti-goals: accepted Evidence Ledger mutation, accepted append policy changes,
accepted formal evidence, Level2+ evidence, score-axis population, proof
artifact generation or promotion, checker transcript generation or promotion,
solver certificate generation or promotion, Lean execution, COBALT execution,
Rust-to-Lean extraction, benchmark submission, production deployment,
semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, full-security claims, or action authority.

Exit criteria: HSAI now has local accepted formal-evidence handoff metadata
that binds one Phase 333 reviewed formal-evidence record to the current
accepted append blocker and an unresolved future policy decision. It still has
no accepted formal evidence, no accepted Evidence Ledger mutation, no Level2+
evidence, no score axes, no proof-authority claim, and no
production/SOTA/security/correctness claim.

## Phase 336 HSAI Accepted Formal Evidence Policy Decision Boundary

Status: complete. See
`docs/336-hsai-accepted-formal-evidence-policy-decision-boundary.md`.

Goal: define the docs-first policy decision for accepted formal evidence in the
current accepted append path.

Implemented: current-path policy decision that formal evidence remains
forbidden in the existing `zkbench-core` accepted append path, current code
constraint summary, allowed future policy shapes, bounded-class prerequisites,
forbidden shortcuts, evidence meaning limits, and future Phase 337
policy-decision metadata exit criteria.

Validation coverage: documentation now records that Phase 335 handoff metadata
does not become accepted formal evidence and that the current accepted append
path must keep rejecting formal evidence classes until a separate future phase
defines, implements, and tests a bounded formal-evidence policy.

Validation gate: formatting, docs/hygiene checks, diff hygiene, empty-file
hygiene, package-root lint check, claim-boundary source scans, repo docs tests,
and full workspace tests.

Anti-goals: Rust implementation code, Cargo metadata changes, accepted Evidence
Ledger mutation, accepted append policy changes, accepted formal evidence,
Level2+ evidence, score-axis population, proof artifact generation or
promotion, checker transcript generation or promotion, solver certificate
generation or promotion, Lean execution, COBALT execution, Rust-to-Lean
extraction, benchmark submission, production deployment, semantic-correctness
claims, production-readiness claims, SOTA claims, breakthrough claims,
full-security claims, or action authority.

Exit criteria: HSAI now has an explicit policy boundary stating that accepted
formal evidence remains forbidden in the current accepted append path. It still
has no accepted formal evidence, no accepted Evidence Ledger mutation, no
Level2+ evidence, no score axes, no proof-authority claim, and no
production/SOTA/security/correctness claim.

## Phase 337 HSAI Accepted Formal Evidence Policy Decision Metadata Implementation

Status: complete. See
`docs/337-hsai-accepted-formal-evidence-policy-decision-metadata-notes.md`.

Goal: implement local policy-decision metadata that records
`AcceptedFormalEvidenceStillForbidden` for the current accepted append path,
bound to one Phase 335 handoff.

Implemented: policy-decision schema/state/version/claim-boundary constants,
policy-decision input and record data models, validation issue taxonomy,
validation report, canonical current-path policy-decision statement, required
nonclaim helper, policy-decision builder, and fail-closed validation.

Validation coverage: focused tests build policy-decision metadata from a Phase
335 handoff and reject handoff digest drift, accepted append policy-version
drift, attempted bounded formal-evidence class approval, current accepted
append blocker drift, policy-decision statement drift, promoted handoff state
drift, accepted evidence mutation, accepted append policy change, Level2+,
score-axis, proof/checker/solver promotion, SOTA, full-security, and authority
attempts.

Validation gate: formatting, focused `hsai-agent-admission` tests,
docs/hygiene checks, diff hygiene, empty-file hygiene, package-root lint check,
claim-boundary source scans, repo docs tests, and full workspace tests.

Anti-goals: accepted Evidence Ledger mutation, accepted append policy changes,
accepted formal evidence, bounded formal-evidence class approval, Level2+
evidence, score-axis population, proof artifact generation or promotion,
checker transcript generation or promotion, solver certificate generation or
promotion, Lean execution, COBALT execution, Rust-to-Lean extraction, benchmark
submission, production deployment, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, or action authority.

Exit criteria: HSAI now has local policy-decision metadata recording that
accepted formal evidence remains forbidden in the current accepted append path,
bound to one Phase 335 handoff and the current accepted append blocker set. It
still has no accepted formal evidence, no accepted Evidence Ledger mutation, no
accepted append policy change, no Level2+ evidence, no score axes, no
proof-authority claim, and no production/SOTA/security/correctness claim.

## Phase 338 HSAI Bounded Formal Evidence Class Feasibility Boundary

Status: complete. See
`docs/338-hsai-bounded-formal-evidence-class-feasibility-boundary.md`.

Goal: define a docs-first feasibility boundary for a possible future local
reviewed formal-evidence metadata class without approving or implementing that
class.

Implemented: feasibility question, candidate class shape, required ownership
decision, feasibility criteria, required rejection cases, evidence meaning
limits, and future Phase 339 feasibility metadata exit criteria.

Validation coverage: documentation now separates feasibility from approval. It
records that the candidate class remains unimplemented, unapproved, and outside
the current accepted append path while accepted formal evidence remains
forbidden.

Validation gate: formatting, docs/hygiene checks, diff hygiene, empty-file
hygiene, package-root lint check, claim-boundary source scans, repo docs tests,
and full workspace tests.

Anti-goals: Rust implementation code, Cargo metadata changes, bounded
formal-evidence class approval, accepted Evidence Ledger mutation, accepted
append policy changes, accepted formal evidence, Level2+ evidence, score-axis
population, proof artifact generation or promotion, checker transcript
generation or promotion, solver certificate generation or promotion, Lean
execution, COBALT execution, Rust-to-Lean extraction, benchmark submission,
production deployment, semantic-correctness claims, production-readiness
claims, SOTA claims, breakthrough claims, full-security claims, or action
authority.

Exit criteria: HSAI now has a feasibility boundary for a possible future local
reviewed formal-evidence metadata class. It still has no bounded
formal-evidence class, no accepted formal evidence, no accepted Evidence Ledger
mutation, no accepted append policy change, no Level2+ evidence, no score axes,
no proof-authority claim, and no production/SOTA/security/correctness claim.

## Phase 339 HSAI Bounded Formal Evidence Feasibility Metadata

Status: complete. See
`docs/339-hsai-bounded-formal-evidence-feasibility-metadata-notes.md`.

Goal: implement local non-mutating feasibility metadata for the possible
`LocalReviewedFormalEvidenceMetadata` class without approving the class or
creating accepted formal evidence.

Implemented: Phase 339 schema/state/claim-boundary constants, feasibility
candidate class/status/ownership constants, feasibility input and record data
models, validation issues, feasibility question helper, required nonclaim
helper, builder, validator, and focused tests in `crates/hsai-agent-admission`.

Validation coverage: the metadata binds one Phase 337 forbidden policy decision
digest and preserves the current accepted append blocker digest. Validators
reject policy-decision drift, promoted policy-decision state, candidate class
drift, class-status drift, ownership drift, feasibility question drift, explicit
nonclaim drift, accepted evidence mutation, accepted append policy change,
bounded-class approval, accepted formal-evidence creation, Level2+, score-axis,
proof/checker/solver promotion, SOTA, full-security, and authority attempts.

Validation gate: formatting, focused `hsai-agent-admission` tests,
docs/hygiene checks, diff hygiene, empty-file hygiene, package-root lint check,
claim-boundary source scans, repo docs tests, and full workspace tests.

Anti-goals: bounded formal-evidence class approval, accepted Evidence Ledger
mutation, accepted append policy changes, accepted formal evidence, Level2+
evidence, score-axis population, proof artifact generation or promotion,
checker transcript generation or promotion, solver certificate generation or
promotion, Lean execution, COBALT execution, Rust-to-Lean extraction, benchmark
submission, production deployment, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, or action authority.

Exit criteria: HSAI now has local feasibility metadata for a possible local
reviewed formal-evidence metadata class, bound to one Phase 337 forbidden
policy decision and the current accepted append blocker set. It still has no
bounded formal-evidence class, no accepted formal evidence, no accepted Evidence
Ledger mutation, no accepted append policy change, no Level2+ evidence, no
score axes, no proof-authority claim, and no production/SOTA/security/correctness
claim.

## Phase 340 HSAI Bounded Formal Evidence Class Policy Boundary

Status: complete. See
`docs/340-hsai-bounded-formal-evidence-class-policy-boundary.md`.

Goal: define the docs-first policy boundary for the Phase 339 feasibility
candidate and decide whether it can proceed as anything stronger than
feasibility metadata.

Implemented: a policy outcome that rejects `accepted_append_path` and
`accepted_formal_evidence_class`, while allowing only
`local_non_accepted_metadata_class` for a future implementation phase. The
boundary records required future class constraints, required rejection cases,
evidence meaning limits, and Phase 341 implementation exit criteria.

Validation coverage: documentation now separates a local non-accepted metadata
class from accepted formal evidence. It preserves the current accepted append
guard and requires any future implementation to bind Phase 339 feasibility,
Phase 337 policy-decision, Phase 335 handoff, Phase 333 reviewed-record, and
current accepted append blocker digests.

Validation gate: formatting, docs/hygiene checks, diff hygiene, empty-file
hygiene, package-root lint check, claim-boundary source scans, repo docs tests,
and full workspace tests.

Anti-goals: Rust implementation code, Cargo metadata changes, accepted
Evidence Ledger mutation, accepted append policy changes, accepted formal
evidence, Level2+ evidence, score-axis population, proof artifact generation or
promotion, checker transcript generation or promotion, solver certificate
generation or promotion, Lean execution, COBALT execution, Rust-to-Lean
extraction, benchmark submission, production deployment, semantic-correctness
claims, production-readiness claims, SOTA claims, breakthrough claims,
full-security claims, or action authority.

Exit criteria: HSAI now has a policy boundary allowing a future local
non-accepted metadata class for reviewed formal-evidence metadata. It still has
no implemented bounded formal-evidence class, no accepted formal evidence, no
accepted Evidence Ledger mutation, no accepted append policy change, no Level2+
evidence, no score axes, no proof-authority claim, and no
production/SOTA/security/correctness claim.

## Phase 341 HSAI Local Non-Accepted Formal Evidence Class Policy Metadata

Status: complete. See
`docs/341-hsai-local-non-accepted-formal-evidence-class-policy-metadata-notes.md`.

Goal: implement local policy metadata that binds one Phase 339 feasibility
record and records that `LocalReviewedFormalEvidenceMetadata` may only be a
future local non-accepted metadata class.

Implemented: Phase 341 schema/state/claim-boundary constants, local
non-accepted owner-path and class-status constants, policy input and record data
models, validation issues, required nonclaim helper, requirement digest helper,
builder, validator, and focused tests in `crates/hsai-agent-admission`.

Validation coverage: the metadata binds Phase 339 feasibility, Phase 337
policy-decision, Phase 335 handoff, Phase 333 reviewed-record, and current
accepted append blocker digests. Validators reject feasibility drift, promoted
feasibility state, class-name drift, owner-path drift, class-status drift,
requirement digest drift, explicit nonclaim drift, accepted evidence mutation,
accepted append policy change, bounded-class implementation, accepted
formal-evidence creation, Level2+, score-axis, proof/checker/solver promotion,
SOTA, full-security, and authority attempts.

Validation gate: formatting, focused `hsai-agent-admission` tests,
docs/hygiene checks, diff hygiene, empty-file hygiene, package-root lint check,
claim-boundary source scans, repo docs tests, and full workspace tests.

Anti-goals: bounded formal-evidence class implementation, accepted Evidence
Ledger mutation, accepted append policy changes, accepted formal evidence,
Level2+ evidence, score-axis population, proof artifact generation or
promotion, checker transcript generation or promotion, solver certificate
generation or promotion, Lean execution, COBALT execution, Rust-to-Lean
extraction, benchmark submission, production deployment, semantic-correctness
claims, production-readiness claims, SOTA claims, breakthrough claims,
full-security claims, or action authority.

Exit criteria: HSAI now has local policy metadata saying a future
`LocalReviewedFormalEvidenceMetadata` class may only be local non-accepted
metadata. It still has no implemented bounded formal-evidence class, no
accepted formal evidence, no accepted Evidence Ledger mutation, no accepted
append policy change, no Level2+ evidence, no score axes, no proof-authority
claim, and no production/SOTA/security/correctness claim.

## Phase 342 HSAI Local Reviewed Formal Evidence Metadata Class Boundary

Status: complete. See
`docs/342-hsai-local-reviewed-formal-evidence-metadata-class-boundary.md`.

Goal: define the docs-first boundary for a future
`LocalReviewedFormalEvidenceMetadata` class without implementing that class or
creating accepted formal evidence.

Implemented: future class name, required future fields, required future
validation, required rejection cases, evidence meaning limits, and Phase 343
implementation exit criteria. The boundary requires Phase 341 class-policy,
Phase 339 feasibility, Phase 337 policy-decision, Phase 335 handoff, Phase 333
reviewed-record, and current accepted append blocker digest bindings.

Validation coverage: documentation now specifies the future class shape while
preserving `local_non_accepted_metadata_class` owner path,
`not_accepted_formal_evidence` status, and the existing accepted append guard.

Validation gate: formatting, docs/hygiene checks, diff hygiene, empty-file
hygiene, package-root lint check, claim-boundary source scans, repo docs tests,
and full workspace tests.

Anti-goals: Rust implementation code, Cargo metadata changes, bounded
formal-evidence class implementation, accepted Evidence Ledger mutation,
accepted append policy changes, accepted formal evidence, Level2+ evidence,
score-axis population, proof artifact generation or promotion, checker
transcript generation or promotion, solver certificate generation or promotion,
Lean execution, COBALT execution, Rust-to-Lean extraction, benchmark submission,
production deployment, semantic-correctness claims, production-readiness claims,
SOTA claims, breakthrough claims, full-security claims, or action authority.

Exit criteria: HSAI now has a boundary for a future local reviewed
formal-evidence metadata class. It still has no implemented class, no accepted
formal evidence, no accepted Evidence Ledger mutation, no accepted append policy
change, no Level2+ evidence, no score axes, no proof-authority claim, and no
production/SOTA/security/correctness claim.

## Phase 343 HSAI Local Reviewed Formal Evidence Metadata Class

Status: complete. See
`docs/343-hsai-local-reviewed-formal-evidence-metadata-class-notes.md`.

Goal: implement `LocalReviewedFormalEvidenceMetadata` as a local non-accepted
metadata class without creating accepted formal evidence.

Implemented: Phase 343 schema/state/claim-boundary constants, metadata input
and record data models, validation issues, claim-boundary helper, required
nonclaim helper, builder, validator, and focused tests in
`crates/hsai-agent-admission`.

Validation coverage: the metadata binds Phase 341 class-policy, Phase 339
feasibility, Phase 337 policy-decision, Phase 335 handoff, Phase 333
reviewed-record, current accepted append blocker, reviewed-scope,
source-correspondence requirement, replay requirement, reviewer-policy, and
explicit nonclaim digests. Validators reject class-policy drift, promoted
class-policy state, class-name drift, owner-path drift, class-status drift,
requirement digest drift, explicit nonclaim drift, accepted evidence mutation,
accepted append policy change, accepted formal-evidence creation, Level2+,
score-axis, proof/checker/solver promotion, SOTA, full-security, and authority
attempts.

Validation gate: formatting, focused `hsai-agent-admission` tests,
docs/hygiene checks, diff hygiene, empty-file hygiene, package-root lint check,
claim-boundary source scans, repo docs tests, and full workspace tests.

Anti-goals: accepted Evidence Ledger mutation, accepted append policy changes,
accepted formal evidence, Level2+ evidence, score-axis population, proof
artifact generation or promotion, checker transcript generation or promotion,
solver certificate generation or promotion, Lean execution, COBALT execution,
Rust-to-Lean extraction, benchmark submission, production deployment,
semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, full-security claims, or action authority.

Exit criteria: HSAI now has a local non-accepted
`LocalReviewedFormalEvidenceMetadata` class. It still has no accepted formal
evidence, no accepted Evidence Ledger mutation, no accepted append policy
change, no Level2+ evidence, no score axes, no proof-authority claim, and no
production/SOTA/security/correctness claim.

## Phase 344 HSAI Local Reviewed Metadata Review Boundary

Status: complete. See
`docs/344-hsai-local-reviewed-metadata-review-boundary.md`.

Goal: define the docs-first review boundary for the Phase 343 local metadata
class without implementing review metadata or creating accepted formal evidence.

Implemented: allowed future review labels, required future review inputs,
required future validation and rejection cases, evidence meaning limits, and
Phase 345 implementation exit criteria.

Validation coverage: documentation now constrains future review labels to
`review_scope_acceptable`, `review_rejected`, `replay_blocked`,
`source_correspondence_blocked`, and `accepted_evidence_blocked`, with
`accepted_evidence_blocked` explicitly non-promotional.

Validation gate: formatting, docs/hygiene checks, diff hygiene, empty-file
hygiene, package-root lint check, claim-boundary source scans, repo docs tests,
and full workspace tests.

Anti-goals: Rust implementation code, Cargo metadata changes, review metadata
implementation, accepted Evidence Ledger mutation, accepted append policy
changes, accepted formal evidence, Level2+ evidence, score-axis population,
proof artifact generation or promotion, checker transcript generation or
promotion, solver certificate generation or promotion, Lean execution, COBALT
execution, Rust-to-Lean extraction, benchmark submission, production deployment,
semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, full-security claims, or action authority.

Exit criteria: HSAI now has a boundary for reviewing local non-accepted
formal-evidence metadata. It still has no implemented review metadata, no
accepted formal evidence, no accepted Evidence Ledger mutation, no accepted
append policy change, no Level2+ evidence, no score axes, no proof-authority
claim, and no production/SOTA/security/correctness claim.

## Phase 345 HSAI Local Metadata Review Record

Status: complete. See
`docs/345-hsai-local-metadata-review-record-notes.md`.

Goal: implement the local metadata review record authorized by Phase 344 without
creating accepted formal evidence or weakening the accepted append blocker.

Implemented: Phase 345 schema/state/claim-boundary constants,
`GatewayFormalRealCommandLaneLocalMetadataReviewLabel`, review input and output
records, validation issues, validation result, claim-boundary helper, required
nonclaim helper, review builder, digest binding to one Phase 343 local metadata
record, current accepted append blocker checks, reviewer id/timestamp checks,
and focused tests.

Validation coverage: tests build an `AcceptedEvidenceBlocked` review record as
non-promotional metadata, reject metadata digest drift, reject invalid reviewer
policy ids, reject missing reviewer decision timestamps, reject accepted append
blocker drift, and reject accepted-evidence, Level2, score-axis, proof,
checker, solver, SOTA, full-security, and action-authority promotion attempts.

Validation gate: formatting, docs/hygiene checks, diff hygiene, empty-file
hygiene, package-root lint check, claim-boundary source scans, repo docs tests,
focused `hsai-agent-admission` tests, and full workspace tests.

Anti-goals: accepted Evidence Ledger mutation, accepted append policy changes,
accepted formal evidence, Level2+ evidence, score-axis population, proof
artifact generation or promotion, checker transcript generation or promotion,
solver certificate generation or promotion, additional process-spawn APIs,
generic backend runners, solver scripts, checker scripts, proof assistant setup
files, Lean execution, COBALT execution, Rust-to-Lean extraction, benchmark
submission, production deployment, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, or action authority.

Exit criteria: HSAI now has a local review record for Phase 343 metadata. It
still has no accepted formal evidence, no accepted Evidence Ledger mutation, no
accepted append policy change, no Level2+ evidence, no score axes, no
proof-authority claim, and no production/SOTA/security/correctness claim.

## Phase 346 HSAI Local Metadata Review Audit Package Boundary

Status: complete. See
`docs/346-hsai-local-metadata-review-audit-package-boundary.md`.

Goal: define the docs-first boundary for a future local non-accepted audit
package over Phase 345 review records without implementing the package or
creating accepted evidence.

Implemented: future package purpose, allowed digest references, forbidden raw
artifact classes, required future validation, package meaning limits, and Phase
347 implementation exit criteria.

Validation coverage: documentation now requires future packages to bind one
Phase 345 review digest, one Phase 343 metadata digest, one Phase 341
class-policy digest, one Phase 337 policy-decision digest, the current accepted
append blocker digest, reviewer identifiers, review label, and explicit
nonclaim digest while rejecting promotion text and accepted-ledger mutation
attempts.

Validation gate: formatting, docs/hygiene checks, diff hygiene, empty-file
hygiene, package-root lint check, claim-boundary source scans, repo docs tests,
and full workspace tests.

Anti-goals: Rust implementation code, Cargo metadata changes, filesystem
artifact writes, accepted Evidence Ledger mutation, accepted append policy
changes, accepted formal evidence, Level2+ evidence, score-axis population,
proof artifact generation or promotion, checker transcript generation or
promotion, solver certificate generation or promotion, additional process-spawn
APIs, generic backend runners, solver scripts, checker scripts, proof assistant
setup files, Lean execution, SMT execution, COBALT execution, Rust-to-Lean
extraction, benchmark submission, production deployment, semantic-correctness
claims, production-readiness claims, SOTA claims, breakthrough claims,
full-security claims, or action authority.

Exit criteria: HSAI now has a boundary for future local non-accepted audit
packages over Phase 345 review records. It still has no implemented audit
package, no accepted formal evidence, no accepted Evidence Ledger mutation, no
accepted append policy change, no Level2+ evidence, no score axes, no
proof-authority claim, and no production/SOTA/security/correctness claim.

## Phase 347 HSAI Local Metadata Review Audit Package

Status: complete. See
`docs/347-hsai-local-metadata-review-audit-package-notes.md`.

Goal: implement the local non-accepted audit package authorized by Phase 346
without writing artifacts, mutating accepted evidence, or introducing backend
execution.

Implemented: Phase 347 schema/state/claim-boundary constants,
`GatewayFormalRealCommandLaneLocalReviewAuditPackageInput`,
`GatewayFormalRealCommandLaneLocalReviewAuditPackage`,
`GatewayFormalRealCommandLaneLocalReviewAuditPackageIssue`,
`GatewayFormalRealCommandLaneLocalReviewAuditPackageValidation`, required
nonclaim helper, package builder, validator, Phase 345 review-record digest
binding, current accepted append blocker preservation, package manifest digest
binding, raw-artifact rejection, package-summary promotion text rejection, and
focused tests.

Validation coverage: tests build a local non-accepted audit package, verify the
Phase 345 review digest and Phase 343 metadata digest bindings, reject review
digest drift, reject raw proof artifacts and secret-bearing inputs, reject
promotional package-summary text, and reject accepted-evidence, Level2,
score-axis, proof, checker, solver, SOTA, full-security, and action-authority
promotion attempts.

Validation gate: formatting, docs/hygiene checks, diff hygiene, empty-file
hygiene, package-root lint check, focused `hsai-agent-admission` tests,
claim-boundary source scans, repo docs tests, and full workspace tests.

Anti-goals: filesystem artifact writes, accepted Evidence Ledger mutation,
accepted append policy changes, accepted formal evidence, Level2+ evidence,
score-axis population, proof artifact generation or promotion, checker
transcript generation or promotion, solver certificate generation or promotion,
additional process-spawn APIs, generic backend runners, solver scripts, checker
scripts, proof assistant setup files, Lean execution, SMT execution, COBALT
execution, Rust-to-Lean extraction, benchmark submission, production deployment,
semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, full-security claims, or action authority.

Exit criteria: HSAI now has a deterministic local non-accepted audit package
metadata type over one Phase 345 review record. It still has no accepted formal
evidence, no accepted Evidence Ledger mutation, no accepted append policy
change, no Level2+ evidence, no score axes, no proof-authority claim, and no
production/SOTA/security/correctness claim.

## Phase 348 HSAI Audit Package Serialization Preview Boundary

Status: complete. See
`docs/348-hsai-audit-package-serialization-preview-boundary.md`.

Goal: define the docs-first boundary for deterministic serialization-preview
metadata over Phase 347 local non-accepted audit packages without implementing
serialization or writing artifacts.

Implemented: future preview purpose, allowed digest references, forbidden
materialized/raw artifact classes, required future validation, meaning limits,
and Phase 349 implementation exit criteria.

Validation coverage: documentation now requires future previews to bind one
Phase 347 package digest, one Phase 345 review record digest, one Phase 343
metadata digest, the current accepted append blocker digest, serialization
profile id, canonical field-order digest, canonical JSON shape digest, expected
package bytes digest, and explicit nonclaim digest while rejecting paths, raw
bytes, promotion text, and accepted-ledger mutation attempts.

Validation gate: formatting, docs/hygiene checks, diff hygiene, empty-file
hygiene, package-root lint check, claim-boundary source scans, repo docs tests,
and full workspace tests.

Anti-goals: Rust implementation code, Cargo metadata changes, filesystem
artifact writes, raw package bytes, accepted Evidence Ledger mutation, accepted
append policy changes, accepted formal evidence, Level2+ evidence, score-axis
population, proof artifact generation or promotion, checker transcript
generation or promotion, solver certificate generation or promotion, additional
process-spawn APIs, generic backend runners, solver scripts, checker scripts,
proof assistant setup files, Lean execution, SMT execution, COBALT execution,
Rust-to-Lean extraction, benchmark submission, production deployment,
semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, full-security claims, or action authority.

Exit criteria: HSAI now has a boundary for future deterministic
serialization-preview metadata over Phase 347 packages. It still has no
implemented serialization preview, no materialized audit package, no accepted
formal evidence, no accepted Evidence Ledger mutation, no accepted append policy
change, no Level2+ evidence, no score axes, no proof-authority claim, and no
production/SOTA/security/correctness claim.

## Phase 349 HSAI Audit Package Serialization Preview Metadata

Status: complete. See
`docs/349-hsai-audit-package-serialization-preview-metadata-notes.md`.

Goal: implement deterministic digest-only serialization-preview metadata over
Phase 347 local non-accepted audit packages without writing artifacts or storing
raw package bytes.

Implemented: Phase 349 schema/state/claim-boundary constants,
`GatewayFormalRealCommandLaneLocalAuditPackageSerializationPreviewInput`,
`GatewayFormalRealCommandLaneLocalAuditPackageSerializationPreview`,
`GatewayFormalRealCommandLaneLocalAuditPackageSerializationPreviewIssue`,
`GatewayFormalRealCommandLaneLocalAuditPackageSerializationPreviewValidation`,
required nonclaim helper, canonical field-order helper, canonical JSON-shape
helper, preview builder, validator, Phase 347 package digest binding, Phase 345
review digest binding, current accepted append blocker preservation, path/raw
payload rejection, preview-summary promotion text rejection, and focused tests.

Validation coverage: tests build deterministic serialization-preview metadata,
verify Phase 347 package digest and Phase 345 review digest bindings, reject
package digest drift, reject filesystem paths and raw package bytes, reject
promotional preview-summary text, and reject accepted-evidence, Level2,
score-axis, proof, checker, solver, SOTA, full-security, and action-authority
promotion attempts.

Validation gate: formatting, docs/hygiene checks, diff hygiene, empty-file
hygiene, package-root lint check, focused `hsai-agent-admission` tests,
claim-boundary source scans, repo docs tests, and full workspace tests.

Anti-goals: filesystem artifact writes, raw package bytes, accepted Evidence
Ledger mutation, accepted append policy changes, accepted formal evidence,
Level2+ evidence, score-axis population, proof artifact generation or
promotion, checker transcript generation or promotion, solver certificate
generation or promotion, additional process-spawn APIs, generic backend
runners, solver scripts, checker scripts, proof assistant setup files, Lean
execution, SMT execution, COBALT execution, Rust-to-Lean extraction, benchmark
submission, production deployment, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, or action authority.

Exit criteria: HSAI now has deterministic digest-only serialization-preview
metadata over one Phase 347 package. It still has no materialized audit package,
no accepted formal evidence, no accepted Evidence Ledger mutation, no accepted
append policy change, no Level2+ evidence, no score axes, no proof-authority
claim, and no production/SOTA/security/correctness claim.

## Phase 350 HSAI Serialization Preview Review Boundary

Status: complete. See
`docs/350-hsai-serialization-preview-review-boundary.md`.

Goal: define the docs-first boundary for future review metadata over Phase 349
serialization previews before any materialized artifact path is authorized.

Implemented: future review purpose, five allowed future review labels, required
future inputs, required future validation, meaning limits, and Phase 351
implementation exit criteria.

Validation coverage: documentation now requires future reviews to bind one
Phase 349 preview digest, one Phase 347 package digest, one Phase 345 review
record digest, one Phase 343 metadata digest, the current accepted append
blocker digest, serialization profile id, canonical shape digests, reviewer
identifiers, reviewer decision timestamp, and explicit nonclaim digest while
rejecting paths, raw bytes, artifact writes, promotion text, and accepted-ledger
mutation attempts.

Validation gate: formatting, docs/hygiene checks, diff hygiene, empty-file
hygiene, package-root lint check, claim-boundary source scans, repo docs tests,
and full workspace tests.

Anti-goals: Rust implementation code, Cargo metadata changes, filesystem
artifact writes, raw package bytes, materialized audit package artifacts,
accepted Evidence Ledger mutation, accepted append policy changes, accepted
formal evidence, Level2+ evidence, score-axis population, proof artifact
generation or promotion, checker transcript generation or promotion, solver
certificate generation or promotion, additional process-spawn APIs, generic
backend runners, solver scripts, checker scripts, proof assistant setup files,
Lean execution, SMT execution, COBALT execution, Rust-to-Lean extraction,
benchmark submission, production deployment, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, or action authority.

Exit criteria: HSAI now has a boundary for future review metadata over Phase
349 serialization previews. It still has no implemented serialization-preview
review, no materialized audit package, no accepted formal evidence, no accepted
Evidence Ledger mutation, no accepted append policy change, no Level2+ evidence,
no score axes, no proof-authority claim, and no production/SOTA/security/
correctness claim.

## Phase 351 HSAI Serialization Preview Review Metadata

Status: complete. See
`docs/351-hsai-serialization-preview-review-metadata-notes.md`.

Goal: implement local digest-only review metadata over one Phase 349
serialization preview while preserving the current materialized-artifact and
accepted-evidence blockers.

Implemented: Phase 351 schema/state/claim-boundary constants, review input
metadata, review record metadata, five bounded review labels, validation
issues, validation result, required nonclaim helper, review builder, digest
binding to one Phase 349 serialization-preview digest/input digest, Phase 347
audit package digest, Phase 345 review record digest, Phase 343 metadata digest,
current accepted append blockers, serialization profile and canonical-shape
digests, reviewer ids, reviewer decision timestamp, explicit nonclaim digest,
path/raw payload rejection, review-summary promotion-text rejection, and focused
tests for valid review construction plus serialization-preview digest drift,
filesystem writes, raw package bytes, promotional review text, accepted-evidence
mutation attempts, accepted append policy-change attempts, accepted formal
evidence creation attempts, Level2+ attempts, score-axis attempts,
proof/checker/solver promotion, SOTA/full-security claims, and authority
attempts.

Validation coverage: the implemented validation requires one Phase 351 review
to bind the Phase 349 preview, the Phase 347 package, the Phase 345 review
record, the Phase 343 metadata record, current accepted append blockers,
canonical serialization digests, reviewer decision metadata, and explicit
nonclaims while rejecting paths, raw bytes, artifact writes, promotion text, and
accepted-ledger mutation attempts.

Validation gate: formatting, focused Phase 351 tests, docs/hygiene checks, diff
hygiene, empty-file hygiene, package-root lint check, claim-boundary source
scans, repo docs tests, and full workspace tests.

Anti-goals: Cargo metadata changes, filesystem artifact writes, raw package
byte storage, materialized audit package artifacts, accepted Evidence Ledger
mutation, accepted append policy changes, accepted formal evidence, Level2+
evidence, score-axis population, proof artifact generation or promotion,
checker transcript generation or promotion, solver certificate generation or
promotion, additional process-spawn APIs, generic backend runners, solver
scripts, checker scripts, proof assistant setup files, Lean execution, SMT
execution, COBALT execution, Rust-to-Lean extraction, benchmark submission,
production deployment, semantic-correctness claims, production-readiness claims,
SOTA claims, breakthrough claims, full-security claims, or action authority.

Exit criteria: HSAI now has deterministic digest-only review metadata over one
Phase 349 serialization preview. It still has no materialized audit package, no
accepted formal evidence, no accepted Evidence Ledger mutation, no accepted
append policy change, no Level2+ evidence, no score axes, no proof-authority
claim, and no production/SOTA/security/correctness claim.

## Phase 352 HSAI Materialized Audit Package Artifact Boundary

Status: complete. See
`docs/352-hsai-materialized-audit-package-artifact-boundary.md`.

Goal: define the docs-first boundary for a future local materialized audit
package artifact path after Phase 351 serialization-preview review metadata.

Implemented: future artifact purpose, declared future file roles, required
future inputs, required future path policy, required future validation, meaning
limits, and Phase 353 implementation exit criteria.

Validation coverage: documentation now requires any future materialization to
bind one Phase 351 review digest, one Phase 349 preview digest, one Phase 347
package digest, one Phase 345 review record digest, one Phase 343 metadata
digest, current accepted append blocker digest, canonical serialization digests,
artifact profile id, declared logical file list digest, expected materialized
manifest digest, and explicit nonclaim digest while rejecting repository-root
outputs, path traversal, symlinks, undeclared files, partial bundles, stale
digests, raw proof/checker/solver payloads, secrets, live backend outputs,
benchmark outputs, promotion text, and accepted-ledger mutation attempts.

Validation gate: formatting, docs/hygiene checks, diff hygiene, empty-file
hygiene, package-root lint check, claim-boundary source scans, repo docs tests,
and full workspace tests.

Anti-goals: Rust implementation code, Cargo metadata changes, filesystem
artifact write implementation, generated package files, raw package byte
storage, accepted Evidence Ledger mutation, accepted append policy changes,
accepted formal evidence, Level2+ evidence, score-axis population, proof
artifact generation or promotion, checker transcript generation or promotion,
solver certificate generation or promotion, additional process-spawn APIs,
generic backend runners, solver scripts, checker scripts, proof assistant setup
files, Lean execution, SMT execution, COBALT execution, Rust-to-Lean extraction,
benchmark submission, production deployment, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, or action authority.

Exit criteria: HSAI now has a docs-first boundary for a future local
materialized audit package artifact path. It still has no implemented
materialized audit package, no accepted formal evidence, no accepted Evidence
Ledger mutation, no accepted append policy change, no Level2+ evidence, no score
axes, no proof-authority claim, and no production/SOTA/security/correctness
claim.

## Phase 353 HSAI Materialized Audit Package Artifact Plumbing

Status: complete. See
`docs/353-hsai-materialized-audit-package-artifact-plumbing-notes.md`.

Goal: implement local materialized audit package artifact plumbing for one Phase
351 serialization-preview review while preserving accepted-evidence blockers.

Implemented: Phase 353 schema/state/claim-boundary constants, output request,
output manifest, output error taxonomy, required nonclaim helper, declared file
helper, declared sidecar helper, staged materialization, read-back validation,
digest sidecars, digest index, protected-root handling, symlink rejection,
undeclared-file rejection, stale-digest rejection, manifest semantic validation,
Phase 351 review binding, Phase 349 preview binding, and focused tests.

Validation coverage: the implemented read-back requires exactly the declared
`audit-package/*` files and sidecars, validates sidecar digests, rejects
undeclared files, binds one Phase 351 review digest, one Phase 349 preview
digest, one Phase 347 package digest, one Phase 345 review record digest, one
Phase 343 metadata digest, current accepted append blocker digest, canonical
serialization digests, artifact profile id, declared file digests, and explicit
nonclaims while rejecting source review promotion attempts before write.

Validation gate: formatting, focused Phase 353 tests, docs/hygiene checks, diff
hygiene, empty-file hygiene, package-root lint check, claim-boundary source
scans, repo docs tests, and full workspace tests.

Anti-goals: accepted Evidence Ledger mutation, accepted append policy changes,
accepted formal evidence, Level2+ evidence, score-axis population, raw proof
artifact generation or promotion, checker transcript generation or promotion,
solver certificate generation or promotion, additional process-spawn APIs,
generic backend runners, solver scripts, checker scripts, proof assistant setup
files, Lean execution, SMT execution, COBALT execution, Rust-to-Lean extraction,
benchmark submission, production deployment, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, or action authority.

Exit criteria: HSAI now has local materialized audit package artifact plumbing
for one Phase 351 serialization-preview review. It still has no accepted formal
evidence, no accepted Evidence Ledger mutation, no accepted append policy
change, no Level2+ evidence, no score axes, no proof-authority claim, and no
production/SOTA/security/correctness claim.

## Phase 354 HSAI Materialized Audit Package Review Boundary

Status: complete. See
`docs/354-hsai-materialized-audit-package-review-boundary.md`.

Goal: define the docs-first boundary for future local review metadata over one
Phase 353 materialized audit package before any accepted-evidence proposal path
is considered.

Implemented: future review purpose, five allowed future review labels, required
future inputs, required future validation, meaning limits, and Phase 355
implementation exit criteria.

Validation coverage: documentation now requires future reviews to bind one
Phase 353 manifest digest, one Phase 353 output request digest, one Phase 351
review digest, one Phase 349 preview digest, one Phase 347 package digest, one
Phase 345 review record digest, one Phase 343 metadata digest, declared file
digests, sidecar digests, digest-index digest, claim-boundary digest, explicit
nonclaim digest, reviewer ids, reviewer decision timestamp, and current accepted
append blocker digest while rejecting promotion text and accepted-ledger
mutation attempts.

Validation gate: formatting, docs/hygiene checks, diff hygiene, empty-file
hygiene, package-root lint check, claim-boundary source scans, repo docs tests,
and full workspace tests.

Anti-goals: Rust implementation code, Cargo metadata changes, filesystem
artifact writes, accepted Evidence Ledger mutation, accepted append policy
changes, accepted formal evidence, Level2+ evidence, score-axis population,
proof artifact generation or promotion, checker transcript generation or
promotion, solver certificate generation or promotion, additional process-spawn
APIs, generic backend runners, solver scripts, checker scripts, proof assistant
setup files, Lean execution, SMT execution, COBALT execution, Rust-to-Lean
extraction, benchmark submission, production deployment, semantic-correctness
claims, production-readiness claims, SOTA claims, breakthrough claims,
full-security claims, or action authority.

Exit criteria: HSAI now has a docs-first boundary for future review metadata
over one Phase 353 materialized audit package. It still has no accepted formal
evidence proposal path, no accepted formal evidence, no accepted Evidence Ledger
mutation, no accepted append policy change, no Level2+ evidence, no score axes,
no proof-authority claim, and no production/SOTA/security/correctness claim.

## Phase 355 HSAI Materialized Audit Package Review Metadata

Status: complete. See
`docs/355-hsai-materialized-audit-package-review-metadata-notes.md`.

Goal: implement local digest-only review metadata over one Phase 353
materialized audit package while preserving the block on any accepted-evidence
proposal path.

Implemented: Phase 355 schema/state/claim-boundary constants, review input
metadata, review record metadata, five bounded review labels, validation
issues, validation result, required nonclaim helper, review builder, digest
binding to one Phase 353 manifest digest/output request digest, Phase 351 review
digest, Phase 349 preview digest, Phase 347 package digest, Phase 345 review
record digest, Phase 343 metadata digest, declared file list digest, declared
sidecar list digest, declared file digest map digest, digest-index digest,
claim-boundary file digest, explicit nonclaim digest, reviewer decision
metadata, current accepted append blocker digest, promotion-text rejection, and
focused tests.

Validation coverage: the implemented validation requires one Phase 355 review
to bind the Phase 353 manifest, Phase 351 review, Phase 349 preview, Phase 347
package, Phase 345 review record, Phase 343 metadata record, current accepted
append blockers, declared file/sidecar/file-digest surfaces, digest-index
digest, claim-boundary file digest, reviewer decision metadata, and explicit
nonclaims while rejecting manifest drift, declared artifact drift, promotion
text, and accepted-ledger mutation attempts.

Validation gate: formatting, focused Phase 355 tests, docs/hygiene checks, diff
hygiene, empty-file hygiene, package-root lint check, claim-boundary source
scans, repo docs tests, and full workspace tests.

Anti-goals: filesystem artifact writes, accepted Evidence Ledger mutation,
accepted append policy changes, accepted formal evidence, Level2+ evidence,
score-axis population, proof artifact generation or promotion, checker
transcript generation or promotion, solver certificate generation or promotion,
additional process-spawn APIs, generic backend runners, solver scripts, checker
scripts, proof assistant setup files, Lean execution, SMT execution, COBALT
execution, Rust-to-Lean extraction, benchmark submission, production deployment,
semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, full-security claims, or action authority.

Exit criteria: HSAI now has deterministic digest-only review metadata over one
Phase 353 materialized audit package. It still has no accepted formal evidence
proposal path, no accepted formal evidence, no accepted Evidence Ledger
mutation, no accepted append policy change, no Level2+ evidence, no score axes,
no proof-authority claim, and no production/SOTA/security/correctness claim.

## Phase 356 HSAI Accepted Evidence Proposal Candidate Boundary

Status: complete. See
`docs/356-hsai-accepted-evidence-proposal-candidate-boundary.md`.

Goal: define the docs-first boundary for future local accepted-evidence proposal
candidate metadata after Phase 355 review metadata, while keeping proposal
candidates separate from acceptance.

Implemented: future candidate purpose, required future candidate inputs, five
allowed future disposition labels, required future validation, meaning limits,
and Phase 357 implementation exit criteria.

Validation coverage: documentation now requires any future proposal candidate
to bind one Phase 355 review digest/input digest, one Phase 353 manifest digest,
one Phase 351 review digest, one Phase 349 preview digest, one Phase 347 package
digest, one Phase 345 review record digest, one Phase 343 metadata digest,
declared file digest map digest, explicit nonclaim digest, reviewer ids,
proposal policy id, proposal candidate id, current accepted append blocker
digest, and candidate disposition label while rejecting promotion text and
accepted-ledger mutation attempts.

Validation gate: formatting, docs/hygiene checks, diff hygiene, empty-file
hygiene, package-root lint check, claim-boundary source scans, repo docs tests,
and full workspace tests.

Anti-goals: Rust implementation code, Cargo metadata changes, filesystem
artifact writes, accepted Evidence Ledger mutation, accepted append policy
changes, accepted formal evidence, Level2+ evidence, score-axis population,
proof artifact generation or promotion, checker transcript generation or
promotion, solver certificate generation or promotion, additional process-spawn
APIs, generic backend runners, solver scripts, checker scripts, proof assistant
setup files, Lean execution, SMT execution, COBALT execution, Rust-to-Lean
extraction, benchmark submission, production deployment, semantic-correctness
claims, production-readiness claims, SOTA claims, breakthrough claims,
full-security claims, or action authority.

Exit criteria: HSAI now has a docs-first boundary for future local
accepted-evidence proposal candidate metadata. It still has no accepted formal
evidence, no accepted Evidence Ledger mutation, no accepted append policy
change, no Level2+ evidence, no score axes, no proof-authority claim, and no
production/SOTA/security/correctness claim.

## Phase 357 HSAI Accepted Evidence Proposal Candidate Metadata

Status: complete. See
`docs/357-hsai-accepted-evidence-proposal-candidate-metadata-notes.md`.

Goal: implement local digest-only accepted-evidence proposal candidate metadata
over one Phase 355 review while preserving accepted-evidence blockers.

Implemented: Phase 357 schema/state/claim-boundary constants, proposal
candidate input metadata, proposal candidate record metadata, five bounded
disposition labels, validation issues, validation result, required nonclaim
helper, candidate builder, digest binding to one Phase 355 review digest/input
digest, Phase 353 manifest digest, Phase 351 review digest, Phase 349 preview
digest, Phase 347 package digest, Phase 345 review record digest, Phase 343
metadata digest, declared file digest map digest, explicit nonclaim digest,
reviewer ids, proposal policy id, proposal candidate id, current accepted
append blocker digest, promotion-text rejection, and focused tests.

Validation coverage: the implemented validation requires one Phase 357 proposal
candidate to bind the Phase 355 review, Phase 353 manifest, Phase 351 review,
Phase 349 preview, Phase 347 package, Phase 345 review record, Phase 343
metadata record, declared file digest map, current accepted append blockers,
reviewer/proposal policy metadata, and explicit nonclaims while rejecting
review drift, promotion text, and accepted-ledger mutation attempts.

Validation gate: formatting, focused Phase 357 tests, docs/hygiene checks, diff
hygiene, empty-file hygiene, package-root lint check, claim-boundary source
scans, repo docs tests, and full workspace tests.

Anti-goals: filesystem artifact writes, accepted Evidence Ledger mutation,
accepted append policy changes, accepted formal evidence, Level2+ evidence,
score-axis population, proof artifact generation or promotion, checker
transcript generation or promotion, solver certificate generation or promotion,
additional process-spawn APIs, generic backend runners, solver scripts, checker
scripts, proof assistant setup files, Lean execution, SMT execution, COBALT
execution, Rust-to-Lean extraction, benchmark submission, production deployment,
semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, full-security claims, or action authority.

Exit criteria: HSAI now has deterministic digest-only proposal candidate
metadata over one Phase 355 materialized audit package review. It still has no
accepted formal evidence, no accepted Evidence Ledger mutation, no accepted
append policy change, no Level2+ evidence, no score axes, no proof-authority
claim, and no production/SOTA/security/correctness claim.

## Phase 358 HSAI Proposal Candidate Review Boundary

Status: complete. See
`docs/358-hsai-proposal-candidate-review-boundary.md`.

Goal: define the docs-first boundary for future local review metadata over one
Phase 357 proposal candidate before any accepted append policy decision is
considered.

Implemented: future review purpose, five allowed future review labels, required
future inputs, required future validation, meaning limits, and Phase 359
implementation exit criteria.

Validation coverage: documentation now requires future reviews to bind one
Phase 357 candidate digest/input digest, one Phase 355 review digest, one Phase
353 manifest digest, one Phase 351 review digest, one Phase 349 preview digest,
one Phase 347 package digest, one Phase 345 review record digest, one Phase 343
metadata digest, declared file digest map digest, explicit nonclaim digest,
reviewer ids, proposal policy id, proposal candidate id, proposal review id,
reviewer decision timestamp, current accepted append blocker digest, candidate
disposition label, and review label while rejecting promotion text and
accepted-ledger mutation attempts.

Validation gate: formatting, docs/hygiene checks, diff hygiene, empty-file
hygiene, package-root lint check, claim-boundary source scans, repo docs tests,
and full workspace tests.

Anti-goals: Rust implementation code, Cargo metadata changes, filesystem
artifact writes, accepted Evidence Ledger mutation, accepted append policy
changes, accepted formal evidence, Level2+ evidence, score-axis population,
proof artifact generation or promotion, checker transcript generation or
promotion, solver certificate generation or promotion, additional process-spawn
APIs, generic backend runners, solver scripts, checker scripts, proof assistant
setup files, Lean execution, SMT execution, COBALT execution, Rust-to-Lean
extraction, benchmark submission, production deployment, semantic-correctness
claims, production-readiness claims, SOTA claims, breakthrough claims,
full-security claims, or action authority.

Exit criteria: HSAI now has a docs-first boundary for future local proposal
candidate review metadata. It still has no accepted formal evidence, no
accepted Evidence Ledger mutation, no accepted append policy change, no Level2+
evidence, no score axes, no proof-authority claim, and no production/SOTA/
security/correctness claim.

## Phase 359 HSAI Proposal Candidate Review Metadata

Status: complete. See
`docs/359-hsai-proposal-candidate-review-metadata-notes.md`.

Goal: implement deterministic local review metadata over one Phase 357 proposal
candidate while preserving the current accepted append and accepted-ledger
blockers.

Implemented: Phase 359 schema/state/claim-boundary constants, proposal
candidate review input metadata, proposal candidate review record metadata,
five bounded review labels, validation issues, validation result, required
nonclaim helper, review builder, digest binding to one Phase 357 proposal
candidate digest/input digest, Phase 355 review digest, Phase 353 manifest
digest, Phase 351 review digest, Phase 349 preview digest, Phase 347 package
digest, Phase 345 review record digest, Phase 343 metadata digest, declared
file digest map digest, explicit nonclaim digest, reviewer ids, proposal policy
id, proposal candidate id, proposal review id, current accepted append blocker
digest, promotion-text rejection, and focused tests for valid review
construction plus Phase 357 candidate digest drift, promotional review text,
accepted-evidence mutation attempts, accepted append policy-change attempts,
accepted formal-evidence creation attempts, Level2+ attempts, score-axis
attempts, proof/checker/solver promotion, SOTA/full-security claims, authority
attempts, and promotional candidate disposition rejection.

Validation gate: formatting, focused Phase 359 tests, docs/hygiene checks, diff
hygiene, empty-file hygiene, package-root lint check, claim-boundary source
scans, repo docs tests, and full workspace tests.

Anti-goals: filesystem artifact writes, accepted Evidence Ledger mutation,
accepted append policy changes, accepted formal evidence, Level2+ evidence,
score-axis population, proof artifact generation or promotion, checker
transcript generation or promotion, solver certificate generation or promotion,
additional process-spawn APIs, generic backend runners, solver scripts, checker
scripts, proof assistant setup files, Lean execution, SMT execution, COBALT
execution, Rust-to-Lean extraction, benchmark submission, production
deployment, semantic-correctness claims, production-readiness claims, SOTA
claims, breakthrough claims, full-security claims, or action authority.

Exit criteria: HSAI now has deterministic digest-only proposal candidate review
metadata over one Phase 357 proposal candidate. It still has no accepted formal
evidence, no accepted Evidence Ledger mutation, no accepted append policy
change, no Level2+ evidence, no score axes, no proof-authority claim, and no
production/SOTA/security/correctness claim.

## Phase 360 HSAI Append-Decision Preflight Boundary

Status: complete. See
`docs/360-hsai-append-decision-preflight-boundary.md`.

Goal: define the docs-first boundary for future local append-decision preflight
metadata over one Phase 359 proposal candidate review before any accepted append
decision is considered.

Implemented: future preflight purpose, five allowed future preflight labels,
required future inputs, required future validation, meaning limits, and Phase
361 implementation exit criteria.

Validation coverage: documentation now requires future preflights to bind one
Phase 359 review digest/input digest, one Phase 357 candidate digest/input
digest, one Phase 355 review digest, one Phase 353 manifest digest, one Phase
351 review digest, one Phase 349 preview digest, one Phase 347 package digest,
one Phase 345 review record digest, one Phase 343 metadata digest, declared
file digest map digest, explicit nonclaim digest, reviewer ids, proposal policy
id, proposal candidate id, proposal review id, append preflight id, preflight
decision timestamp, current accepted append blocker digest, Phase 359 review
label, and append-decision preflight label while rejecting promotion text and
accepted-ledger mutation attempts.

Validation gate: formatting, docs/hygiene checks, diff hygiene, empty-file
hygiene, package-root lint check, claim-boundary source scans, repo docs tests,
and full workspace tests.

Anti-goals: Rust implementation code, Cargo metadata changes, filesystem
artifact writes, accepted Evidence Ledger mutation, accepted append policy
changes, accepted formal evidence, Level2+ evidence, score-axis population,
proof artifact generation or promotion, checker transcript generation or
promotion, solver certificate generation or promotion, additional process-spawn
APIs, generic backend runners, solver scripts, checker scripts, proof assistant
setup files, Lean execution, SMT execution, COBALT execution, Rust-to-Lean
extraction, benchmark submission, production deployment, semantic-correctness
claims, production-readiness claims, SOTA claims, breakthrough claims,
full-security claims, or action authority.

Exit criteria: HSAI now has a docs-first boundary for future local
append-decision preflight metadata. It still has no accepted formal evidence,
no accepted Evidence Ledger mutation, no accepted append policy change, no
Level2+ evidence, no score axes, no proof-authority claim, and no
production/SOTA/security/correctness claim.

## Phase 361 HSAI Append-Decision Preflight Metadata

Status: complete. See
`docs/361-hsai-append-decision-preflight-metadata-notes.md`.

Goal: implement deterministic local append-decision preflight metadata over one
Phase 359 proposal candidate review while preserving the current accepted
append and accepted-ledger blockers.

Implemented: Phase 361 schema/state/claim-boundary constants, append-decision
preflight input metadata, append-decision preflight record metadata, five
bounded preflight labels, validation issues, validation result, required
nonclaim helper, preflight builder, digest binding to one Phase 359 review
digest/input digest, Phase 357 candidate digest/input digest, Phase 355 review
digest, Phase 353 manifest digest, Phase 351 review digest, Phase 349 preview
digest, Phase 347 package digest, Phase 345 review record digest, Phase 343
metadata digest, declared file digest map digest, explicit nonclaim digest,
reviewer ids, proposal policy id, proposal candidate id, proposal review id,
append preflight id, current accepted append blocker digest, promotion-text
rejection, and focused tests for valid preflight construction plus Phase 359
review digest drift, promotional preflight text, accepted-evidence mutation
attempts, accepted append policy-change attempts, accepted formal-evidence
creation attempts, Level2+ attempts, score-axis attempts, proof/checker/solver
promotion, SOTA/full-security claims, and authority attempts.

Validation gate: formatting, focused Phase 361 tests, docs/hygiene checks, diff
hygiene, empty-file hygiene, package-root lint check, claim-boundary source
scans, repo docs tests, and full workspace tests.

Anti-goals: filesystem artifact writes, accepted Evidence Ledger mutation,
accepted append policy changes, accepted formal evidence, Level2+ evidence,
score-axis population, proof artifact generation or promotion, checker
transcript generation or promotion, solver certificate generation or promotion,
additional process-spawn APIs, generic backend runners, solver scripts, checker
scripts, proof assistant setup files, Lean execution, SMT execution, COBALT
execution, Rust-to-Lean extraction, benchmark submission, production
deployment, semantic-correctness claims, production-readiness claims, SOTA
claims, breakthrough claims, full-security claims, or action authority.

Exit criteria: HSAI now has deterministic digest-only append-decision preflight
metadata over one Phase 359 proposal candidate review. It still has no accepted
formal evidence, no accepted Evidence Ledger mutation, no accepted append
policy change, no Level2+ evidence, no score axes, no proof-authority claim,
and no production/SOTA/security/correctness claim.

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
