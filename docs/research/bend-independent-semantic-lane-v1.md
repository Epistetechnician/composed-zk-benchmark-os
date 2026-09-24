# Bend Independent Semantic Lane V1

State slice: `bend-independent-semantic-lane-v1`

Protocol identity: `bend-independent-semantic-lane-v1`

Claim ceiling: `LocalBendCheckedSemanticOracleOnly`

## Purpose

This lane tests whether an implementation-diverse Bend evaluator can reproduce
the finite executable subset of the existing Rust `zkbench-core` Semantic IR
and local oracle. The purpose is differential testing of semantic lowering and
oracle behavior, not a new benchmark backend or a replacement for Lean.

The source of cases is the existing deterministic Rust generator. Cases cover
all nine implemented families and multiple deterministic seeds. Rust computes
the expected local outcome; Bend independently evaluates the exported machine
and trace. The two sides are compared through per-case outcome codes and a
canonical aggregate digest.

## Frozen boundary

The Bend subset contains:

- states and finite transition traces;
- nonnegative integer and boolean fields;
- boolean, equality, inequality, and integer order guards;
- conjunction, disjunction, and negation;
- assign, add-assign, subtract-assign, and no-op actions;
- initial-field overrides, invariants, final-state checks, and final-field checks.

Text-valued metadata and observation fields that are not reachable from the
executable machine or trace are outside the exported projection and are
omitted. A text value or unsupported construct reachable from an executable
guard, action, assignment, or expected result is rejected by the exporter.
Unsupported cases cannot silently become accepted or rejected Bend results.

Expected verdicts are control outputs from Rust, not Bend proof inputs. The
Bend laws prove general evaluator identities such as `Always` being true and a
no-op preserving fields. They do not treat Rust output as an axiom.

## End-to-end command

The focused command is:

```text
pnpm --ignore-workspace run verify:bend-independent-semantic-lane-v1
```

The command requires Bend `2.0.4`, runs with `BEND_NO_TELEMETRY=1`, exports a
fresh deterministic suite, checks Bend laws, builds a native binary, runs it
twice with one thread and once with four threads, compares exact per-case
outputs, and checks a bounded fork-join stress computation. Generated Bend
source, binaries, and reports live only in an external temporary directory.

The frozen execution record is [Bend Independent Semantic Lane V1 Execution](bend-independent-semantic-lane-v1-execution-2026-09-17.md).

## Meaning limits

Passing this lane is local differential-testing evidence only. It does not
prove the Rust exporter, the full Semantic IR, any ZK circuit, a backend
implementation, the correctness of the source specification, or any scientific
or production claim. Bend's host effects and unsafe escape hatches are outside
this lane. Bend is not introduced into the root heavy lint gate because its
compiler is an external evolving tool and its focused command is intentionally
explicit.

Every mutation in this phase names state slice
`bend-independent-semantic-lane-v1`.
