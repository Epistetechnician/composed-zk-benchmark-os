# V26 corrected shared-global-update preflight record

State slice: `continual-learning-protocol-v26-shared-global-update-stream-preflight`.

Source slice: `continual-learning-protocol-v26-shared-global-update-stream`.

Classification: `CorrectedLocalSharedGlobalUpdateStreamPreflightCandidateForReplicationNoBreakthroughClaim`.

## Execution identity

One corrected local preflight ran on the cached
Qwen2.5-0.5B-Instruct-4bit model with seed `20260812` and task order
`0,1,2,3`. V26 used one globally seeded shared update stream, one persistent
AdamW state, one shared eight-layer adapter, and no per-task RNG reseeding.

The earlier output at
`/tmp/continual-learning-model-v26-shared-global-update-stream-preflight-20260812-order0123`
is quarantined as invalid: its runner wrote selected facts without
materializing the frozen 32-row update budget. Its metrics are not used here.
The accepted result is the immutable `-r2` output below.

Both arms used exactly 32 actual dataset rows and 160 optimizer iterations
per update, for 128 actual examples and 640 optimizer iterations. The final
shared adapter was exactly `5,877,295` bytes in both arms. Replay fact IDs
were present in every actual replay dataset, and optimizer-state persistence
was verified.

## Result

| arm | acquisition | retention after update 3 | replay exposure | optimizer state | peak memory |
| --- | ---: | ---: | --- | --- | ---: |
| `shared_replay` | `8/8 = 1.00` | `4/8 = 0.50` | verified | verified | `0.765351252 GB` |
| `shared_no_replay` | `8/8 = 1.00` | `0/8 = 0.00` | verified | verified | `0.764992652 GB` |

Primary retention effect (`shared_replay - shared_no_replay`): `+0.50`
(`4/8 - 0/8`).

Target-task accuracy after each update:

- `shared_replay`: `1.00`, `0.50`, `0.50`, `0.50`;
- `shared_no_replay`: `1.00`, `0.00`, `0.00`, `0.00`.

Replay counts were `{}` at step 0, `{T0: 8}` at step 1,
`{T0: 8, T1: 8}` at step 2, and `{T0: 8, T1: 8, T2: 8}` at step 3.
Each replay dataset contained 32 actual rows after deterministic
materialization.

## Decision

V26 passes the local acquisition, replay exposure, optimizer custody, byte
budget, and strict retention gates. It is eligible for a separately
preregistered bounded replication decision. This is not replication evidence,
a general continual-learning result, a SOTA result, or a breakthrough claim.
H100 provisioning remains closed: peak memory was approximately `0.765 GB`,
so the remaining bottleneck is not demonstrated to be runtime or memory.

External result artifact:

`/tmp/continual-learning-model-v26-shared-global-update-stream-preflight-20260812-order0123-r2/result.json`

Hashes:

```text
contract_sha256: 927f3cf5768fdc65f02be3b94f35a7ab28d3395a47f08c27a0da53751085b227
manifest_sha256: b2d58c38e4bbee99b692ab10d7ffe1d4dca5ed8eca4bb546da2bdc167de420e2
result_sha256:   14aedb6136848868a68713a666526680ac574762111d83545831c520e56af0eb
```
