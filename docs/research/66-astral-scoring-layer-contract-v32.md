# Astral Scoring-Layer Contract V32

State slice: `astral-scoring-layer-contract-v32`.

Status: `Executed / LocalDevelopmentScoringLayerContract`.

## Purpose

Formalize the distinction between behavior, mechanism, and introspection so a
successful lower-layer measurement cannot silently become a higher-layer
claim. The contract is a governance and scoring boundary, not a new model
experiment.

## Layer definitions

| Layer | Minimum evidence | Required endpoint | Explicit nonclaim |
| --- | --- | --- | --- |
| `behavior` | Held-out task or output behavior with a locked control | Behavioral effect or task metric | No mechanism recovery or self-report claim |
| `mechanism` | Directly measured intervention effects, a separately represented mechanism object, and shuffled/narrative controls | Held-out intervention-effect prediction plus mechanism support metrics | No introspection or self-understanding claim |
| `introspection` | Actor self-report, external mechanistic evidence, prediction locking, held-out interventions, and locked internal/external controls | Self-report prediction of held-out effects that survives external comparison | No global introspection, consciousness, or complete-computation claim |

The layers are ordered by evidentiary requirements, not by rhetorical strength.
Behavioral success is insufficient for mechanism. Mechanism success is
insufficient for introspection. A narrative explanation never satisfies the
mechanism prerequisite by itself.

## Frozen promotion rules

- `behavior` requires held-out behavior evidence;
- `mechanism` additionally requires direct intervention effects and measured
  mechanism evidence;
- `introspection` additionally requires actor self-report, prediction locking,
  external comparison, and locked controls;
- missing any prerequisite returns the highest lower layer, never an inferred
  higher layer;
- the V30/V31 planted-circuit results classify as `mechanism`, not
  `introspection`;
- all current local profiles remain at repository evidence ceiling
  `Level1LocalReplay` or below;
- no scoring-layer label mutates the accepted Evidence Ledger.

## Validation target

The V32 regression test evaluates frozen profiles for behavior-only,
mechanism-qualified, introspection-incomplete, introspection-qualified, and
narrative-only evidence. The primary gate is exact classification with zero
unsupported upward promotions. The test also verifies that mechanism evidence
without actor self-report cannot reach the introspection layer.

## Executed result

The promotion guard classified all six frozen profiles exactly: `0` unsupported
upward promotions. V30 and V31 evidence stopped at `mechanism`. Removing
self-report, prediction locking, external comparison, or direct intervention
effects lowered an introspection-qualified profile to the appropriate lower
layer. All three V32 tests passed through the Cargo integration-test path.

## Nonclaims

This contract does not establish a model's self-understanding, mechanistic
faithfulness, introspection, consciousness, safety, benchmark standing,
production readiness, HSAI security, provider cryptography, Stage 0C, or Stage
1. It formalizes claim routing for future evidence.
