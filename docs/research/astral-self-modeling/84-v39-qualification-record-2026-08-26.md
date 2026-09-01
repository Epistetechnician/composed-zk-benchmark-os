# V39 Qualification Record — Qwen3.6 Layer-Effect Instrument

State slice: `astral-stage0c-qwen36-layer-effect-v39`.

Status: `InstrumentQualificationPassed / ScientificAssessmentSealed`.

## Authorized scope

This run executed only the fresh V38-derived instrument qualification from
[the V39 protocol](83-stage0c-qwen36-layer-effect-protocol-v39.md). It did not
reopen V28–V29, consume V25 artifacts, use V61 evidence, or advance the V82
Neural Chameleon branch. No scientific corpus, fit/tune/assessment split,
prediction lock, assessment effect, observer, or Stage 0C result was created.

## Custody

- model: `Qwen3.6-35B-A3B-MLX-4bit`;
- model root: `/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit`;
- model files bound: `15`;
- model manifest SHA-256:
  `367ad0c6838db3c831214f2d44da8907f669427fe5376ba9e9f2d2518bc6a90e`;
- architecture: `Qwen3_5MoeForConditionalGeneration`;
- runtime: Python `3.14.5`, `mlx==0.31.2`, `mlx-lm==0.31.3`;
- `qwen3_5.py` source SHA-256:
  `f0daa30bba5cb521c8bdfa7093101a544c6a37bbba09bca582288219cb04ae3a`;
- `qwen3_5_moe.py` source SHA-256:
  `ef9e8e1f6a5c097b29587c8330e8eb9c9cbdc52fbb4597fbc2362606c1996619`;
- V39 protocol source SHA-256:
  `2a0c49ce02f77cbe846fa04ce5f1941fa8263532b28a3802e4a5183ae6519bf3`;
- V39 runner source SHA-256:
  `7cddeedad3ef8918bcd513ba4e5184bcfccc288ef5823090d5503cae4d16a98b`.

The qualification output root was external to the repository:
`/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v39-qualification-2026-08-26-r2`.
It retained only the aggregate result and validator receipt. The qualification
prompt registry was represented by digest
`b5edc2022119e277c2fd36cc61ea3ad113369449d629acde5de79c475baa5cde`; raw
prompt text and intermediate tensors were not retained.

## Gate results

| Gate | Observed result | Disposition |
|---|---:|---|
| native versus wrapped parity | max absolute logit delta `0.0` | pass; threshold `1e-4` |
| deterministic wrapped repeat | max absolute logit delta `0.0` | pass; threshold `1e-5` |
| zero/no-op replacement | max absolute logit delta `0.0` | pass; threshold `1e-5` |
| nonzero layer-19 replacement reaches logits | max absolute logit delta `0.421875` | pass; floor `>1e-6` |
| layer shape | 40 layers, hidden width 2048 | pass |
| replacement shape | same shape as capture | pass |
| assessment and training | assessment `false`, training `false` | pass; closed |
| network and raw retention | network `false`, raw intermediates `false` | pass |

Independent validation returned `valid: true`, with no errors. The validator
recomputed the external model manifest, output census, runtime versions and
source digests, result schema, aggregate gates, and claim-boundary flags. The
aggregate result SHA-256 was
`ba4a1c04292cc3bd365c8e4b191b39b5ac6171c01f69def0d465e26de01dfb42`.

## Narrow classification

Classification: `InstrumentFeasibility`.

Maximum defensible claim:
`LocalDevelopmentInstrumentFeasibilityOnly`.

The result shows only that this exact local runtime exposes a deterministic,
shape-correct layer-19 capture/replacement seam whose synthetic nonzero effect
reaches logits. It does not show held-out intervention-effect prediction,
causal target validity, mechanistic explanation, introspection, causal
self-modeling, Stage 0C, Stage 1, benchmark evidence, or production readiness.

The future assessment remains sealed. It can open only after the V39 protocol's
fresh external concept registry and document-disjoint splits are independently
reviewed, the activation-only/text-only/shuffled/constant/matched controls and
privacy retention are verified, all predictions are digest-locked before
assessment effects are measured, and separate assessment authorization is
recorded. Stage 1 remains blocked by Stage 0C. V82 remains stopped at missing
Gemma/oracle/monitor artifacts.
