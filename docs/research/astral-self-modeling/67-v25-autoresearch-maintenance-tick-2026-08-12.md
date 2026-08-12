# V25 bounded autoresearch maintenance tick — 2026-08-12 (duplicate-JSON-key diagnostics)

State slice: `astral-telemetry-information-presence-v25`.

## Snapshot and measurable question

Initial snapshot: `master` at `fb4adee8`, with pre-existing untracked caches,
generated outputs, `fsm_result.json`, and other user paths. None were modified,
staged, or adopted.

Question: does the independent V25 validator reject duplicate JSON object keys
in configuration-lock input instead of silently applying last-key-wins parsing to
a locked gate or boundary field?

## Change

`_read_json` now rejects duplicate object keys in every validator document and
maps the rejection to the stable document-specific `ValueError` boundary. One
hermetic configuration-lock regression test covers a duplicated ordering marker.
No concepts, prompts, sites, strengths, wrappers, probe mathematics, thresholds,
assessment data, V19 record, or Evidence Ledger changed. No network, download,
model execution, training, adaptive tuning, assessment rerun, retuning, or prior
V22–V25 data/adapter reuse occurred.

## Validation

Targeted command used the exact prescribed environment:

```text
... /opt/homebrew/bin/python3.13 -m pytest -q tools/astral-telemetry-probe-v25/tests/test_validator_hardening.py
......................                                                   [100%]
22 passed in 0.06s
```

The canonical command used the exact prescribed environment:

```text
... /opt/homebrew/bin/python3.13 -m pytest -q experiments/astral_fsm/tests tools/astral-hybrid-instrument-v24/tests tools/astral-telemetry-probe-v25/tests
........................................................................ [ 64%]
........................................                                 [100%]
112 passed in 0.82s
```

`git diff --check` passed before commit. Final `git show --stat --oneline HEAD`
and `git status` verification are recorded in the maintenance report.

Claim ceiling remains
`LocalDevelopmentPrivilegedTelemetryInformationPresence`; this tick makes no
accepted-evidence, benchmark, Stage 0C, Stage 1, introspection, consciousness,
SOTA, breakthrough, or generalization claim.
