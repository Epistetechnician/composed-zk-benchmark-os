# Phase 158 — Oracle Completeness Audit Boundary Spec

## Status

Allowed, not yet implemented.

## Purpose

The local oracle (`crate::dsl::oracle::evaluate_trace`) is explicitly named a
"v0 executable subset" and returns `OracleOutcome::CapabilityGap` for raw-text
guards/actions and for non-integer comparison operands. For the formal-hooks
and adversarial-mutation wedges to mean anything, the oracle's completeness
over the generated surface must be auditable: which generated constructs fall
inside the executable subset, which fall outside, and which are structurally
incapable of evaluation.

This phase adds a static oracle-completeness auditor that walks a
`SurfaceSpec` and returns per-construct coverage labels. It does **not** change
the oracle. It exposes what the oracle can and cannot evaluate, so that
downstream mutation and formal phases can reason about gaps honestly.

## State Slice

This phase is limited to:

- Additive Rust source under `crates/zkbench-core/src/dsl/` introducing:
  - `OracleCompletenessLabel` enum (`Executable`, `RawTextCapabilityGap`,
    `NonExecutableOperandCapabilityGap`, `StructurallyIncapable`)
  - `OracleCompletenessConstruct` struct
  - `OracleCompletenessAudit` struct
  - `audit_oracle_completeness(surface: &SurfaceSpec) -> OracleCompletenessAudit`
- Re-exports from `crates/zkbench-core/src/dsl/mod.rs`,
  `crates/zkbench-core/src/prelude.rs`, and `crates/zkbench-core/src/lib.rs`.
- Additive integration tests under `crates/zkbench-core/tests/`.
- Phase notes under `docs/` and navigation updates under `README.md`,
  `docs/12-task-list.md`, `docs/90-whole-codebase-validation-report.md`, and
  `AGENTS.md`.

It does **not** permit:

- Changes to `evaluate_trace`, `OracleOutcome`, the oracle evaluation logic,
  or any guard/action expression type (`GuardSpec`, `GuardExpr`, `ActionSpec`,
  `OperandSpec`, `BinaryGuard`, `AssignAction`).
- Changes to `SurfaceSpec`, `MachineSpec`, `TransitionSpec`, `InvariantSpec`,
  `LoopSpec`, `ObserveSpec`, `TraceSpec`, or any other DSL type.
- Changes to mutation, scoring, evidence ledgers, accepted-ledger append,
  promotion preflight, official-submission package, external replay preflight,
  pack readiness, report bundle, audit index, local benchmark artifact, local
  artifact campaign, zk-Harness adapter, or any HSAI crate.
- New Cargo dependencies, `Cargo.toml`, or `Cargo.lock` changes.
- External execution, external repo clones, vendored source, network access,
  credentials, command-line tools, UI dashboards, browser apps, JavaScript or
  TypeScript runtime files, package runtime files, or committed generated
  benchmark artifact files.
- Level2+ evidence, formal evidence, accepted Evidence Ledger mutation,
  official benchmark submission, score-axis population, ZK backend performance
  claims, SOTA claims, broad leaderboard claims, production-readiness claims,
  semantic-correctness claims, proof claims, benchmark-evidence claims, or
  global software-agent uniqueness claims.

## Audit Labels

```rust
pub enum OracleCompletenessLabel {
    /// Construct is fully inside the v0 executable oracle subset.
    Executable,
    /// Construct uses RawText and will produce a CapabilityGap.
    RawTextCapabilityGap,
    /// Construct references an operand type the oracle cannot evaluate
    /// (e.g. non-integer in a comparison).
    NonExecutableOperandCapabilityGap,
    /// Construct is structurally incapable of evaluation regardless of operand
    /// types (reserved for future constructs; none shipped today).
    StructurallyIncapable,
}
```

## Construct And Audit

```rust
pub struct OracleCompletenessConstruct {
    pub kind: OracleCompletenessConstructKind,
    pub id: String,
    pub label: OracleCompletenessLabel,
    pub detail: String,
}

pub enum OracleCompletenessConstructKind {
    TransitionGuard,
    TransitionAction,
    InvariantGuard,
    LoopBound,
}

pub struct OracleCompletenessAudit {
    pub constructs: Vec<OracleCompletenessConstruct>,
    pub executable_count: usize,
    pub capability_gap_count: usize,
    pub structurally_incapable_count: usize,
    pub is_fully_executable: bool,
}
```

`audit_oracle_completeness(surface)` walks every transition guard, every
transition action, every invariant guard, and every loop bound in declaration
order, classifies each, and returns the audit. The classification reuses the
existing `GuardSpec::contains_raw_text` and `ActionSpec::contains_raw_text`
helpers plus a local integer-operand check on binary guards, so it cannot
diverge from what the shipped oracle would actually do.

## Required Tests

- One test over a fully-executable generated instance (e.g. `BoundedCounterLoop`)
  showing `is_fully_executable == true` and `capability_gap_count == 0`.
- One test over an instance with a `RawText` guard showing the matching
  construct is labeled `RawTextCapabilityGap`.
- One test over an instance with a `RawText` action showing the matching
  construct is labeled `RawTextCapabilityGap`.
- One test over an instance with a non-integer operand in a comparison guard
  showing `NonExecutableOperandCapabilityGap`.
- One test showing audit counts are consistent with the construct vector length.
- One test showing the audit is deterministic (same surface, same audit).
- One test asserting no new DSL types were added (scope guard).

## Claim Boundary

The audit is local static analysis only, capped at `Level0DesignNote`. It is
not proof that the oracle is correct, not benchmark evidence, not accepted
evidence, not formal evidence, not ZK backend performance evidence, not
semantic correctness, not global software-agent uniqueness, and not evidence
that any backend would produce any particular outcome. It only reports which
generated constructs the shipped oracle can evaluate locally.

## Non-Goals

- Changing the oracle or any DSL type.
- Marking any construct `StructurallyIncapable` in shipped families (the
  variant exists for forward compatibility but is unused today).
- Producing Level2+ evidence or formal evidence.
- Any external execution, network access, or credential use.
