# V25 bounded autoresearch maintenance tick — 2026-08-11 (root symlink boundary)

State slice: `astral-telemetry-information-presence-v25`.

## Research question

Does the independent V25 artifact validator reject a symlinked bundle root before
reading manifest or lock data, in addition to rejecting symlinks below the root?

Measurable criterion: a hermetic root-symlink regression fails before the fix,
passes after the fix, all non-MLX V25 validator tests remain green, and the
change stays within the authorized V25 source/test scope.

## Baseline safety checkpoint

Startup commands:

```text
git status --short && git log -5 --oneline --decorate
```

Observed baseline before this tick:

- `HEAD`: `7c6b2896` (`fix(astral-v25): require boolean lock ordering marker`);
- no staged or modified tracked paths;
- pre-existing untracked paths included `experiments/__pycache__/`,
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

Inspected `validator_v25.py`, the V25 validator tests, the V25 protocol note,
and recent V25 commits. `_reject_symlinks` scanned `root.rglob("*")` but did
not reject `root` itself when called directly with a symlinked bundle root.

Added `test_root_symlink_boundary.py`. Red-before-implementation command:

```text
python3 -m pytest -q tools/astral-telemetry-probe-v25/tests/test_root_symlink_boundary.py
# 1 failed: FileNotFoundError while reading result.json, rather than the expected
# symlink-boundary ValueError
```

## Change kept

Added a fail-closed `root.is_symlink()` check to `_reject_symlinks`, preserving
the existing descendant-symlink rejection and preventing manifest, result, or
lock reads through a symlinked bundle root. No concepts, injection sites,
strengths, wrappers, prompts, probe math, configuration, assessment artifacts,
or claim boundaries changed.

## Validation

```text
PYTHONPATH=/tmp/astral_torch_import_stub:<cached-runtime-paths> \
DYLD_LIBRARY_PATH=<cached-mlx-library> /opt/homebrew/bin/python3.13 -m pytest -q \
tools/astral-telemetry-probe-v25/tests/test_lock_boundary.py \
tools/astral-telemetry-probe-v25/tests/test_lock_boundary_audit.py \
tools/astral-telemetry-probe-v25/tests/test_lock_boundary_hardening.py \
tools/astral-telemetry-probe-v25/tests/test_manifest_reserved_name.py \
tools/astral-telemetry-probe-v25/tests/test_manifest_structure.py \
tools/astral-telemetry-probe-v25/tests/test_root_symlink_boundary.py \
tools/astral-telemetry-probe-v25/tests/test_validator_hardening.py
# 30 passed in 0.05s

python3 -m py_compile tools/astral-telemetry-probe-v25/validator_v25.py \
tools/astral-telemetry-probe-v25/tests/test_root_symlink_boundary.py
# passed

git diff --check
# passed
```

The authorized full V25 test collection was attempted with the recorded cached
Python 3.13/MLX environment but remained blocked during `test_v25.py` import:
NumPy 2.4.3 provides only `_multiarray_umath.cpython-311-darwin.so` while
Python 3.13 is running. No installation, network access, download, model
execution, training, adaptive tuning, assessment rerun, retuning, prior data or
adapter reuse, or Evidence Ledger mutation occurred.

## Checkpoint and claim boundary

Kept and committed exactly these two authorized paths:

- `tools/astral-telemetry-probe-v25/validator_v25.py`
- `tools/astral-telemetry-probe-v25/tests/test_root_symlink_boundary.py`

Commit: `c26cf6a` (`fix(astral-v25): reject symlinked bundle roots`).

The V19 completion record remains unchanged: V19 completed end to end; compact
task-routed residual 8/8 acquisition, retention, recovery; adapter budget
5,877,252 vs 5,877,295 bytes; validator valid; 37 tests passed; H100
unauthorized; no breakthrough/general continual-learning claim; commit
`c8d2b34` on `codex/v19-task-routed-compact-residual`.

No V25 assessment was rerun or retuned. No accepted Evidence Ledger mutation or
scientific claim upgrade occurred. The unchanged claim ceiling is
`LocalDevelopmentPrivilegedTelemetryInformationPresence`.
