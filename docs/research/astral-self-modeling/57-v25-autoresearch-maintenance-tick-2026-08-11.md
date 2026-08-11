# V25 bounded autoresearch maintenance tick — 2026-08-11 (CLI root boundary)

State slice: `astral-telemetry-information-presence-v25`.

## Research question

Does the V25 validator command-line entry point preserve the library-level
symlinked-bundle-root rejection, rather than resolving the user-supplied root
before validation?

Measurable criterion: invoking `validator_v25.py` on a symlink to a directory
must return exit status `1` and the exact JSON failure
`{"reason": "symlinked bundle root", "valid": false}`; the targeted boundary
tests and the canonical suite must pass; and all changes must remain within the
authorized V25 source/test/documentation scope.

## Baseline safety checkpoint

Startup snapshot:

```text
git status --short && git branch --show-current
# ?? experiments/__pycache__/
# ?? experiments/astral_fsm/__pycache__/
# ?? experiments/astral_fsm/tests/__pycache__/
# ?? fsm_result.json
# ?? output/artifacts/
# ?? output/catalyst-strategy-surface.html
# ?? tools/astral-activation-discrimination-v22/__pycache__/
# ?? tools/astral-hybrid-instrument-v24/__pycache__/
# ?? tools/astral-hybrid-instrument-v24/tests/__pycache__/
# ?? tools/astral-lm-explainer-v17/__pycache__/
# ?? tools/astral-telemetry-probe-v25/__pycache__/
# ?? tools/astral-telemetry-probe-v25/tests/__pycache__/
# master
```

These pre-existing untracked paths were not staged, modified, or committed.
The recent V25 checkpoint history included `fea1629a`, `ee52cb1d`, and
`c26cf6ad`; no baseline user files were changed.

## Inspection and reproduction

Inspection found that `_reject_symlinks()` correctly rejects a symlinked root
when `validate()` is called directly, but `main()` passed
`args.root.resolve()` into `validate()` and `validate_lock()`. That erased the
symlink boundary before the validator could inspect it. This was a
command-line-only fail-closed gap; no model, prompt, concept, configuration,
assessment, or artifact data was involved.

## Change kept

Changed only the CLI dispatch to pass `args.root` unchanged. Added one
hermetic regression to `test_root_symlink_boundary.py` that invokes `main()`
with a symlinked bundle root and checks the exact failure JSON. No protocol
constants, V25 concepts, configuration, assessment artifacts, probe math, or
claim boundaries changed.

## Validation

Targeted command:

```text
PYTHONPATH=/tmp/astral_torch_import_stub:/Users/shaanp/.cache/uv/archive-v0/DD4lPkGabhq7gIuUlQUdL:/Users/shaanp/.cache/uv/archive-v0/oDCUdaF3CoZQZwAVwTpox:/Users/shaanp/.cache/uv/archive-v0/eWGr8IC0NtaMkom2aqcVR:/Users/shaanp/.cache/uv/archive-v0/vnmgrwvNUMDgXjyLtw4ee:/Users/shaanp/.cache/uv/archive-v0/faDZ9cYbXTm6vuM4VP3ge:/Users/shaanp/.cache/uv/archive-v0/ZpKB9X2S45gW2-D3cgrbC:/Users/shaanp/.cache/uv/archive-v0/MIQf_H2GFFb0O0k9k2fuK:/Users/shaanp/.hermes/hermes-agent/venv/lib/python3.11/site-packages DYLD_LIBRARY_PATH=/Users/shaanp/.cache/uv/archive-v0/FX94lcPaFbhQQDA6j1NpI/mlx/lib /opt/homebrew/bin/python3.13 -m pytest -q tools/astral-telemetry-probe-v25/tests/test_root_symlink_boundary.py
# ... [100%]
# 3 passed in 0.02s
```

Canonical command:

```text
PYTHONPATH=/tmp/astral_torch_import_stub:/Users/shaanp/.cache/uv/archive-v0/DD4lPkGabhq7gIuUlQUdL:/Users/shaanp/.cache/uv/archive-v0/oDCUdaF3CoZQZwAVwTpox:/Users/shaanp/.cache/uv/archive-v0/eWGr8IC0NtaMkom2aqcVR:/Users/shaanp/.cache/uv/archive-v0/vnmgrwvNUMDgXjyLtw4ee:/Users/shaanp/.cache/uv/archive-v0/faDZ9cYbXTm6vuM4VP3ge:/Users/shaanp/.cache/uv/archive-v0/ZpKB9X2S45gW2-D3cgrbC:/Users/shaanp/.cache/uv/archive-v0/MIQf_H2GFFb0O0k9k2fuK:/Users/shaanp/.hermes/hermes-agent/venv/lib/python3.11/site-packages DYLD_LIBRARY_PATH=/Users/shaanp/.cache/uv/archive-v0/FX94lcPaFbhQQDA6j1NpI/mlx/lib /opt/homebrew/bin/python3.13 -m pytest -q experiments/astral_fsm/tests tools/astral-hybrid-instrument-v24/tests tools/astral-telemetry-probe-v25/tests
# .......................................................................  [100%]
# 71 passed in 1.09s
```

No network, downloads, model execution, training, adaptive tuning, assessment
rerun, retuning, prior-data/adapter reuse, or Evidence Ledger mutation
occurred.

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

No V25 assessment was rerun or retuned. No accepted Evidence Ledger mutation
or scientific claim upgrade occurred. The unchanged claim ceiling is
`LocalDevelopmentPrivilegedTelemetryInformationPresence`.
