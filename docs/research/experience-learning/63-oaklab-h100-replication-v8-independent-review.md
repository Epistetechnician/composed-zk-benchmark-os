# Oak Lab H100 replication V8 independent review

State slice: `oaklab-experience-learning-h100-replication-v8`.

Decision: `ACCEPT`.

Verified:

- Canonical bytes and recursive nested contracts in the source/validator chain.
- Source, compiler, validator, tests, `AGENTS.md`, compiled protocol, and review packet bindings.
- Current campaign-manifest artifact binding and its self-digest.
- Execution-authorization loading of the actual campaign-manifest path from the provider plan.
- Provider allocation, cost, and stop cross-binding.
- Fit, tune, and prediction-lock ordering.
- USD equality and hard-ceiling binding.
- Counter-derived statistics and energy.
- Closed result-root validation.
- Historical lane isolation and assessment absence.

Required commands:

- `python -B -m experiments.experience_learning.compile_oaklab_h100_v8_protocol --repo-root . --output experiments/experience_learning/oaklab_h100_v8_compiled_protocol.json`
- `python -B -m experiments.experience_learning.validate_oaklab_h100_v8_protocol`
- `python -B -m pytest experiments/experience_learning/tests/test_oaklab_h100_v8_protocol.py -q`

Results:

- Compile: `ab155479773b16f6bf9661837c54a78ef652c393107d304049abb41f73542fc4`
- Validate: `valid: true`
- Pytest: `11 passed`

