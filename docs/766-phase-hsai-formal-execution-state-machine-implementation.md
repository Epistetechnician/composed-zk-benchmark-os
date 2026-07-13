# Phase 766 HSAI Formal Execution State Machine Implementation

## Status

Complete as a committed, hermetic execution-state implementation.

State slice: `phase-766-hsai-formal-execution-state-machine`.

Classification: `CanonicalFormalExecutionStateMachineImplemented`.

Execution status: `Succeeded` for compilation, 25 focused state-machine tests,
55 total formal-preflight tests, canonical CLI output, source hashing, and diff
hygiene; `NotRun` for network, Rustup, Charon, Aeneas, Lean, Cargo, Lake,
sandbox controls, backend extraction, generated source, and kernel checking.
Evidence ceiling: `Level1LocalReplayOrLower`.

## Implemented Surface

| File | SHA-256 |
|---|---|
| `tools/hsai-formal-preflight/execution_state_machine.py` | `9bb9d287fef5a3409e8e101dc0867e479c1a1cbb53281b57b165833596635122` |
| `tools/hsai-formal-preflight/tests/test_execution_state_machine.py` | `e1e201f9917b926fea429f87b6f0948aef5b6982853c3b8ad0008c3e6dd9c8e5` |

The module provides:

- a twelve-stage immutable registry from primary preservation through cleanup;
- stable stage ordinals, predecessors, mutation owners, and network policies;
- immutable argv-array command specifications with environment, network, and
  output-collision validation;
- canonical duplicate-key-safe JSON for plans, state, snapshots, and errors;
- monotonic stage transitions and terminal first-failure recording;
- an injected producer executor that preserves argv identity and stops before
  invoking any command after the first failure;
- exact Git HEAD, NUL-delimited porcelain, and dirty regular-file digest
  snapshots for both clean and dirty primary checkouts; and
- CLI commands `plan-v1`, `snapshot-v1`, and `verify-snapshot-v1`.

The implementation prohibits shell executables, relative executables, unknown
environment keys, stage skipping, stage replay, duplicate command/result ids,
network-policy drift, output reuse, wrong producer-result identity, and
transition after failure or completion.

## Validation

Observed locally under `/usr/bin/python3`:

```text
py_compile: passed
execution-state-machine tests: 25 passed
all formal-preflight tests: 55 passed
plan-v1 canonical output: passed
git diff --check: passed
```

The tests use temporary Git repositories and fake producers only. They cover
clean and dirty primary snapshots, mutation detection, rename rejection,
canonical JSON, immutable argv preservation, all stage transitions, replay and
skip rejection, first-failure short-circuiting, producer exceptions, command
identity mismatch, network drift, environment rejection, and output collision.

## Next Boundary

Phase 767 must bind the exact inherited helper, parser, client, fixture, Rust,
Charon, Aeneas, Lean, Cargo, Lake, sandbox, extraction, and kernel command arrays
to this state machine and implement the bounded-runner producer adapter. It may
use fake producers only during implementation. A later attempt is prohibited
until that exact plan and adapter are committed and tested.

Phase 766 creates no backend result, proof, accepted evidence, Level2+, score
axis, semantic correctness, production readiness, SOTA, breakthrough,
full-security claim, external audit, or action authority.
