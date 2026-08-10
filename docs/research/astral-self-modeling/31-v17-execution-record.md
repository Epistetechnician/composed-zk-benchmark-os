# V17 Execution Record

State slice: `astral-lm-explainer-feasibility-and-prospective-pilot-v17`.

Execution: `SingleModelFeasibilityNoCandidate`. Confirmation:
`NotAuthorized`. Stage 1: `BlockedByStage0C`.

## Branch and integrity

The frozen reciprocal branch was ineligible because the two cached local model
conversions exceeded the preregistered `2:1` comparability cap. The executed
branch used only the cached 4-bit Qwen2.5-0.5B-Instruct conversion and therefore
supports no own-model-versus-other-model comparison.

The final primary bundle passed its independent structural validator:

- 320 frozen prompts across 40 lexical families;
- fit/tune/assessment clean accuracy: `100% / 100% / 96.875%`;
- controlled-forward versus native maximum absolute logit error: `0`;
- deterministic-repeat maximum absolute logit error: `0`;
- no-op residual replacement maximum absolute logit error: `0`;
- 64 sealed assessment rows and six signed effects per row;
- assessment predictions written and hashed before assessment effects.

Prediction-lock SHA-256:
`6ace47fc2f507320099881d0bb2cafdcf253be7b2f2f48a799c3fa97c3bacc0a`.

Manifest SHA-256:
`fc6cb18433549a17357005a2cbf97fe84d6085382bd5da3e1bf868a524435f23`.

The validated repository-external bundle is
`/tmp/astral-lm-v17-20260726-run3`.

## Primary result

| Method | Fit-mean replacement MSE | Subject-flip patch MSE |
|---|---:|---:|
| Nonlinear telemetry | 0.453493 | 0.225315 |
| Activation summaries | 0.141903 | 0.143601 |
| Text/input-output | 0.169794 | 0.111968 |
| Shuffled telemetry | 0.413779 | 0.230726 |
| Fit constant | 2.048189 | 0.194152 |
| Linear telemetry | 0.327285 | 0.362346 |

Nonlinear telemetry was `219.58%` worse than activation summaries for
fit-mean replacement and `56.90%` worse for subject-flip patching. It also
failed to beat text/input-output for either operator. The single-model
feasibility gate therefore fails without needing a favorable interpretation of
secondary diagnostics.

Read-only diagnostics over the unchanged primary predictions and effects found
positive raw correlations (`0.894` mean replacement, `0.612` patch) but
negative activation-comparison family-bootstrap lower bounds and unfavorable
direction at all three sites. Correlation did not translate into incremental
predictive value beyond simpler controls.

## Retained failures and rerun disposition

Two pre-effect implementation failures are retained:

1. the first attempt used an unsupported MLX indexed-set operation and stopped
   before fit/tune or assessment effects;
2. the second attempt exposed a float32 capture/float16 replacement mismatch;
   the no-op gate stopped before fit/tune or assessment effects.

The capture boundary was corrected to preserve float16 residuals exactly before
the primary run. A later diagnostic-enhanced rerun reproduced byte-identical
assessment predictions and effect arrays, but it occurred after the primary
assessment effects had been opened. It is protocol-invalid for prospective
evidence and is excluded. The first complete run remains the sole primary V17
result.

## Disposition

V17 establishes that the local intervention instrument works exactly at the
tested boundaries, but it does not provide a candidate explainer. Do not tune
the exposed families, sites, PCA width, MLP width, thresholds, or seeds.
Further work requires a new preregistration and a materially different
scientific system, such as a genuinely trained language-model explainer with
new sealed data and adequate compute.

Claim ceiling:
`LocalDevelopmentPretrainedModelEffectExplainerPilot`. This is not
introspection, self-modeling, semantic self-knowledge, Stage 0C confirmation,
Stage 1 authorization, benchmark evidence, or production readiness.
