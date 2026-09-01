# V48 independent design review receipt

State slice: `astral-stage0c-cross-view-causal-state-transport-independent-review-v48-2026-08-28`.

Date: 2026-08-28.

Reviewer role: independent scientific review worker.

Reviewed memo: `docs/research/astral-self-modeling/107-stage0c-cross-view-causal-state-transport-audit-v48.md`.

Reviewed memo SHA-256: `76afdde2ce8c2b5007998a9401c02b1351c5ba4ed8ad378e8d89179d23044b09`.

## Verdict

`REJECT`

The V48 design is substantially more precise than V47, but one localization
estimand remains insufficiently defined for implementation authorization.

## Findings

- Causal assignment and timing: the memo explicitly fixes consistency,
  label-independent seeded counterbalancing, positivity, single-pass timing,
  no mutable cross-trial state, stable family identity, and independent view
  generation. The executable authorization must preserve these assumptions.
- New estimand: `tau_CST` is a genuinely distinct reciprocal, cross-view,
  donor-direction transport contrast rather than V46's correlation or V47's
  latent-access interaction. Its response-margin scale and no-post-effect
  predictor boundary are clear.
- Cell identification: the memo requires every `P,V,D` condition and excludes
  incomplete families before effect inspection. The implementation manifest
  must retain the complete paired cell rule and counterbalancing digest.
- Localization: the fixed carrier (`source_layer=26`, `destination_layer=12`,
  final anchor, one pass, `alpha=0.10`, norm matching) is theory-predeclared,
  and the numerical gates (`0.10`, standardized `0.20`, generic-control cap
  `0.05`) are explicit. However, `Delta_null` is not defined as a potential
  outcome or condition distinct from the already-defined `P=0` access-null,
  while `N` is separately introduced as a control. Define the null operator,
  its exact cells, and `lambda_local` algebraically before authorization.
- Power: the planning arithmetic is correct for `d=0.35`: 86 independent
  family units, 138 after the 1.60 design effect, 35 documents, and 44 with
  20% attrition. The required sealed four-cell simulation over covariance,
  ICC range `[0.10,0.30]`, missingness, and `tau_CST` must still be completed
  before assessment; the planning table cannot be treated as final evidence.
- Reliability and missingness: `ICC(A,1) >= 0.80`, sign stability `>=0.80`,
  per-cell missingness `<=5%`, complete-family exclusion, repeatability, and
  cluster-level uncertainty are appropriate. Repeat counts, resampling, and
  interval procedures must be sealed before fit data are read.
- Controls and prediction lock: the unchanged V46 controls plus transport
  access-null and matched-energy/norm controls are retained. Fit-only
  prediction, digest-before-effect ordering, configuration freeze, and
  independent review before assessment are adequate.
- Fresh data, retention, and claim ceiling: the new dual-view/state-graph
  custody requirements, split-disjointness checks, aggregate-only retention,
  validator restrictions, and bounded causal-state-transport classification
  are appropriate. No result may establish introspection, self-modeling,
  Stage 0C, Stage 1, benchmark evidence, or production readiness.

## Execution authorization status

`NOT AUTHORIZED` — no corpus acquisition, node creation, model loading,
qualification, fit/tune execution, assessment, or scientific measurement is
authorized by this receipt. V46 remains permanently closed; V82 remains
isolated and blocked. A revised localization estimand requires a new
independent review before any implementation authorization.
