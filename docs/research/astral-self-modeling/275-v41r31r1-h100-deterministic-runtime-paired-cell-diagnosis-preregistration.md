# V41R31R1 H100 Deterministic-Runtime Paired Cell Diagnosis Preregistration

State slice: `V41R31R1H100DeterministicRuntimePairedCellDiagnosis`.

V41R27R19 terminated after `v41r27-panel-8-seed-412019` returned
`pass:false` with protected accuracy `1.0`. V41R30R1 and V41R30R2 each
completed a fresh exact replication of that cell with `pass:true`, `4/4`
acquisition cases, and protected accuracy `1.0`. Those non-replications leave
rare stochastic or runtime-history dependence unresolved.

Hermes Agent v0.20.0 using `openai-codex/gpt-5.6-luna` reviewed this design
before execution. Its required correction is binding here: the control is a
fresh contemporaneous process, and the frozen V41R27 worker remains
byte-identical in both arms.

## Autoresearch contract

- Goal: test whether deterministic CUDA/runtime controls change the terminal
  scientific result of the retained failing cell.
- Writable scope: this preregistration, terminal execution record, and exported
  arm artifacts only.
- Read-only source: frozen RGS source commit
  `c3b287d4227db94a43af7888d0211fb337c330fa` and its existing source binding.
- Primary metric: paired terminal worker result
  `(pass, acquisition_cases_passing, protected_accuracy)`.
- Verification: terminal command exit, complete worker JSON, manifest
  validation, and byte-hashed export for each arm.
- Budget: exactly one control arm and one intervention arm in fresh processes
  during one 1x H100 session.
- Git policy: preregistration committed and pushed before runtime; terminal
  artifacts and record committed and pushed afterward.

## Frozen variables

Both arms use:

- worker `v41r27-panel-8-seed-412019`;
- exactly 256 optimizer steps;
- one real H100;
- the same frozen model revision, tokenizer, requirements, source archive,
  method, optimizer, learning rate, schedule, protected/acquisition examples,
  gates, and thresholds;
- fresh process, model load, adapter, optimizer, CUDA state, and output
  directory;
- no retries, replacement arms, tuning, threshold changes, assessment, census
  update, or qualification continuation.

The control runs the unmodified frozen worker with
`CUBLAS_WORKSPACE_CONFIG` absent.

The intervention uses a thin launch wrapper and leaves the worker source
unchanged. Before model execution or CUDA initialization it sets:

- `CUBLAS_WORKSPACE_CONFIG=:4096:8`;
- `torch.use_deterministic_algorithms(True)`;
- `torch.backends.cudnn.benchmark = False`;
- `torch.backends.cudnn.deterministic = True`.

The intervention must not silently fall back from an unsupported deterministic
operation.

## Outcomes

- `DeterministicRuntimeRescue`: control returns `pass:false` with protected
  accuracy `1.0`, while intervention returns `pass:true` with `4/4`.
- `DeterministicRuntimeAdverseEffect`: control passes and intervention fails
  a scientific gate, or the intervention reports a deterministic-operation
  incompatibility.
- `NoDetectedDeterministicRuntimeEffect`: both arms have the same terminal
  scientific result, including both pass or both fail.
- `InfrastructureIncomplete`: provider/node loss, bootstrap/model acquisition
  failure, timeout before terminal result, or artifact-export failure.

Floating-point or hash differences alone do not establish rescue or adverse
effect unless a preregistered terminal gate changes.

## Required comparison

Retain and compare terminal classification, exit code, pass, acquisition cases
passing, protected accuracy/drop, all case gates and candidate scores, all 256
receipts, preflight/protected rows, reload exactness, initial/post/reload
trainable-state hashes, adapter and manifest hashes, source/runtime identity,
and explicit deterministic settings.

Stop each arm after terminal result or unrecoverable error. Export and hash its
output before node stop. Stop the paired experiment after both arms terminate.
An infrastructure-incomplete arm produces no causal conclusion.

Claim ceiling:
`RemoteH100V41R31R1DeterministicRuntimePairedCellDiagnosis`.

V41R27 remains terminal at census `30/48`, qualification `NotAssessed`.
This identity cannot establish root cause, cross-cell/GPU reproducibility,
qualification, continual self-improvement, introspection, SOTA, production
readiness, or breakthrough status.
