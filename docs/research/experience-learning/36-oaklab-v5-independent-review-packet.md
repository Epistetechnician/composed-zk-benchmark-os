# Oak Lab V5 independent protocol review packet

State slice: `oaklab-experience-learning-constrained-update-policy-v5`

Review status: `pending`

Review authorization: no V5 learner implementation, fit, tune, assessment,
real-stream, or energy execution is authorized by this packet. The reviewer
must inspect the exact bytes and issue a separate signed decision.

## Frozen inputs

The following files are the complete review input. SHA-256 values are over the
repository bytes at packet creation:

| file | SHA-256 |
|---|---|
| `AGENTS.md` | `7068251ae9ecfea8bebc99499a1842447dcc87a200f9ab2548d00d7d2d93f4ff` |
| `experiments/experience_learning/v5_protocol_spec.json` | `ac02dca181feea32b1e9547e381c94c9399f3a34c4bc0ac3df2ed9095b0c813c` |
| `experiments/experience_learning/compile_v5_protocol.py` | `82a5075a1c39c629ec4b5d169d1d4c171f1a5de7fff791e5b2734538e5e211ad` |
| `experiments/experience_learning/validate_v5_protocol_compilation.py` | `b4ab7e542a4665de2e2cc6837fe828cea65304ab593d534862b0487b996f9c22` |
| `experiments/experience_learning/v5_compiled_protocol.json` | `9be25c99303912b695e025f97da02a5ccd7459896855d24eb9c9ea9e54e188d3` |
| `experiments/experience_learning/tests/test_v5_protocol_compiler.py` | `f3d4d46c2b530491691d5abfc4203fc46a6fb8bcfa0386b20452097a49b509eb` |
| `docs/research/experience-learning/35-oaklab-v5-protocol-compiler.md` | `58478e30f6441c0c783b97ef514c58731f0eef0231813c7d2aaa9dddac1142ae` |

Compiled protocol digest: `d3d677cff22f9a4587ed204cb0c182a71ac85db6009e2db2200fbc77306e3117`.

Source-spec digest: `ac02dca181feea32b1e9547e381c94c9399f3a34c4bc0ac3df2ed9095b0c813c`.

## Reproduction commands

Run from the repository root with the repository package context:

```text
python -B -m experiments.experience_learning.compile_v5_protocol \
  experiments/experience_learning/v5_protocol_spec.json \
  --check experiments/experience_learning/v5_compiled_protocol.json

python -B -m experiments.experience_learning.validate_v5_protocol_compilation \
  experiments/experience_learning/v5_protocol_spec.json \
  experiments/experience_learning/v5_compiled_protocol.json \
  --repo-root .

PYTHONDONTWRITEBYTECODE=1 PYTHONOPTIMIZE=0 PYTEST_ADDOPTS= \
PYTEST_PLUGINS= PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -B -m pytest -q \
  experiments/experience_learning/tests/test_v5_protocol_compiler.py
```

Observed results: five compiler tests passed; compiler `--check` returned
`valid`; the independent validator returned `valid` with
`assessment_materialization_state=absent` and
`decision=pending_independent_review`.

## Required independent checks

The reviewer must recompute source bytes, source digest, all seven section
digests, compiled digest, and the PRNG/action test vector independently. The
review must verify that every transition index and pending field is explicit;
all generator draws are unconditional and ordered; formulas have typed ASTs
and byte layouts; ablation participation and Holm groups are fixed; adaptation
windows cannot cross a shift; and lock, counter, control, validator, and
assessment-absence schemas are closed-world and digest-bound.

The reviewer must also verify the negative capability: no V5 learner, runner,
assessment, real campaign, energy, Astral, or plasticity-guard execution is
present or imported. The complete-policy estimand may survive, but V4 source,
receipts, and results cannot be scientific inputs.

## Decision schema

The independent decision must be either `ACCEPT` or `REJECT`, bind every frozen
input hash above plus the compiled protocol digest, enumerate any rejection
codes, and set `implementation_authorized` to `true` only for `ACCEPT`. Any
hash drift, missing field, ambiguous formula, stale packet, or hidden runtime
capability is a fail-closed `REJECT`. A rejection closes V5 without retuning.
