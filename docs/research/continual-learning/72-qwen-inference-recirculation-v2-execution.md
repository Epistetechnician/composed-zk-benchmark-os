# Qwen Inference-Time Recirculation V2 Execution

State slice: `continual-learning-qwen-inference-recirculation-v2`.

Status: complete at the local broader-feasibility ceiling. The canonical
campaign is the immutable external artifact
`/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-qwen-inference-recirculation-v2-20260826-r2`.

## Protocol

This execution followed the V2 boundary in
`71-qwen-inference-recirculation-v2-boundary.md`. It used the already-cached
Qwen2.5-0.5B-Instruct-4bit MLX checkpoint, kept model weights frozen, and
preserved the V1 inference-time deep-to-shallow residual recurrence. The
evaluation used 12 fit and 12 document-disjoint assessment prose sequences
from six repository-owned Markdown sources. Source bytes and extracted text
units were digest-bound in the corpus manifest; raw corpus text was not copied
into the external result bundle.

The candidate grid was fixed before execution at source/destination pairs
`(7,2)`, `(9,3)`, `(11,4)`, and `(12,5)`, each with `alpha=0.10`. Selection
used fit text only. The assessment was run once with the selected pair and
once as a deterministic locked repeat.

## Execution history

The first producer attempt (`r1`) completed its artifact files but exited
nonzero when it attempted to create an output root that had already been
claimed. It is not the canonical execution. The producer was then corrected
within this state slice to claim the immutable root before model execution;
the clean `r2` run exited successfully. The `r1` root remains preserved for
auditability and was not promoted.

## Canonical result

The independent validator reported:

```json
{
  "assessment_sequence_count": 12,
  "claim_ceiling": "LocalDevelopmentQwenInferenceRecirculationBroaderFeasibility",
  "fit_sequence_count": 12,
  "performance_improved_on_assessment": false,
  "state_slice": "continual-learning-qwen-inference-recirculation-v2",
  "valid": true,
  "zero_alpha_parity_passed": true
}
```

The locked configuration was `source=12`, `destination=5`, `alpha=0.10`.
Assessment mean NLL changed from `5.238627717` to `5.240304740`, a
selected-minus-baseline delta of `+0.001677023`; lower is better. Mean
perplexity changed from `188.411371272` to `188.727606415`, a delta of
`+0.316235143`. The deterministic repeat had maximum metric delta `0.0`.
Manual/native zero-alpha parity passed for all 24 sequences with maximum
absolute logit delta `0.0` against the `1e-5` tolerance.

The receipt records `training=false`, `network=false`, and
`weights_frozen=true`. The corpus, model, configuration, results, and receipt
are digest-bound in the external artifact. The relevant manifest and result
digests are:

- source manifest: `3eb8428a79cbde5d032a2bacfc825d0d141576c5554df8c621214ff4d1b861e1`
- model manifest: `0aaa27ea97be0c050fa54231418191e197dd33e5f051828aea7d92d39c9b959a`
- configuration: `04d70ba222ab5f2f41bb0d25c0372086dcac74e7d8ed6385ec4dfcf891fac891`
- results: `3becb52e534cf1a27b7f01718f829e25116e13f8f9ab75f7a3c3d302e98b30f8`
- receipt: `46c812dd4b65c84b6e14418bc60ab05a82db6c949831bf9fc2cf87681996c10e`

## Interpretation and ceiling

V2 is valid local broader-feasibility evidence for this cached Qwen
checkpoint, frozen mechanism, and preregistered repository-owned corpus. It
does not support a positive continual-learning promotion: the V1 improvement
did not reproduce on the broader document-disjoint assessment. It is not a
paper replication, a general Qwen result, a cross-model result, accepted
scientific evidence, provider validation, or production authorization.

The next scientific gate is a separately authorized campaign with a fresh,
larger disjoint corpus and locked repeats, or a separately authorized second
eligible model with a genuinely comparable protocol. Provider and production
lanes remain closed.
