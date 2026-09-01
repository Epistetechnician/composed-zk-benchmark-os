# TimesFM3 Sidecar V1 Validation

State slice: `timesfm3-temporal-stress-scenarios-v1`.

The hermetic suite at
`tools/timesfm3-temporal-stress-scenarios-v1/tests/test_sidecar_v1.py` covers:

- canonical request, result, and scenario round trips;
- duplicate and unknown JSON fields;
- absolute/traversal artifact references;
- input, model, configuration, runtime, output, and manifest digest binding;
- nonfinite input and output values;
- context, horizon, series, covariate, and artifact bounds;
- timestamp ordering and covariate alignment/future span;
- quantile shape, ordering, and point/q50 agreement;
- explicit `completed`, `inconclusive`, `invalid`, and `resource_limited`
  status behavior;
- same-device fake repeatability;
- deterministic q10/q50/q90 scenario bytes;
- fixed benchmark-case binding and synthetic-input labeling;
- claim-text, backend-outcome, and post-lock assessment-field rejection;
- the CLI's fake-only behavior and real-execution refusal;
- strict JSON shape for all three machine-readable schemas.

The test suite does not load the 1.3 GB checkpoint, access the network, run a
benchmark, invoke a backend, import evidence, or write an accepted ledger
entry. The real checkpoint qualification command remains a later gated action
after independent review of the frozen contract.
