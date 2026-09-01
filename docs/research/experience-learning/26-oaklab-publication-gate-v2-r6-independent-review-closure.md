# Oak Lab publication gate V2 R6 independent review and closure

State slice: `oaklab-experience-learning-benchmark-v2`

## Review target

The reviewed claim target is the synchronized operator campaign
`oaklab-real-campaign-v2-operator-20260830-r2`, not the earlier V2 receipt and
not the fresh-sensitivity campaign. The exact campaign manifest is:

`/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-energy-v2-operator-20260830-r2/campaign_manifest.json`

Its campaign binding digest is
`9f3374b21ad2b9f8129e5d03b3db437f6908494eef3d98a1414aa61dd8b74131`. The
canonical backend order is `event_camera, long_horizon, noisy_mnist,
sensor`; the earlier sealed V2 backend receipts used a different 256-row
workload and were not mixed into this review.

## Independent mechanical checks

The following checks were rerun from disk without modifying any campaign
result:

- all three matrix receipts, four powered guard receipts, and four backend
  receipts independently validated against their custody roots;
- source-manifest file hashes, result-file hashes, and the campaign payload
  digest matched the new manifest;
- the raw `powermetrics` trace hash is
  `4b3b2d450788b5d961de830005bd621d9fca7ff910222eee22eadf3a20f2deea`;
- the derived CPU trace has 178 finite, non-negative, strictly increasing
  samples over 179 seconds and integrates by the fixed trapezoidal rule to
  `664.824 J`;
- the one-row energy receipt binds all matrix, guard, and backend result
  digests and records `154523591` declared learned events;
- the workload transcript contains the complete result-digest set. Its
  post-run shell cleanup error is retained as an operational note, while
  capture coverage is confirmed by output completion before sampler stop;
- the independent validation record is
  `/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-energy-v2-operator-20260830-r2/energy_receipt_independent_validation.json`
  with status `valid`;
- the closure-only mechanical review receipt is
  `/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-energy-v2-operator-20260830-r2/campaign_binding_independent_review.json`
  with review digest
  `69e088ff57d92b8e4e252322e6e79184b25badd8c01e6efe394db520e4604dbf`;
- the recomputed publication gate is
  `/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-publication-gate-v2-r6-operator/publication_gate.json`
  with result digest
  `749b5968b5de3fd467b928e4132ba27c967567f94edef014e93fb9a27554d0f7` and
  independent validator status `valid`.

## Decision

The gate is `no_candidate` and is closed for V2. The measured-energy
requirement is true, but
`candidate_beats_fixed_sgd_on_quality_adaptation_resources` is false. No
algorithm satisfies the strict loss, adaptation, paired-statistical, and
resource requirements across at least two real stream families.

Review disposition: `accepted_for_closure_only`.

`execution_authorization=false` and `publication_authorization=false`.
This review cannot promote a failed mechanism, reopen the plasticity guard,
or combine V2 with fresh-sensitivity `adam_b32` results. The claim ceiling is
`LocalDevelopmentOakLabExperienceLearningBenchmarkV2`; there is no SOTA,
production, causal, whole-system-energy, or Astral claim.

## Required continuation boundary

The next scientific attempt requires a materially new selective-credit theory
and estimand addressing adaptation-forgetting or sequential-utility
confounding, with fresh data and seeds, prediction locking, preregistered
power and multiplicity rules, independent review, and synthetic qualification
before any real-stream execution. The closed plasticity guard must not be
retuned.

Per-arm energy efficiency is a separate campaign. The aggregate `664.824 J`
receipt cannot be interpreted as an algorithm-level energy comparison.
