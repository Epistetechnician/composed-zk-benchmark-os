# V25 Execution Record

State slice: `astral-docker-closed-loop-correction-simulation-v25`.

Status: `SyntheticDockerContinualCorrectionHarnessQualified`.

## Frozen source

- Source commit:
  `2e6eaa6ea50a3d2db7138b63bc9752345ff343e1`.
- Assessment opening: after the protocol, experiment contract, Dockerfile,
  source, validators, tests, and claim contract were committed.
- Configuration changes after opening: none.
- Assessment attempts: one completed Docker execution.

## Runtime

- Base image:
  `python@sha256:76d4b7b6305788c6b4c6a19d6a22a3921bf802e9af4d5e1e5bd771208dba74bf`.
- Built image:
  `sha256:c9cd761c04e3ab7913daa487c96eeb46b783391a869a6fcbcf46a5cc9e0050dc`.
- Python: CPython `3.12.13`.
- Container platform: `Linux aarch64` under Docker Desktop.
- Network: disabled during build and execution.
- Runtime controls: read-only container root, all capabilities dropped,
  `no-new-privileges`, 128-process limit, 512 MiB memory limit, two-CPU limit,
  numeric non-root user, and one writable caller-selected artifact mount.

## Content-addressed artifact

The nine-payload-file, 12 MiB artifact is:

`/Users/shaanp/Documents/ResearchArtifacts/astral-v25-8da3411441d8de84b53bf7e8cbce62008a1eb72c60a68d4029cecb4ed83eab95`

Manifest identity:

`8da3411441d8de84b53bf7e8cbce62008a1eb72c60a68d4029cecb4ed83eab95`

Raw census:

- adaptation records: `768`;
- update records: `1,536`;
- future unseen observations: `73,728`;
- replay checks: `11,520`.

The retained artifact includes the frozen contract, source inventory, runtime
identity, raw adaptation examples, every condition update, every future
prediction, every replay check, deterministic replay record, result, and sorted
SHA-256 manifest.

## Positive-control world

| Metric | Result |
|---|---:|
| Telemetry future accuracy | `0.9989149306` |
| Strongest control | `ordinary_update` |
| Strongest-control accuracy | `0.7458767361` |
| Mean paired advantage | `0.2530381944` |
| Bootstrap 95% interval | `[0.2376302083, 0.2684461806]` |
| Telemetry Brier score | `0.0583322420` |
| Strongest-control Brier score | `0.1781486766` |
| Maximum replay accuracy loss | `0.0` |
| Frozen gate | `Passed` |

Every positive-world sensitivity, uncertainty, calibration, and retention gate
passed.

## Null world

| Metric | Result |
|---|---:|
| Telemetry future accuracy | `0.6178385417` |
| Strongest control | `ordinary_update` |
| Strongest-control accuracy | `0.7458767361` |
| Mean paired advantage | `-0.1280381944` |
| Bootstrap 95% interval | `[-0.1553819444, -0.1006944444]` |
| Positive gate | `Failed as required` |
| Null-specificity gate | `Passed` |

The independent telemetry signal did not reproduce the planted mechanism's
gain.

## Validation

The fail-closed validator independently verified the content address and file
census, exact contract and source inventory, raw record counts, result
recomputation, complete deterministic replay, Docker runtime binding, claim
ceiling, and external-state stops.

Validation report:

`/Users/shaanp/Documents/ResearchArtifacts/astral-v25-validation-8da34114.json`

Report SHA-256:

`08a35799169c9636671e4c6dc9382219444e83019f938eaa0544440bc2052bb7`

Pre-assessment focused validation recorded eight V25 tests passing. The pinned
historical Astral runtime recorded 138 Astral tests passing, and the locked Rust
protocol suite recorded six tests passing.

## Disposition

C045 changes append-only from `In test` to `Not refuted` within the exact
synthetic setup. This qualifies the Docker sensitivity/null-specificity harness.

The result does not test a language model. Task-local adapters make the zero
retention loss an engineered invariant, not evidence that a shared neural model
avoids catastrophic forgetting. The planted telemetry is construction-known,
not discovered privileged access.

Unchanged external states:

- model-backed continual learning: `NotRun`;
- independently verified: `NotRun`;
- confirmation: `NotAuthorized`;
- Stage 0C: `Blocked`;
- Stage 1: `BlockedByStage0C`;
- thesis: `NotValidated`.
