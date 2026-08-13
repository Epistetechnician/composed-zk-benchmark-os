# V28 task-stratified microbatch confirmation record

State slice: `continual-learning-protocol-v28-task-stratified-microbatch-confirmation-preflight`.

Source slice: `continual-learning-protocol-v28-task-stratified-microbatch-confirmation`.

Classification: `CorrectedLocalTaskStratifiedMicrobatchConfirmationPreflightNoBreakthroughClaim`.

## Execution

One immutable local confirmation ran on the second pre-identified V27 tie
cell: seed `20260812`, order `0,3,1,2`. It used the V28
`task_stratified_round_robin_microbatch_v1` schedule and retained the V26
fact IDs, one shared adapter, one persistent AdamW state, exact data budgets,
and exact optimizer budgets.

The pure-data plan was independently validated with plan hash:

`c4e26ee2a4f6076b7a0a86bb6d9f16227e2784c4bd7bea38cfd3194931c5904e`.

The immutable output was:

`/tmp/continual-learning-model-v28-task-stratified-microbatch-confirmation-preflight-20260812-order0312`.

## Result

| arm | acquisition | after update 1 | after update 2 | after update 3 | retention | replay exposure | optimizer state | adapter bytes | peak memory |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |
| `shared_replay` | 8/8 | 2/8 | 2/8 | 2/8 | 2/8 | verified | verified | 5,877,295 | 0.763497016 GB |
| `shared_no_replay` | 8/8 | 0/8 | 0/8 | 2/8 | 2/8 | verified | verified | 5,877,295 | 0.763924856 GB |

Both arms used 128 actual examples and 640 optimizer iterations. All 24
observed 32-row iterator constructions matched the declared batch policy.
Replay fact IDs were present in the actual replay training datasets for every
update. The independent validator returned `valid: true`.

Retention effect:

`shared_replay 2/8 - shared_no_replay 2/8 = 0.00`.

## Decision

The replay mechanism is now mechanically verified, but the task-stratified
microbatch change does not improve retention in this second frozen tie cell.
V28 therefore fails its candidate retention gate and is rejected as a robust
retention repair. The first V28 cell remains a targeted positive signal only;
the second confirmation is tied, and V27 had already shown both `20260812`
orders tied under the prior protocol.

The claim ceiling remains local protocol evidence. This is not a replication,
general continual-learning result, SOTA result, breakthrough claim, or H100
authorization. The next research object must redesign the task/update
protocol and pass a new pure-data contract before another model preflight.

Hashes:

```text
contract_sha256: 0ed5a1cd609d8efa961d390e9b62845e6be19d2a401531996aa13f38b1b7bd1a
manifest_sha256: f50b31fad291123121b5816248e3c14af637576b970fd7e7bc2488dbe50bd9d3
result_sha256:   31c0e9a19ef7d7cb419fab50810d2a8ed0bc03646f13fefa5c56d5cfd039a175
```
