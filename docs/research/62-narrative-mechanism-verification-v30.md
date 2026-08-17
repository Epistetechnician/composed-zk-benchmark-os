# Narrative–Mechanism–Verification V30

State slice: `astral-narrative-mechanism-verification-v30`.

Status: `Executed / LocalDevelopmentPlantedMechanismVerification`.

## Scientific question

Can a mechanistic evidence object predict a known actor's held-out intervention
effects better than a plausible narrative report, while a shuffled mechanism
control fails? This converts the paper's information/report distinction into a
small planted-circuit validation.

The narrative, mechanism, and verification objects are separate:

```text
narrative report -> plausible feature/weight story
mechanism report -> measured feature/weight evidence
verification     -> held-out intervention effect against planted ground truth
```

## Frozen design

- actor: a deterministic four-feature planted circuit with weights `[3,-2,0,1]`;
- narrative report: plausible but wrong weights `[3,-2,1,0]`;
- mechanism report: correct sparse feature/weight evidence;
- shuffled mechanism: fixed permuted weights `[0,3,-2,1]`;
- assessment: eight held-out intervention vectors;
- endpoint: mean squared error on directly computed intervention effects;
- auxiliary endpoints: active-feature recall and narrative/mechanism Jaccard;
- combined observer: mechanism evidence remains authoritative for verification;
- no model, provider, API, raw reasoning, secret, PII, or V25/V28/V29 artifact.

## Gates

The mechanism observer must beat narrative-only and shuffled-mechanism MSE,
recover all planted active features, and retain the exact local claim ceiling.
The combined observer must not be credited for narrative plausibility when its
verification score comes from mechanism evidence.

## Result

| Metric | Narrative-only | Mechanism-only | Combined | Shuffled mechanism |
|---|---:|---:|---:|---:|
| Held-out MSE | `0.5` | `0.0` | `0.0` | `12.0` |
| Active-feature recall | `2/3` | `3/3` | `3/3` | not promoted |

Narrative/mechanism active-feature Jaccard was `0.5`. All three V30 tests and
the full `zkbench-core` test suite passed.

## Interpretation and ceiling

This is positive local planted-circuit evidence that a separately represented
mechanism object can outperform a plausible narrative object on a known causal
verification task. It validates the measurement distinction, not a real model's
internal mechanism and not the paper's provider attack.

Maximum claim: `LocalDevelopmentPlantedMechanismVerification`.

It does not establish Astral Stage 0C, Stage 1, generalization, mechanistic
faithfulness in a trained model, HSAI security, provider cryptography,
consciousness, global introspection, benchmark status, or production readiness.
