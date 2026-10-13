# V24 corrected shared-adapter preflight record

State slice: `continual-learning-protocol-v24-shared-adapter-task-keyed-optimizer-state-preflight`.

Source slice: `continual-learning-protocol-v24-shared-adapter-task-keyed-optimizer-state`.

Classification: `CorrectedLocalSharedAdapterTaskKeyedOptimizerStatePreflightNoBreakthroughClaim`.

## Run identity

External output:

`/tmp/continual-learning-model-v24-shared-adapter-task-keyed-optimizer-state-preflight-20260812-order0123-r2`.

The one corrected local preflight used the cached Qwen2.5-0.5B-Instruct-4bit,
seed `20260812`, order `0,1,2,3`, 32 rows and 160 optimizer iterations per
update, 128 examples and 640 optimizer iterations per arm, AdamW at `0.0001`,
batch size `2`, maximum sequence length `192`, and one shared eight-layer
adapter. Task-keyed optimizer states were serialized after each group and
restored before subsequent activation.

## Result

| Arm | Acquisition | Retention after update 3 | Replay exposure | State custody | Adapter bytes | Peak memory |
| --- | ---: | ---: | --- | --- | ---: | ---: |
| `shared_replay` | 2/8 | 2/8 | verified | verified | 5,877,295 | 0.819 GB |
| `shared_no_replay` | 2/8 | 2/8 | verified | verified | 5,877,295 | 0.802 GB |

Both arms used the exact 128-example and 640-optimizer-iteration budgets. The
shared adapter matched the eight-layer byte reference exactly. Replay fact IDs
were present in the actual per-task training datasets. Optimizer-state receipts
showed fresh zero state on first activation and persistent state on subsequent
activation.

## Decision

The protocol plumbing passed, but the candidate failed the acquisition floor:
the target task reached only `2/8` before interference. The retention tie is
therefore not interpretable as a replay result. V24 is rejected as a candidate
for replication and does not authorize an H100 or any breakthrough claim.

This is a solvability failure, not a compute failure. The next research object
must repair shared-adapter acquisition while preserving a shared interference
surface, then rerun one local acquisition/retention preflight. Do not tune the
replay selector, reuse this failed cell as positive evidence, or provision
accelerator capacity.
