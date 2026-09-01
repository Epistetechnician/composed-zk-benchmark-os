# Oak Lab powered plasticity-guard assessment V2

State slice: `oaklab-experience-learning-benchmark-v2`

## Frozen protocol

After V1's seven-cohort power of `0.2625`, V2 sealed 40 source-order cohorts
of 128 items: four fit, four tune, and 32 disjoint assessment cohorts. The
declared paired standardized effect is `0.5`, alpha is `0.05`, and the normal
approximation gives power `0.8074304194325571`. Plan digest:
`3117b59c5241a5a3d5f63b55ae1b847faba0a42eff43e3d9d106db371f87f721`.

The learning rate and guard parameters were fixed before assessment. No
replay, reshuffling, hidden accumulation, or assessment retuning was allowed.

## Receipt

The 5,120-row custody root is:

`/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-real-data-powered-v2`

Manifest digest: `5b88b7e680c2bbb40b7f2210afa9f2d22ed65403e6268f35d349b295d4a58a2e`.

Aggregate-only receipts are in:

`/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-plasticity-guard-assessment-v2`

All four receipts independently validate and report power `0.8074304194325571`.

| stream | fixed SGD loss | guard loss | paired p | result |
|---|---:|---:|---:|---|
| AWGN n-MNIST | 4.728428 | 9.037194 | `8.13e-199` | no candidate |
| UCI HAR sensor | 0.575685 | 0.976889 | `3.23e-05` | no candidate |
| household power | 0.051502 | 0.051848 | `0.09055` | no candidate |
| EDHT21 event camera | 0.436025 | 0.436025 | `1.0` | no candidate |

The powered result closes the current plasticity guard as a candidate for
this real-panel lane. It does not prove universal ineffectiveness, but a new
selective-credit theory is required before reopening the mechanism.
