# Stage 0C Structured Effect Explainer V16

State slice: `astral-stage0c-structured-effect-explainer-v16`.

Status: `PreregisteredDevelopmentOnly`. Confirmation: `NotAuthorized`.
Stage 1: `BlockedByStage0C`.

## Design

V16 predicts the complete signed ten-effect vector jointly rather than treating
each site/operator effect as an unrelated scalar. This tests whether V15's two
unstable cells arose from ignoring covariance among causally related effects.

- actor seeds: `283, 293, 307, 311`;
- fit families: `688..703`;
- sealed assessment families: `704..711`;
- unchanged actor recipe, five CLS sites, zero and matched-patch operators;
- prohibited reserves: seeds `173/179/181`, families `512..575`;
- no prior actor or assessment range may be substituted.

Every actor must reproduce at `>=0.95` train and development accuracy before
fit interventions.

## Structured Target and Inputs

For each example, order the target as five zero effects followed by five patch
effects. Using fit effects only, center all targets and compute a deterministic
rank-four SVD basis with fixed signs. Assessment effects never influence the
basis.

Inputs contain four bits, two logits, label, and 64 method values formed by
concatenating four eight-dimensional head vectors with the 32-dimensional MLP
vector. Every learned comparator receives 71 scalars.

Per actor, fit standardized multivariate ridge (`alpha=0.001`, unpenalized
intercept) from inputs to four effect coordinates, then reconstruct ten effects.

## Comparators

- `own_telemetry`;
- mean of the three unchanged `other_actor_telemetry` projections;
- `pooled_telemetry`;
- `own_activation`, using norm/mean/max/attention summaries and zero padding;
- `own_text_io`, using a zero method field;
- `own_shuffled_telemetry`, permuted within actor and family;
- `own_constant` and `global_constant`.

Actor seed and family ID are forbidden inputs. No rank, alpha, feature, or
checkpoint selection occurs.

## Ordering

Qualify actors; generate fit telemetry/effects; freeze basis, scalers, and
projections; generate assessment telemetry; write all predictions and a digest
lock; verify no assessment effects exist; only then generate assessment effects,
join, score, classify, and independently validate.

## Gate

`StructuredDevelopmentCandidate` requires:

1. complete qualification, parity, census, source-pair, ordering, digest, and
   finiteness controls;
2. own telemetry MSE at least 5% below own activation for every actor/operator;
3. own telemetry at least 10% below mean other-actor telemetry for every
   actor/operator;
4. own telemetry pooled MSE below every comparator separately for both
   operators;
5. positive correlation and calibration slope in `[0.5,1.5]` for both
   operators;
6. shuffled telemetry cannot reproduce either advantage.

Otherwise classify `StructuredDevelopmentNoCandidate`. No averaging may rescue
an actor/operator failure. Either result leaves Stage 0C, confirmation, and
Stage 1 blocked.

## Ceiling

A passing result supports only a prospective actor-specific supervised
intervention-effect explainer in this tiny setup. It is not introspection,
self-modeling, causal-graph recovery, correction value, benchmark evidence, or
production readiness.
