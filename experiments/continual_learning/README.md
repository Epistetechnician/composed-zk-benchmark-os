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

The latest signed task/update pilot is documented in
`docs/research/continual-learning/23-v11-execution-record.md`. Its outputs
must stay outside the repository because adapter weights and raw run logs are
generated artifacts, not source fixtures.
