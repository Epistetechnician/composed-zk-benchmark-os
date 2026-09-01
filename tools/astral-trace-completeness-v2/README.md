# Gemma 3 end-to-end trace completeness V2

State slice: `astral-trace-completeness-gemma3-end-to-end-v2`

This package implements the frozen Gemma 3 1B PT qualification path recorded
in
`docs/research/astral-self-modeling/121-trace-completeness-gemma3-end-to-end-v2.md`.
It provides:

- deterministic fit/tune/assessment prompt-family generation;
- an exact 446-module runtime registry for Transformers `4.57.3`;
- generation-step token, module, attention-score/pattern, cache transition,
  RNG, intervention, output-distribution, sampled-token, and behavioral events;
- owner-only external raw custody and aggregate-only validation;
- exact Gemma Scope 2 every-layer asset manifests and transcoder loading;
- native/instrumented, repeat, no-op, intervention-reach, reconstruction, and
  feature-stability qualification.

The isolated runtime is external to the repository at:

`/Users/shaanp/Documents/astral-custody/trace-completeness-gemma3-end-to-end-v2/assets/runtime-venv`

Run hermetic tests:

```text
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q tools/astral-trace-completeness-v2/tests
```

The qualification command requires the frozen external assets and must run
offline:

```text
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 \
PYTHONDONTWRITEBYTECODE=1 \
/Users/shaanp/Documents/astral-custody/trace-completeness-gemma3-end-to-end-v2/assets/runtime-venv/bin/python \
tools/astral-trace-completeness-v2/qualify_v2.py
```

The single accepted V2 execution is
`QualificationFailedSAEReconstruction`. Do not rerun or change the
normalization, threshold, layer, asset, or prompt under this state slice.
Assessment, graph construction, causal scrubbing, and signed review remain
closed. Reconciliation R2 completed and all six raw event/capture files were
irreversibly expired; only aggregate artifacts, manifests, and receipts remain.
