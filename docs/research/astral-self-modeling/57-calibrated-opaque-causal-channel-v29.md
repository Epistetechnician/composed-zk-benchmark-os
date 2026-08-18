# Calibrated Opaque Causal-Channel Test V29

State slice: `astral-calibrated-opaque-causal-channel-v29`.

Status: `AuthorizedDesign / AssessmentSealed`.

V28 found a weak channel-ordering signal but failed held-out utility because
the fit was poorly conditioned. V29 changes only the estimator conditioning
and sample allocation. It does not reuse V28 prompts, control amplitude,
assessment rows, or result artifacts.

## Frozen question

Can a richer derived final-embedding channel or a fixed quantized opaque
projection predict directly measured held-out intervention effects better than
the assessment mean baseline and a shuffled-channel control?

## Frozen protocol

- actor: the same locally cached Qwen3.5 9B Q4_K_M GGUF, bound by digest;
- prompts: 32 fresh deterministic choice prompts;
- intervention: coordinate 0, amplitude `0.75`, layer range `1..1`;
- target: clean-versus-intervention `A-B` logit-margin effect;
- split: 16 fit, 8 tune, 8 assessment;
- rich channel: 4 deterministic signed projections of the final-embedding delta;
- opaque channel: the first 2 projections, quantized to a fixed `1/16` grid;
- ridge candidates: `0.001`, `0.01`, `0.1`, and `1.0`;
- selection: minimum tune MSE, fit only before tune selection; ties choose the
  smaller ridge; selected weights are locked before assessment scoring;
- control: reversed rich-panel coordinates in fit and tune;
- retention: aggregate metrics only; derived rows travel through a pipe.

The channels are synthetic local summaries, not provider artifacts. V29 cannot
establish faithful computation, mechanistic explanation, cryptographic
provenance, privacy safety, or introspection.

## Gates and ceiling

Positive utility requires both rich and opaque assessment relative MSE below
`1.0` and no worse than the shuffled control. A result below that bar is a
negative or diagnostic result. The maximum ceiling remains
`LocalDevelopmentCalibratedOpaqueCausalChannel` and cannot advance V25, V26,
Stage 0C, Stage 1, benchmark status, or the Evidence Ledger.
