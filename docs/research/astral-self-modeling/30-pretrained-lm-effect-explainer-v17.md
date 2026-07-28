# Pretrained-LM Effect Explainer V17

State slice: `astral-lm-explainer-feasibility-and-prospective-pilot-v17`.

Status: `PreregisteredFeasibilityOnly`. Confirmation: `NotAuthorized`.
Stage 1: `BlockedByStage0C`.

## Question and scientific boundary

V17 asks whether a small nonlinear explainer can predict prospectively sealed
intervention effects in a frozen pretrained causal language model from its
hidden states better than activation summaries, input/output features, shuffled
hidden states, and a constant. This is a numeric intervention-prediction
analogue of the own-model-access comparison in Li et al.,
[*Emergent Introspective Awareness in Large Language Models*](https://arxiv.org/abs/2511.08579).
It is not a replication: the paper trains language-model explainers at much
larger scale, while V17 trains a small external numeric predictor against a
local quantized target.

The official [reference implementation](https://github.com/TransluceAI/introspective-interp)
targets substantially larger models and accelerator budgets. V17 therefore
uses only already-cached weights and stops rather than downloading or silently
changing the design.

## Preflight and branch decision

An eligible model must have an identifiable local checkpoint and tokenizer,
recorded configuration and file hashes, single-token ` is` and ` are`
completions, deterministic finite logits, exact residual replacement, no-op
parity, and a complete forward below 75% of physical memory. Two-model
reciprocal comparison additionally requires compatible causal decoders and a
parameter-count ratio no greater than `2:1`.

The local preflight found:

- `mlx-community/Qwen2.5-0.5B-Instruct-4bit`, 24 blocks, width 896;
- `mlx-community/Llama-3.2-1B-Instruct-4bit`, 16 blocks, width 2048.

The models exceed the frozen `2:1` width/parameter comparability limit. V17 is
therefore locked to Qwen as `SingleModelFeasibilityOnly`. It cannot support an
own-model-versus-other-model claim. The result is specific to the cached 4-bit
conversion and the locally installed MLX runtime.

## Frozen task and split

Create and hash 40 lexical families before model execution. Each family crosses
subject number, distractor number, and two frozen relation surface forms,
producing eight examples.

- fit families: `lm-agreement-v17-000..023`;
- tune families: `lm-agreement-v17-024..031`;
- sealed assessment families: `lm-agreement-v17-032..039`.

No noun pair or token sequence may cross splits. The primary clean margin is
the correct completion logit minus the incorrect completion logit. Fit and tune
accuracy must each be at least 70%; assessment accuracy must be at least 65%.
Both answer classes must occur in every split.

## Intervention target

For 24 blocks, the frozen post-block residual sites are blocks `5`, `11`, and
`17`. At the final prompt position V17 applies:

1. fit-mean replacement at each site;
2. matched subject-number-flip patching at each site, holding family,
   distractor number, template, and surface form fixed.

The six signed targets are intervened correct-token margins minus clean
correct-token margin. Clean controlled-forward parity, no-op replacement, donor
identity, and restoration are hard gates.

## Explainers and controls

Every learned method receives a 16-value shared task/input-output prefix and a
64-value method field. Target telemetry concatenates the three residuals and
uses deterministic fit-only PCA with sign fixing. Activation summaries use
norm, mean, standard deviation, and maximum absolute value per site with zero
padding. Text/input-output uses zeros. Shuffled telemetry is permuted within fit
family and subject class. A fit constant and multivariate ridge are retained.

Nonlinear methods use the same `80 -> 64 -> 32 -> 6` GELU MLP, AdamW
(`lr=0.001`, weight decay `0.0001`), at most 500 updates, tune selection every
25 updates, and seeds `1701`, `1703`, `1709`. PCA and standardization are fit
only. Tune labels select checkpoints only.

## Prospective ordering

1. Freeze and hash families, model identity, sites, operators, and source.
2. Pass task, parity, no-op, restoration, memory, and deterministic-repeat gates.
3. Materialize fit/tune telemetry and effects.
4. Freeze transforms, checkpoints, fit means, and controls.
5. Materialize assessment clean logits and telemetry without assessment effects.
6. Write and hash every assessment prediction and `prediction-lock.json`.
7. Independently prove that no assessment-effect artifact exists.
8. Only then execute assessment interventions, score, classify, and validate.

Generating an assessment effect before the lock invalidates the run.

## Feasibility classification

The single-model branch yields `SingleModelTelemetryFeasibilityObserved` only
when all integrity gates pass and target telemetry:

- has at least 10% lower MSE than activation summaries for both operators;
- has lower MSE than text/input-output, shuffled telemetry, and the constant;
- is favorable at all three sites;
- has positive correlation and calibration slope in `[0.5, 1.5]`;
- has a positive 10,000-draw family-bootstrap lower bound versus activation for
  both operators.

Otherwise it yields `SingleModelFeasibilityNoCandidate`. Either classification
leaves Stage 0C, confirmation, and Stage 1 blocked. Any preflight failure uses a
specific `NotRun*` classification and stops.

## Ceiling

The maximum claim is
`LocalDevelopmentPretrainedModelEffectExplainerPilot`. A positive result would
show only task-scoped prospective predictive value for hidden telemetry in one
local quantized model against named controls. It would not establish
introspection, self-explanation faithfulness, semantic self-knowledge,
consciousness, causal-graph recovery, correction value, safety, benchmark
evidence, production readiness, Stage 0C confirmation, or Stage 1 authorization.
