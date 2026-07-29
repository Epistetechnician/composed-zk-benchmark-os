# V28R3 Infrastructure Failure Execution Record

State slice: `astral-rgs-v28r3-infrastructure-failure-sealing`.

Status: `Consumed / NoveltyPassed / PhaseBInfrastructureFailure / NotSealed`.

Both isolated baseline processes completed all 73,728 queries with exact
observation parity and accuracy `0.25`, so the fresh R3 corpus passed the
preregistered novelty gate. The first Phase B `context_only` control produced
no result: Metal terminated the process with code `-6` and
`kIOGPUCommandBufferCallbackErrorOutOfMemory`.

No persistent cell, optimizer step, update token, adapter, acquisition result,
or Gate 1 classification exists. This is a valid local novelty result and a
retained infrastructure failure, not continual-learning evidence. Repair and
rerun remain unauthorized.
