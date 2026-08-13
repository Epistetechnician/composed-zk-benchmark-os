# V29 replay-anchored temporal replication record

State slice: `continual-learning-protocol-v29-replay-anchored-temporal-replication-preflight`.

Source slice: `continual-learning-protocol-v29-replay-anchored-temporal-replication`.

Classification: `FreshLocalReplayAnchoredTemporalReplicationMatrixNoBreakthroughClaim`.

## Matrix result

The two V29 anchor cells were independently validated and not rerun. Seven
fresh cells then ran exactly once under the frozen V29 contract.

| seed | order | replay retention | no-replay retention | effect |
| ---: | :---: | ---: | ---: | ---: |
| 20260812 | 0312 anchor | 6/8 | 0/8 | +0.75 |
| 20260812 | 0231 anchor | 4/8 | 0/8 | +0.50 |
| 20260811 | 0123 | 4/8 | 0/8 | +0.50 |
| 20260811 | 0231 | 2/8 | 0/8 | +0.25 |
| 20260811 | 0312 | 4/8 | 0/8 | +0.50 |
| 20260812 | 0123 | 2/8 | 0/8 | +0.25 |
| 20260813 | 0123 | 8/8 | 0/8 | +1.00 |
| 20260813 | 0231 | 6/8 | 0/8 | +0.75 |
| 20260813 | 0312 | 8/8 | 0/8 | +1.00 |

All nine cells achieved `8/8` acquisition. Every fresh cell and both anchors
passed replay exposure, optimizer-state persistence, exact 128-example/640-
step budgets, matched `5,877,295`-byte adapter budgets, and 24 temporal batch
audits. Peak memory remained approximately `0.764 GB`.

The independent matrix validator returned `valid: true`. The corrected
validator distinguishes required false authority boundaries from required true
scientific gates; the immutable run artifact was not modified.

## Decision

The strict local V29 matrix gate passes: replay retention exceeds no-replay in
all nine cells, including both pre-identified V27 tie cells. This establishes a
robust local protocol result for this benchmark matrix: replay-anchored
temporal microbatch ordering is a credible retention intervention under the
frozen setup.

The claim ceiling remains `LocalDevelopmentReplayAnchoredTemporalReplicationMatrix`.
This is not yet a general continual-learning theorem, SOTA claim, breakthrough
claim, production result, or independent replication. The next scientific
step is external review plus a preregistered independent implementation or
dataset/model replication. H100 remains unauthorized because the local run is
memory-light and runtime has not been shown to be the limiting bottleneck.

Hashes:

```text
plan_sha256:     9f4e40fb779077efc0300f00b0b391d5f6679a1d5fe2bf41f5fff0e29e03cdcd
manifest_sha256: 1f7d1feb94ca86a93eb8d05fe7b0c761558b5ea3de4a4eb9f0eefaadff30c7ba
result_sha256:   ceedf7a34bdfd2f362c0d42f85a464a2cc8e65c5e59e15d29c211e3522e39799
```
