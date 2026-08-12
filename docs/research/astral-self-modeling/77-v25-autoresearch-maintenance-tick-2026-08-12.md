# V25 bounded Astral maintenance tick — 2026-08-12 (tokenizers ABI guard)

State slice: `astral-telemetry-information-presence-v25`.

## Snapshot and measurable question

The initial snapshot command was:

```text
git status --short --untracked-files=all && git branch --show-current && git show --stat --oneline HEAD
```

It reported branch `master`, HEAD `492494f0 docs(astral-v25): record lock manifest audit`, no staged or modified tracked paths, and pre-existing untracked generated paths under `experiments/**/__pycache__/`, `tools/**/__pycache__/`, `fsm_result.json`, and `output/**`. Those paths were not modified, staged, or adopted.

Measurable question: does the repository-owned offline runner reject a cached `tokenizers` archive that has Python package metadata but lacks its required native `tokenizers.abi3.so` extension, while retaining the existing CPython-3.13 compatibility selection behavior?

## Inspection, implementation, and disposition

Inspection of `run_canonical_suite.py` found ABI-specific native markers for NumPy and regex, but `tokenizers` was accepted using only `tokenizers/__init__.py`. The runner could therefore select an unusable cached tokenizers archive before the canonical preflight. The bounded improvement adds the ABI-independent `tokenizers/tokenizers.abi3.so` marker to the existing local archive discovery and adds one hermetic rejection test. No production protocol, model, concept, configuration, assessment, or artifact data was changed.

The first validation attempt exposed a fixture defect: the shared fake archive helper did not provide the new native marker, and the existing missing-MLX test consequently failed earlier with `missing cached tokenizers`. The fixture helper was corrected to model the real package shape; the targeted new test then removed that marker and verified the intended failure. This was a test-only correction, not a change in the runtime conclusion.

No network, installation, download, model execution, training, adaptive tuning, assessment rerun, retuning, or V19/V22–V25 data, concepts, or configuration reuse occurred. The V19 record and accepted Evidence Ledger were untouched. Pre-existing untracked generated paths remain a cleanliness blocker and were preserved.

## Validation

Whitespace check and canonical offline runner:

```text
git diff --check
```

Result: passed with no output.

```text
python3 tools/astral-telemetry-probe-v25/run_canonical_suite.py
```

Actual final output:

```text
mlx=/Users/shaanp/.cache/uv/archive-v0/DD4lPkGabhq7gIuUlQUdL/mlx/core.cpython-313-darwin.so mlx_lm=/Users/shaanp/.cache/uv/archive-v0/oDCUdaF3CoZQZwAVwTpox/mlx_lm/__init__.py
........................................................................ [ 56%]
.......................................................                  [100%]
127 passed in 1.01s
```

The runner selected cached local CPython 3.13 MLX artifacts and reported the actual suite result. No fixed test count was substituted.

## Result and claim boundary

Kept the runner guard, hermetic test, and this additive phase note. The improvement is limited to fail-closed cached-package discovery. It produces no scientific result or accepted evidence.

Commit: recorded after validation as a small isolated checkpoint; the final report names the resulting commit and post-commit status.

Claim ceiling remains `LocalDevelopmentPrivilegedTelemetryInformationPresence`; this tick makes no accepted-evidence, benchmark, Stage 0C, Stage 1, introspection, consciousness, SOTA, breakthrough, or generalization claim.
