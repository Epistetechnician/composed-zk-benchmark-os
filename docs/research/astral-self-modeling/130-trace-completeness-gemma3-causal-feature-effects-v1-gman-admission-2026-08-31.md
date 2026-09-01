# Gemma 3 causal feature-effects V1 GiveMeANode admission record

State slice: `astral-trace-completeness-gemma3-causal-feature-effects-v1`.

The exact model, model-matched feature asset, and V1 source/test payload were
staged through the authenticated GiveMeANode CLI (`gman 0.7.18`) into the
dedicated bucket
`astral-trace-completeness-gemma3-causal-feature-effects-v1`. The bucket is
transfer staging only; it is not a raw-trace custody root.

The provider allocation binding is
`/Users/shaanp/Documents/astral-custody/trace-completeness-gemma3-causal-feature-effects-v1/node/allocation-receipt.json`.
The exact node is H100 node
`7289c582-2e04-4d6a-ac3c-6ca8d4139356`, mission
`astral-trace-completeness-gemma3-causal-feature-effects-v1`, CUDA image
`cuda-12.9`, driver `595.71.05`, clock lock enabled, 16 CPU units, 100 GiB
scratch, and provider rate USD 0.0666/minute. The node ran only for bounded
bootstrap activity, then auto-stopped with its disk intact. No model-bearing
V1 execution occurred.

At final provider audit the node remained `stopped (disk intact)`. GiveMeANode
reported August workspace spend of USD `41.812492` against the USD `333.00`
workspace hard cap. This account-level figure is not treated as an exact V1
campaign-cost attribution.

The operator-bound hard ceiling is USD 50.00. This is a cost bound, not an
independent scientific review or assessment authorization. The current
packet binds:

- packet SHA-256: `497071dcc14bdd9601747ccee060f2c9b0e7c1ac0c86a871b91b47f9a0911d10`;
- contract SHA-256: `877fa58ad5cc6236357ee5bcc54a32cc86beaac857b6d3bc694e354c8154c1cf`;
- source manifest SHA-256: `ca94ef3d48a2335ab6457c63d674f9479efe4c6ca6ea30b8a49713dc7666a70d`;
- node receipt SHA-256: `0857292969957ad4a504769ac7086b2a2eb93b0db3f4eb2990b6378f8ad30dbe`;
- static packet file SHA-256: `14447c853a7d3f0cd9daeee689d75c43dba5594c2bdccea4480d18d81a67d9f2`;
- preflight file SHA-256: `e85340d16f7857efa8186e19b5979dd0ff034cae7ecdc5e707136f621980d099`.

The exact preflight output is
`/Users/shaanp/Documents/astral-custody/trace-completeness-gemma3-causal-feature-effects-v1/aggregate/preflight-v1.json`.
It is `REJECT` with `V1-NODE-002` and `V1-REVIEW-001`: the node and cost are
bound, but no genuinely independent packet-bound signed Ed25519 `ACCEPT` has
been supplied. The runner therefore reports
`execution_authorized: false` and `assessment_opened: false`.

The repository fast gate passed and the V1 suite passed (`18 passed`). The
heavy `pnpm run lint` gate reached `1215 passed` before failing on an
unrelated OakLab V4 validator defect: `_finite_number()` was called without
its required `label` argument. The terminally closed OakLab slice was not
modified to mask that failure.

The external custody root remains owner-only `0700`; its raw directory is
empty. No prompts, token sequences, activations, logits, cache/state payloads,
per-trial outcomes, causal effects, or scientific result bytes were created.
The qualification ceiling remains
`LocalDevelopmentGemma3CausalFeatureEffectsQualificationV1`.

The next admissible transition is receipt-only: an independent reviewer must
sign this exact packet digest and place the packet-bound receipt below the V1
review root. Only after the receipt verifies may the parked node be woken,
imports completed, and offline qualification attempted. The operator cannot
manufacture that receipt.
