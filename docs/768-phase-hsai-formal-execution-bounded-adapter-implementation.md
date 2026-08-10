# Phase 768 HSAI Formal Execution Bounded Adapter Implementation

## Status

Complete as a committed, hermetic producer-adapter implementation.

State slice: `phase-768-hsai-formal-execution-bounded-adapter`.

Classification: `CanonicalBoundedProducerAdapterImplemented`.

Execution status: `Succeeded` for compilation, 36 focused state-machine and
adapter tests, 66 total formal-preflight tests, source hashing, and diff
hygiene; `NotRun` for network, Rustup, Charon, Aeneas, Lean, Cargo, Lake,
sandbox controls, backend extraction, generated source, and kernel checking.
Evidence ceiling: `Level1LocalReplayOrLower`.

## Implemented Surface

| File | SHA-256 |
|---|---|
| `tools/hsai-formal-preflight/execution_state_machine.py` | `709aca15cd3746721f73dbb7f7a9b5b33f222eb4e22abd17caf1662b8a641d0e` |
| `tools/hsai-formal-preflight/tests/test_execution_state_machine.py` | `80353226bc20f7f1326a33e471d6cdad2c715d14f4f6045f5e407675f2395cce` |

`CommandSpec` now binds canonical cwd, command role, finite positive timeout,
positive stdout/stderr caps, three distinct absolute output paths, and exact
expected reason/return-code/signal. Generic shell executables remain rejected.
Only the two byte-exact Phase 732 shell fixtures are accepted under role
`exact-process-fixture`, their exact stage/network policy, bounds, outcomes,
and SIGTERM identity.

`BoundedRunnerAdapter` invokes the committed bounded runner as an argv array
with explicit cwd, null stdin, and only plan-allowlisted environment entries.
It rejects pre-existing outputs, runner invocation failure, non-regular or
symlink outputs, noncanonical or duplicate-key status JSON, status shape/schema
drift, child argv drift, reason/return/signal drift, cap drift, byte-count drift,
and retained-stream size drift. Every rejection maps directly to one terminal
`CommandResult` failure code.

macOS may inject `__CF_USER_TEXT_ENCODING` below `subprocess.run`; tests verify
that the adapter itself supplies only the declared allowlisted environment and
does not authorize that OS-injected key in a plan.

## Validation

```text
py_compile: passed
focused execution-state/adapter tests: 36 passed
all formal-preflight tests: 66 passed
git diff --check: passed
```

Hermetic adapter tests cover normal exit, expected nonzero exit, timeout,
stdout limit, stderr limit, exact and near-match shell fixtures, environment
replacement, output reuse, status argv drift, cwd rejection, and terminal
first-failure behavior. They use no network or formal backend.

## Next Boundary

Phase 769 must bind every inherited helper, parser, client, fixture, Rust,
Charon, Aeneas, Lean, Cargo, Lake, sandbox, extraction, and kernel command to
typed `CommandSpec` values. It must publish a canonical plan digest and prove
with fake producers that every stage and command is reachable exactly once and
that failure at every command prevents all successors. No live attempt is
authorized until that complete plan is committed and validated.

Phase 768 creates no backend result, proof, accepted evidence, Level2+, score
axis, semantic correctness, production readiness, SOTA, breakthrough,
full-security claim, external audit, or action authority.
