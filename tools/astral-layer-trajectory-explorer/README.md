# Astral Layer Trajectory Explorer

State slice: `astral-layer-trajectory-explorer-prototype-v1`.

This is a deterministic, local-only visual prototype inspired by the supplied layer-trajectory reference. It uses a synthetic 255-path × 78-layer fixture to exercise the intended interaction model: direction/raw projection, timeline replay, path selection, drag-to-propose, zoom, and visual-only push annotations.

It is not a model runner and contains no activations, logits, causal effects, assessment results, or provider evidence. The claim ceiling is instrument-feasibility design only.

Serve the repository root and open:

```text
/tools/astral-layer-trajectory-explorer/index.html
```

For example:

```sh
python -m http.server 4178
```
