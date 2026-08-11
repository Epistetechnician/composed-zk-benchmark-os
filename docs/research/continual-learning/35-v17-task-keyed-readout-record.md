# V17 task-keyed readout feasibility record

State slice: `continual-learning-protocol-v17-task-keyed-readout-feasibility`.

Classification: `TaskKeyedReadoutFeasibilityNoBreakthroughClaim`.

Claim ceiling: `LocalDevelopmentTaskKeyedReadoutFeasibility`.

## Scope and execution

V17 tested a lightweight task-keyed readout over the accepted V14 final shared
replay adapter. It enumerated all 24 four-label permutations for each task,
selected the best permutation using only that task's eight training facts, and
evaluated the locked readout on eight held-out facts. No model retraining or
new adapter was performed.

Source artifact:

`/tmp/continual-learning-model-v14-qwen-seed20260810-order0123`.

## Findings

| measure | result |
| --- | --- |
| route slots | 4/4 present (`T0` through `T3`) |
| readout candidates per slot | 24 |
| readout training fit, every slot | 2/8 (0.25) |
| raw shared-replay target retention | 2/8 (0.25) |
| readout target retention | 2/8 (0.25) |
| naive target retention reference | 2/8 (0.25) |
| shared replay target retention reference | 2/8 (0.25) |

The final shared representation predicted `B` for every assessed fact in this
readout pass. A task-keyed permutation cannot recover information that is absent
from the raw representation. The readout therefore neither fits the training
codebooks nor improves held-out retention.

Gates:

```text
route_slot_count: true
readout_training_fit_floor: false
target_readout_above_shared_replay: false
target_readout_above_naive: false
candidate_eligible: false
breakthrough_claim_eligible: false
```

Independent validator:

```text
valid: true
report_sha256: 21946c064d4b48d4aee8b51164ba5a184e9e0b02631369451eb1cb6ac3f82f25
```

## Decision

Stop V17. Do not implement a readout-only architecture, replicate it, or
provision an H100. The next research object must change the learned shared
representation or update interface so task identity and residue remain
separable before readout. This remains a local feasibility negative, not a
general continual-learning or breakthrough claim.
