# Phase 749 HSAI Gateway Threat Ordinal Canonical Helper Implementation

## Status

Complete as a committed, hermetic execution-helper implementation.

State slice:
`phase-749-hsai-gateway-threat-ordinal-canonical-helper-implementation`.

Classification: `CanonicalExecutionHelpersImplemented`.

Execution status: `Succeeded` for helper compilation, focused unit tests,
bounded-runner integration fixtures, raw-parser self-tests, canonical CLI help,
source hashing, and diff hygiene; `NotRun` for external archive validation,
network acquisition, Rust, Charon, Aeneas, Lean, Cargo, Lake, sandbox backend,
generated source, and kernel checking. Evidence ceiling:
`Level1LocalReplayOrLower`.

## Implemented Surface

Phase 749 adds only the Phase 748-authorized Python standard-library surface:

| File | SHA-256 |
|---|---|
| `tools/hsai-formal-preflight/bounded_runner.py` | `933c573a0820106df62b431db829668bf45a305b84a49a2d3bdcb6899b9b0198` |
| `tools/hsai-formal-preflight/raw_archive_validator.py` | `31fa2450fe7e3ce87c13dd844ac6fde1cde0a4a81e7d351276e5dd2a4ba32692` |
| `tools/hsai-formal-preflight/fixture_validator.py` | `75a0e13aa06123b7bcc7ffd8d1f13bed9d318eb89f9e378e7c7ab6ff5bdd4c07` |
| `tools/hsai-formal-preflight/tests/test_bounded_runner.py` | `9c392c9b6b0804eeed730c03f35743176bc51e9953c6496f8888c32d7bc46e6a` |
| `tools/hsai-formal-preflight/tests/test_raw_archive_validator.py` | `48e15976ba9a1dcbb86e1d5adc400a41dba328ebea1f156c5f0469e6a9ebdc77` |
| `tools/hsai-formal-preflight/tests/test_fixture_validator.py` | `c6ec9bcd6e79d823e2cd2f4c7ea16c6f1cce908e6195606290efb42fbb2122c1` |

The bounded runner exposes only `run-v1`, reserves three distinct mode-`0600`
regular output files, records canonical schema
`hsai-bounded-runner-status-v1`, reads both streams concurrently, retains exact
caps, and terminates the complete process group.

The raw validator exposes only `self-test` and `validate`. It performs a strict
streaming raw-header pass, duplicate-safe PAX parsing, GNU-name handling,
direct member-type checks, path/root/collision/ancestor checks, stable
descriptor checks, the Phase 741 structural inventory algorithm, a Python
`tarfile` cross-check with pre-normalization raw metadata, exact Phase 742
profile comparison, and embedded Lean-asset byte equality.

The raw self-test emits schema `hsai-raw-archive-self-test-v1` and measured:

```text
passed = 31
failed = 0
```

The fixture validator consumes canonical duplicate-key-safe JSON and validates
the exact four Phase 732 runner fixtures, including grandchild death and exact
1,024-byte flood retention.

## Validation

Observed locally under host `/usr/bin/python3` 3.9.6:

```text
python3 -m py_compile: passed for all three helpers
python3 -m unittest discover: 30 passed, 0 failed
raw_archive_validator.py self-test: 31 passed, 0 failed
all three top-level CLI help commands: passed
git diff --check: passed
```

No bytecode, dependency file, package manager state, shell wrapper, external
asset, generated archive, binary fixture, transcript, or machine path is
retained.

## Phase 750 Handoff

After this implementation is committed and independently validated from a
clean detached worktree, Phase 750 may make one full attempt. Its canonical run
root is `hsai-phase750-efa3782c`, detached repository root is
`hsai-phase750-repo-efa3782c`, and witness is
`phase750ExtractedThreatOrdinalWitnesses`.

Phase 750 inherits the Phase 744 sequence with these controlling corrections:

1. Stage 2 executes the three committed helpers only after verifying the exact
   Phase 749 source hashes; it does not materialize or rewrite them.
2. The loopback listener is materialized exactly once in Stage 13 from the
   exact Phase 732 bytes, after all acquisition and immediately before sandbox
   controls.
3. Helper status, self-test, fixture, and archive acceptance parsers remain
   standalone top-level commands with direct failure propagation.

The first failed gate stops Phase 750 without helper edits or replay.

## Claims

Phase 749 creates reusable local preflight tooling and regression evidence only.
It creates no external archive-validation result, backend result, generated
Lean source, kernel result, proof, accepted evidence, Level2+, score axis,
semantic correctness, production readiness, SOTA, breakthrough, full-security
claim, external audit, or action authority.
