# Evidence Synthesis and Research Reset V11

State slice: `astral-self-modeling-evidence-ledger-and-research-reset-v11`.

Status: `DocsFirstResearchReset`. Execution authorization:
`DevelopmentOnlyAfterPreregistration`. Stage 1: `BlockedByStage0C`.

## Finding

The actor-training problem and the attribution problem are now separated.
Family-complete-2000 training qualified every named V7 actor. The learned-model
attribution hypothesis did not survive: V5 failed its activation-magnitude gate,
and all five V10 gradient-derived methods were worse than activation magnitude.
The planted control remains valid plumbing evidence but was algebraically
privileged by construction.

The supported conclusion is narrow:

> Simple one-pass local gradient-derived head scores did not reliably
> outperform activation magnitude for zero-ablation head ranking in this tiny
> learned Boolean-transformer setup.

This does not show that activation magnitude is a mechanism, that gradient
attribution is universally ineffective, or that observer self-modeling cannot
work.

## Revised Thesis

The immediate target is predictive validity under frozen internal
interventions, not self-modeling:

> Can a preregistered estimator predict the full vector of directly measured
> intervention effects on held-out actor seeds and prompt families better than
> activation-only, text/input-output-only, constant, shuffled, and
> capacity-matched controls?

Only after this passes may the original conditional thesis be tested: whether
privileged telemetry adds value to an observer and whether a calibrated causal
prediction mediates useful correction.

## Methodological Reset

- Direct intervention effects are canonical labels. Attribution scores nominate
  candidates; they are not ground truth.
- Activation magnitude is a mandatory strong baseline.
- Freeze corruption, patch direction, intervention operator, metric,
  normalization, granularity, aggregation, and uncertainty analysis.
- Predict continuous effect vectors; retain ranking and regret as secondary
  summaries.
- Compare at least two operators, including patch/resample rather than relying
  only on zero ablation.
- Require parameter and label randomization, behavior-preserving invariance,
  baseline/reference sensitivity, necessity, sufficiency, completeness, and
  independent patching checks.
- Split by whole prompt family and actor seed. Do not tune on confirmation data.
- Treat the Python/PyTorch numerical instrument as current. The V9 Rust crate is
  a pure-data control-plane foundation and has no numerical-parity or scientific
  claim.

## Evidence Preservation

V1, V4, and the V5/V10 records remain retained with their original
dispositions. They are not pooled because protocols and evidential roles differ.
The V4 opened range is retired. Seeds `173/179/181` and families `512..575`
remain untouched; they will not be repurposed during exploratory redesign.
The authoritative full manifest digests remain in the original V0, V5, and V10
records; this reset does not replace or reissue them.

## Advancement and Stop Rules

Stage 0C development uses new ranges only. A single estimator may advance only
after the protocol and practical margin are frozen and independently reviewed.
A new untouched confirmation range is then allocated. Failure to beat the
activation-only estimator across every preregistered seed and operator stops
this architecture/task lane; it does not trigger another search over local
gradient formulas.

Even a pass establishes only intervention-predictive localization for a tiny
learned transformer. It does not establish introspection, self-knowledge,
semantic understanding, consciousness, global software-agent uniqueness,
benchmark evidence, production readiness, or accepted evidence elsewhere.
