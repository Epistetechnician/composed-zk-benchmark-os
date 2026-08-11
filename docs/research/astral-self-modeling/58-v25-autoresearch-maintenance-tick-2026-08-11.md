# V25 bounded autoresearch maintenance tick — 2026-08-11 (finite fork metrics)

State slice: `astral-telemetry-information-presence-v25`.

## Research question

Does the independent V25 validator fail closed on non-finite numeric values in a
fork result, rather than allowing IEEE `NaN` comparison behavior to bypass the
classification predicates?

Measurable criterion: `_validate_fork()` must reject non-finite values in
`probe_accuracy`, `self_report_accuracy`, `fork_margin_observed`, and all three
bootstrap metrics; the targeted fork tests and the exact canonical suite must
pass; and changes must remain within the authorized V25 source/test/documentation
scope.

## Baseline safety checkpoint

Startup `git status --short --untracked-files=all` showed only pre-existing
untracked Python caches and generated files outside the change set, including
`experiments/**/__pycache__`, `fsm_result.json`, `output/**`, and
`tools/**/__pycache__`. The branch was `master`; no staged or modified tracked
paths were present. These baseline paths were not staged, modified, or removed.

## Inspection and reproduction

Inspection of `validator_v25.py` found that `_validate_fork()` compared numeric
fields directly and did not reject `NaN` or infinities. Because `abs(nan) >
FORK_MARGIN` is false and `nan >= FORK_MARGIN` is false, a parity classification
with a non-finite observed margin could evade the intended arithmetic and margin
checks. This was a validator-only integrity issue; no model, prompt, concept,
configuration, assessment, or scientific artifact was involved.

## Change kept

Added finite-number validation for the three fork metrics and the bootstrap
interval metrics, explicitly rejecting booleans and non-numeric values as well.
Added six hermetic parameterized cases covering positive/negative infinity and
`NaN`. No V25 concepts, configuration, prompts, assessment artifacts, probe math,
assessment execution, or claim boundaries changed.

## Validation

Targeted command:

```text
PYTHONPATH=/tmp/astral_torch_import_stub:/Users/shaanp/.cache/uv/archive-v0/DD4lPkGabhq7gIuUlQUdL:/Users/shaanp/.cache/uv/archive-v0/oDCUdaF3CoZQZwAVwTpox:/Users/shaanp/.cache/uv/archive-v0/eWGr8IC0NtaMkom2aqcVR:/Users/shaanp/.cache/uv/archive-v0/vnmgrwvNUMDgXjyLtw4ee:/Users/shaanp/.cache/uv/archive-v0/faDZ9cYbXTm6vuM4VP3ge:/Users/shaanp/.cache/uv/archive-v0/ZpKB9X2S45gW2-D3cgrbC:/Users/shaanp/.cache/uv/archive-v0/MIQf_H2GFFb0O0k9k2fuK:/Users/shaanp/.hermes/hermes-agent/venv/lib/python3.11/site-packages DYLD_LIBRARY_PATH=/Users/shaanp/.cache/uv/archive-v0/FX94lcPaFbhQQDA6j1NpI/mlx/lib /opt/homebrew/bin/python3.13 -m pytest -q tools/astral-telemetry-probe-v25/tests/test_v25.py -k 'fork'
# ........                                                                 [100%]
# 8 passed, 15 deselected in 0.61s
```

The required canonical command was run after the change:

```text
PYTHONPATH=/tmp/astral_torch_import_stub:/Users/shaanp/.cache/uv/archive-v0/DD4lPkGabhq7gIuUlQUdL:/Users/shaanp/.cache/uv/archive-v0/oDCUdaF3CoZQZwAVwTpox:/Users/shaanp/.cache/uv/archive-v0/eWGr8IC0NtaMkom2aqcVR:/Users/shaanp/.cache/uv/archive-v0/vnmgrwvNUMDgXjyLtw4ee:/Users/shaanp/.cache/uv/archive-v0/faDZ9cYbXTm6vuM4VP3ge:/Users/shaanp/.cache/uv/archive-v0/ZpKB9X2S45gW2-D3cgrbC:/Users/shaanp/.cache/uv/archive-v0/MIQf_H2GFFb0O0k9k2fuK:/Users/shaanp/.hermes/hermes-agent/venv/lib/python3.11/site-packages DYLD_LIBRARY_PATH=/Users/shaanp/.cache/uv/archive-v0/FX94lcPaFbhQQDA6j1NpI/mlx/lib /opt/homebrew/bin/python3.13 -m pytest -q experiments/astral_fsm/tests tools/astral-hybrid-instrument-v24/tests tools/astral-telemetry-probe-v25/tests
# ........................................................................ [100%]
# 77 passed in 0.77s
```

`git diff --check` passed. No network, downloads, model execution, training,
adaptive tuning, assessment rerun, retuning, prior-data/adapter reuse, or
Evidence Ledger mutation occurred.

## Checkpoint and claim boundary

Kept exactly these authorized paths:

- `tools/astral-telemetry-probe-v25/validator_v25.py`
- `tools/astral-telemetry-probe-v25/tests/test_v25.py`
- this phase note

No V25 assessment was rerun or retuned. No accepted Evidence Ledger mutation or
scientific claim upgrade occurred. The unchanged claim ceiling is
`LocalDevelopmentPrivilegedTelemetryInformationPresence`.
