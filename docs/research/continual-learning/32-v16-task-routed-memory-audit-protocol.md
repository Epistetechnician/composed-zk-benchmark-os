# V16 task-routed memory architecture audit protocol

Status: `ProspectiveLocalDevelopmentTaskRoutedMemoryAudit`.

State slice: `continual-learning-protocol-v16-task-routed-memory-audit`.

## Purpose

V14 showed that the immutable task adapter bank retained the codebook at `8/8`
while shared replay tied naive at `2/8`. V15 showed that changing replay row
order made retention worse (`0/8`). V16 audits the architecture boundary using
the accepted V14 and V15 artifacts without retraining.

The audit answers three bounded questions:

1. Were the shared replay and routed-bank comparisons made under the same fixed
   model, task, optimizer, seed, order, and update contract?
2. Does the task-routed bank resolve every task token to a fresh, non-resumed
   adapter with exact route keys?
3. Is local runtime or memory the remaining bottleneck, or is the failure still
   scientific/protocol-level?

## Measurements and gates

The audit records retention and acquisition comparisons, route resolution,
adapter slot count and bytes, total artifact bytes, training-log throughput,
peak memory, and source result hashes. It does not reinterpret training loss as
task accuracy and does not claim production readiness or general learning.

The H100 gate remains closed unless a corrected protocol first passes its
scientific retention gates and local telemetry demonstrates runtime or memory as
the remaining bottleneck.

```text
PYTHONDONTWRITEBYTECODE=1 python experiments/continual_learning/task_routed_memory_audit.py \
  --v14 /tmp/continual-learning-model-v14-qwen-seed20260810-order0123 \
  --v15 /tmp/continual-learning-model-v15-qwen-seed20260810-order0123 \
  --output /tmp/continual-learning-model-v16-task-routed-memory-audit
```
