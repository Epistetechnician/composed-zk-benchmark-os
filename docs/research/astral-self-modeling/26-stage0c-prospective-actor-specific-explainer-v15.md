# Stage 0C Prospective Actor-Specific Explainer V15

State slice: `astral-stage0c-prospective-actor-specific-explainer-v15`.

Status: `PreregisteredDevelopmentOnly`. Confirmation: `NotAuthorized`.
Stage 1: `BlockedByStage0C`.

## Question

Does an actor-specific learned projection of bounded telemetry predict that
actor's prospectively sealed intervention effects better than equally specified
other-actor, activation-only, text-only, shuffled, and constant controls?

This is the tiny-model analogue of the privileged-access comparison in
"Training Language Models to Explain Their Own Computations." It predicts
numeric effects rather than natural-language explanations.

## Frozen Population

- actor architecture and five CLS sites: unchanged V13;
- actor recipe: `family-complete-2000`;
- actor seeds: `263, 269, 271`;
- estimator-fit families: `664..679`;
- assessment families: `680..687`;
- operators: exact zero and same-family bit-zero-flip patch;
- prohibited seeds: `173, 179, 181`;
- prohibited reserve: `512..575`;
- all V12-V14 assessment ranges remain excluded.

Each actor must reproduce at train/development accuracy `>=0.95` before any
intervention measurement.

## Frozen Estimator Panel

All learned estimators use the V13 48-input representation, fit-fold
standardization, intercept, deterministic ridge with `alpha=0.001`, and signed
effect targets.

- `same_actor_telemetry`: fit on all 16 fit families from the target actor;
- `other_actor_telemetry`: fit on eight frozen families from each of the other
  two actors, keeping total fit families equal at 16;
- `same_actor_activation`: actor-specific activation-only field;
- `same_actor_text_io`: actor-specific zero telemetry field;
- `same_actor_shuffled`: telemetry suffix deterministically permuted within
  target actor, site kind, and operator;
- `same_actor_constant`: actor-specific mean by exact site and operator.

Actor seed and family ID are prohibited inputs. No tuning or method selection
occurs.

## Mandatory Ordering

1. qualify all actors;
2. materialize fit telemetry and effects;
3. freeze every actor/estimator projection;
4. materialize assessment telemetry without assessment interventions;
5. write all predictions and `prediction-lock.json`;
6. validate the lock and absence of assessment effects;
7. only then execute and record assessment effects;
8. join, score, finalize, and independently validate.

Any assessment effect produced before the prediction lock makes the run
`Invalid`.

## Development Gate

Classify `DevelopmentCandidateEligible` only if:

1. qualification, parity, census, finiteness, source pairing, ordering, and
   digest controls pass;
2. same-actor telemetry MSE is at least 5% below same-actor activation for every
   actor and operator;
3. same-actor telemetry pooled MSE is below every other comparator;
4. same-actor telemetry pooled correlation is positive;
5. pooled calibration slope lies in `[0.5,1.5]`;
6. shuffled telemetry does not reproduce the advantage.

Otherwise classify `DevelopmentNoCandidate`. No cross-operator average may
rescue a failing actor/operator cell. Either result keeps `stage0_pass=false`,
`accepted_evidence=false`, confirmation unauthorized, and Stage 1 blocked.

## Ceiling

A passing development result would support only prospective actor-specific
privileged intervention prediction in this tiny setup. It would not establish
introspection, natural-language explanation faithfulness, self-modeling,
correction value, semantic understanding, benchmark evidence, or production
readiness.
