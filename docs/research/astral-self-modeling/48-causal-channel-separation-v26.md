# Causal-Channel Separation Protocol V26

State slice: `astral-causal-channel-separation-v26-protocol`.

Status: `DocsOnlyDesign / ExecutionNotAuthorized`.

This protocol is the docs-first successor candidate to the paper synthesis in
`docs/research/2608.09867-synthesis-v1.md`. It tests whether an opaque channel
can carry information about a directly measured causal effect. It does not
attempt to reproduce a proprietary provider, recover chain-of-thought, or
establish that decoded text is faithful computation.

## Primary question

On a frozen actor and sealed intervention corpus, does a report-plus-opaque-
artifact observer predict held-out intervention effects better than the
actor-report-only observer, while the gain survives shuffled-artifact controls?

The causal target is the directly measured change in a fixed output-logit
margin between a clean and an intervention condition. The target is generated
by paired forward passes; it is not a label inferred from a report, artifact,
token count, or attribution score.

## Hypotheses and falsifiers

| ID | Hypothesis | Falsifier |
| --- | --- | --- |
| H26-A | The report-plus-opaque-artifact observer has at least 10% lower held-out MSE than report-only. | The relative MSE reduction is below 10%, or its paired bootstrap lower bound is not positive. |
| H26-B | The artifact gain is not a pipeline artifact. | The shuffled-artifact control obtains a gain of at least 2%, or artifact provenance/lock validation fails. |
| H26-C | The artifact channel is not merely a report restatement. | The artifact-plus-report arm does not beat the report-only arm after equal-capacity fitting. |
| H26-D | The direct effect target is measurable under the locked instrument. | Parity, repeatability, zero-intervention, or behavioral-effect gates fail. |

H26-A is the sole primary success criterion. H26-B through H26-D are guard
conditions. A failed guard condition prevents a positive interpretation even if
the primary metric appears favorable.

## Channel definitions

The experiment compares fixed-capacity observers over separately sealed input
surfaces:

1. `report_only`: the actor's structured intervention report and fixed report
   confidence fields; no residual state or artifact tokens.
2. `artifact_only`: a synthetic opaque artifact surface and its permitted
   metadata; no report or residual state.
3. `report_plus_artifact`: the primary arm.
4. `telemetry_only`: the captured residual feature panel; this is a positive
   information-access comparator, not a ground-truth mechanism.
5. `report_plus_telemetry`: a privileged comparator.
6. `shuffled_artifact`: artifact records permuted across source trials within
   the sealed partition; provenance must make the permutation explicit.
7. `shuffled_telemetry`: telemetry records permuted across source trials within
   the sealed partition.
8. `constant`: fit-only mean-effect baseline.

All observers use the same deterministic estimator family, feature budget,
regularization-selection budget, fit rows, and stopping rule. No observer is a
trained language model. No observer receives raw reasoning text.

## Paper-informed report endpoint

The S005 literature crosswalk requires the actor report to remain a secondary
observable rather than a proxy for the causal target. If a future authorized
runner emits a report, it must preserve the following fixed scoring boundary:

- score the first structured detection/choice before any later narrative;
- keep activation and no-intervention prompts byte-identical;
- include an unrelated-intervention control so generic affirmation or anomaly
  detection cannot count as internal-state identification;
- reject report content that appears only after the actor has named or repeated
  the injected concept; and
- retain later phenomenological or mechanistic language as unverified metadata,
  never as a causal label or target feature.

These rules operationalize report quality and report-gap diagnostics only. They
do not change H26-A, the directly measured intervention-effect target, or the
requirement that the primary arm beat matched report-only and shuffled controls
on held-out effect prediction. A report endpoint may be reported as a secondary
metric even when it is inaccurate; it cannot convert a probe/report gap into an
introspection or self-modeling claim.

## Synthetic opaque-channel proxy

The artifact surface is deliberately synthetic. It is not provider evidence.
Before any target labels or assessment rows are opened, a fixed renderer is
sealed:

- source: one predeclared post-intervention residual snapshot at the
  observation boundary;
- transform: a public, fixed-seed, low-capacity projection followed by fixed
  scalar quantization;
- exposed surface: quantized token IDs, token count, schema version, and a
  non-authoritative source digest;
- excluded surface: raw residuals, prompts, decoded prose, secrets, PII,
  signatures, credentials, and provider artifacts;
- renderer seed: `26082601`;
- renderer: `opaque-channel-renderer-v1`.

The renderer is a controlled information-channel proxy. A positive result can
show only that this bounded opaque surface retains predictive information under
the tested construction. It cannot show that any provider envelope has the
same structure, cryptographic properties, or semantic fidelity.

The renderer must be deterministic, target-blind, and frozen before assessment
predictions are sealed. The source snapshot is used transiently by the runner;
repository artifacts retain only typed metadata, digests, aggregate metrics,
and validation receipts.

## Freshness and isolation

V26 has a new protocol identity and may not reuse V25 concepts, assessment
rows, wrappers, sites, strengths, configuration, predictions, or artifacts.
The runner must assert disjointness before data collection.

Reserved V26 design inputs are:

- intervention sites: `14/25/36`, disjoint from V22 `5/11/17`, V23 `3/7/11`,
  and V24/V25 `10/21/32`;
- intervention strengths: `0.75/1.5`, disjoint from the V22-V25 strength
  values;
- fit concepts: `acorn`, `bramble`, `cairn`, `drift`, `elm`, `fallow`,
  `grove`, `heath`, `islet`, `juniper`, `knoll`, `lichen`;
- tune concepts: `marsh`, `nimbus`, `orchard`, `quartz`, `rill`, `sable`;
- sealed assessment concepts: `thicket`, `upland`, `valley`, `willow`,
  `yarrow`, `zephyr`;
- protocol seeds: renderer `26082601`, run `26082602`, bootstrap `26082603`.

The concept names are reserved design inputs, not evidence that they are
disjoint. Execution must compare them against the complete V22-V25 registries
and stop before collection on any collision. A collision is resolved by a
documented pre-lock replacement, never by post-hoc filtering.

The primary arm requires a fresh eligible local actor identity selected before
fit results are exposed. If no such cached actor is available, execution stops
as `NoFreshActor` rather than silently reusing V25. A same-checkpoint feasibility
run is not a substitute for the primary arm.

## Target and trial construction

Each trial contains a fixed binary-choice prompt with two predeclared output
tokens. The target is:

```text
effect = (logit_A - logit_B)_intervened
       - (logit_A - logit_B)_clean
```

Clean and intervention passes use identical prompt bytes, tokenizer settings,
sampling settings, and output-position selection. The intervention direction,
site, strength, and operator are frozen before assessment. The behavioral-effect
gate requires a non-silent effect on fit data for the selected intervention
cell; a silent target stops the protocol.

Partitioning is by concept family and prompt template, not random row order:

- fit: 12 concepts;
- tune: 6 concepts;
- sealed assessment: 6 concepts.

Fit may select only the estimator regularization and one observation cell under
the frozen tie-break rule. Tune may qualify the selection but may not reseat it.
Assessment predictions are generated and hashed before assessment effects are
computed.

## Estimator and primary metric

The estimator is deterministic ridge regression with a fixed feature budget.
The same fit-only regularization grid and closed-form solver are used for every
channel. Feature dimensions are padded or projected to the same parameter
budget before fitting. No assessment residuals, effects, or report outcomes may
enter selection.

The primary metric is relative held-out MSE reduction on the sealed assessment:

```text
gain = (MSE_report_only - MSE_report_plus_artifact) / MSE_report_only
```

The paired uncertainty interval resamples complete concept families with
bootstrap seed `26082603`. H26-A requires `gain >= 0.10` and a positive 95%
lower bound. The artifact shuffle guard requires the corresponding shuffled
gain to remain below `0.02`.

Secondary reports are required for artifact-only, telemetry-only,
report-plus-telemetry, constant, and shuffled-telemetry arms. They do not
override the primary metric or raise the claim ceiling.

The actor's report accuracy, first-decision latency/order, and probe-minus-report
gap are secondary diagnostics. They must be computed from the locked report
fields and cannot be used to reseat the estimator, select the intervention cell,
open assessment effects, or qualify H26-A.

## Execution phases and stop rules

1. **Preflight:** verify actor inventory, source revision, protocol digest,
   concept/site/strength disjointness, renderer determinism, and absence of
   V25 artifacts.
2. **Instrument qualification:** pass controlled/native parity, deterministic
   repeat, zero-intervention parity, and behavioral-effect gates.
3. **Fit:** construct only fit artifacts and fit targets; choose the locked
   estimator cell and regularization.
4. **Tune:** qualify without reselection; stop on failed target variance,
   control floors, or renderer mismatch.
5. **Prediction lock:** seal all assessment predictions and their digest before
   generating assessment effects.
6. **Assessment:** generate the sealed effects once, compute all channel metrics,
   and emit aggregate-only external artifacts.
7. **Independent validation:** verify manifest binding, permutation controls,
   prediction-before-label ordering, metric recomputation, and claim ceiling.

Stop immediately on any parity failure, target degeneracy, concept collision,
renderer nondeterminism, prediction-lock violation, raw-payload retention,
assessment leakage, or missing provenance. There is no adaptive rerun.

## Interpretation ceiling

A positive result supports only:

> In one fresh local actor construction, a fixed synthetic opaque artifact
> surface added predictive information about a directly measured held-out
> intervention effect beyond a matched report-only observer, under the frozen
> renderer and controls.

It does not establish faithful reasoning recovery, faithful computation,
mechanistic explanation, provider cryptography, provider vulnerability,
generalization, introspection, self-modeling, consciousness, safety,
production monitoring, Stage 0C confirmation, Stage 1 authorization, benchmark
evidence, or accepted Evidence Ledger status.

A null result is equally bounded: it does not show that opaque provider
artifacts lack information, only that this synthetic surface did not add
predictive value under this protocol.

## Required artifacts and retention

Execution artifacts must remain repository-external and contain only:

- protocol, source, renderer, and configuration digests;
- actor inventory identifiers and license metadata;
- aggregate channel metrics and uncertainty intervals;
- stop/failure codes and validation receipts;
- prediction-lock and assessment-label timestamps or sequence numbers.

No raw activations, raw artifact token streams, model reports, prompts,
credentials, PII, signatures, or provider traces may enter the repository or
the retained bundle without a separately approved privacy decision.

## Authorization boundary

This document authorizes no model execution. The current state slice permits
only this protocol specification, navigation, and review documentation. A
future execution slice requires a separate explicit authorization naming the
runner paths, actor inventory, external artifact directory, validation command,
and exact claim ceiling.
