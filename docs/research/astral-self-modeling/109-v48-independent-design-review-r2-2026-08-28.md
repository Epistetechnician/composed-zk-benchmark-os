# V48 independent design review receipt — round 2

State slice: `astral-stage0c-cross-view-causal-state-transport-independent-review-v48-r2-2026-08-28`.

Date: 2026-08-28.

Reviewer role: independent scientific review worker.

Reviewed memo: `docs/research/astral-self-modeling/107-stage0c-cross-view-causal-state-transport-audit-v48.md`.

Reviewed memo SHA-256: `29ffd2c43f35652eed2fb0cb94c6148d3da6d05c5b4f802f21f1ef1c79eecd8e`.

## Verdict

`ACCEPT`

The revised design is precise enough to permit a separate implementation
authorization. This receipt authorizes no execution itself.

## Findings

- Causal assignment and timing are adequately specified: consistency,
  label-independent seeded counterbalancing, positivity, completed donor
  capture, one downstream patch, no post-intervention predictor input, stable
  family identity, and no mutable cross-trial state are explicit.
- The estimand is genuinely new relative to V46 and V47. `tau_CST` is a
  reciprocal donor-direction, cross-view causal transport contrast, not a
  correlation or a latent-access interaction. The fixed response-token margin
  and no-scale-switching rule are clear.
- Complete cell identification is now explicit. The revised algebra defines
  `Y(p,n,v,d)` with permitted cells `P=0,N=0` identity reinsertion,
  `P=1,N=0` state-matched transport, and `P=0,N=1` state-shuffled,
  norm-matched generic transport; `P=1,N=1` is forbidden and validator-
  rejected. `Delta_CST`, `Delta_null`, and `lambda_local` are now defined.
- The localization operator is theory-predeclared and not tuned: source 26,
  destination 12, final anchor position, one pass, norm matching, and
  `alpha=0.10`. The localization gates are exact: lower 95% cluster-bootstrap
  bound for `lambda_local >= 0.10`, standardized lower bound `>=0.20`, and
  generic-control cap `0.05`.
- Power arithmetic is correct for the stated planning sensitivity: `d=0.35`
  gives 86 independent family units, 138 after the 1.60 design effect, 35
  documents, and 44 after 20% attrition. A sealed four-cell simulation over
  actual covariance, ICC range `[0.10,0.30]`, missingness, and `tau_CST` is a
  mandatory pre-assessment gate and cannot be replaced by this table.
- Reliability and missingness are adequately bounded by `ICC(A,1)` lower
  bounds of `0.80` for decoder and transport effect, sign stability `>=0.80`,
  per-cell missingness `<=5%`, complete-family exclusion, repeats, and
  document-cluster uncertainty. Repeat counts and interval procedures must be
  sealed before fit data are read.
- Cross-view recoverability is explicit: the fixed four-class decoder must
  exceed the lower-bound balanced-accuracy threshold `0.35` in both
  directions. Cross-view effect equivalence is separately declared with the
  two-sided 90% interval inside `[-0.10,+0.10]`.
- Controls, prediction locking, retention, validation, fresh-data split
  identity, and claim ceiling are adequate. The unchanged V46 controls and
  new access-null/norm controls remain mandatory; tune predictions precede
  tune effects; raw data are prohibited from retained results; and the result
  ceiling remains bounded causal state transport for the named actor/operator/
  panel only.

## Execution authorization status

`IMPLEMENTATION_AUTHORIZATION_ELIGIBLE_SEPARATELY` — this receipt does not
authorize corpus acquisition, node creation, model loading, qualification,
fit/tune execution, assessment, or scientific measurement. A separate
authorization must name the actor, runtime, fixed operator, fresh corpus,
runner, validator, external custody root, and claim ceiling. Assessment remains
closed until qualification, sealed fit/tune predictions, the required power
simulation, configuration lock, and independent pre-assessment review pass.
V46 remains permanently closed; V82 remains isolated and blocked.
