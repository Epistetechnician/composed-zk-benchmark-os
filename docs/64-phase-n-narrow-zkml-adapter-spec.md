# Phase N Narrow zkML Adapter Spec

## Status And Claim Boundary

Phase N is implemented through the inert manifest-contract slice.

This phase defines the narrow zkML/control-flow adapter lane after Phase L local
soak acceptance and Phase M inert recursion-envelope metadata. The current
implementation is limited to inert Rust manifest metadata, validation,
serialization, source-scan tests, and docs/navigation updates. It does not
authorize live zkML execution, external repository checkout, external result
import, benchmark outputs, official benchmark evidence, ZK backend performance
claims, Level2+ evidence creation, dashboard work, broad zkML benchmarking, or
treating model accuracy as proof-system soundness.

The current authorized state slice is:

```text
crates/zkbench-core/src/zkml.rs
crates/zkbench-core/src/lib.rs
crates/zkbench-core/src/prelude.rs
crates/zkbench-core/tests/phase_n_zkml_manifest.rs
docs/64-phase-n-narrow-zkml-adapter-spec.md
docs/12-task-list.md
README.md
AGENTS.md
```

All Phase N manifest artifacts remain `Level0DesignNote` until a future
explicit phase opens executable adapter work.

## Purpose

Phase N should keep zkML narrow: a workload class that stresses control-flow
semantics, not a new center of the project. The useful question is:

```text
Can a zkML-shaped workload bind model-like private outputs to public
control-flow decisions without hiding weak boundary evidence?
```

The answer must remain claim-capped by the weakest input. A zkML metric can
describe workload shape or future adapter output; it cannot prove semantic
soundness, model correctness, or official benchmark status.

## Inputs

Future implementation may consume only local, non-secret, already-classified
inputs:

- `ZkMlControlFlowMixed` benchmark family metadata;
- local replay manifests;
- local replay results;
- benchmark pack manifests;
- artifact digest sets;
- public/private boundary fixtures;
- evidence-record candidates;
- append previews;
- local health reports;
- explicit claim-boundary labels.

Inputs must carry stable artifact hashes and explicit claim boundaries. Missing
hashes, ambiguous claim boundaries, official benchmark wording, formal-proof
wording, unclassified model artifacts, or hidden external result imports must
fail closed.

## Narrow Manifest Model

`ZkMlWorkloadManifest` remains inert metadata. It describes:

- manifest id;
- workload family id;
- source benchmark instance id;
- control-flow machine id;
- public input names;
- private witness names;
- model artifact references as local metadata only;
- threshold or decision policy metadata;
- expected verdict mapping;
- metric labels;
- output claim boundary;
- explicit limitations.

The manifest output claim boundary must remain `Level0DesignNote` in the
current inert implementation, even when referenced local replay inputs carry
`Level1LocalReplay` boundaries.

## Candidate Metrics

Phase N defines metric names but does not populate official benchmark scores.

Candidate metric labels:

- `zkml_model_artifact_digest_present`;
- `zkml_public_input_count`;
- `zkml_private_witness_count`;
- `zkml_threshold_policy_present`;
- `zkml_boundary_check_result`;
- `zkml_observation_omission_result`;
- `zkml_model_accuracy_if_source_declares`;
- `zkml_constraint_count`;
- `zkml_proof_size_bytes`;
- `zkml_prover_time_ms`;
- `zkml_verifier_time_ms`;
- `zkml_memory_bytes`.

Timing, memory, proof-size, constraint-count, and accuracy labels are future
adapter metrics only. The validator rejects populated values for those labels
in the inert manifest slice. They must not be produced by local soak telemetry
and must not be reported as ZK backend performance without a future explicit
execution phase.

## Validation Rules

The Phase N inert implementation validates:

- every workload input has a stable digest;
- every input claim boundary is explicit;
- output claim boundary does not exceed the weakest input boundary;
- model artifact references are local `Level0DesignNote` metadata;
- model accuracy is never treated as proof-system correctness;
- future executable zkML metric values are absent unless a future execution
  phase is explicitly authorized;
- public/private boundary mismatches remain local negative-test evidence;
- append previews remain previews and do not mutate `EvidenceLedger`;
- Level2 eligibility reports remain not Level2 evidence;
- imported result candidates remain quarantined or pending review until future
  validation.

## Required Negative Tests

The Phase N tests reject:

- manifest output claiming semantic proof from zkML workload metadata;
- manifest output claiming official benchmark evidence from local telemetry;
- missing model artifact digest;
- stale digest over source workload inputs;
- model accuracy treated as proof-system correctness;
- hidden `prover_time`, `verifier_time`, `proof_size`, `constraint_count`, or
  memory metric emitted before executable adapter authorization;
- broad zkML benchmark suites treated as core benchmark families;
- append preview treated as accepted evidence;
- Level2 eligibility report treated as Level2 evidence;
- external repository paths, absolute paths, shell payloads, or live execution
  fields.

## Non-Goals

- No live zkML execution.
- No zkonduit or legacy zkML repository checkout.
- No external repo clone or vendored source.
- No external benchmark run.
- No official benchmark evidence.
- No Level2+ evidence creation.
- No dashboard.
- No broad zkML benchmark suite.
- No claim that model accuracy is proof-system correctness.
- No claim that zkML metrics prove semantic soundness.

## Implemented Slice

The implemented Phase N slice is inert manifest metadata only:

```text
Phase N narrow zkML purpose
input contract
candidate metric labels
ZkMlWorkloadManifest data model
ZkMlWorkloadInputRef and ZkMlModelArtifactRef data model
ZkMlMetric metadata
workload digest-root validation
JSON serialization helpers
validation rules
required negative tests
non-goals
claim-boundary restrictions
```

This slice avoids live zkML execution and does not produce benchmark outputs.
