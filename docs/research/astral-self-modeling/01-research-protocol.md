# Research Protocol

## Questions

Primary question:

> Can a preregistered estimator predict the vector of directly measured
> intervention effects on held-out actor seeds and prompt families better than
> activation-only, text-only, constant, shuffled, and capacity-matched controls?

The original observer question is now conditional: if this measurement gate
passes, does privileged telemetry add predictive value over matched
non-privileged observers, and can the prediction improve behavior without
degrading calibration or safety?

Secondary questions:

1. Which telemetry and target representations contribute to causal fidelity?
2. Do gains survive task distribution shift and actor checkpoint changes?
3. Is correction gain mediated by causal accuracy rather than verbal
   plausibility?
4. Does actor-observer optimization create tracer gaming or auditor
   disagreement?

## Constructs and Operational Definitions

- Actor: the model whose task behavior and selected internal states are observed.
- Observer: the model or head trained to predict a measured mechanism and
  intervention outcomes.
- External tracer: a frozen measurement pipeline that produces
  `G_trace`; it is an auditor, not an oracle.
- Privileged telemetry: activations or derived internal measurements unavailable
  to a text-only baseline.
- Causal fidelity: accuracy and calibration when predicting held-out
  intervention effects.
- Instrumental improvement: the paired change in held-out task reward after a
  correction uses the observer output.
- Introspection gap: a pre-registered difference between two explicitly named
  systems on the same metric. It must not mix recall, model scale, data access,
  or intervention conditions.

## Hypotheses

| ID | Hypothesis | Null or refuter |
|---|---|---|
| H0A | A locked intervention-effect estimator predicts held-out continuous effect vectors better than activation-only and other mandatory controls | It fails the practical margin on any preregistered actor seed, intervention operator, or uncertainty gate |
| H0B | A circuit selected from those predictions is necessary, sufficient, and faithful under independent intervention checks | Removal, retention/restoration, resampling, or alternate-operator checks contradict the proposed circuit |
| H1 | A telemetry-enabled observer predicts held-out intervention effects better than actor self-report and matched text-only observers | No statistically or practically meaningful paired improvement under the preregistered metric |
| H2 | Mechanistic prediction quality predicts correction gain after controlling for actor scale, observer scale, and task difficulty | The association vanishes under controls or corrections improve equally with shuffled mechanism reports |
| H3 | Intervention-effect supervision produces greater held-out causal fidelity than feature-label supervision alone | Feature-label supervision matches or exceeds it under equal compute and data |
| H4 | Unconstrained actor-observer optimization increases trace predictability without equivalent independently audited causal fidelity | Independent audit fidelity rises proportionally and no gaming indicators increase |

## Candidate Objective

\[
L_{\mathrm{total}} =
L_{\mathrm{task}}
+ \lambda_m L_{\mathrm{mechanism}}
+ \lambda_i L_{\mathrm{improvement}}
\]

\[
L_{\mathrm{mechanism}} =
\alpha L_{\mathrm{features}}
+ \beta L_{\mathrm{edges}}
+ \gamma L_{\mathrm{counterfactual}}
+ \delta L_{\mathrm{calibration}}
\]

This is a design family, not yet a validated loss. Each component must be
ablated. The primary causal endpoint is `L_counterfactual`; feature and edge
targets are auxiliary because their identities can depend on the tracer and
dictionary.

## Evaluation Contract

Report separately:

1. original and revised task performance;
2. intervention-effect prediction accuracy or divergence;
3. calibration, including reliability plots and Brier score where applicable;
4. feature and edge recovery with alignment-aware matching;
5. observer benefit over every matched baseline;
6. distribution-shift degradation;
7. independent-auditor disagreement;
8. safety and policy regression results;
9. compute, sample count, exclusions, and confidence intervals.

No weighted aggregate may conceal failure on causal fidelity, calibration, or
safety. Missing measurements remain missing.

The principal experimental outcome for self-correction is:

\[
\Delta R = R(y_{\mathrm{retry}})-R(y_{\mathrm{initial}})
\]

The original conversation proposed two example gates: at least `0.10`
mechanism-access improvement over a text-only projected observer, and at least
`0.10` self-correction improvement over text self-reflection. It also proposed
`65%` intervention-ranking accuracy. These remain provisional design inputs.
They must be justified and preregistered before data collection; they are not
current acceptance thresholds.

## Acceptance Criteria for a First Positive Result

A first positive result requires all of the following:

- frozen actor and frozen external tracer;
- a passed Stage 0C target-validity gate before observer training;
- directly measured intervention effects as canonical supervision and
  evaluation, with attribution used only to nominate candidates;
- preregistered held-out prompts and held-out interventions;
- telemetry observer beats actor self-report, same-scale text-only observer, and
  shuffled-telemetry control on intervention prediction;
- correction gain exceeds a matched reflection baseline;
- shuffled or incorrect mechanism reports do not reproduce the gain;
- calibration does not materially degrade;
- an independent intervention method confirms the direction of the main effect;
- all negative and null results are retained.

Passing these criteria supports only a task- and setup-scoped result.

## Initial Study Frame

This frame is deferred until Stage 0C passes. The conversation nominates a
frozen `qwen3:4b` actor and deterministic SRE
incident triage as the narrow first study, with `gpt-oss-20b` and `qwen3-14b`
reserved for later replication. Model availability, exact checkpoints, licenses,
and compatibility with the tracer are unverified.

Proposed task scale:

- 200-500 training incidents;
- 100 validation incidents;
- 100-200 hidden held-out incidents;
- variation across logs, timestamps, symptoms, topology, distractors, and root
  causes with deterministic ground truth.

Hold actor, task, retry count, token and tool budgets, sampling settings, and
intervention count fixed across conditions.
