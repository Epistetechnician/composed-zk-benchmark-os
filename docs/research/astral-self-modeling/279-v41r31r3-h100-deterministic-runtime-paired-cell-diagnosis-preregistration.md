# V41R31R3 H100 Deterministic-Runtime Paired Cell Diagnosis Preregistration

State slice: `V41R31R3H100DeterministicRuntimePairedCellDiagnosis`.

V41R31R2 independently verified that the preserved GMAN snapshot restores to a
real H100 and accepts a CUDA command. V41R31R1 failed before either scientific
arm during infrastructure restoration. This identity runs the paired
scientific diagnosis once the infrastructure path is known-good.

## Locked protocol

- one contemporaneous control process and one intervention process;
- worker `v41r27-panel-8-seed-412019`;
- exactly 256 optimizer steps per process;
- fresh model load, adapter, optimizer, CUDA state, and output directory per
  process;
- same real H100, frozen model revision, tokenizer, source archive, source
  commit, requirements, optimizer, schedule, examples, gates, and thresholds;
- control uses the byte-identical frozen V41R27 worker with
  `CUBLAS_WORKSPACE_CONFIG` absent;
- intervention uses an external thin launch wrapper, leaving the frozen worker
  source byte-identical, and sets before CUDA/model execution:
  `CUBLAS_WORKSPACE_CONFIG=:4096:8`,
  `torch.use_deterministic_algorithms(True)`,
  `torch.backends.cudnn.benchmark=False`, and
  `torch.backends.cudnn.deterministic=True`;
- no silent deterministic fallback;
- no retries, substitutions, tuning, threshold changes, assessment, census
  update, or qualification continuation.

## Primary outcomes

- `DeterministicRuntimeRescue`: control `pass:false` with protected
  accuracy `1.0`, intervention `pass:true` with `4/4`.
- `DeterministicRuntimeAdverseEffect`: control passes and intervention fails
  a scientific gate, or intervention reports deterministic-operation
  incompatibility.
- `NoDetectedDeterministicRuntimeEffect`: both arms have the same terminal
  scientific result.
- `InfrastructureIncomplete`: restore, node, command, dependency, model,
  timeout, or artifact-export failure before a valid terminal arm result.

Floating-point or hash differences alone do not establish an effect unless a
preregistered terminal gate changes.

## Required evidence and stop rule

Retain each arm's terminal JSON, exit code, all case gates and candidate
scores, protected before/after rows, all 256 receipts, gradient/projection
metrics, reload exactness, initial/post/reload state hashes, adapter hash,
manifest hash, runtime/source identities, and deterministic settings or
exception evidence.

Stop each arm at terminal result or unrecoverable error. Export and verify each
arm before node stop. Stop the node immediately after both arms are terminal.
If infrastructure fails, preserve the failure and draw no causal conclusion.

V41R27 remains terminal at census `30/48`, qualification `NotAssessed`.

Claim ceiling:
`RemoteH100V41R31R3DeterministicRuntimePairedCellDiagnosis`.

This identity cannot establish root cause beyond this frozen cell/runtime,
cross-cell or cross-GPU reproducibility, qualification, continual
self-improvement, introspection, SOTA, production readiness, or breakthrough
status.
