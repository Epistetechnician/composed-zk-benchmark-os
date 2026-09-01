# V40 qualification, preassessment, and early-stop record

State slice: `astral-stage0c-qwen36-intervention-conditioned-target-v40`.

Status: `DevelopmentNoCandidate / AssessmentNotOpened`.

V40 was executed under its separately authorized state slice. The final fresh
external chain used:

- corpus: `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v40-corpus-r2-2026-08-26`;
- panel: `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v40-panel-r5-2026-08-26`;
- qualification: `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v40-qualification-r5-2026-08-26`;
- preassessment: `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v40-preassessment-r3-2026-08-26`;
- pending review packet: `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v40-independent-review-r2-2026-08-26`;
- final disposition: `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v40-final-r1-2026-08-27`.

## Custody and qualification

The corpus contains 18 fresh Project Gutenberg records and 144 families: six
documents and 48 families in each fit, tune, and assessment split. The final
selection digest is
`436fc1bf7e1e60cfaa53d57f33fd5c9b4fc75080a6f44cee1b588250c7ca8726`.
The panel uses exact 320-token ordinary/counterfactual prompts, fixed 256-wide
hash sketches, and cross-document exact-length norm-matched donors. Corpus and
panel validators passed.

The re-custodied Qwen3.6 qualification passed independently:

- native parity maximum absolute logit delta: `0.0`;
- deterministic repeat maximum absolute logit delta: `0.0`;
- zero replacement at layers 12, 19, and 26: `0.0` each;
- nonzero reach at layers 12, 19, and 26: `1.0546875`, `1.025390625`, and
  `0.59375` maximum absolute logit delta;
- observed shape: 40 layers by hidden width 2048;
- runtime: Python 3.14.5, MLX 0.31.2, mlx-lm 0.31.3.

## Locked preassessment result

Fit/tune direct intervention effects and matched-control effects were measured
before any assessment effects. The prediction lock retains estimator states and
assessment family order only; no per-family predictions, effects, prompts,
tokens, activations, logits, or traces were retained. Independent
preassessment validation passed.

The primary tune metric was:

```text
pair_conditioned_activation RMSE = 0.09667799272702594
constant RMSE                 = 0.10224463765312801
delta RMSE                    = -0.00556664492610207
required delta RMSE           <= -0.01
```

The fixed tune utility gate therefore failed. V40 stopped immediately under
its no-adaptive-retry rule. The assessment target and matched-control effects
were not measured, and the pending review packet was not accepted or used to
open assessment.

Final classification: `DevelopmentNoCandidate`.

Claim ceiling: `LocalDevelopmentV40DevelopmentNoCandidate`. This is a local
development disposition only. It establishes neither introspection, causal
self-modeling, Stage 0C, Stage 1, benchmark evidence, accepted Evidence Ledger
status, nor production readiness. V39, V25, V28-V29, V30-V37, V61, and V82
remain separate lanes.
