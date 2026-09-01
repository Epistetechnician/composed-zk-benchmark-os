# Astral Model Observatory — Prototype

Question being answered: can a local app display a changing model telemetry stream beside sleep-stage proxies, an explicitly unverified astral-projection hypothesis channel, general self-model diagnostics, and the past/present/future research record?

State slice: `astral-research-progress-app-prototype`.

This is a throwaway UI prototype. The default stream is simulated. It does not claim to measure biological sleep, astral projection, consciousness, introspection, retrospection, faithful computation, or a model's complete internal state.

Run from the repository root:

```text
python3 -m http.server 4173 --directory .
```

Open [http://localhost:4173/tools/astral-research-progress-app/](http://localhost:4173/tools/astral-research-progress-app/).

## Live local model mode

The prototype can poll the loopback bridge backed by the already-cached local
`nemotron_h` checkpoint and the V25 all-layer final-position capture seam:

```text
python3.13 tools/astral-research-progress-app/live_bridge.py --port 4174 --interval 1.5
```

Then open
[http://127.0.0.1:4173/tools/astral-research-progress-app/?variant=telemetry&source=live](http://127.0.0.1:4173/tools/astral-research-progress-app/?variant=telemetry&source=live).
The bridge is local-only and serves the latest native forward pass over
`127.0.0.1:4174/sample`. It does not access the network, train, or write
research artifacts.

The bridge remains an implementation surface for the V25 local observatory,
not the latest overall Astral status. The canonical status slice is
`astral-status-reconciliation-v2`: V38 is the latest executed instrument-
feasibility result, while V25 remains the latest privileged-telemetry result.

Views:

- `?variant=telemetry` — live per-layer residual field, 36-tick layer-by-time salience field, a 32-layer nodal graph with pulsing representative channels, stage history, node focus, ranked channel focus, stream chart, events, and adapter status
- `?variant=sleep` — operational sleep-stage proxy map and unresolved projection hypothesis panel
- `?variant=self-model` — actor/observer diagnostics, causal-channel separation design, and retrospection proxy

## Graph interaction

The Telemetry view exposes a derived salience proxy that can be switched between
the transparent components `intervention delta`, `residual energy`, and
`attention entropy`. The default ordering is `delta * .56 + energy * .28 +
entropy * .16`. Hovering the layer-by-time field reveals the tick, layer, and
component values; clicking a cell or ranked row focuses that layer across the
instrument. The field is an inspection aid, not a semantic salience detector.

The nodal graph renders every layer column and six representative channels per
layer, with weighted same-channel and diagonal adjacency links. Node opacity and
pulse timing are driven by the current layer telemetry. It is a complete view of
the layer-depth topology represented by this prototype, not a claim to show
every neuron or every runtime edge; the current adapter contract does not carry
neuron-level topology.

In live local model mode the current cached actor exposes 42 layers. Residual
energy, residual-distribution entropy, activation sparsity, temporal residual
delta, and six residual-vector segment summaries are captured. Intervention
effects, self-model coherence, actor-observer divergence, retrospection, and
counterfactual consistency are not captured by this forward-only bridge and are
displayed as unavailable.

## Adapter boundary

The page exposes a deliberately small local hook:

```js
window.pushAstralTelemetry({
  timestamp: new Date().toISOString(),
  model_id: "local-model-id",
  run_id: "run-id",
  layers: [{ layer: 1, energy: 0.2, entropy: 0.4, sparsity: 0.7, delta: 0.1 }],
  activeLayer: 1,
  phase: { id: "awake" },
  metrics: {
    residualEnergy: 0.2,
    attentionEntropy: 0.4,
    activationSparsity: 0.7,
    interventionDelta: 0.1,
    selfModelCoherence: 0.4,
    actorObserverDivergence: 0.2,
    retrospectionProxy: 0.3,
    counterfactualConsistency: 0.7
  },
  events: ["adapter sample received"]
});
```

An adapter must provide custody, timestamp, model identity, layer shape, and capture semantics before its samples can be treated as anything beyond local visualization. The current repository does not supply an authorized live feed for these sleep, projection, or self-model labels.

Journal entries are stored in browser `localStorage` and can be exported as Markdown. They do not mutate research documents, the Evidence Ledger, or Git state.
