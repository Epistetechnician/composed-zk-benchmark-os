# V25 bounded autoresearch maintenance tick — 2026-08-12 (missing lock-input boundary)

State slice: `astral-telemetry-information-presence-v25`.

## Snapshot and measurable question

Initial snapshot: `master` at `25c5f7aa`, with pre-existing untracked caches,
generated outputs, `fsm_result.json`, and other user paths. None were modified,
staged, or adopted.

Question: does the independent V25 validator fail closed with a stable missing-input
error when a configuration lock names a path that is absent or is a directory,
rather than passing the path to hashing and leaking an incidental filesystem error?

## Change

`validate_lock` now checks that each resolved locked input is a regular file before
hashing it and reports `lock input missing: <name>` otherwise. Two hermetic tests
cover an absent input and a directory input. No concepts, prompts, sites, strengths,
wrappers, probe mathematics, thresholds, assessment data, V19 record, or Evidence
Ledger changed. No network, download, model execution, training, adaptive tuning,
assessment rerun, retuning, or prior V22–V25 data/adapter reuse occurred.

## Validation

The targeted command used the exact prescribed environment:

```text
... /opt/homebrew/bin/python3.13 -m pytest -q tools/astral-telemetry-probe-v25/tests/test_lock_boundary_hardening.py
...........                                                              [100%]
11 passed in 0.04s
```

The canonical command used the exact prescribed environment:

```text
... /opt/homebrew/bin/python3.13 -m pytest -q experiments/astral_fsm/tests tools/astral-hybrid-instrument-v24/tests tools/astral-telemetry-probe-v25/tests
........................................................................ [ 63%]
..........................................                               [100%]
114 passed in 1.02s
```

`git diff --check` passed. Final commit and status verification are recorded in
the maintenance report delivered with this tick.

Claim ceiling remains
`LocalDevelopmentPrivilegedTelemetryInformationPresence`; this tick makes no
accepted-evidence, benchmark, Stage 0C, Stage 1, introspection, consciousness,
SOTA, breakthrough, or generalization claim.
