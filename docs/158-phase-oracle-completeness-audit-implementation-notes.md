# Phase 158 — Oracle Completeness Audit Implementation Notes

## Status

Implemented and tested.

## Purpose

The local oracle (`crate::dsl::oracle::evaluate_trace`) is explicitly a "v0
executable subset": it returns `OracleOutcome::CapabilityGap` for raw-text
guards/actions and for non-integer comparison operands. For the formal-hooks
and adversarial-mutation wedges to mean anything, the oracle's completeness
over the generated surface must be auditable. Phase 158 adds a static auditor
that walks a `SurfaceSpec` and reports which constructs the shipped oracle can
evaluate locally and which fall into capability gaps.

## Surface

`crates/zkbench-core/src/dsl/oracle_completeness.rs` adds:

- `OracleCompletenessLabel` (`Executable`, `RawTextCapabilityGap`,
  `NonExecutableOperandCapabilityGap`, `StructurallyIncapable`).
- `OracleCompletenessConstructKind` (`TransitionGuard`, `TransitionAction`,
  `InvariantGuard`, `LoopBound`).
- `OracleCompletenessConstruct` carrying kind, id, label, and detail.
- `OracleCompletenessAudit` carrying the construct vector plus
  `executable_count`, `capability_gap_count`, `structurally_incapable_count`,
  and `is_fully_executable`.
- `audit_oracle_completeness(surface: &SurfaceSpec) -> OracleCompletenessAudit`
  walking every transition guard, every transition action, every invariant
  guard, and every loop bound in declaration order.

The module re-exports through `crates/zkbench-core/src/dsl/mod.rs`,
`crates/zkbench-core/src/prelude.rs`, and `crates/zkbench-core/src/lib.rs`.

## Design Decisions

### Mirror the oracle's shipped static checks

The audit mirrors the shipped oracle's static raw-text and literal operand
checks on the generated surface. To keep that mirror bounded:

- Raw-text detection reuses the existing `GuardSpec::contains_raw_text` and
  `ActionSpec::contains_raw_text` helpers (the same helpers the oracle uses
  to decide it cannot evaluate a construct).
- Non-integer-operand detection mirrors the oracle's `compare_ints` behavior:
  a `Lt`/`Lte`/`Gt`/`Gte` guard with a non-integer literal operand
  (`Value::Bool` or `Value::Text`) is flagged
  `NonExecutableOperandCapabilityGap`. Field operands cannot be typed without
  the field declaration, so only literal mismatches are flagged statically.

### Declaration order

Constructs are emitted in declaration order: transitions first (guard then
actions), then invariants, then loops. This makes the audit deterministic and
the construct ids stable.

### `StructurallyIncapable` is reserved

The `StructurallyIncapable` variant exists for forward compatibility but no
shipped family produces it today. A dedicated test asserts no shipped family
produces a structurally incapable construct.

## Tests

`crates/zkbench-core/src/dsl/oracle_completeness.rs` carries inline unit tests
for empty machines, executable guards, raw-text guards, raw-text actions,
non-integer operands in comparisons, count consistency, and determinism.

`crates/zkbench-core/tests/phase_158_oracle_completeness.rs` carries 6
integration tests over actual generated instances:

- `BoundedCounterLoop` is fully executable.
- `NestedLoop` is fully executable.
- `GuardHeavyMachine` is fully executable.
- Audit counts are self-consistent for every shipped family.
- Audit is deterministic across runs.
- No shipped family produces a structurally incapable construct.

All 6 tests pass.

## Claim Boundary

The audit is local static analysis capped at `Level0DesignNote`. It is not
proof of oracle correctness, not benchmark evidence, not accepted evidence,
not formal evidence, not ZK backend performance evidence, not semantic
correctness, not global software-agent uniqueness, and not evidence that any
backend would produce any particular outcome. It only reports which generated
constructs the shipped oracle can evaluate locally.

## What This Does Not Do

- Does not change `evaluate_trace`, `OracleOutcome`, or any guard/action
  expression type.
- Does not change any DSL type or the generator.
- Does not mark any construct `StructurallyIncapable` in shipped families.
- Does not call any real backend.
- Does not produce Level2+ evidence or formal evidence.
