# V41 Qualification Record — Directional-Block Qwen3.6 Instrument

State slice: `astral-stage0c-qwen36-directional-block-target-v41`.

Status: `InstrumentFeasibility / ScientificExecutionSealed`.

V41 qualification was executed against the already-cached
`Qwen3.6-35B-A3B-MLX-4bit` checkpoint under a fresh V41 protocol identity and
external output root. The instrument gate passed. No V40 scientific artifact,
corpus, panel, concept, prediction, effect, review receipt, or result was
consumed.

## Custody and runtime

Qualification output root:

`/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v41-qualification-r3-2026-08-27`

The re-custodied model manifest digest is
`a95dc0f89c98c82331865ef0f51fc52ee832e41d6a97bd9b76351d37cec1e9e4`.
The V41 directional-block feature-map digest is
`f1363030e8068225e38972945f8ba9f60346dbbbfdf23326bed090ce1506ac4c`.
The locked runtime was Python `3.14.5`, MLX `0.31.2`, and MLX-LM `0.31.3`.
Installed Qwen source digests were recomputed and retained in the qualification
receipt.

## Qualification gates

| gate | result |
|---|---:|
| native/wrapper maximum absolute logit delta | `0.0` |
| deterministic repeat maximum absolute logit delta | `0.0` |
| zero replacement, layers 12/19/26 | `0.0 / 0.0 / 0.0` |
| nonzero reach, layers 12/19/26 | `1.2890625 / 1.28125 / 0.875` |
| observed layer count | `40` |
| observed hidden width | `2048` |
| feature-map binding | passed |
| aggregate-only/no-training/no-network gates | passed |

The independent validator returned `valid: true`, classification
`InstrumentFeasibility`, with no errors. Qualification result digest:
`562f991c0e24701fa8c86c03e2e95cfaa43639a1a002538b5554f667a8e61198`.

## Boundary

The maximum defensible claim is
`LocalDevelopmentV41InstrumentFeasibilityOnly`. This result establishes only
that the locally cached Qwen3.6 layer-capture and replacement seam passed the
declared deterministic qualification checks under the V41 custody receipt. It
does not establish target predictability, causal target validity, introspection,
self-modeling, Stage 0C, Stage 1, benchmark evidence, or production readiness.

Assessment remains closed. No family panel, fit/tune effects,
prediction lock, independent review packet, or assessment effects were
created. The fresh 18-document external corpus has now passed its independent
custody validator; the next V41 gate is the independently validated
144-family panel. A missing or invalid panel stops V41.
