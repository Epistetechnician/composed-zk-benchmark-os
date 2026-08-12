# V25 bounded autoresearch maintenance tick — 2026-08-11 (container-shape fail-closed checks)

State slice: `astral-telemetry-information-presence-v25`.

## Research question

Does the independent V25 artifact validator reject malformed manifest and
configuration-lock container shapes through controlled fail-closed validation,
rather than leaking incidental `TypeError`/`AttributeError` exceptions?

Measurable criterion: non-object `manifest.files` and non-object
`configuration-lock.inputs` must raise explicit `ValueError`s; targeted
regressions and the exact canonical suite must pass; and the change must remain
within the authorized V25 source/test/documentation scope.

## Baseline safety checkpoint

Startup `git status --short` showed no staged or modified tracked paths. It
showed only pre-existing untracked Python caches and generated files, including
`experiments/**/__pycache__`, `fsm_result.json`, `output/**`, and
`tools/**/__pycache__`. Those baseline paths were not staged, modified, or
removed.

## Inspection and reproduction

Inspection found that `validate()` iterated `manifest["files"]` without first
requiring an object, while `validate_lock()` called `.items()` on
`configuration-lock.inputs` without checking its container shape. Reproduction
showed `manifest.files = null` raised `TypeError`, and `inputs = []`, `null`, or
a string raised `AttributeError`; these were rejected but did not provide the
validator's controlled failure boundary.

## Change kept

Added explicit object checks for `manifest.files` and
`configuration-lock.inputs`, with deterministic `ValueError` messages. Added
hermetic parameterized regressions for null, list, and string container forms.
No V25 concepts, configuration, prompts, injection sites, strengths, wrappers,
probe math, qualification, sealed assessment, assessment artifacts, or claim
boundaries changed.

## Validation

Targeted command:

```text
PYTHONPATH=/tmp/astral_torch_import_stub:/Users/shaanp/.cache/uv/archive-v0/DD4lPkGabhq7gIuUlQUdL:/Users/shaanp/.cache/uv/archive-v0/oDCUdaF3CoZQZwAVwTpox:/Users/shaanp/.cache/uv/archive-v0/eWGr8IC0NtaMkom2aqcVR:/Users/shaanp/.cache/uv/archive-v0/vnmgrwvNUMDgXjyLtw4ee:/Users/shaanp/.cache/uv/archive-v0/faDZ9cYbXTm6vuM4VP3ge:/Users/shaanp/.cache/uv/archive-v0/ZpKB9X2S45gW2-D3cgrbC:/Users/shaanp/.cache/uv/archive-v0/MIQf_H2GFFb0O0k9k2fuK:/Users/shaanp/.hermes/hermes-agent/venv/lib/python3.11/site-packages DYLD_LIBRARY_PATH=/Users/shaanp/.cache/uv/archive-v0/FX94lcPaFbhQQDA6j1NpI/mlx/lib /opt/homebrew/bin/python3.13 -m pytest -q tools/astral-telemetry-probe-v25/tests/test_manifest_structure.py tools/astral-telemetry-probe-v25/tests/test_lock_boundary_hardening.py
```

Result: `16 passed in 0.04s`.

The required canonical command was run before the change for baseline context:
`81 passed in 1.40s`. It will be rerun after the final documentation change
and recorded in the maintenance report.

`git diff --check` passed after the source/test change. No network, downloads,
model execution, training, adaptive tuning, assessment rerun, retuning,
prior-data/adapter reuse, or Evidence Ledger mutation occurred.

## Checkpoint and claim boundary

The kept paths are exactly:

- `tools/astral-telemetry-probe-v25/validator_v25.py`
- `tools/astral-telemetry-probe-v25/tests/test_manifest_structure.py`
- this phase note

No V25 assessment was rerun or retuned. No accepted Evidence Ledger mutation
or scientific claim upgrade occurred. The unchanged claim ceiling is
`LocalDevelopmentPrivilegedTelemetryInformationPresence`.
