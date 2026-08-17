# Opaque Causal-Channel Separation V28

State slice: `astral-opaque-causal-channel-separation-v28`.

Status: `Executed / OpaqueCausalChannelOrderingSignalOnly`.

## Question

After V27 established only a local public-ABI final-embedding intervention
seam, does a richer derived final-embedding feature panel predict directly
measured held-out intervention effects better than a fixed low-dimensional
opaque projection and a shuffled-channel control?

This is a new local protocol. It is not V26 per-layer telemetry, V25
privileged-telemetry evidence, provider-trace recovery, or an Astral Stage 0C
or Stage 1 execution.

## Frozen design

- actor: the locally cached Qwen3.5 9B Q4_K_M GGUF used only after the V27
  public-ABI feasibility result;
- fresh prompts: 16 deterministic choice prompts, disjoint from V27's prompt;
- intervention: one fixed control vector, coordinate 0, amplitude `0.5`, layer
  range `1..1`, distinct from V27's amplitude `1.0` execution;
- target: direct clean-versus-intervention `A-B` logit-margin effect;
- splits: 8 fit, 4 tune, 4 assessment;
- rich channel: 16 deterministic signed projections of the final embedding
  delta;
- opaque channel: the first 4 projections, quantized to a fixed `1/32` grid;
- estimator: fixed ridge `1e-3`, fit only on the fit split, prediction locked
  before assessment scoring;
- shuffled control: reversed rich-panel coordinates in the fit split;
- retained output: aggregate metrics only.

The feature panels are local synthetic derived channels. They are not decoded
provider traces and do not establish cryptographic provenance, plaintext
faithfulness, or recovered computation.

## Gates

The positive utility gate requires both rich and opaque relative assessment MSE
to beat the assessment mean baseline (`relative MSE < 1`) and both channels to
beat the shuffled control. A weaker channel-ordering result is recorded
separately and cannot be called held-out causal prediction.

## Ceiling

The maximum positive claim would have been
`LocalDevelopmentOpaqueCausalChannelSeparation`. It would still have been a
single-checkpoint local behavioral effect result, not evidence for mechanistic
explanation, faithful reasoning recovery, introspection, generalization,
security, privacy, production readiness, benchmark status, Stage 0C, Stage 1,
or an accepted Evidence Ledger record.

No raw prompts, embeddings, logits, control vectors, model outputs, credentials,
PII, provider artifacts, or opaque signatures are retained by this protocol.
