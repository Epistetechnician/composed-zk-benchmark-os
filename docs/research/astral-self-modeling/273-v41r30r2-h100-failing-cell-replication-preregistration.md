# V41R30R2 H100 Failing-Cell Second Independent Replication Preregistration

State slice: `V41R30R2H100FailingCellSecondIndependentReplication`.

V41R30R1 completed the frozen `v41r27-panel-8-seed-412019` worker on a real
H100 with `pass:true`, `4/4` acquisition cases, and protected accuracy `1.0`.
That result did not reproduce the V41R27R19 failure. A single non-replication
cannot determine whether the earlier failure was rare stochastic behavior or
history-dependent state.

This fresh identity runs one additional exact replication from the preserved
V41R30R1 runtime disk. The source, model, tokenizer, seed, worker method,
thresholds, and selected cell remain unchanged. Only the experiment identity
and fresh process/adapter state differ.

## Locked protocol

- one worker: `v41r27-panel-8-seed-412019`;
- exactly 256 optimizer steps;
- fresh process, optimizer, and adapter state;
- same real H100, frozen model revision, tokenizer, and V41R27 runner;
- same protected and acquisition gates;
- no retries within this identity, substitutions, tuning, threshold changes,
  assessment, or census update;
- immediate byte-hashed export and node stop after terminal result.

## Budget and interpretation

Maximum one 1x H100 session at the locked `$0.0666/min` rate, with no more
than the platform 15-minute minimum. A second `pass:true` strengthens the
non-deterministic/non-reproducing finding. A `pass:false` with protected
accuracy `1.0` establishes recurrence but not a cause. Any infrastructure
failure is non-scientific and is retained separately.

Claim ceiling: `RemoteH100V41R30R2FailingCellSecondIndependentReplication`.

V41R27 remains terminal at census `30/48`, qualification `NotAssessed`.
Governance remains `tune_opened:false`, `assessment_opened:false`,
`production_actions:false`, `provider_direct_authority:false`.
