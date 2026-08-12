# V25 bounded Astral maintenance tick — 2026-08-12 (nested-symlink lock audit)

State slice: `astral-telemetry-information-presence-v25`.

## Snapshot and measurable question

Initial snapshot was captured with:

```text
git status --short --untracked-files=all
git branch --show-current
git log -1 --oneline
```

The working tree had no staged or modified tracked paths. It contained the
pre-existing untracked generated paths under `experiments/**/__pycache__/`,
`tools/**/__pycache__/`, `fsm_result.json`, and `output/**`; these were not
modified, staged, or adopted. The branch was `master` and HEAD was
`e5fb9841 test(astral-v25): cover malformed classification documents`.

Question: does the V25 lock validator reject a symlinked directory in a
nested declared input path before resolving or hashing its contents?

## Inspection, reproduction, and disposition

Inspection of `tools/astral-telemetry-probe-v25/validator_v25.py` confirmed
that `_reject_symlinks(root)` recursively rejects symlinks before lock parsing,
while `_bundle_path` separately enforces relative, root-contained declared
paths. Existing tests covered a symlinked input file and accepted nested
regular inputs, but did not directly cover a symlinked nested directory.

Added one hermetic regression test,
`test_validate_lock_rejects_symlinked_nested_directory`, which creates a
bundle-local `inputs` symlink to an outside directory and verifies that
`validate_lock` fails closed with `symlinked file in bundle`. No production
validator behavior was changed. No network, download, model execution,
training, adaptive tuning, assessment rerun, retuning, or V22–V25 concept or
configuration reuse occurred. The V19 record and accepted Evidence Ledger
were untouched.

## Validation

Focused test and whitespace check:

```text
PYTHONPATH=/tmp/astral_torch_import_stub:/Users/shaanp/.cache/uv/archive-v0/DD4lPkGabhq7gIuUlQUdL:/Users/shaanp/.cache/uv/archive-v0/oDCUdaF3CoZQZwAVwTpox:/Users/shaanp/.cache/uv/archive-v0/eWGr8IC0NtaMkom2aqcVR:/Users/shaanp/.cache/uv/archive-v0/vnmgrwvNUMDgXjyLtw4ee:/Users/shaanp/.cache/uv/archive-v0/faDZ9cYbXTm6vuM4VP3ge:/Users/shaanp/.cache/uv/archive-v0/ZpKB9X2S45gW2-D3cgrbC:/Users/shaanp/.cache/uv/archive-v0/MIQf_H2GFFb0O0k9k2fuK:/Users/shaanp/.hermes/hermes-agent/venv/lib/python3.11/site-packages DYLD_LIBRARY_PATH=/Users/shaanp/.cache/uv/archive-v0/FX94lcPaFbhQQDA6j1NpI/mlx/lib /opt/homebrew/bin/python3.13 -m pytest -q tools/astral-telemetry-probe-v25/tests/test_lock_boundary_hardening.py && git diff --check
.............                                                            [100%]
13 passed in 0.03s
```

Canonical suite, run before the change and again as the required current-HEAD
validation after the change:

```text
PYTHONPATH=/tmp/astral_torch_import_stub:/Users/shaanp/.cache/uv/archive-v0/DD4lPkGabhq7gIuUlQUdL:/Users/shaanp/.cache/uv/archive-v0/oDCUdaF3CoZQZwAVwTpox:/Users/shaanp/.cache/uv/archive-v0/eWGr8IC0NtaMkom2aqcVR:/Users/shaanp/.cache/uv/archive-v0/vnmgrwvNUMDgXjyLtw4ee:/Users/shaanp/.cache/uv/archive-v0/faDZ9cYbXTm6vuM4VP3ge:/Users/shaanp/.cache/uv/archive-v0/ZpKB9X2S45gW2-D3cgrbC:/Users/shaanp/.cache/uv/archive-v0/MIQf_H2GFFb0O0k9k2fuK:/Users/shaanp/.hermes/hermes-agent/venv/lib/python3.13/site-packages DYLD_LIBRARY_PATH=/Users/shaanp/.cache/uv/archive-v0/FX94lcPaFbhQQDA6j1NpI/mlx/lib /opt/homebrew/bin/python3.13 -m pytest -q experiments/astral_fsm/tests tools/astral-hybrid-instrument-v24/tests tools/astral-telemetry-probe-v25/tests
........................................................................ [ 59%]
..................................................                       [100%]
122 passed in 0.98s
```

## Result and claim boundary

Kept the additive hermetic test and this phase note. The nested symlink
boundary is now directly covered; no external artifact was opened or changed.
The pre-existing untracked generated paths remain a cleanliness blocker and
were preserved per instruction.

Checkpoint commit: recorded after validation as a small isolated commit; the
final report names its exact hash. Confidence is high for this local
symlink-ordering regression and the current-HEAD hermetic suite. Confidence
does not extend beyond local validation.

Claim ceiling remains
`LocalDevelopmentPrivilegedTelemetryInformationPresence`; this tick makes no
accepted-evidence, benchmark, Stage 0C, Stage 1, introspection, consciousness,
SOTA, breakthrough, or generalization claim.
