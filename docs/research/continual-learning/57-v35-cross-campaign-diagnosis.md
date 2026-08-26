# V35 cross-campaign diagnosis

Status: `CompleteComparativeAcquisitionDiagnosis`.

State slice: `continual-learning-cross-campaign-diagnosis-v35`.

V35 is read-only. It independently validates the sealed V32 and V34 campaign
receipts, then compares one mechanical metric: non-target task acquisition
stability. A task is stable when adapter train accuracy exceeds its own
no-update baseline, held-out accuracy is at least `0.75`, and train output is
nonconstant. V32 and V34 use disjoint seeds, so the comparison is diagnostic,
not causal proof.

## Finding

The raw-text V34 boundary is consistent with improved non-target stability:

| Campaign | Non-target stable | Target stable | Eligible cases |
| --- | ---: | ---: | ---: |
| V32 | 7/9 | 3/3 | 2/3 |
| V34 | 9/9 | 2/3 | 2/3 |

V34 removes the two V32 non-target failure patterns from the fresh campaign,
but introduces no campaign-level eligibility improvement because seed
`20260857` fails target T0 at `2/8` train and held-out accuracy. The correct
classification is
`NonTargetStabilityImprovedTargetSeedSensitivityRemains`, with causal status
`DisjointSeedComparisonNotCausalProof`.

The immutable diagnosis was executed at
`/private/tmp/continual-learning-cross-campaign-diagnosis-v35-20260824-r1`
and copied byte-identically into durable repository-external custody at
`/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-cross-campaign-diagnosis-v35-20260824-r1/diagnosis.json`.
The diagnosis report digest is
`5fb6248457075c338ce6b9d3c6e97c8fca85e0c58028e5a54f819d5fc9ee05da` and the
file SHA-256 is
`c1c2c48bf46a7423dd0a0cde5d3e0b3a01fa7905f66a145abc21119ec972722f`.

On 2026-08-24, the diagnosis was re-run against the durable V32 campaign
receipt and the reconstituted durable V34 campaign receipt. The new immutable
root is
`/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-cross-campaign-diagnosis-v35-20260824-r2`.
Its independent validator returned `valid: true`, and its `diagnosis.json` is
byte-identical to the existing `r1` receipt.

No model execution, training, retention, interference, provider, production,
or network work occurred. The next hypothesis requires a separately
preregistered controlled initialization or optimizer-seed diagnosis for target
T0. Retention remains unauthorized.

Claim ceiling: `LocalDevelopmentQwen25CrossCampaignAcquisitionDiagnosis`.
