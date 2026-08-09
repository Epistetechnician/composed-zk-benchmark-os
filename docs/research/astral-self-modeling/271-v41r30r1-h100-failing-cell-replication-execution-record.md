# V41R30R1 H100 Failing-Cell Independent Replication Execution Record

State slice: `V41R30R1H100FailingCellIndependentReplication`.

Status: `InfrastructureBlockedBeforeScientificExecution`.

The fresh identity was preregistered in record 270 and grouped under GMAN
mission `v41r30r1-h100-failing-cell-replication`.

## Runtime attempt

- node: `astral-v41r30r1-failing-cell-replication-node-r1`;
- chip: H100, clock-locked;
- image: `cuda-12.4`;
- node ID: `ead26876-3726-44d3-bf72-4a18e6262792`;
- command: `cmd-6mswm`;
- node reached `running` and was stopped immediately after setup failure;
- no worker process, model load, optimizer step, or scientific artifact ran.

The node could not clone the private `recoverable-ghost-states` repository:
`fatal: could not read Username for 'https://github.com': No such device or address`.
No credential was available or passed. The node was stopped, so compute did not
continue accruing. This is an access/infrastructure result, not a replication
result.

## Disposition

V41R27R19 remains terminal at census `30/48` and qualification `NotAssessed`.
V41R30R1 produced no scientific evidence and does not alter any campaign
identity, threshold, method, or claim ceiling.

Claim ceiling: `RemoteH100V41R30R1FailingCellIndependentReplication`.
