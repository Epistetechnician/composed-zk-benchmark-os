# V41R31R2 H100 Infrastructure-Recovery Smoke Preregistration

State slice: `V41R31R2H100InfrastructureRecoverySmoke`.

V41R31R1 was classified `InfrastructureIncomplete` because its snapshotted
H100 failed during restoration before either scientific arm started. This new
identity tests only the infrastructure path. It does not rerun V41R31R1 and
does not produce scientific evidence.

## Locked protocol

- use the existing snapshotted H100 node
  `astral-v41r30r1-failing-cell-replication-node-r1`;
- restore the disk and dispatch one bounded command;
- command: print GPU identity, CUDA availability, and a fixed smoke marker;
- no model load, training, worker execution, tuning, or threshold change;
- stop the node immediately after terminal command result;
- preserve any provider or restore failure as infrastructure evidence;
- no retries within this identity.

## Outcomes

- `InfrastructureRecoverySmokePass`: node reaches running, command exits
  zero, reports one H100 and CUDA available, and the node is stopped.
- `InfrastructureRecoverySmokeFail`: restore, dispatch, GPU, CUDA, or
  terminal command gate fails.

Claim ceiling:
`RemoteH100V41R31R2InfrastructureRecoverySmoke`.

This identity cannot change V41R27 census `30/48`, qualification
`NotAssessed`, or any scientific claim. A successful smoke test permits a
separate preregistered V41R31R3 paired scientific diagnosis.
