# V41R31R4 H100 Deterministic-Runtime Paired Cell Diagnosis Preregistration

State slice: `V41R31R4H100DeterministicRuntimePairedCellDiagnosis`.

V41R31R3 produced a valid contemporaneous control pass, but its intervention
wrapper failed before worker import because the frozen source `scripts/`
directory was absent from `sys.path`. This identity corrects only that
launcher defect. The frozen worker source, model, tokenizer, cell, seed,
optimizer, steps, and gates remain unchanged.

## Locked protocol

- one fresh control process and one fresh intervention process;
- worker `v41r27-panel-8-seed-412019`;
- exactly 256 optimizer steps per process;
- same real H100, frozen source binding, model revision, tokenizer,
  requirements, optimizer, schedule, examples, gates, and thresholds;
- control: byte-identical worker, `CUBLAS_WORKSPACE_CONFIG` absent;
- intervention: external wrapper sets
  `CUBLAS_WORKSPACE_CONFIG=:4096:8`, enables
  `torch.use_deterministic_algorithms(True)`, sets cuDNN benchmark false and
  deterministic true, explicitly inserts `/home/dev/rgs/scripts` into
  `sys.path`, then imports and calls the frozen worker;
- fresh model, adapter, optimizer, CUDA state, and output directory per arm;
- no retries, substitutions, tuning, threshold changes, assessment, census
  update, qualification continuation, or silent deterministic fallback.

## Outcomes

- `DeterministicRuntimeRescue`: control fails the acquisition gate with
  protected accuracy `1.0`, intervention passes `4/4`.
- `DeterministicRuntimeAdverseEffect`: control passes and intervention fails a
  scientific gate or reports a deterministic-operation incompatibility.
- `NoDetectedDeterministicRuntimeEffect`: both arms have the same terminal
  scientific result.
- `InfrastructureIncomplete`: restore, node, dependency, model, timeout,
  wrapper, or export failure prevents a valid arm result.

Floating-point or hash differences alone do not establish an effect unless a
preregistered terminal gate changes.

## Evidence and stop rule

Retain terminal JSON, exit codes, gates, protected rows, all 256 receipts,
gradient/projection metrics, reload exactness, state/adapter/manifest hashes,
runtime/source identities, and deterministic settings or exception evidence.
Export and verify each arm before stopping the node. Stop after both arms
terminate. Infrastructure failure produces no causal conclusion.

V41R27 remains terminal at census `30/48`, qualification `NotAssessed`.

Claim ceiling:
`RemoteH100V41R31R4DeterministicRuntimePairedCellDiagnosis`.

This identity cannot establish general root cause, cross-cell or cross-GPU
reproducibility, qualification, continual self-improvement, introspection,
SOTA, production readiness, or breakthrough status.
