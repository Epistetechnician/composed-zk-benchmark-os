# V47 independent design review receipt

State slice: `astral-stage0c-causal-accessibility-independent-design-review-v47-2026-08-28`.

Date: 2026-08-28.

Reviewer role: independent review worker.

Reviewed memo: `docs/research/astral-self-modeling/105-stage0c-causal-accessibility-measurement-audit-v47.md`.

Reviewed memo SHA-256: `221d7bdfb347ed753c47abe57b7c1fe71ebc139645a72c2e509f680b8b8928a3`.

## Verdict

`REJECT`

The memo is not precise enough to authorize a separate implementation slice.

## Findings

- Causal theory: the corrected DAG and variable roles are clear enough to
  state the proposed access-by-intervention hypothesis, but assignment,
  timing, consistency, positivity, and no-interference assumptions are not
  fully operationalized for the executable design.
- 2x2 estimand identification: the memo correctly requires all four paired
  cells `(I=0,A=0)`, `(I=1,A=0)`, `(I=0,A=1)`, and `(I=1,A=1)` and defines the
  family contrast `D`. The implementation manifest must preserve the complete
  cell rule, counterbalanced order, and pre-effect exclusion of incomplete
  families.
- Estimands: `tau_access` is a causal interaction/difference-in-differences;
  it must not be described as standard mediation without additional
  interventional mediation assumptions. The secondary predictive estimands
  are appropriately distinct and held out.
- Power arithmetic: the corrected table gives 188 clustered family
  equivalents for `d=.30`, 106 for `d=.40`, and 69 for `d=.50`. The table is
  still a planning approximation; before assessment, replace it with a sealed
  four-cell cluster simulation tied to the actual covariance, ICC, missingness,
  family cardinality, attrition, and `D` estimand.
- Reliability: `ICC(A,1)`, repeatability, sign stability, bootstrap coverage,
  and variance decomposition are specified as required gates. The executable
  protocol must freeze repeat counts, estimators, confidence intervals, and
  missingness handling before data are opened.
- Recoverability/localization: cross-view recoverability has an explicit
  balanced-accuracy lower-bound gate. Localization is not fully gated: the
  phrase “beyond” a matched generic-output control lacks a declared effect
  metric, minimum threshold, uncertainty bound, and multiplicity rule. Add
  those exact criteria before implementation authorization.
- Controls: activation-only, text-only, exact-copy, shuffled, constant,
  matched, access-null, and matched-energy/norm controls are retained. The
  implementation must freeze their construction and all four factorial cells
  before fit data are read.
- Prediction lock: the required ordering correctly emits and digests
  fit/tune predictions before corresponding effects, freezes the predictor and
  configuration, and obtains independent review before assessment.
- Retention and claim ceiling: aggregate-only retention, validator rejection
  rules, and the narrow `BoundedCausalAccessibilityResult` ceiling are
  appropriate. No outcome may be promoted to introspection, causal
  self-modeling, Stage 0C, Stage 1, benchmark, or production evidence.

## Execution authorization status

`NOT AUTHORIZED` — no corpus acquisition, model loading, qualification,
fit/tune execution, assessment, artifact-root creation, or scientific
measurement is authorized by this receipt. V46 remains permanently closed and
V82 remains isolated and blocked.
