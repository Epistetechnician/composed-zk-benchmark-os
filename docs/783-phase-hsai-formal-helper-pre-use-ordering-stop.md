# Phase 783 HSAI Formal Helper Pre-Use Ordering Stop

## Status

Stopped documentation-only after source correspondence exposed an unresolved
pre-use operation-order conflict.

State slice: `phase-783-hsai-formal-helper-pre-use-ordering-stop`.

Classification: `HelperPreUseOrderingConflict`.

Execution status: `StoppedDocumentationOnly`. Evidence ceiling:
`Level1LocalReplayOrLower`.

## Verdict

Phase 783 cannot honestly resolve Phase 780 lane `L04`.

The ordered Phase 749 helper and focused-test sets are known, and deterministic
Python argv candidates can be written. The inherited sources do not permit
those candidates to become accepted successor-ledger contracts because three
required helper-hash child producers are absent from the immutable Phase 778
operation order.

Historical Phase 779 JSONL remains unchanged. All 1,469 historical blocker
objects and all 102 blocked rows remain; no source-ledger digest exists. Lane
`L04` remains open, so the ordered closure program may not advance to `L05`.

## Exact Ordering Conflict

The controlling requirements are incompatible without an explicit
supersession:

1. Phase 759 requires three separate `shasum -a 256` child producers, each
   followed immediately by its own digest assertion, before helper compilation
   or focused tests.
2. Phase 771 requires one bounded operation per actual child invocation and
   prohibits hiding child processes inside an aggregate operation.
3. Phase 778 fixes ordinals 001 through 102 and its order digest. It proceeds
   directly from ordinal 006 `capture-detached-status` to ordinal 007
   `compile-helper-sources`, ordinal 008 `run-helper-tests`, and ordinal 009
   `run-raw-parser-self-test`.
4. Neither Phase 778 nor historical Phase 779 contains the three required
   helper-hash operations.

Adding the producers would change operation membership, cardinality, every
later affected ordinal, the Phase 778 order digest, and the Phase 779 row set.
Treating them as hidden children would violate Phase 771. Treating them as
pure in-process observations would require an explicit supersession of Phase
759. Phase 783 is authorized only to resolve helper compile/test argv order;
it cannot make any of those changes.

## Closed Candidate Sets

The helper candidate set is exactly the three Phase 749 implementation files,
in this order:

| Order | File | SHA-256 |
|---:|---|---|
| 1 | `tools/hsai-formal-preflight/bounded_runner.py` | `933c573a0820106df62b431db829668bf45a305b84a49a2d3bdcb6899b9b0198` |
| 2 | `tools/hsai-formal-preflight/raw_archive_validator.py` | `31fa2450fe7e3ce87c13dd844ac6fde1cde0a4a81e7d351276e5dd2a4ba32692` |
| 3 | `tools/hsai-formal-preflight/fixture_validator.py` | `75a0e13aa06123b7bcc7ffd8d1f13bed9d318eb89f9e378e7c7ab6ff5bdd4c07` |

The focused-test candidate set is exactly the three Phase 749 test files, in
matching helper order:

| Order | Module | File | SHA-256 |
|---:|---|---|---|
| 1 | `test_bounded_runner` | `tools/hsai-formal-preflight/tests/test_bounded_runner.py` | `9c392c9b6b0804eeed730c03f35743176bc51e9953c6496f8888c32d7bc46e6a` |
| 2 | `test_raw_archive_validator` | `tools/hsai-formal-preflight/tests/test_raw_archive_validator.py` | `48e15976ba9a1dcbb86e1d5adc400a41dba328ebea1f156c5f0469e6a9ebdc77` |
| 3 | `test_fixture_validator` | `tools/hsai-formal-preflight/tests/test_fixture_validator.py` | `c6ec9bcd6e79d823e2cd2f4c7ea16c6f1cce908e6195606290efb42fbb2122c1` |

`execution_state_machine.py` and `test_execution_state_machine.py` are later
Phase 766 files. They are not members of either Phase 749 set and may not be
added by discovery, directory contents, naming convention, or convenience.

Only the three helper-source hashes have the explicit Phase 759 pre-use child
producer mandate. Phase 780's `L04` exit language requires hashes accepted
before use but does not say whether the three test-file hashes require separate
producers, typed in-process acceptance, or another already ordered gate. That
identity-acceptance ambiguity is also unresolved.

## Non-Accepted Argv Candidates

The inherited Phase 749 validation shape yields this compile candidate:

```json
["/usr/bin/python3","-m","py_compile","tools/hsai-formal-preflight/bounded_runner.py","tools/hsai-formal-preflight/raw_archive_validator.py","tools/hsai-formal-preflight/fixture_validator.py"]
```

It is not accepted. Python 3.9 documents that `py_compile` writes `.pyc` cache
files. Phase 749 reports that no bytecode was retained, but the current
102-operation contract has no typed bytecode output, placement rule, or
pre-test cleanup operation. Replacing `py_compile` with an inline built-in
`compile()` program would avoid bytecode output, but that is a new semantic
decision rather than source normalization. Output inventory and cleanup are
outside `L04`.

The explicit focused-test candidate is:

```json
["/usr/bin/python3","-m","unittest","tools/hsai-formal-preflight/tests/test_bounded_runner.py","tools/hsai-formal-preflight/tests/test_raw_archive_validator.py","tools/hsai-formal-preflight/tests/test_fixture_validator.py"]
```

It names all three test files and does not use unittest discovery. It is not
accepted because the required pre-use identity path and the predecessor
operation sequence remain unresolved. The committed tests may import exactly
named helper modules; the Phase 780 prohibition must mean no module-set or
filesystem discovery, not a literal ban on imports performed by the tests.

Neither candidate resolves cwd, replacement environment, bounds, transcripts,
typed artifacts, outcomes, acceptance operation, placeholders, or literal
`/usr/bin/python3` machine identity. Those fields remain `L09` and `L11` work.

## Required Route Correction

The next documentation-only correction must precede native transcript work.
It must:

1. reconcile Phase 759's three child producers with Phase 771's one-child-per-
   operation rule and Phase 778's 102-operation order;
2. publish an explicit supersession or a revised operation membership,
   cardinality, order, and order digest;
3. freeze whether all six Phase 749 files require pre-use identity acceptance
   and how that acceptance maps to ordinary operations;
4. resolve the `py_compile` bytecode output and cleanup conflict without
   inventing undeclared mutable output; and
5. publish a corrected closure-lane schedule before `L04` resumes.

Phase 784's previously assigned `L05` native-transcript work is deferred. A
future phase number may not be assumed from the stale Phase 780 schedule. No
later lane may proceed until the route correction explicitly reauthorizes it.

## Source Correspondence

| Conflict or fact | Controlling source |
|---|---|
| Closed helper/test files, hashes, historical compile/test shape, 30-test result, and no retained bytecode | Phase 749 `Implemented Surface` and `Validation` |
| Three separate pre-use helper-hash child producers | Phase 759 helper-hash command closure |
| Separate raw-parser self-test after 30 focused tests | Phase 761 bounded self-test closure |
| One bounded operation per child invocation | Phase 771 `Plan-v2 Correspondence Rules` |
| Missing helper order and test argv | Phase 772 `Field Gaps By Producer Group`; Phase 773 `Helper and fixture preflight` |
| Fixed 102-operation order without helper-hash rows | Phase 778 `Corrected Ordinary Command Order` |
| `L04` hash-before-use exit gate | Phase 780 resolution matrix |
| `py_compile` cache output | [Python 3.9 py_compile](https://docs.python.org/3.9/library/py_compile.html), checked 2026-07-14 |
| Explicit unittest file-list behavior | [Python 3.9 unittest command line](https://docs.python.org/3.9/library/unittest.html#command-line-interface), checked 2026-07-14 |

## Claim Boundary

Phase 783 records a correspondence stop only. It does not resolve `L04`,
authorize `L05`, correct the operation order, change historical ledger rows,
or create an executable source ledger, source-ledger digest, plan-v2 object,
executor binding, machine identity, transcript, backend result, generated Lean,
retained kernel result, proof artifact, checker transcript, accepted evidence,
Level2+, score axis, semantic correctness, production readiness, SOTA,
breakthrough, full security, external audit, or action authority.
