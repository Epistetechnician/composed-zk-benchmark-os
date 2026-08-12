# Continual-learning protocol harness

`benchmark.py` is a deterministic, leakage-controlled setup benchmark. It
separates:

- acquisition after one update with source context removed;
- retention after three interfering task updates;
- recovery after explicit reacquisition;
- a context-only leakage control; and
- bounded replay, sequential-update, and persistent-retrieval controls.

Run the hermetic tests with:

```text
python -m pytest -q experiments/continual_learning/tests
```

Run the protocol into an external artifact directory:

```text
python experiments/continual_learning/benchmark.py --output /tmp/continual-learning-v1
```

This harness validates endpoint definitions and control behavior. It is not a
neural-training result and cannot support breakthrough, transfer, production,
or general continual-learning claims.

The latest signed task/update protocol is documented in
`docs/research/continual-learning/47-v23-task-routed-replay-consolidation-record.md`.
Its one corrected local preflight is recorded in
`docs/research/continual-learning/48-v23-corrected-replay-preflight-record.md`.
The next preregistered protocol is
`docs/research/continual-learning/49-v24-shared-adapter-task-keyed-optimizer-state-protocol.md`.
Its pure-data record is
`docs/research/continual-learning/50-v24-shared-adapter-task-keyed-optimizer-state-record.md`.
Its corrected local preflight is recorded in
`docs/research/continual-learning/51-v24-corrected-shared-adapter-preflight-record.md`.
The next acquisition-repair protocol is
`docs/research/continual-learning/52-v25-shared-adapter-reference-initialization-protocol.md`.
Its pure-data record is
`docs/research/continual-learning/53-v25-shared-adapter-reference-initialization-record.md`.

V25 corrected local preflight result and rejection:

`docs/research/continual-learning/54-v25-shared-adapter-reference-initialization-preflight-record.md`.
V26 shared-global-update-stream protocol:

`docs/research/continual-learning/55-v26-shared-global-update-stream-protocol.md`.

V26 corrected local preflight candidate:

`docs/research/continual-learning/56-v26-shared-global-update-stream-preflight-record.md`.
V27 bounded replication protocol:

`docs/research/continual-learning/57-v27-shared-global-update-stream-replication-protocol.md`.

V27 replication record:

`docs/research/continual-learning/58-v27-shared-global-update-stream-replication-record.md`.
V28 task-stratified microbatch protocol:

`docs/research/continual-learning/59-v28-task-stratified-microbatch-protocol.md`.

V28 corrected local preflight record:

`docs/research/continual-learning/60-v28-task-stratified-microbatch-preflight-record.md`.
Outputs must stay outside the repository because adapter weights and raw run
logs are generated artifacts, not source fixtures.
