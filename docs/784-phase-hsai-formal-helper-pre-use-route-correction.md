# Phase 784 HSAI Formal Helper Pre-Use Route Correction

## Status

Complete as a documentation-first helper pre-use route and argv correction.

State slice: `phase-784-hsai-formal-helper-pre-use-route-correction`.

Classification: `HelperPreUseRouteCorrected`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Resolution Verdict

Phase 784 resolves Phase 780 lane `L04` at the contract-input level for:

```text
007 compile-helper-sources
008 run-helper-tests
```

It does so without adding a child command, changing the Phase 778 operation
order, or weakening Phase 771's one-command-to-one-row rule. The correction:

1. narrowly supersedes Phase 759's three `shasum` child producers with typed,
   descriptor-relative, in-process SHA-256 acceptance over all six Phase 749
   helper and focused-test files;
2. replaces the bytecode-writing `py_compile` candidate with an exact
   no-bytecode built-in `compile()` argv;
3. freezes an explicit ordered three-module unittest argv with discovery
   disabled; and
4. clarifies that Phase 771 cardinality counts executor-submitted logical
   command argv, not descendants contained inside that command's bounded
   process group.

The 102 Phase 778 ordinary operation IDs and their order digest remain exact:

```text
490c30a8098214754d20e4025696e2e3c702df8d4f7114a611157653ea7a4464
```

Historical Phase 779 JSONL remains unchanged. All 1,469 historical blocker
objects and all 102 historical rows remain blocked; no source-ledger digest
exists. Lane `L04` is resolved, while `L05` through `L11` remain open.

## Narrow Phase 759 Supersession

Phase 759's three `shasum -a 256` producer requirement remains historical for
its Phase 760 attempt protocol. It is superseded only for the future successor
ledger and plan-v2 route.

The replacement is a closed, standard-library, in-process identity gate. This
is permitted by Phase 774's classification of frozen file hashes as pure
descriptor-relative observations and Phase 778's rule that pre-use acceptance
may consume descriptor-relative filesystem observations without spawning a
child.

The gate may not call `shasum`, Python, a shell, a helper, an executable
resolver, or any subprocess. It may not enumerate a directory, expand a glob,
discover files by imports or naming patterns, combine results into an untyped
string, or accept a path outside `${DETACHED_ROOT}`.

For each declared file, in declared order, it must:

1. resolve the fixed relative path beneath an already accepted detached-root
   directory descriptor;
2. reject every symlink component, non-regular final object, duplicate path,
   path escape, owner mismatch, replacement, or link count other than one;
3. open the file read-only with no-follow semantics;
4. record relative path, expected SHA-256, observed SHA-256, byte length,
   device, inode, and pre-read and post-read descriptor metadata;
5. require stable file identity and metadata across the complete read; and
6. compare the observed digest to the one immutable expected digest before
   closing the descriptor.

Any failed or ambiguous result stops before child launch. Expected paths and
digests are source-ledger inputs. Observed device, inode, size, metadata, and
digest receipts are attempt-specific machine observations and never enter the
immutable source-ledger digest.

The accepted detached root must have no competing writer, and mutation of the
six paths is prohibited from pre-use acceptance through child completion. The
same ordered set is reaccepted after each child before its result may be
accepted. Any post-use identity or digest drift fails the row even when the
child otherwise exits with the expected outcome.

All six files are accepted after ordinal 006 and before ordinal 007. All six
are independently reaccepted immediately before ordinal 008 because the tests
import the helpers. Every later Phase 749 helper consumer, including ordinal
009, must receive the same immediate typed pre-use acceptance during future
row expansion. That later per-consumer binding remains `L11` work.

## Closed Six-File Identity Set

The identity set and order are exact:

| Order | Role | Relative path | Expected SHA-256 |
|---:|---|---|---|
| 1 | helper | `tools/hsai-formal-preflight/bounded_runner.py` | `933c573a0820106df62b431db829668bf45a305b84a49a2d3bdcb6899b9b0198` |
| 2 | helper | `tools/hsai-formal-preflight/raw_archive_validator.py` | `31fa2450fe7e3ce87c13dd844ac6fde1cde0a4a81e7d351276e5dd2a4ba32692` |
| 3 | helper | `tools/hsai-formal-preflight/fixture_validator.py` | `75a0e13aa06123b7bcc7ffd8d1f13bed9d318eb89f9e378e7c7ab6ff5bdd4c07` |
| 4 | focused test | `tools/hsai-formal-preflight/tests/test_bounded_runner.py` | `9c392c9b6b0804eeed730c03f35743176bc51e9953c6496f8888c32d7bc46e6a` |
| 5 | focused test | `tools/hsai-formal-preflight/tests/test_raw_archive_validator.py` | `48e15976ba9a1dcbb86e1d5adc400a41dba328ebea1f156c5f0469e6a9ebdc77` |
| 6 | focused test | `tools/hsai-formal-preflight/tests/test_fixture_validator.py` | `c6ec9bcd6e79d823e2cd2f4c7ea16c6f1cce908e6195606290efb42fbb2122c1` |

Set equality is strict. Missing, extra, duplicate, reordered, renamed, or
digest-mismatched entries fail. Phase 766's `execution_state_machine.py` and
`test_execution_state_machine.py` remain excluded.

## Ordinal 007 Compile Argv

The exact ordered argv array is:

```json
["/usr/bin/python3","-B","-c","import sys\nfor source_path in sys.argv[1:]:\n    with open(source_path,\"rb\") as source:\n        compile(source.read(),source_path,\"exec\",0,True,0)","${DETACHED_ROOT}/tools/hsai-formal-preflight/bounded_runner.py","${DETACHED_ROOT}/tools/hsai-formal-preflight/raw_archive_validator.py","${DETACHED_ROOT}/tools/hsai-formal-preflight/fixture_validator.py"]
```

The inline program reads only the three explicit source arguments as bytes and
calls built-in `compile()` in `exec` mode with flags `0`,
`dont_inherit = True`, and optimization level `0`. It creates code objects in
memory but never calls `exec()` or `eval()`, imports a helper, executes helper
code, scans a directory, reads standard input, or writes an output file.

`-B` prevents imported interpreter support modules from creating bytecode
caches. Built-in `compile()` returns an in-memory code object; unlike
`py_compile`, it does not create a `.pyc` output. Ordinal 007 therefore has no
bytecode, `__pycache__`, generated-source, or other mutable output contract.

Changing the inline program token, source argument count, path, or order is an
argv mismatch. Cwd, environment, bounds, transcripts, outcome, typed artifact
bindings, acceptance operation, allowed-placeholder expansion, and literal
Python machine identity remain unresolved `L09`/`L11` fields.

## Ordinal 008 Focused-Test Argv

The exact ordered argv array is:

```json
["/usr/bin/python3","-B","-m","unittest","test_bounded_runner","test_raw_archive_validator","test_fixture_validator"]
```

The module-to-file mapping is exactly:

```text
test_bounded_runner          tools/hsai-formal-preflight/tests/test_bounded_runner.py
test_raw_archive_validator   tools/hsai-formal-preflight/tests/test_raw_archive_validator.py
test_fixture_validator       tools/hsai-formal-preflight/tests/test_fixture_validator.py
```

The future row-specific cwd must make exactly those three module names resolve
to those three committed files without a package prefix or `PYTHONPATH`.
Phase 784 does not resolve that `cwd_template`; Phase 791 must bind and validate
it as part of `L11` expansion.

The argv does not use bare `python -m unittest`, `discover`, `-s`, `-p`, a
directory argument, a glob, generated module names, classes, methods, or the
Phase 766 state-machine tests. `-B` prevents the explicit test and helper
imports from creating bytecode cache files. The accepted semantic result
remains exactly 30 passed and zero failed tests; its row-level transcript
grammar and acceptance binding remain `L11` work.

## Child-Cardinality Clarification

Phase 771's bounded-child rule counts each logical command argv submitted by
the executor to the bounded adapter. Each such argv requires exactly one
ordinary operation, one future `CommandSpec`, and three unique transcript
artifacts. An assertion or in-process acceptance may not launch such an argv.

Processes created by the submitted command inside its one bounded process
group are command behavior, not additional executor-submitted logical command
rows. They remain subject to the parent operation's timeout, stream caps,
process-group termination, reap, and retained transcript contract. This is
required by the existing bounded-runner design, the admitted timeout fixture,
the focused tests, and later tools such as Cargo that create descendants.

This clarification does not create a generic plan-level controller exception.
The controlled-loopback lifecycle remains the only operation allowed to manage
multiple independently submitted plan-level process argv concurrently. No
assertion, acceptance predicate, group label, or ordinary row may hide a
second executor submission.

## Deferred Fields And Non-Execution

Phase 784 resolves only the specialized `helper-file-order-unresolved`
blockers and their hash-before-use exit condition. It does not resolve:

```text
controlling_phase_and_anchor
cwd_template
replacement_environment
timeout_seconds
stdout_cap_bytes
stderr_cap_bytes
expected_reason
expected_return_code
expected_signal
typed_input_artifacts
typed_output_artifacts
acceptance_operation_id
allowed_placeholders
executable_roles and machine acceptance
```

Those values remain blocked for successor-ledger expansion. Phase 784 does not
implement the in-process identity gate, modify a helper or test, create an
attempt root, resolve `/usr/bin/python3`, or run either argv.

## Corrected Closure Schedule

This schedule supersedes only the stale phase assignments in Phase 780 and
later forward references. Lane definitions and exit criteria remain unchanged:

```text
784 route correction and L04 helper compile/test order closure
785 L05 native transcript grammar contract and fixtures
786 L06 Charon driver preflight argv contract
787 L07 archive inventory contracts
788 L08 mutable output inventory contracts
789 L09 immutable executable-role registry and machine-policy schema
790 L10 canonical JSONL serialization profile and conformance vectors
791 L11 row expansion tranche 001-038
792 L11 row expansion tranche 039-064
793 L11 row expansion tranche 065-102
794 independent whole-ledger audit and conditional digest publication
795 earliest possible plan-v2 boundary, only after Phase 794 success
```

Accordingly, historical forward references to Phase 787 for `M8`, Phase 788
for executable-role acceptance, Phase 789 for canonical JSONL, Phases 790-792
for row expansion, Phase 793 for whole-ledger audit, and Phase 794 for plan-v2
are each shifted by one phase. This section is the controlling forward
schedule; earlier phase documents remain historical records.

## Source Correspondence

| Contract fact | Controlling source |
|---|---|
| Six-file sets, hashes, 30-test result, and historical no-bytecode result | Phase 749 `Implemented Surface` and `Validation` |
| Historical three-`shasum` mechanism superseded for successor work | Phase 759 helper-hash command closure; Phase 783 ordering stop |
| Separate ordinal-009 raw-parser self-test | Phase 761 bounded self-test closure |
| One logical executor command per operation | Phase 771 `Bounded child rule` |
| Pure descriptor-relative file-hash acceptance | Phase 774 `Repository And Cleanup Resolution`; Phase 778 `Pre-Use Acceptance Order` |
| Exact ordinals 007 and 008, fixed 102-row order, and order digest | Phase 778 operation-order correction |
| `L04` set-equality and hash-before-use exit gate | Phase 780 resolution matrix |
| Built-in compile semantics | [Python 3.9 built-in functions](https://docs.python.org/3.9/library/functions.html#compile), checked 2026-07-14 |
| `-B` bytecode-cache behavior | [Python 3.9 command line](https://docs.python.org/3.9/using/cmdline.html#cmdoption-B), checked 2026-07-14 |
| Explicit unittest module-list behavior | [Python 3.9 unittest command line](https://docs.python.org/3.9/library/unittest.html#command-line-interface), checked 2026-07-14 |

## Phase 785 Gate

Phase 785 remains documentation-first. It may resolve only Phase 780 lane
`L05`: executable-version-bound `codesign`, `spctl`, and `otool` transcript
grammars, typed parser outputs, acceptance operation IDs, and immutable
positive and negative fixtures for the 21 native-audit rows. Missing,
duplicate, reordered, ambiguous, and extra semantic records must fail;
substring-only and return-code-only acceptance remain prohibited.

Phase 785 may not modify Python or Rust source, rewrite historical Phase 779
rows, create attempt roots, resolve machine observations, publish a
source-ledger digest, or run any helper, test, producer, network, Rustup,
Cargo, Charon, Aeneas, Lean, Lake, native audit, sandbox, SMT, Z3, COBALT, or
kernel command.

## Claim Boundary

Phase 784 creates route, pre-use-acceptance, argv, and schedule metadata only.
It is not an implemented identity gate, executable source ledger, source-ledger
digest, plan-v2 object, executor binding, machine identity, transcript,
backend result, generated Lean, retained kernel result, proof artifact,
checker transcript, accepted evidence, Level2+, score axis, semantic
correctness, production readiness, SOTA, breakthrough, full security,
external audit, or action authority.
