# V31 Execution Record: Narrative–Mechanism Measurement Stress Test

State slice: `astral-narrative-mechanism-stress-test-v31`.

Status: `Executed / LocalDevelopmentSyntheticMeasurementStressTest`.

## Scope and authorization

This run follows the frozen matrix in
[V31](64-narrative-mechanism-stress-test-v31.md) and the user's explicit
request to continue the measurement-validity work end to end. It is a
repository-local pure-data test only. No model, provider, network, reasoning
trace, secret, PII, V25/V28/V29 artifact, new loss, Stage 0C, Stage 1, or
Evidence Ledger mutation was used.

## Execution

The test source was compiled and run independently as a pure-data confirmation.
The exact independent commands were:

```text
rustc --edition 2021 --test crates/zkbench-core/tests/astral_narrative_mechanism_stress_test_v31.rs -o /tmp/astral_narrative_mechanism_stress_test_v31
/tmp/astral_narrative_mechanism_stress_test_v31 --nocapture
```

Result: three tests passed; zero failed.

The focused V31 Cargo test, V30 regression test, repository claim-boundary
test, full `cargo test -p zkbench-core --quiet`, format check, and diff check
also passed. An earlier transient Cargo failure involving the unrelated
untracked `crates/zkbench-core/src/experiment.rs` path resolved in the dirty
checkout without mutation by this task.

## Result

- 36 total tasks;
- 24/24 clean/noisy linear tasks beat narrative, shuffled, zero, and fit-mean
  baselines;
- 24/24 linear tasks beat the narrative control;
- 7/12 interaction tasks failed the all-baseline gate and were retained;
- measured mechanism mean MSE `12.0833333333`;
- narrative mean MSE `25.9236111111`;
- shuffled mechanism mean MSE `51.1689814815`;
- zero mean MSE `37.4074074074`;
- fit-mean baseline mean MSE `34.8518518519`;
- measured MSE variance `305.2006172840`;
- exact actor oracle mean MSE `0.0`.

## Disposition

The synthetic stress-test gate passed. The result strengthens the local claim
that the scoring design distinguishes measured structure from narrative and
shuffle controls across a broader deterministic range. The interaction
failures demonstrate why the mechanism representation must declare its model
class and why aggregate wins cannot be promoted to general mechanistic truth.

Maximum defensible claim:
`LocalDevelopmentSyntheticMeasurementStressTest`.

This does not establish trained-model mechanism recovery, model-family
transfer, introspection, self-understanding, HSAI security, provider
cryptography, benchmark status, production readiness, consciousness, Stage
0C, or Stage 1. V25 and the repository claim ceiling remain unchanged.
