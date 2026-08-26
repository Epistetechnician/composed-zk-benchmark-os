# Qwen3.6 Layer-Instrument Feasibility V38

State slice: `astral-qwen36-layer-instrument-feasibility-v38`.

Status: `Executed / InstrumentFeasibilityOnly / ScientificAssessmentClosed`.

## Purpose

V33 stopped because no fresh non-reserved actor had a validated per-layer
intervention surface. A new local `Qwen3.6-35B-A3B-MLX-4bit` checkpoint was
subsequently discovered. V38 tests only whether the installed MLX path can
capture layer outputs and apply a bounded synthetic replacement. It is not an
Astral assessment and does not consume V25 concepts, prompts, predictions,
effects, configurations, or artifacts.

## Frozen local inputs

- actor: `Qwen3.6-35B-A3B-MLX-4bit`;
- architecture: `Qwen3_5MoeForConditionalGeneration`;
- text path: 40 layers, hidden width 2048, 256 experts, top-8 routing;
- model size: approximately 19 GB;
- MLX: `0.31.2`;
- MLX-LM: `0.31.3`;
- prompt identity: SHA-256 only in the execution record;
- target layer: 19;
- replacement scale: `0.01` at the final token position;
- launcher: repository-owned `tools/astral-qwen36-layer-instrument-feasibility-v38/probe_v38.py`.

The complete model-file manifest and runtime source digests are emitted by the
runner. Raw weights, prompts, logits, hidden states, and traces remain outside
the repository and are not retained by this slice.

## Required checks

1. Baseline repeated on identical tokens has zero logit delta.
2. Zero replacement has zero logit delta.
3. Nonzero replacement changes logits.
4. Layer count and hidden width match the local model configuration.
5. Assessment remains closed and no scientific result is emitted.

## Claim ceiling

Maximum defensible claim:
`LocalDevelopmentInstrumentFeasibilityOnly`.

V38 establishes that this local MLX implementation exposes a usable
layer-wrapping seam for a bounded feasibility probe. It does not establish
telemetry validity, intervention-effect prediction, mechanistic explanation,
introspection, self-understanding, HSAI security, provider security, Stage 0C,
Stage 1, or any benchmark or production claim.

## Advancement condition

A future scientific protocol still requires a new identity, independent
custody packet, frozen fresh concepts and fit/tune/assessment splits,
prediction locking, directly measured held-out intervention effects, mandatory
text-only/activation-only/shuffled/constant controls, independent validation,
and separate authorization to open an assessment. V38 does not authorize that
transition.
