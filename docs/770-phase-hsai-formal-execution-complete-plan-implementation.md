# Phase 770 HSAI Formal Execution Complete Plan Implementation

## Status

Complete as a committed, hermetic operation-plan implementation.

State slice: `phase-770-hsai-formal-execution-complete-plan`.

Classification: `CompleteFormalOperationPlanImplemented`.

Execution status: `Succeeded` for compilation, 53 focused state-machine tests,
83 total formal-preflight tests, canonical plan construction, plan hashing, and
diff hygiene; `NotRun` for network, Rustup, Charon, Aeneas, Lean, Cargo, Lake,
sandbox controls, backend extraction, generated source, kernel checking, SMT,
and COBALT. Evidence ceiling: `Level1LocalReplayOrLower`.

## Immutable Identity

| Artifact | SHA-256 |
|---|---|
| canonical 65-operation plan | `1644a895733d769fbe89795cc3fc7d4886d71b03c8c28b9f1866f5a075a1db14` |
| `tools/hsai-formal-preflight/execution_state_machine.py` | `1e264172d5f77580328456162a085b4b99bb0c9b15aa7abcdd51e8977b5a030f` |
| `tools/hsai-formal-preflight/tests/test_execution_state_machine.py` | `de805bfb3ca08856dd2a13e2759686b24031d0aa82ff39ce888434e570aa81c6` |

The canonical plan contains 21 internal assertions, 7 atomic
materializations, 35 bounded producers, 1 persistent loopback control, and 1
cleanup-and-verify operation. It contains no machine-specific root and no
shell text.

## Implemented Surface

`OperationSpec` binds a stable operation id, stage, immediate predecessor,
stage-owned mutation slice, stage network policy, closed operation kind, and an
exact kind-specific payload. Validation rejects unknown kinds, unknown stages,
owner or network drift, duplicate payload keys, payload shape drift, hidden
shell text, noncanonical contract references, materialization-target drift,
bounded-command identity drift, loopback identity or argv drift, and cleanup
contract drift.

`CompleteOperationPlan` rejects duplicate ids, predecessor gaps, stage-order
drift, empty stages, early cleanup, and missing final cleanup. Canonical JSON
serialization and SHA-256 make the path-normalized operation contract
reproducible.

`OperationAttemptState` makes every ordinary operation reachable exactly once
in predecessor order. The first failure blocks every normal successor and
routes directly to the final cleanup-and-primary-verification operation.
Cleanup success after a prior failure yields `failed-cleaned`; cleanup failure
yields `cleanup-failed`; normal completion yields `complete`. Terminal replay
or post-terminal transition is rejected.

## Operation Inventory

| Stage | Count | Operations |
|---|---:|---|
| `primary-preservation` | 2 | `snapshot-primary`, `create-owned-roots` |
| `frozen-identities` | 2 | `verify-frozen-repository`, `verify-helper-identities` |
| `helper-self-tests` | 4 | `compile-helper-sources`, `run-helper-tests`, `run-raw-parser-self-test`, `accept-raw-parser-self-test` |
| `client-and-fixtures` | 6 | `materialize-client-metadata`, `fixture-normal-exit`, `fixture-process-timeout`, `fixture-stdout-limit`, `fixture-stderr-limit`, `validate-process-fixtures` |
| `rust-acquisition` | 5 | `download-rust-manifest`, `verify-rust-manifest`, `install-rust-toolchain`, `capture-rust-identities`, `accept-rust-identities` |
| `charon-source` | 9 | `initialize-charon-source`, `fetch-charon-source`, `checkout-charon-source`, `assert-charon-head`, `assert-charon-status`, `assert-charon-paths`, `hash-charon-paths`, `assert-charon-license-absence`, `assert-charon-stability` |
| `aeneas-assets` | 4 | `download-aeneas-main`, `download-aeneas-lean`, `verify-aeneas-assets`, `validate-aeneas-archives` |
| `archive-equivalence` | 4 | `extract-aeneas-main`, `extract-aeneas-lean-staging`, `assert-lean-tree-equivalence`, `remove-lean-staging` |
| `lean-acquisition` | 4 | `download-lean`, `verify-lean-archive`, `extract-lean`, `accept-lean-identities` |
| `dependency-freeze` | 5 | `compile-rustc-private-probe`, `fetch-charon-dependencies`, `lake-update`, `lake-cache-get`, `freeze-dependencies` |
| `sandboxed-backends` | 18 | `materialize-sandbox-profile`, `materialize-loopback-listener`, `run-loopback-control`, `run-sandbox-controls`, `build-charon`, `verify-charon-binaries`, `freeze-checker-cargo-cache`, `extract-checker-llbc`, `pretty-print-checker-llbc`, `assert-single-ordinal-body`, `generate-aeneas-lean`, `assert-generated-source`, `materialize-rfl-witness`, `check-types-olean`, `check-funs-olean`, `check-witness-olean`, `lake-build`, `assert-final-freeze` |
| `retention-and-cleanup` | 2 | `retain-path-free-proof-slice`, `cleanup-and-verify-primary` |

## Validation

```text
py_compile: passed
focused execution-state tests: 53 passed
all formal-preflight tests: 83 passed
canonical operation-plan construction: passed
failure injection at every non-cleanup operation: passed
mandatory cleanup routing after every injected failure: passed
path and hidden-shell scans: passed
```

The tests use fake state transitions and local process fixtures only. They do
not perform acquisition or execute a formal backend.

## Remaining Execution Gate

The plan binds every inherited operation to a stable contract reference, but
it does not yet materialize all 35 bounded producers as exact `CommandSpec`
argv, environment, cwd, bounds, expected outcome, and output identities. It
also does not implement executors for atomic materialization, internal
assertions, persistent loopback lifetime, or cleanup.

Phase 771 must be documentation-first exact operation-to-executor
materialization. It must freeze each producer's argv and inputs, define the
non-producer executor interfaces, prove one-to-one plan coverage, and preserve
the Phase 770 plan digest or explicitly version it. A live backend attempt
remains prohibited until that executable coverage is committed and validated.

Phase 770 creates no backend result, proof artifact, checker transcript,
accepted evidence, Level2+, score axis, semantic correctness, production
readiness, SOTA, breakthrough, full-security claim, external audit, or action
authority.

Phase 771 subsequently found that several v1 operations aggregate independently
bounded inherited child commands and that stage network labels are too coarse
for executor capabilities. The v1 digest remains valid as a conceptual
inventory identity but is not an executable-plan identity. Phase 772 must
implement the versioned correspondence correction in
`docs/771-phase-hsai-formal-execution-correspondence-correction-boundary.md`
before executor materialization.
