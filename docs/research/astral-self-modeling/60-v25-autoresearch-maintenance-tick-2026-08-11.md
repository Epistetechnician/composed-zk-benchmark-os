# V25 bounded autoresearch maintenance tick — 2026-08-11 (top-level JSON shape checks)

State slice: `astral-telemetry-information-presence-v25`.

## Research question

Does the independent V25 artifact validator reject non-object top-level JSON
documents with explicit fail-closed errors, instead of leaking incidental
subscription or indexing exceptions?

Measurable criterion: top-level `manifest.json`, `result.json`, and
`configuration-lock.json` documents supplied as `null`, arrays, or strings must
raise deterministic `ValueError`s; the exact canonical suite must pass; and the
change must remain within the authorized V25 source/test/documentation scope.

## Baseline safety checkpoint

Startup inspection recorded pre-existing untracked Python caches and generated
files. No baseline user files were modified, staged, removed, or cleaned.

## Inspection and reproduction

The validator assumed each decoded top-level JSON document was an object. A
non-object manifest or result could therefore fail later through indexing, and
a non-object lock could fail while reading its fields. These are malformed
artifact containers and should be rejected at the validator boundary.

## Change kept

Added explicit object checks for the manifest, result, and configuration-lock
documents, plus hermetic parameterized regressions for null, array, and string
documents. No concepts, prompts, injection sites, strengths, wrappers, probe
math, qualification, assessment, or claim boundary changed.

## Validation

Targeted command:

```text
PYTHONPATH=/tmp/astral_torch_import_stub:/Users/shaanp/.cache/uv/archive-v0/DD4lPkGabhq7gIuUlQUdL:/Users/shaanp/.cache/uv/archive-v0/oDCUdaF3CoZQZwAVwTpox:/Users/shaanp/.cache/uv/archive-v0/eWGr8IC0NtaMkom2aqcVR:/Users/shaanp/.cache/uv/archive-v0/vnmgrwvNUMDgXjyLtw4ee:/Users/shaanp/.cache/uv/archive-v0/faDZ9cYbXTm6vuM4VP3ge:/Users/shaanp/.cache/uv/archive-v0/ZpKB9X2S45gW2-D3cgrbC:/Users/shaanp/.cache/uv/archive-v0/MIQf_H2GFFb0O0k9k2fuK:/Users/shaanp/.hermes/hermes-agent/venv/lib/python3.11/site-packages DYLD_LIBRARY_PATH=/Users/shaanp/.cache/uv/archive-v0/FX94lcPaFbhQQDA6j1NpI/mlx/lib /opt/homebrew/bin/python3.13 -m pytest -q tools/astral-telemetry-probe-v25/tests/test_manifest_structure.py
```

Result: `16 passed in 0.03s`.

Exact canonical command:

```text
PYTHONPATH=/tmp/astral_torch_import_stub:/Users/shaanp/.cache/uv/archive-v0/DD4lPkGabhq7gIuUlQUdL:/Users/shaanp/.cache/uv/archive-v0/oDCUdaF3CoZQZwAVwTpox:/Users/shaanp/.cache/uv/archive-v0/eWGr8IC0NtaMkom2aqcVR:/Users/shaanp/.cache/uv/archive-v0/vnmgrwvNUMDgXjyLtw4ee:/Users/shaanp/.cache/uv/archive-v0/faDZ9cYbXTm6vuM4VP3ge:/Users/shaanp/.cache/uv/archive-v0/ZpKB9X2S45gW2-D3cgrbC:/Users/shaanp/.cache/uv/archive-v0/MIQf_H2GFFb0O0k9k2fuK:/Users/shaanp/.hermes/hermes-agent/venv/lib/python3.11/site-packages DYLD_LIBRARY_PATH=/Users/shaanp/.cache/uv/archive-v0/FX94lcPaFbhQQDA6j1NpI/mlx/lib /opt/homebrew/bin/python3.13 -m pytest -q experiments/astral_fsm/tests tools/astral-hybrid-instrument-v24/tests tools/astral-telemetry-probe-v25/tests
```

Result: `94 passed in 0.82s`.

No network, downloads, model execution, training, adaptive tuning, assessment
rerun, retuning, prior-data/adapter reuse, or Evidence Ledger mutation occurred.

## Checkpoint and claim boundary

Kept paths are exactly this validator, its manifest-structure tests, and this
phase note. The unchanged claim ceiling is
`LocalDevelopmentPrivilegedTelemetryInformationPresence`.