# V25 canonical-suite offline runner

State slice: `astral-telemetry-information-presence-v25`.

## Purpose

The V25 maintenance cadence previously embedded a long machine-specific
`PYTHONPATH`. That made a valid local runtime easy to mis-detect and allowed a
lexicographically first but incompatible cached native package to shadow the
correct CPython build. `run_canonical_suite.py` is now the repository-owned
offline preflight and canonical-suite entrypoint.

It discovers only already-cached artifacts, requires the CPython 3.13 MLX
extension and native Metal library, selects native NumPy and `regex` builds
matching the selected interpreter ABI, enables offline Transformers/HF mode,
and runs the unchanged authorized suite:

```text
experiments/astral_fsm/tests
tools/astral-hybrid-instrument-v24/tests
tools/astral-telemetry-probe-v25/tests
```

The `/tmp/astral_torch_import_stub/torch.py` dependency remains an import-only
compatibility shim for historical V17 collection. The runner never uses it for
model execution or training.

## Verification

- Runner hermetic tests: `3 passed`.
- Runner preflight and canonical suite:
  `mlx=.../mlx/core.cpython-313-darwin.so`,
  `mlx_lm=.../mlx_lm/__init__.py`, followed by `126 passed in 0.95s`.
- The tests cover missing native libraries and incompatible-versus-compatible
  cached `regex` candidates.
- No network, download, model training, assessment rerun, adaptive tuning, or
  V22–V25 concept/configuration reuse occurred.

This is reproducibility and local regression evidence only. The V25 result,
V19 record, accepted Evidence Ledger, and claim ceiling remain unchanged:
`LocalDevelopmentPrivilegedTelemetryInformationPresence`.
