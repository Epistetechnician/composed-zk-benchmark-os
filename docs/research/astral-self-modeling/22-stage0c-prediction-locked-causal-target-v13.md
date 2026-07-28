# Stage 0C Prediction-Locked Causal Target V13

State slice: `astral-stage0c-prediction-locked-causal-target-v13`.

Status: `PreregisteredDevelopmentOnly`. Confirmation: `NotAuthorized`.
Stage 1: `BlockedByStage0C`.

## Scope

V13 tests whether adding an explicit MLP site and sealing predictions before
assessment interventions repairs the two principal limitations of V12. It is a
bounded CLS-token screen, not the full 60-site study.

Sites are `head0.cls` through `head3.cls` before attention output projection and
`mlp.cls` before its residual addition. Operators are exact zero replacement
and same-family bit-zero-flip patching. Signed correct-minus-incorrect margin
change is canonical.

## Frozen Boundaries

- actor recipe: `family-complete-2000`;
- fitting actors: `239, 241`;
- assessment actors: `251, 257`;
- fitting families: `640..655`;
- assessment families: `656..663`;
- forbidden: seeds `173/179/181`, family reserve `512..575`, every V12 range;
- sites: five; operators: two; truth-table rows per family: sixteen.

Every actor must reproduce at `>=0.95` train and development accuracy before
measurement.

## Estimators

Deterministic ridge with `alpha=0.001`, fit-fold standardization, intercept, and
exactly 48 inputs: a frozen 16-scalar shared prefix plus a 32-value method
field. Head vectors use their eight raw coordinates followed by 24 zeros; the
MLP site uses all 32 raw coordinates.

- `text_io`: bits, logits, label, site/operator one-hot, zero padding;
- `activation_only`: shared prefix plus site-vector L2, mean, maximum absolute,
  and attention summary;
- `telemetry`: shared prefix plus the zero-padded local site vector;
- `shuffled_telemetry`: telemetry suffix permuted within site kind and operator;
- `constant`: fitting mean by site kind and operator.

No seed or family identifier is an input. No tuning or method selection occurs.

## Mandatory Execution Order

1. qualify actors;
2. materialize fitting telemetry and fitting effects;
3. fit estimators;
4. materialize assessment telemetry without assessment interventions;
5. write all assessment predictions and `prediction-lock.json`;
6. only then materialize assessment effects;
7. join predictions to effects, compute metrics, finalize, and validate.

Any assessment-effect file existing before the prediction lock is `Invalid`.

## Gate

`DevelopmentCandidateEligible` requires telemetry MSE at least 5% below
activation-only for each assessment seed and operator, lower pooled MSE than
every comparator, positive pooled correlation, calibration slope in
`[0.5,1.5]`, complete finite census, and all ordering/hash checks. Otherwise
classify `DevelopmentNoCandidate`. Both dispositions keep `stage0_pass=false`,
`accepted_evidence=false`, confirmation unauthorized, and Stage 1 blocked.

## Stop Rule and Ceiling

Failure closes this bounded CLS head-plus-MLP estimator lane. Success nominates
only a later independently reviewed protocol. Evidence ceiling:
`LocalDevelopmentCausalTargetDiagnostic`; no circuit, introspection,
self-modeling, correction, benchmark, or production claim.
