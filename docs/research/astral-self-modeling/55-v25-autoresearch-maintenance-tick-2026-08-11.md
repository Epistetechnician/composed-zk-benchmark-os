# V25 bounded autoresearch maintenance tick — 2026-08-11 (bundle-root type boundary)

State slice: `astral-telemetry-information-presence-v25`.

## Research question

Does the independent V25 artifact validator fail closed with a stable boundary
error when its supplied bundle root is a regular file, before attempting to
read manifest data?

Measurable criterion: the new hermetic regression fails before the guard,
passes after the guard, all non-MLX V25 validator tests remain green, and the
change stays within the authorized V25 source/test scope.

## Baseline safety checkpoint

Startup command:

```text
git status --short && git log -5 --oneline --decorate
```

Observed baseline:

- `HEAD`: `a5e1c48b` (`docs(astral-v25): record root symlink maintenance tick`);
- no staged or modified tracked paths;
- pre-existing untracked paths were `experiments/__pycache__/`,
  `experiments/astral_fsm/__pycache__/`, `experiments/astral_fsm/tests/__pycache__/`,
  `fsm_result.json`, `output/artifacts/`, `output/catalyst-strategy-surface.html`,
  `tools/astral-activation-discrimination-v22/__pycache__/`,
  `tools/astral-hybrid-instrument-v24/__pycache__/`,
  `tools/astral-hybrid-instrument-v24/tests/__pycache__/`,
  `tools/astral-lm-explainer-v17/__pycache__/`,
  `tools/astral-telemetry-probe-v25/__pycache__/`, and
  `tools/astral-telemetry-probe-v25/tests/__pycache__/`.

These baseline paths were not staged, modified, or committed.

## Inspection and reproduction

Inspected `validator_v25.py`, existing root/descendant symlink tests, lock
boundary tests, manifest-shape tests, and recent V25 commits. `_reject_symlinks`
rejected symlink roots and descendants but did not explicitly reject a regular
file root. The red-before-implementation command was:

```text
python3 -m pytest -q tools/astral-telemetry-probe-v25/tests/test_root_symlink_boundary.py
# 1 failed, 1 passed; the failure was NotADirectoryError while reading
# bundle-file/manifest.json rather than the expected boundary ValueError
```

## Change kept

Added a fail-closed `root.is_dir()` check to `_reject_symlinks` and a hermetic
regression test. Symlink checks, manifest/lock semantics, concepts, injection
sites, strengths, wrappers, prompts, probe math, configuration, assessment
artifacts, and claim boundaries are unchanged.

## Validation

```text
python3 -m pytest -q tools/astral-telemetry-probe-v25/tests/test_lock_boundary.py \
  tools/astral-telemetry-probe-v25/tests/test_lock_boundary_audit.py \
  tools/astral-telemetry-probe-v25/tests/test_lock_boundary_hardening.py \
  tools/astral-telemetry-probe-v25/tests/test_manifest_reserved_name.py \
  tools/astral-telemetry-probe-v25/tests/test_manifest_structure.py \
  tools/astral-telemetry-probe-v25/tests/test_root_symlink_boundary.py \
  tools/astral-telemetry-probe-v25/tests/test_validator_hardening.py
# 31 passed in 0.05s

python3 -m py_compile tools/astral-telemetry-probe-v25/validator_v25.py \
  tools/astral-telemetry-probe-v25/tests/test_root_symlink_boundary.py
# passed

git diff --check
# passed
```

The full V25 test collection was attempted with `python3 -m pytest -q
tools/astral-telemetry-probe-v25/tests` but was blocked at `test_v25.py`
collection because the available NumPy binary is `cpython-311-darwin.so`
while the active interpreter is Python 3.14. No installation, network access,
download, model execution, training, adaptive tuning, assessment rerun,
retuning, prior data/adapter reuse, or Evidence Ledger mutation occurred.

## Checkpoint and claim boundary

Kept exactly these three authorized paths:

- `tools/astral-telemetry-probe-v25/validator_v25.py`
- `tools/astral-telemetry-probe-v25/tests/test_root_symlink_boundary.py`
- this phase note

The V19 completion record remains unchanged: V19 completed end to end; compact
task-routed residual 8/8 acquisition, retention, recovery; adapter budget
5,877,252 vs 5,877,295 bytes; validator valid; 37 tests passed; H100
unauthorized; no breakthrough/general continual-learning claim; commit
`c8d2b34` on `codex/v19-task-routed-compact-residual`.

No V25 assessment was rerun or retuned. No accepted Evidence Ledger mutation or
scientific claim upgrade occurred. The unchanged claim ceiling is
`LocalDevelopmentPrivilegedTelemetryInformationPresence`.