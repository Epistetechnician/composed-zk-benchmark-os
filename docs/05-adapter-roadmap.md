# Adapter Roadmap

Adapters convert Benchmark Instances and Mutation Variants into backend artifacts, replay commands, Backend Outcomes, Evidence Records, and Score Reports.

## Phases

| Phase | Adapter | Goal | Validation |
|---|---|---|---|
| Phase 0 | Mock/local JSON adapter | Implemented in `zkbench-core` as `LocalJsonAdapter`; exercises Semantic IR, oracle, expected verdicts, replay serialization, and evidence normalization without external dependencies. | Local replay, serialization, evidence ledger, and benchmark pack tests. |
| Phase G | zk-Harness dry-run adapter preparation | Implemented in `zkbench-core` as typed adapter manifest, inert planned commands, candidate pack mapping, metric schema, evidence policy, and dry-run validation. | zk-Harness manifest and dry-run plan round-trip tests; inertness and claim-boundary tests. |
| Phase H | External-runner boundary and manual handoff | Implemented in `zkbench-core` as disabled/manual-only external-runner policy, manual handoff bundle schema, artifact capture contract, provenance contract, result import validation schema, quarantine schema, and zk-Harness handoff mapping. | Policy, handoff, capture, provenance, result import, quarantine, and claim-boundary tests. |
| Phase I | Synthetic result import prototype | Implemented in `zkbench-core` as JSON candidate import, artifact digest validation against caller-provided local bytes, provenance validation, metric validation, quarantine, normalized pending-review drafts, evidence append proposal primitives, and proposal ledger persistence. | Synthetic import, digest, provenance, metric, proposal, proposal ledger, and claim-boundary tests. |
| Phase J | Reviewed proposal acceptance policy | Implemented in `zkbench-core` as manual review decisions, evidence acceptance policy, claim-boundary escalation guard, evidence-record candidates, append previews, Level2 eligibility reports, and review ledger persistence. | Proposal review, acceptance policy, candidate, append preview, eligibility, review ledger, and claim-boundary tests. |
| Phase K | Local soak runner and internal telemetry | Implemented in `zkbench-core` as local soak configuration, deterministic shard planning, resumable checkpoints, local runner APIs, internal benchmark OS telemetry, health reports, failure corpus extraction, artifact layout, and report bundles. | Soak config, sharding, runner smoke, resume, telemetry, health report, failure corpus, and claim-boundary tests. |
| Phase 2 | One formal lane, clean or zkLean | Prove one scoped property for one tiny machine or loop. | Claim Boundary Level 5 only for that property. |
| Phase 3 | Garden/Rocq trace-property lane | Model trace validity and mutation classification in a second proof style. | Scoped trace-property evidence. |
| Phase 4 | gnark recursion-envelope adapter | Stress recursion envelopes and proof aggregation. | Recursion evidence with semantic limitations. |
| Phase 5 | Narrow zkML metrics adapter | Add mixed control-flow plus zkML workload cases. | zkML manifest metrics without scope expansion. |
| Phase 6 | Cross-backend evidence comparison | Compare Backend Outcomes and capability gaps across lanes. | Cross-backend evidence matrix. |

## Capability Flags

Every adapter declares:

- supports_execution
- supports_proving
- supports_verification_timing
- supports_negative_tests
- supports_trace_export
- supports_constraint_count
- supports_formal_semantics
- supports_machine_checked_proof
- supports_recursion
- supports_zkml_metrics
- supports_replay_manifest
- supports_artifact_hashing
- supports_public_private_boundary_checks

## Adapter Manifest Shape

Phase G implements a dry-run zk-Harness adapter manifest. It records adapter status, source policy, schema assumption, candidate compatibility target, local family and mutation scope, capability declaration, evidence policy, claim-boundary policy, review status, and notes. It does not claim complete zk-Harness schema compatibility.

```yaml
adapter:
  id: zk_harness_dry_run_adapter_v0
  status: DryRunOnly
  source_policy:
    external_repo_checkout_allowed: false
    external_command_execution_allowed: false
    external_benchmark_result_import_allowed: false
    future_source_verification_required: true
  schema_assumption: internal_candidate_mapping_only
  capability_flags:
    supports_execution: false
    supports_replay_manifest: true
    supports_artifact_hashing: true
  accepted_input:
    - BenchmarkPackManifest
  output:
    - ZkHarnessDryRunPlan
  claim_boundary_max: Level0DesignNote
```

## Replay Manifest Shape

Phase F implements a local JSON replay manifest with logical schema version `phase-f-local-replay-v0`. It embeds local generated or mutated subjects for self-contained local replay and records selected traces, expected verdicts, local target id, adapter id, capability flags, claim boundary, input artifact references, expected output roles, and notes. `ReplayCommand` is an enum for local replay intent; it is not a shell command.

Phase G adds a separate zk-Harness dry-run plan shape. A dry-run plan maps a local benchmark pack into candidate zk-Harness labels and inert planned command descriptions. zk-Harness dry-run plans are not benchmark results. External execution is disabled by default.

Phase H adds an external-runner boundary and manual handoff bundle shape. A manual handoff bundle preserves the dry-run plan id, source benchmark pack id, source digests, artifact capture contract, provenance contract, result import validation schema, quarantine behavior, and future execution prerequisites. Manual handoff bundles are not benchmark results. Result import candidates are quarantined or pending review until validated.

Phase I adds a synthetic result import bundle shape. A synthetic bundle preserves a parsed candidate, validation report, optional normalized draft, optional quarantine manifest, source metadata, and Level0DesignNote claim boundary. Synthetic result candidates are not benchmark results. Evidence append proposals are not accepted evidence.

Phase J adds reviewed proposal acceptance metadata. A review decision can approve candidate-only creation, an acceptance policy can validate a proposal/decision pair, an evidence-record candidate can preserve reviewed local-only metadata, an append preview can simulate a future ledger transaction, a Level2 eligibility report can identify future-review readiness, and a review ledger can persist decisions/previews. None of these artifacts are accepted evidence. Append previews and review ledgers do not mutate `EvidenceLedger`.

Phase K adds local soak metadata and internal benchmark OS telemetry. A soak config plans deterministic local cases over existing families and mutation passes, a shard plan partitions those cases into resumable shards, a local runner exercises generation, mutation, local replay, optional sampled packs, telemetry, health reporting, and failure corpus extraction. Soak reports, telemetry reports, shard manifests, checkpoints, report bundles, and failure corpus indexes are `Level0DesignNote`. Local replay artifacts referenced or produced during a soak remain `Level1LocalReplay` at most. Local soak telemetry is not official benchmark evidence. Internal timing telemetry is not ZK backend performance. Failure corpus entries are reproduction aids, not accepted evidence.

```yaml
replay_manifest:
  benchmark_instance_id: instance.counter_loop.depth_4.seed_7
  mutation_variant_id: mutation.stale_read.001
  backend_target: zk_harness
  command: pending_adapter_definition
  artifacts:
    input_hash: sha256:pending
    output_hash: sha256:pending
  expected_verdict: expected_reject
```

## Evidence Normalization

The implemented local JSON adapter normalizes only local oracle outcomes. `OracleOutcome::Accepted` maps to `BackendOutcome::Accepted` only inside the local adapter context, and `OracleOutcome::Rejected` maps to `BackendOutcome::Rejected` only inside the local adapter context. These are not proof-system backend accept/reject results.

The Phase G zk-Harness preparation layer does not normalize backend output because no backend output exists. It preserves local pack digests and expected verdict mappings, but it never converts local replay results into zk-Harness results.

The Phase H external-runner boundary still does not normalize backend output because no external output is imported. It defines result import validation only. Quarantined external result candidates must not affect Evidence Records or Score Reports.

The Phase I synthetic importer normalizes only validated synthetic candidates into pending-review drafts. These drafts preserve metric candidates as candidate-only metadata and do not populate Score Reports. Proposal ledgers are separate from `EvidenceLedger`.

The Phase J review layer normalizes only review decisions, acceptance validations, candidates, append previews, eligibility reports, and review-ledger entries. It does not normalize backend output, does not append accepted evidence, and does not populate Score Reports from imported metric candidates.

The Phase K soak layer normalizes local pipeline health only. It records internal generation, mutation, local oracle, local replay, pack, proposal-preview, failure, and byte counters. These counters are operational telemetry and do not populate Score Reports. No soak report becomes a benchmark result.

Normalize all backend output into:

- backend target,
- capability flags,
- replay command,
- metrics,
- artifacts,
- expected verdict,
- backend outcome,
- failure mode,
- evidence class,
- claim boundary,
- reproducibility metadata.

## Failure Mode Normalization

Failure modes:

- accepted
- rejected
- backend_error
- timeout
- malformed_artifact
- capability_gap
- inconclusive
- unsupported_feature

Unsound acceptance candidates and false rejection candidates are result classifications, not raw backend failure modes. Expected reject plus accepted is an `ExpectedRejectAcceptedUnsoundCandidate`, not a proven exploit.

## Adapter Anti-Goals

- Do not force every backend into the same feature model.
- Do not rewrite backend internals first.
- Do not treat adapter success as semantic proof.
- Do not implement gnark recursion before DSL/oracle/scoring works.
- Do not add zkML until core benchmark families and negative tests exist.
- Do not enable live zk-Harness execution until reviewed proposal acceptance policy, local soak telemetry, supersession, and future append eligibility exist and are tested.
- Do not reinterpret local soak telemetry as adapter performance.

## What Not To Implement First

Do not implement dashboarding, external clone automation, CI, package setup, broad zkML support, or multi-adapter orchestration before the Rust DSL/core schema is stable.
