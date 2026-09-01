# V39 panel sealing and fit/tune preassessment

State slice: `astral-stage0c-qwen36-layer-effect-v39`.

Status: `PreassessmentPredictionLocked / PendingIndependentReview`.

This record covers the fresh V39 data panel, qualification recheck, fit/tune
direct-effect measurements, and prediction lock. It does not authorize or
record assessment intervention effects.

## External custody

The 12 supplied Project Gutenberg documents were acquired and independently
validated in the external corpus bundle recorded by [the V39 corpus
acquisition record](86-v39-gutenberg-corpus-acquisition-record-2026-08-26.md).
The sealed panel is:

- panel root: `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v39-panel-2026-08-26`;
- panel manifest SHA-256: `e61203e02b0621188b99fd14b6776c5ff19134ec715a698070bdc39275af3905`;
- concept registry SHA-256: `a9048ddde6e41ab301e91106cfab1c8a38ad7757b1b02873160727776652a250`;
- split manifest SHA-256: `d65912ec5000de52fc1b2d5ed4ff3198ecb29808add1f54bf0664ea5629fd6b3`;
- panel validator receipt: `valid=true`;
- family census: 48 total, 16 fit, 16 tune, 16 assessment.

The family registry is document-derived, uses paired ordinary/counterfactual
token-presence prompts, and excludes the recorded V25/V28/V29 artifact
digests. The Complete Works of Shakespeare and Romeo and Juliet remain in the
same assessment split; the review packet requires explicit inspection for
contained-work passage reuse.

## Qualification binding

The run is bound to the already passed external Qwen3.6 qualification:

- model manifest SHA-256: `367ad0c6838db3c831214f2d44da8907f669427fe5376ba9e9f2d2518bc6a90e`;
- qualification result SHA-256: `ba4a1c04292cc3bd365c8e4b191b39b5ac6171c01f69def0d465e26de01dfb42`;
- qualification validator receipt SHA-256: `cf6cac6604c7ee65d56c489e98c74cbcc0736885f21db0921fca6dd253ee6583`;
- model: `Qwen3.6-35B-A3B-MLX-4bit`;
- runtime: Python `3.14.5`, MLX `0.31.2`, MLX-LM `0.31.3`;
- target layer: 19 of 40, hidden width 2048.

The qualification remains `InstrumentQualificationPassed` at
`LocalDevelopmentInstrumentFeasibilityOnly`; it is not scientific evidence.

## Preassessment execution

The aggregate-only preassessment bundle is:

- root: `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v39-preassessment-2026-08-26`;
- run manifest SHA-256: `e8e0a15ee0a8cf61473d52581c5baebfa4084936e6979a19d1e7bd9711428cc9`;
- preassessment validator receipt: `valid=true`;
- classification: `PreassessmentPredictionLocked`;
- claim ceiling: `LocalDevelopmentV39PreassessmentPredictionLocked`.

Only fit and tune direct effects were measured: 16 families per split. The
assessment split had clean forwards only to materialize the locked predictions
for activation-only, text-only, shuffled, and constant controls. No assessment
replacement, assessment effect, or assessment control statistic exists in the
bundle.

The observed aggregate fit/tune values are descriptive preassessment outputs,
not a target-validity result:

| panel | fit RMSE | tune RMSE | selected ridge alpha |
|---|---:|---:|---:|
| activation-only | `0.0002951` | `0.1433937` | `0.1` |
| text-only | `0.0003753` | `0.7853533` | `0.1` |
| shuffled | `0.0004793` | `0.1190152` | `0.1` |
| constant | `0.1281196` | `0.1312087` | not applicable |

The direct target-effect means were `-0.0332031` on fit and `0.0` on tune.
The matched-control means were `-0.0371094` on fit and `-0.0625` on tune.
The runner selected same-document matched donors by minimum prompt-token
length difference, then source-word count and a deterministic hash; maximum
observed donor length differences were 16 fit tokens and 25 tune tokens. This
is an explicit independent-review item under the frozen matched-control
requirement, not a claim of exact donor-length equality.

## Prediction lock and stop condition

The prediction lock is `prediction-lock.json` in the external preassessment
root. It contains 16 assessment family IDs and four aggregate prediction
values per family, binds the panel, corpus, qualification, model, runtime, and
source digests, and states:

- `prediction_locked_before_assessment=true`;
- `assessment_effects_absent=true`;
- `assessment_effects_measured=false`;
- `raw_intermediates_retained=false`;
- `aggregate_only=true`.

The independent-review packet is at
`/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v39-independent-review-2026-08-26`.
All eight review items are pending. Assessment remains closed until an
independent reviewer verifies custody, freshness, split identity, controls,
prediction locking, privacy retention, validator behavior, and the claim
ceiling. The executing agent does not supply that receipt.

This record establishes only a validated local preassessment bundle. It does
not establish instrument feasibility beyond the qualification result,
held-out target validity, a `DevelopmentNoCandidate` or
`BoundedTargetValidity` final classification, introspection, causal
self-modeling, Stage 0C, Stage 1, benchmark evidence, or production readiness.
