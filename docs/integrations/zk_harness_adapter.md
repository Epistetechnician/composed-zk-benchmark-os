# zk-Harness Adapter Plan

## Current Status

Phase G implements zk-Harness dry-run adapter preparation only. Phase H implements an external-runner boundary and manual handoff mapping only. Phase I implements synthetic result candidate import only. The repo still does not implement live zk-Harness execution, does not clone zk-Harness, does not import real zk-Harness data, and does not claim official schema compatibility.

zk-Harness dry-run plans are not benchmark results. Manual handoff bundles are not benchmark results. Synthetic result candidates are not benchmark results. Evidence append proposals are not accepted evidence. External execution is disabled by default.

## Dry-Run-Only Scope

The Phase G adapter preparation layer maps a local benchmark pack into:

- `ZkHarnessAdapterManifest`,
- `ZkHarnessDryRunPlan`,
- candidate workload labels,
- candidate negative-test labels,
- inert planned command descriptions,
- planned metric mapping schema,
- evidence and claim-boundary policy.

It never maps local oracle acceptance to zk-Harness acceptance. It never maps local replay results to external backend results.

## Phase H External-Runner Boundary

The Phase H boundary adds:

- `ExternalRunnerPolicy`,
- `ManualHandoffBundle`,
- `ArtifactCaptureContract`,
- `ProvenanceContract`,
- `ExternalResultImportSchema`,
- `ExternalResultCandidate`,
- `QuarantineManifest`,
- `ZkHarnessManualHandoffBundle`.

The policy mode is disabled or manual-handoff-only. The feature flag `external-runner` is a boundary marker only; it does not enable live execution.

## Manual Handoff Flow

The zk-Harness handoff mapping converts a `ZkHarnessDryRunPlan` into a `ManualHandoffBundle`. The bundle preserves:

- dry-run plan id,
- source benchmark pack id,
- source pack digest,
- source artifact digests,
- inert planned commands as manual instructions,
- artifact capture contract,
- provenance contract,
- result import validation schema,
- quarantine expectations,
- future execution prerequisites,
- `Level0DesignNote` claim boundary.

The handoff mapping never emits a zk-Harness result. Local replay results remain local-only source references and are not converted into zk-Harness acceptance.

## Adapter Manifest Shape

The adapter manifest records:

- manifest id and version,
- adapter id,
- adapter status,
- integration phase,
- source policy,
- schema assumption,
- compatibility target,
- supported local family kinds,
- supported mutation classes,
- supported local artifact kinds,
- unsupported features,
- dry-run capability declaration,
- evidence policy,
- claim-boundary policy,
- review status,
- notes.

Actual Phase G manifests use dry-run-only or external-execution-disabled status. They do not mark anything as live.

## Source Policy

The source policy states:

- no external repo checkout,
- no external command execution,
- no external benchmark result import,
- future source verification required.

Public repo/source verification is required before live integration.

## Schema Assumption

The schema assumption is internal candidate mapping only. Future verification is required. This is not an official zk-Harness schema unless a later phase verifies and implements that schema from source material.

## Dry-Run Plan Shape

The dry-run plan records:

- plan id and version,
- adapter manifest id,
- source benchmark pack id,
- source pack manifest digest,
- local family mappings,
- mutation mappings,
- trace mappings,
- expected outcome mappings,
- planned steps,
- planned artifacts,
- unsupported features,
- warnings,
- execution policy,
- claim boundary,
- evidence policy,
- notes.

Dry-run plan claim boundary is `Level0DesignNote`.

## Pack Mapping Rules

The mapper preserves:

- source pack id,
- source file digests,
- generated instance ids,
- mutation ids,
- replay manifest ids,
- replay result ids as local-only references,
- expected verdicts.

Candidate family labels:

- `BaselineFsm` -> `control_flow_baseline_fsm`,
- `BranchingFsm` -> `control_flow_branching_fsm`,
- `BoundedCounterLoop` -> `control_flow_bounded_counter_loop`.

Candidate mutation labels:

- `MissingConstraints` -> `missing_constraints_negative_case`,
- `CorruptedGuards` -> `corrupted_guards_negative_case`,
- `BadCounters` -> `bad_counters_negative_case`.

These labels are internal candidate labels only. They are not claimed to be accepted by zk-Harness.

## Planned Command Inertness Rules

`ZkHarnessPlannedCommand` is inert data. It may describe a future tool name, arguments, environment data, input artifact references, expected output roles, and working-directory policy.

It must not contain:

- process handles,
- shell scripts,
- external command execution methods,
- absolute local repo paths,
- shell metacharacter payloads,
- methods named as live execution APIs.

Planned step kinds are future labels only:

- `PrepareInputs`,
- `CompileCircuit`,
- `GenerateWitness`,
- `Prove`,
- `Verify`,
- `CollectMetrics`,
- `NormalizeResults`.

## Metric Mapping Placeholders

Phase G defines metric kinds only:

- prover time,
- verifier time,
- proof size,
- memory usage,
- constraint count,
- setup time,
- witness generation time.

All metric values are absent in Phase G. No performance score is produced from dry-run plans.

Phase H result import schemas still do not provide metric values. Metric candidates with values require source artifact references and remain quarantined or pending review until a later phase validates provenance and artifacts.

Phase I synthetic import can validate metric candidate shape and source artifact refs, but the values remain candidate-only metadata. They do not populate Score Reports and do not become zk-Harness metrics.

## Evidence Policy

The evidence policy states:

- dry-run plan generation is `Level0DesignNote`,
- local source pack evidence remains `Level1LocalReplay`,
- future live external replay may become Level2 only after reproducible artifacts exist,
- imported external results require provenance and validation,
- benchmark pass is not proof,
- local replay is not official benchmark evidence,
- external replay is not formal evidence.

No Phase G code creates Level2 evidence records.

No Phase I code creates Level2 evidence records. Synthetic import bundles, normalized drafts, proposals, and proposal ledgers remain `Level0DesignNote`.

## Claim-Boundary Policy

Phase G artifacts remain `Level0DesignNote`. Referenced local pack evidence remains `Level1LocalReplay`. Claim boundaries are not elevated by mapping.

## Unsupported Features

Unsupported in Phase G:

- live zk-Harness execution,
- official zk-Harness schema compatibility,
- metric ingestion,
- external result import,
- proof-system acceptance classification,
- official benchmark evidence.

Unsupported in Phase I:

- live zk-Harness execution,
- real zk-Harness result import,
- accepted external evidence,
- official benchmark evidence,
- performance score population,
- formal evidence,
- proof-system soundness claims.

## Future Live-Execution Prerequisites

Before live integration:

1. Verify zk-Harness source, license, current runner shape, and metric schema.
2. Review the dry-run mapping.
3. Review external tool installation process.
4. Review sandbox policy.
5. Review artifact capture contract.
6. Review provenance contract.
7. Review result import validation.
8. Review synthetic import proposal policy.
9. Review claim-boundary policy.
10. Run only with explicit future approval.

## Result Import And Quarantine

External result candidates must include source pack id, dry-run plan id, raw output artifact refs, provenance draft, artifact digests, requested claim boundary, status, and notes. Candidates that request Level2+ evidence, claim official benchmark evidence, claim formal evidence, claim proof-system soundness, use absolute paths, omit provenance, or include metric values without source artifact refs are rejected by validation.

Rejected or unreviewed candidates become quarantine entries. Quarantine is a local review mechanism only. It is not evidence acceptance and must not affect Score Reports.

Phase I synthetic candidates may normalize into pending-review drafts and evidence append proposals. Those proposals are not accepted evidence and do not mutate `EvidenceLedger`.

## Risks And Mitigations

Risk: dry-run plans are mistaken for benchmark results.
Mitigation: every plan is `Level0DesignNote`, and docs state zk-Harness dry-run plans are not benchmark results.

Risk: local replay is mistaken for zk-Harness acceptance.
Mitigation: local replay ids are referenced as local-only source artifacts, never external backend outcomes.

Risk: metric schema placeholders become fake performance data.
Mitigation: validation rejects observed metric values in Phase G.

Risk: unverified schema compatibility is overstated.
Mitigation: manifest schema assumption records candidate mapping only and future verification required.
