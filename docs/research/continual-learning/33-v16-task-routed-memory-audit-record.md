# V16 task-routed memory architecture audit record

State slice: `continual-learning-protocol-v16-task-routed-memory-audit`.

Classification: `TaskRoutedMemoryArchitectureAuditNoBreakthroughClaim`.

Claim ceiling: `LocalDevelopmentTaskRoutedMemoryAudit`.

## Scope and execution

V16 was a read-only audit of the accepted V14 and V15 external artifacts. It
performed no model training. It checked matched fixed contracts, exact task
routes, adapter freshness, retention comparisons, artifact storage, training
log telemetry, and the H100 gate.

Sources:

- V14: `/tmp/continual-learning-model-v14-qwen-seed20260810-order0123`
- V15: `/tmp/continual-learning-model-v15-qwen-seed20260810-order0123`

## Findings

| measure | result |
| --- | --- |
| fixed contract match | passed |
| task routes | 4/4 exact (`T0` through `T3`) |
| routed adapters fresh/non-resumed | passed |
| naive retention | 2/8 (0.25) |
| shared replay retention | 2/8 (0.25) |
| interleaved replay retention | 0/8 (0.00) |
| task-adapter-bank retention | 8/8 (1.00) |
| V14 peak memory telemetry | 0.765 GB |
| V15 peak memory telemetry | 0.764 GB |
| V14 mean logged throughput | 13.022 it/s |
| V15 mean logged throughput | 13.474 it/s |
| bank adapter slots | 4 |
| bank adapter bytes | 23,509,180 |
| full V14 artifact bytes | 165,022,814 |
| full V15 artifact bytes | 165,022,489 |

The route audit confirms that explicit task routing is a valid memory
architecture control: every task token resolves to a distinct fresh adapter,
and the target task remains at `8/8`. Shared replay and interleaved replay do
not preserve the codebook under the same local contract.

The logged memory is below 1 GB in both accepted runs, and the scientific
retention gates fail before any resource bottleneck is relevant. Throughput is
training-log telemetry, not wall-clock benchmarking.

Gates:

```text
fixed_contract_match: true
route_resolution: true
shared_replay_retention_above_naive: false
interleaved_replay_retention_above_naive: false
bank_retention_above_shared_naive: true
runtime_or_memory_bottleneck_demonstrated: false
h100_authorized: false
breakthrough_claim_eligible: false
```

Independent validator:

```text
valid: true
report_sha256: edfbcbb44799cb52c79033203885c031f3608a57defd13a68f467616dffcaf78
```

## Decision

Accept V16 as a route-preservation architecture audit and stop. The next
research object must redesign the shared representation/update interface if the
goal remains replay-based retention. The evidence does not justify another
replay schedule, replication panel, second model, or H100 allocation.
