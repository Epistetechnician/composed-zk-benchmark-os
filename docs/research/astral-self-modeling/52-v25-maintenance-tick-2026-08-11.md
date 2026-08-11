# V25 bounded maintenance tick — 2026-08-11

State slice: `astral-telemetry-information-presence-v25`.

## Research question

Does the current independent V25 validator remain fail-closed for the recently
hardened manifest census and malformed-manifest cases, without changing any
protocol, concept, configuration, assessment, or claim-boundary material?

Measurable criterion: the authorized cached-runtime suite passes, and the
focused manifest/validator hardening regressions all pass.

## Baseline safety checkpoint

Startup commands:

```text
git status --short --untracked-files=all
git log -8 --oneline --decorate
```

Observed baseline:

- branch: `master`;
- `HEAD`: `03aad75f` (`fix(astral-v25): census nested manifest files`);
- staged paths: none;
- modified tracked paths: none;
- untracked baseline paths: generated `fsm_result.json`, generated files under
  `output/`, and Python caches under `experiments/**/__pycache__/`,
  `tools/astral-activation-discrimination-v22/**/__pycache__/`,
  `tools/astral-hybrid-instrument-v24/**/__pycache__/`,
  `tools/astral-lm-explainer-v17/**/__pycache__/`, and
  `tools/astral-telemetry-probe-v25/**/__pycache__/`.

All startup untracked paths were treated as user baseline. None was modified,
staged, or committed.

## Inspection and reproduction

Inspected `validator_v25.py`, the V25 tests, and the recent V25 commits. The
validator now performs a full recursive manifest census, rejects path escapes
and symlinks, checks digests, closes classification and result-boundary cases,
and rejects fork results marked `assessment_unopened`.

Exact commands and results:

```text
PYTHONPATH=/tmp/astral_torch_import_stub:/Users/shaanp/.cache/uv/archive-v0/DD4lPkGabhq7gIuUlQUdL:/Users/shaanp/.cache/uv/archive-v0/oDCUdaF3CoZQZwAVwTpox:/Users/shaanp/.cache/uv/archive-v0/eWGr8IC0NtaMkom2aqcVR:/Users/shaanp/.cache/uv/archive-v0/vnmgrwvNUMDgXjyLtw4ee:/Users/shaanp/.cache/uv/archive-v0/faDZ9cYbXTm6vuM4VP3ge:/Users/shaanp/.cache/uv/archive-v0/ZpKB9X2S45gW2-D3cgrbC:/Users/shaanp/.cache/uv/archive-v0/MIQf_H2GFFb0O0k9k2fuK:/Users/shaanp/.hermes/hermes-agent/venv/lib/python3.11/site-packages DYLD_LIBRARY_PATH=/Users/shaanp/.cache/uv/archive-v0/FX94lcPaFbhQQDA6j1NpI/mlx/lib /opt/homebrew/bin/python3.13 -m pytest -q experiments/astral_fsm/tests tools/astral-hybrid-instrument-v24/tests tools/astral-telemetry-probe-v25/tests
# 63 passed in 0.81s

PYTHONPATH=/tmp/astral_torch_import_stub:/Users/shaanp/.cache/uv/archive-v0/DD4lPkGabhq7gIuUlQUdL:/Users/shaanp/.cache/uv/archive-v0/oDCUdaF3CoZQZwAVwTpox:/Users/shaanp/.cache/uv/archive-v0/eWGr8IC0NtaMkom2aqcVR:/Users/shaanp/.cache/uv/archive-v0/vnmgrwvNUMDgXjyLtw4ee:/Users/shaanp/.cache/uv/archive-v0/faDZ9cYbXTm6vuM4VP3ge:/Users/shaanp/.cache/uv/archive-v0/ZpKB9X2S45gW2-D3cgrbC:/Users/shaanp/.cache/uv/archive-v0/MIQf_H2GFFb0O0k9k2fuK:/Users/shaanp/.hermes/hermes-agent/venv/lib/python3.11/site-packages DYLD_LIBRARY_PATH=/Users/shaanp/.cache/uv/archive-v0/FX94lcPaFbhQQDA6j1NpI/mlx/lib /opt/homebrew/bin/python3.13 -m pytest -q tools/astral-telemetry-probe-v25/tests/test_manifest_structure.py tools/astral-telemetry-probe-v25/tests/test_manifest_reserved_name.py tools/astral-telemetry-probe-v25/tests/test_validator_hardening.py
# 12 passed in 0.03s
```

No network, installation, download, model execution, training, adaptive
selection, assessment rerun, retuning, prior data/adapter reuse, or Evidence
Ledger mutation occurred.

## Decision and checkpoint

Keep this additive maintenance note as the only campaign-owned change. No
source fix was indicated by the reproduced cases, so no validator or existing
test path was changed. The note was committed with an exact path-only commit;
no broad staging command was used.

The unchanged claim ceiling is
`LocalDevelopmentPrivilegedTelemetryInformationPresence`. This tick is not
benchmark evidence, SOTA or breakthrough evidence, introspection or
consciousness evidence, Stage 0C confirmation, Stage 1 advancement, or accepted
Evidence Ledger evidence.
