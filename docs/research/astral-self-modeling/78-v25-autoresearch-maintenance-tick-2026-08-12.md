# V25 bounded maintenance tick — exact-suite and MLX pair hardening

State slice: `astral-telemetry-information-presence-v25`.

## Question

Can the repository-owned offline runner guarantee that its advertised canonical
suite is the exact suite, and that the selected cached MLX Python extension is
paired with the matching cached Metal runtime?

## Finding and change

The runner previously accepted unknown command-line arguments and forwarded them
to pytest. That allowed `-k`, `--ignore`, or an extra test path to silently turn
the canonical command into a partial or different suite. The runner now rejects
extra arguments at the command-builder boundary and uses strict `argparse`
parsing at the CLI boundary.

The runner previously selected the first cached Metal library independently of the
selected MLX Python extension. The runner now reads local distribution metadata
without importing packages, requires exactly one MLX/Metal version match, and
fails closed when the pair is missing, ambiguous, or mismatched.

An independent review then found a second exact-suite bypass: ambient
`PYTEST_ADDOPTS` could inject `-k` and produce a green but partial run, while
`PYTEST_PLUGINS` and plugin autoload could alter collection. The runner now
removes those ambient controls and forces `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` for
both subprocesses.

Hermetic regressions cover both behaviors. No protocol, model, concept,
configuration, assessment, artifact, or Evidence Ledger data changed.

## TDD evidence

The new tests were first run red:

```text
2 failed, 4 passed in 0.05s
```

The failures demonstrated the pre-fix behaviors: mismatched MLX/Metal metadata
was accepted, and `-k` was forwarded. After the minimal implementation and
fixture correction:

```text
6 passed in 0.03s
```

The environment-isolation regression was then run red before its fix:

```text
2 failed, 5 passed in 0.03s
```

After the scrub and plugin-autoload hardening:

```text
7 passed in 0.02s
```

## Validation

```text
python3 -m compileall -q tools/astral-telemetry-probe-v25/run_canonical_suite.py tools/astral-telemetry-probe-v25/tests/test_canonical_suite_runner.py
git diff --check
```

Both passed with no output.

The repository-owned offline runner then selected the cached CPython 3.13 MLX
extension and its matching local Metal runtime and ran the exact suite:

```text
mlx=/Users/shaanp/.cache/uv/archive-v0/DD4lPkGabhq7gIuUlQUdL/mlx/core.cpython-313-darwin.so mlx_lm=/Users/shaanp/.cache/uv/archive-v0/oDCUdaF3CoZQZwAVwTpox/mlx_lm/__init__.py
150 passed in 1.05s
```

The same runner was also executed with hostile ambient values for
`PYTEST_ADDOPTS`, `PYTEST_PLUGINS`, and `PYTEST_DISABLE_PLUGIN_AUTOLOAD`; it
still ran the complete suite and reported `150 passed in 1.05s`, with no
deselected tests.

## Follow-up hardening

The independent review passed the previous checkpoint and identified two
non-blocking robustness improvements. The runner now validates the canonical
pytest command before launching the MLX preflight, so a direct caller supplying
extra arguments causes zero subprocesses. It also converts corrupt UTF-8
package metadata into a controlled `RuntimeError` rather than leaking a raw
`UnicodeDecodeError`.

Additional hermetic cases cover missing, malformed, duplicate, and multiple
matching MLX/Metal metadata layouts. The new regressions were run red before
implementation:

```text
2 failed, 10 passed in 0.07s
```

After the minimal boundary fixes:

```text
12 passed in 0.03s
```

The final runner result after this follow-up was:

```text
mlx=/Users/shaanp/.cache/uv/archive-v0/DD4lPkGabhq7gIuUlQUdL/mlx/core.cpython-313-darwin.so mlx_lm=/Users/shaanp/.cache/uv/archive-v0/oDCUdaF3CoZQZwAVwTpox/mlx_lm/__init__.py
155 passed in 0.96s
```

The delayed independent review also recommended a CLI-level regression for the
controlled malformed-metadata failure. The first fixture run was intentionally
red because it reached the earlier missing-native-library gate; after adding
the matching fixture runtime, the exact CLI assertion passed:

```text
1 passed in 0.06s
```

The complete focused runner test file then passed `13 passed in 0.07s`, and the
canonical runner passed `156 passed in 0.97s`. The CLI emitted exit code `2`, no
stdout, and the expected `offline canonical preflight blocked: ...` stderr.

## Optimization-environment follow-up

An additional delayed independent review found a confirmed false-green path:
an ambient `PYTHONOPTIMIZE=1` caused Python to strip test assertions while
pytest still returned success and warned that assertions were ignored. The
reproduction was observed directly:

```text
PYTHONOPTIMIZE=1 ... test_build_env_is_explicit_and_does_not_write_bytecode
1 passed, 1 warning
```

The runner now forces `PYTHONOPTIMIZE=0` in both child subprocesses. The new
regression was first red with a `KeyError: PYTHONOPTIMIZE`, then passed after
the minimal environment fix. Under hostile `PYTHONOPTIMIZE=1`,
`PYTEST_ADDOPTS`, `PYTEST_PLUGINS`, and plugin-autoload settings, the real
canonical runner completed:

```text
156 passed in 0.98s
```

No network, installation, download, model execution, training, adaptive tuning,
assessment rerun, retuning, or restricted V19/V22–V25 material reuse occurred.

## Boundary

This is local runtime reproducibility and regression evidence only. The claim
ceiling remains `LocalDevelopmentPrivilegedTelemetryInformationPresence`.
There is no accepted-evidence, benchmark, Stage 0C, Stage 1, introspection,
consciousness, SOTA, breakthrough, or generalization claim.
