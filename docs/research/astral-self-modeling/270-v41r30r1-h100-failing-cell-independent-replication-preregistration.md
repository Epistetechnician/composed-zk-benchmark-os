# V41R30R1 H100 Failing-Cell Independent Replication Preregistration

State slice: `V41R30R1H100FailingCellIndependentReplication`.

V41R27R19 is terminal at census `30/48` after the frozen cell
`v41r27-panel-8-seed-412019` returned `pass:false` with protected accuracy
`1.0`. Its disk is irrecoverable. V41R28 and V41R29 established that the
failure is not reproduced by the executable local surrogate and that no local
substrate is qualification-viable.

This fresh identity measures whether the H100 failure is reproducible under the
same frozen runtime, model, tokenizer, logits, worker method, cell, and seed.
It is an independent diagnostic replication, not a continuation, retry, or
qualification campaign.

## Frozen bindings

- worker: `v41r27-panel-8-seed-412019`;
- frozen V41R27 worker runner and contract, with no source or threshold change;
- real H100 runtime, frozen `openai/gpt-oss-20b` revision and tokenizer;
- exactly one worker, exactly 256 optimizer steps, no adaptive stopping;
- protected accuracy, four case gates, reload exactness, and byte-hashed output;
- no substitution, tuning, assessment, census update, or qualification.

## Budget and stop rules

One 1x H100 node, clock-locked, maximum 20 billed minutes and `$1.332` at the
locked `$0.0666/min` rate. The node is stopped immediately after the worker
reaches a terminal result or an unrecoverable error. A terminal result is
exported before stopping; a snapshot is requested after stopping if the disk is
healthy. Any provider loss is recorded as infrastructure failure.

## Interpretation

- `pass:false` with protected accuracy `1.0` and the same failing case gate:
  independent replication of the acquisition failure;
- `pass:true`: the prior failure was not reproduced; no qualification claim;
- any other result: characterize the exact gate and retain the result;
- runtime/provider failure: no scientific conclusion.

Claim ceiling: `RemoteH100V41R30R1FailingCellIndependentReplication`.

This identity does not alter V41R27 census or qualification, and does not
support continual self-improvement, introspection, SOTA, production, or
breakthrough claims by itself.

Governance: `tune_opened:false`, `assessment_opened:false`,
`provider_direct_authority:false`, `production_actions:false`.
