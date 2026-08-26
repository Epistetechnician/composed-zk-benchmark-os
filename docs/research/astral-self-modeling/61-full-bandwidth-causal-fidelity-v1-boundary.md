# Full-Bandwidth Causal-Fidelity Comparison V1

State slice: `astral-full-bandwidth-causal-fidelity-v1-boundary`.

Status: `DocsOnly / ExecutionNotAuthorized`.

This document freezes a future comparison between a standard autoregressive
transformer and a full-bandwidth transformer with latent feedback. It is a
protocol boundary, not an execution record. No model is loaded, trained,
modified, or evaluated by this document.

## Motivation

The [Full-bandwidth transformer](https://arxiv.org/abs/2608.08888) returns a
previous top-layer state to the next decoding input alongside the next token
embedding. The paper reports improved task performance and substantially higher
linear-probe recovery of synthetic state variables in shallow residuals. It
also states the critical limitation for Astral: decodability demonstrates
information presence, not that the model uses that information to produce its
output.

Astral therefore treats latent feedback as an architectural factor in the
external-versus-internal comparison. The comparison must distinguish four
questions:

1. Is a target state externally decodable?
2. Can the actor report that state?
3. Does the state predict held-out intervention effects?
4. Does using those predictions improve behavior without degrading calibration
   or safety?

An improvement at an earlier question does not establish an improvement at a
later question.

## Primary question

Holding task, parameter budget, data mixture, tokenizer, optimizer budget,
evaluation prompts, and intervention operators fixed as far as feasible, does
latent feedback change the gap between:

- an external privileged-telemetry observer;
- the actor's own report;
- matched text-only and activation-only observers; and
- prediction of directly measured held-out intervention effects?

The primary endpoint is held-out intervention-effect prediction. Task accuracy,
reasoning length, probe accuracy, report accuracy, and correction gain are
secondary endpoints and must not replace it.

## Comparison matrix

The future run must preserve the following orthogonal factors:

| Factor | Required conditions |
|---|---|
| Actor | Standard and full-bandwidth actors with a digest-bound model/training manifest |
| Decode | Standard, soft latent-feedback, and fused-prefill modes where supported |
| Observer input | Text-only, activation-only, privileged telemetry, shuffled telemetry, and constant baselines |
| Report | Fixed actor report wrapper and fixed output mapping across actor conditions |
| Causal target | Directly measured intervention-effect vector, not attribution labels alone |
| Evaluation | Fresh fit, tune, and sealed assessment concepts/prompts |
| Downstream use | Locked correction policy, matched reflection baseline, calibration, and safety checks |

The standard and full-bandwidth actors must not differ in a way that makes
architecture inseparable from parameter count, training tokens, tokenizer,
data mixture, or evaluation budget. If exact matching is impossible, the
unmatched dimensions must be recorded as limitations and no architecture-only
causal claim may be made.

## Preregistered predictions

These are hypotheses, not results:

- `H1 Accessibility`: latent feedback increases shallow-layer decodability of
  task-relevant state relative to standard prefilling.
- `H2 Report gap`: latent feedback reduces the external-probe minus actor-report
  gap on the same locked trials.
- `H3 Causal fidelity`: any architecture-related improvement in external
  telemetry predicts held-out intervention effects better than matched controls.
- `H4 Instrumental value`: a correction policy using locked telemetry predictions
  improves held-out behavior over matched text reflection without calibration or
  safety regression.

`H1` can pass while `H2`, `H3`, or `H4` fails. That outcome is an accessibility
result, not self-modeling evidence.

## Required gates

Execution, if separately authorized, must stop at the first failed gate:

1. **Custody gate:** actor, runtime, source, data, and configuration digests are
   captured before model execution.
2. **Parity gate:** standard and feedback paths pass deterministic repeat,
   zero-strength, tokenizer, and prompt-identity checks.
3. **Behavioral-effect gate:** every selected intervention cell changes the
   measured output under the frozen effect rule; behaviorally silent cells are
   rejected.
4. **Probe-control gate:** shuffled labels, shuffled telemetry, constant, and
   capacity-matched observers remain within preregistered floors.
5. **Prediction-lock gate:** all assessment predictions and correction decisions
   are sealed before assessment effects are generated.
6. **Causal-fidelity gate:** privileged telemetry must beat the mandatory
   activation-only, text-only, shuffled, and constant baselines on the locked
   held-out intervention-effect endpoint.
7. **Correction gate:** any behavioral improvement must survive a matched
   reflection control and must not materially worsen calibration or safety.
8. **Independent-readback gate:** an independent validator must recompute the
   manifest, configuration lock, prediction lock, metrics, and claim class.

Probe accuracy alone cannot pass the causal-fidelity gate.

## Freshness and artifact rules

The future run must use a new protocol identity, new concepts, new seeds, and a
new assessment split. V22-V25 concepts, configurations, predictions, sealed
effects, and result bundles are closed and must not be reused. V27-V29 final
embedding and opaque-channel outputs may provide only documented feasibility
context; they are not per-layer telemetry or causal ground truth.

Raw prompts, embeddings, logits, residuals, model outputs, credentials, and
runtime logs remain outside the repository in an operator-selected transient
artifact root. The repository may retain only source hashes, configuration
digests, validator results, aggregate metrics, and an explicit non-secret
manifest sufficient for independent readback.

## Claim ceiling

This boundary creates no scientific result and no claim escalation. A future
positive execution could support only a setup-scoped local statement such as:

> Under the frozen actor pair, task, intervention operator, and observer
> protocol, latent feedback changed the measured relationship between residual
> telemetry, actor report, and held-out intervention-effect prediction.

It would not establish introspection, consciousness, semantic self-knowledge,
faithful explanation, general causal understanding, cross-model transfer,
production monitoring validity, benchmark evidence, or Stage 0C/Stage 1
authorization.

## Explicitly not authorized

This docs-only boundary does not authorize:

- model downloads, network access, or provider calls;
- pretraining, fine-tuning, LoRA, or architecture modification;
- loading a cached checkpoint for this protocol;
- reuse of V22-V29 artifacts or assessment outcomes;
- nonlinear, adaptive, or multi-layer assessment tuning;
- observer training before a separately reviewed target-validity gate;
- accepted Evidence Ledger mutation, benchmark claims, or SOTA claims;
- introspection, consciousness, agency, or global self-modeling claims.

## Transition requirement

Execution requires a separate authorization record naming the execution state
slice, eligible actor pair, fresh data identity, exact runtime seam, artifact
root policy, resource bound, validator, and claim ceiling. Until that record is
present, the status remains `DocsOnly / ExecutionNotAuthorized`.
