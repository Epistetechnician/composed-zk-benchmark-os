# V27 shared-global-update-stream replication record

State slice: `continual-learning-protocol-v27-shared-global-update-stream-replication-preflight`.

Source slice: `continual-learning-protocol-v27-shared-global-update-stream-replication`.

Classification: `FreshLocalSharedGlobalUpdateStreamReplicationMatrixNoBreakthroughClaim`.

## Matrix result

The V26 development anchor passed independently at seed `20260812`, order
`0,1,2,3`, with replay retention `4/8` versus no-replay `0/8`. It was
not rerun. Eight fresh cells then ran once under the frozen V26 contract.

| seed | order | replay acquisition | no-replay acquisition | replay retention | no-replay retention | effect |
| ---: | :---: | ---: | ---: | ---: | ---: | ---: |
| 20260811 | 0123 | 8/8 | 8/8 | 2/8 | 0/8 | +0.25 |
| 20260811 | 0231 | 8/8 | 8/8 | 6/8 | 2/8 | +0.50 |
| 20260811 | 0312 | 8/8 | 8/8 | 4/8 | 2/8 | +0.25 |
| 20260812 | 0231 | 8/8 | 8/8 | 2/8 | 2/8 | 0.00 |
| 20260812 | 0312 | 8/8 | 8/8 | 2/8 | 2/8 | 0.00 |
| 20260813 | 0123 | 8/8 | 8/8 | 6/8 | 0/8 | +0.75 |
| 20260813 | 0231 | 8/8 | 8/8 | 6/8 | 0/8 | +0.75 |
| 20260813 | 0312 | 8/8 | 8/8 | 8/8 | 0/8 | +1.00 |

All eight cells passed replay exposure, optimizer-state persistence, exact
128-example/640-step budgets, and matched `5,877,295`-byte adapter budgets.
Peak memory stayed approximately `0.763--0.764 GB` per cell.

## Decision

Acquisition replicated in all eight fresh cells. Replay retention exceeded
no-replay in six of eight fresh cells and tied in both fresh `20260812`
orders. Including the V26 anchor, the effect was positive in seven of nine
matrix cells and tied in two.

The strict all-cell replication gate fails. V27 is partial local replication
evidence with seed/order sensitivity, not a robust replication, general
continual-learning, SOTA, or breakthrough claim. Do not provision an H100.
The next research object must address the `20260812` tie pattern or define a
new preregistered robustness test; do not silently expand this matrix or
select favorable cells.

External result artifact:

`/tmp/continual-learning-model-v27-shared-global-update-stream-replication`.

Hashes:

```text
plan_sha256:     e58ffdc94ab9cc585c23728296b0f6b6d007b9c32485983334132f1b76698e6e
manifest_sha256: 4afcdfc974bdcd513ad12c398655b7c1e9c18c5469440688817d6335827944ec
result_sha256:   8493ad65a0b36b64ba0028417f2c4acfb6e11ad70e415a198e734fe317e688d7
```
