# V29 replay-anchored temporal microbatch preflight record

State slice: `continual-learning-protocol-v29-replay-anchored-temporal-microbatch-preflight`.

Source slice: `continual-learning-protocol-v29-replay-anchored-temporal-microbatch`.

Classification: `CorrectedLocalReplayAnchoredTemporalMicrobatchPreflightNoBreakthroughClaim`.

## Execution

One corrected local preflight ran on the frozen V28 tie cell: seed
`20260812`, order `0,3,1,2`. The only changed variable was
`replay_anchored_oldest_first_temporal_microbatch_v1`, which removes random
batch permutation and places oldest replay-task microbatches before the
current-task phase in each temporal cycle.

The pure-data plan passed independent validation with plan hash:

`2e64c61b15f3b763f96914a0ed6a2b5ed1501652a7ff7abe687581c115f1193e`.

The immutable output was:

`/tmp/continual-learning-model-v29-replay-anchored-temporal-preflight-20260812-order0312`.

## Result

| arm | acquisition | after update 1 | after update 2 | after update 3 | retention | replay exposure | optimizer state | adapter bytes | peak memory |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |
| `shared_replay` | 8/8 | 4/8 | 6/8 | 6/8 | 6/8 | verified | verified | 5,877,295 | 0.764216340 GB |
| `shared_no_replay` | 8/8 | 0/8 | 0/8 | 0/8 | 0/8 | verified | verified | 5,877,295 | 0.764118180 GB |

Both arms used 128 actual examples and 640 optimizer iterations. All 24
observed 32-row iterator constructions matched the declared temporal policy.
Replay fact IDs were present in the actual replay training datasets for every
update. The independent validator returned `valid: true`.

Retention effect:

`shared_replay 6/8 - shared_no_replay 0/8 = +0.75`.

## Decision

V29 passes the local candidate gate on the previously tied V28 cell. The
effect is a targeted local protocol signal: the redesign repaired the
retention tie under this frozen seed/order while preserving the replay
exposure and compute controls. It is not a replication, general
continual-learning result, SOTA result, breakthrough claim, or H100
authorization.

The next gate is one preregistered V29 confirmation on the other V27
`20260812` tie cell, seed `20260812`, order `0,2,3,1`. If both V29 tie-cell
confirmations pass, expand only through a frozen V29 replication matrix. Do
not allocate H100 compute while peak memory remains approximately `0.764 GB`.

Hashes:

```text
contract_sha256: 533c6b7b527fb33bfe3c988c511db123921269816aae679e97e6c940136e44e6
manifest_sha256: 6bd0e55dab323f25afe976a687b4355370a273815056ebeeecc6f45dcf7944fd
result_sha256:   c0862461b1e38d580eb05bfd115dcc6e6c9ea88ed1a67b434a4136f67126c2f4
```
