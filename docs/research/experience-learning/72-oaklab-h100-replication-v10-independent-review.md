# Oak Lab H100 replication V10 independent review

State slice: `oaklab-experience-learning-h100-replication-v10`.

Decision: `ACCEPT`.

Verified:

- Current packet, source, compiled artifact, and `AGENTS.md` digests match the frozen V10 bindings.
- Recursive closed schemas for the estimand, controller, generator roster, AST/byte algebra, locks, and execution schemas.
- Dual-budgeted segment-credit no-leakage rule: current segment is unread during action selection, and only the completed segment feeds the next decision.
- Charged controller storage, resource accounting, and replay exclusion.
- Generator draw order and segment boundaries.
- Raw-row statistics and caller-supplied-boolean rejection.
- Lock ordering, absence of assessment materialization, and prediction-lock-before-assessment.
- Provider, cost, stop, energy, and closed result-root bindings.
- Historical lane isolation.
- The repository gates: compile, validate, and pytest all passed.

Required commands:

- `python -B -m experiments.experience_learning.compile_oaklab_h100_v10_protocol --repo-root . --output experiments/experience_learning/oaklab_h100_v10_compiled_protocol.json`
- `python -B -m experiments.experience_learning.validate_oaklab_h100_v10_protocol`
- `python -B -m pytest experiments/experience_learning/tests/test_oaklab_h100_v10_protocol.py -q`

Results:

- Compile self-digest: `526aa01617aff46e83508d424fed347f9a36597614546d0e0a89300a70362bab`
- Compiled file digest: `985a48b044c325786b66c209187b6613c60d14516ea99ebe55a927dcb0cd2743`
- Campaign-manifest self-digest: `50c259fcf2c62818ca18a5b6a6cdb083b6d90d1ffa66e3bb99f7ce48c308a40c`
- Campaign-manifest artifact digest: `a89b6fb0f80fc315b291341d9f2be8f8612165823ca1ccd7e963c1355731f2b9`
- Validate: `valid: true`
- Pytest: `4 passed`

