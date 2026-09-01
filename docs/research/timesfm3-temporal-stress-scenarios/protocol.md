# TimesFM3 Temporal Stress-Scenario Sidecar V1

State slice: `timesfm3-temporal-stress-scenarios-v1`.

## Purpose

This sidecar produces bounded, model-derived temporal workload scenarios around
already fixed benchmark cases. The intended flow is:

```text
historical telemetry
  -> TimesFM3 forecast sidecar
  -> q10/q50/q90 scenario manifest
  -> predeclared local workload plan
  -> fixed Semantic IR cases and backend adapters
  -> measured backend outcomes
```

TimesFM3 predicts numeric time series. It does not define benchmark semantics,
Oracle verdicts, mutation labels, proof validity, backend soundness, or score
axes. The benchmark OS owns the Semantic IR, Oracle, workload mapping,
provenance, validation, quarantine, and claim boundary.

## Ownership and external boundary

The independent TimesFM repository is the model implementation and dependency
source:

```text
/Users/shaanp/Documents/GitHub/timesfm
source commit: 331c6d33cb1ac2611de3056d0ac7164aab6301eb
public API: timesfm3.TimesFM3Forecaster / TimesFM3Evaluator
checkpoint: google/timesfm-3.0-pytorch
observed checkpoint revision: 900fcab43d1bfe71733a33b3fec61a41fce28a27
```

The sidecar references that API through an explicit process or dependency
boundary. It does not copy TimesFM implementation into this repository. Model
acquisition is separate from execution. A future model-bearing run must use a
pre-materialized local checkpoint, record its exact weight digest and model
configuration digest, pass `local_files_only=true` or an equivalent offline
guard, and record Python, PyTorch, NumPy, host, architecture, hardware, and
device identities.

## Contract

`request_schema.json`, `result_schema.json`, and `scenario_schema.json` define
the closed-world JSON shapes. `sidecar_v1.py` is the executable validator and
canonicalization boundary.

Requests bind:

- request identity and state slice;
- bounded finite telemetry, strictly increasing millisecond timestamps, and
  source artifact digest;
- context, horizon, and exactly q10/q50/q90 levels;
- covariate identities, artifact digests, target alignment, and future span;
- model, checkpoint, source revision, configuration, and runtime identities;
- offline network policy;
- benchmark-pack, instance, Semantic IR, Oracle, and mutation digests;
- the local-development claim ceiling and machine-readable non-claim codes.

Results bind the request, model, configuration, runtime, input, output, and
artifact digests. Completed results require finite point and quantile tensors,
q10 <= q50 <= q90, point/q50 agreement, and same-device repeatability. Failure
statuses are explicit and contain no forecast artifacts.

Scenario manifests contain exactly three fixed-case arms: `low`, `median`, and
`high`. Each arm carries the selected forecast quantile, the exact fixed case
IDs, the label `model_derived_synthetic_input`, the raw forecast values, and a
deterministic nonnegative ceiling/rounding mapping for a local workload plan.
The manifest digest covers every field except the digest field itself.

## Qualification gate

The current implementation includes only a deterministic fake model and
hermetic validation. No checkpoint is loaded here. A real local qualification
requires independent review of the frozen contract first, then a fresh bounded
telemetry fixture, pre-materialized checkpoint custody, exact provenance,
same-device repeatability, output shape/finiteness checks, and deterministic
scenario-manifest binding. Any failed contract, custody, digest, repeatability,
or offline gate stops the slice without adaptive repair.
