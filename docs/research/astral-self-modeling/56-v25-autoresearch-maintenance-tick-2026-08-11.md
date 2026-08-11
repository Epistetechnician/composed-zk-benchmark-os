# V25 bounded autoresearch maintenance tick — 2026-08-11 (assessment bootstrap floor)

State slice: `astral-telemetry-information-presence-v25`.

## Research question

Does the independent V25 artifact validator enforce the preregistered
assessment bootstrap lower-bound gate above chance (`0.5`) when accepting a
fork classification?

Measurable criterion: a forged fork result with `probe_accuracy=0.90`,
`fork_margin_observed=0.40`, and `bootstrap.lower_95=0.10` must be rejected;
valid fork semantics must remain accepted; the canonical suite must pass; and
all changes must remain within the authorized V25 source/test/documentation
scope.

## Baseline safety checkpoint

Startup command:

```text
git status --short && git branch --show-current && git log -1 --oneline
```

Observed baseline:

- branch: `master`;
- `HEAD`: `ee52cb1d fix(astral-v25): reject non-directory bundle roots`;
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

Inspected the V25 protocol note, `validator_v25.py`, fork-semantic tests, and
prior V25 maintenance notes. The protocol requires the assessment bootstrap
lower bound to be above chance (`0.5`), but `_validate_fork` only checked
`lower_95 > 0`.

The exact pre-change reproduction was:

```text
PYTHONPATH=/tmp/astral_torch_import_stub:/Users/shaanp/.cache/uv/archive-v0/DD4lPkGabhq7gIuUlQUdL:/Users/shaanp/.cache/uv/archive-v0/oDCUdaF3CoZQZwAVwTpox:/Users/shaanp/.cache/uv/archive-v0/eWGr8IC0NtaMkom2aqcVR:/Users/shaanp/.cache/uv/archive-v0/vnmgrwvNUMDgXjyLtw4ee:/Users/shaanp/.cache/uv/archive-v0/faDZ9cYbXTm6vuM4VP3ge:/Users/shaanp/.cache/uv/archive-v0/ZpKB9X2S45gW2-D3cgrbC:/Users/shaanp/.cache/uv/archive-v0/MIQf_H2GFFb0O0k9k2fuK:/Users/shaanp/.hermes/hermes-agent/venv/lib/python3.11/site-packages DYLD_LIBRARY_PATH=/Users/shaanp/.cache/uv/archive-v0/FX94lcPaFbhQQDA6j1NpI/mlx/lib /opt/homebrew/bin/python3.13 - <<'PY'
import importlib.util
from pathlib import Path
p=Path('tools/astral-telemetry-probe-v25/validator_v25.py')
s=importlib.util.spec_from_file_location('v',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
r={'classification':'InformationPresenceReportGapObserved','probe_accuracy':.9,'self_report_accuracy':.5,'fork_margin_observed':.4,'bootstrap':{'lower_95':.1}}
try:
    m._validate_fork(r)
except ValueError as exc:
    print('rejected:', exc)
else:
    print('accepted: lower_95=0.1')
PY
# accepted: lower_95=0.1
```

## Change kept

Added the named `ASSESS_CHANCE_FLOOR = 0.5` validator constant and changed
fork qualification to require `bootstrap.lower_95 > ASSESS_CHANCE_FLOOR`. Added a
hermetic fork-semantic regression for a below-chance lower bound and updated
valid synthetic fork fixtures to use a lower bound above chance. No V25
concepts, configuration, prompts, assessment artifacts, probe math, or claim
boundaries changed.

## Validation

The first targeted test after the source change exposed stale synthetic valid
fixtures using `lower_95=0.2`; those fixtures were corrected to satisfy the
frozen above-chance contract. The targeted test then passed:

```text
PYTHONPATH=<the exact canonical PYTHONPATH> DYLD_LIBRARY_PATH=<the exact canonical DYLD_LIBRARY_PATH> /opt/homebrew/bin/python3.13 -m pytest -q tools/astral-telemetry-probe-v25/tests/test_v25.py::test_validator_fork_semantics
# 1 passed
```

Canonical command and result:

```text
PYTHONPATH=/tmp/astral_torch_import_stub:/Users/shaanp/.cache/uv/archive-v0/DD4lPkGabhq7gIuUlQUdL:/Users/shaanp/.cache/uv/archive-v0/oDCUdaF3CoZQZwAVwTpox:/Users/shaanp/.cache/uv/archive-v0/eWGr8IC0NtaMkom2aqcVR:/Users/shaanp/.cache/uv/archive-v0/vnmgrwvNUMDgXjyLtw4ee:/Users/shaanp/.cache/uv/archive-v0/faDZ9cYbXTm6vuM4VP3ge:/Users/shaanp/.cache/uv/archive-v0/ZpKB9X2S45gW2-D3cgrbC:/Users/shaanp/.cache/uv/archive-v0/MIQf_H2GFFb0O0k9k2fuK:/Users/shaanp/.hermes/hermes-agent/venv/lib/python3.11/site-packages DYLD_LIBRARY_PATH=/Users/shaanp/.cache/uv/archive-v0/FX94lcPaFbhQQDA6j1NpI/mlx/lib /opt/homebrew/bin/python3.13 -m pytest -q experiments/astral_fsm/tests tools/astral-hybrid-instrument-v24/tests tools/astral-telemetry-probe-v25/tests
# ......................................................................   [100%]
# 70 passed in 0.80s
```

`git diff --check` passed. No network, downloads, model execution, training,
adaptive tuning, assessment rerun, retuning, prior-data/adapter reuse, or
Evidence Ledger mutation occurred.

## Checkpoint and claim boundary

Kept exactly these three authorized paths:

- `tools/astral-telemetry-probe-v25/validator_v25.py`
- `tools/astral-telemetry-probe-v25/tests/test_v25.py`
- this phase note

The V19 completion record remains unchanged: V19 completed end to end; compact
task-routed residual 8/8 acquisition, retention, recovery; adapter budget
5,877,252 vs 5,877,295 bytes; validator valid; 37 tests passed; H100
unauthorized; no breakthrough/general continual-learning claim; commit
`c8d2b34` on `codex/v19-task-routed-compact-residual`.

No V25 assessment was rerun or retuned. No accepted Evidence Ledger mutation or
scientific claim upgrade occurred. The unchanged claim ceiling is
`LocalDevelopmentPrivilegedTelemetryInformationPresence`.
