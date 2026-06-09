# Formal Semantics Lanes

Formal lanes produce scoped evidence. They do not define the full project semantics and do not prove the full benchmark OS.

## clean

Expected role: Lean formal-circuit proof lane for a small generated machine or loop.

Evidence type: future machine-checked proof for a scoped property.

Likely input boundary: Semantic IR subset lowered to a small formal statement around transition relation or invariant satisfaction.

Can prove: scoped properties such as a bounded counter transition preserving an invariant.

Cannot prove: that every adapter, benchmark backend, or mutation result is correct.

Claim boundary: Level 5 only for the named checked property.

Adapter risks: proof scope drift, unsupported DSL constructs, trusted lowering boundary.

## zkLean

Expected role: Lean ZK-statement semantics lane for constraints, witness policy, and small RAM-like patterns.

Evidence type: future formal or machine-checked proof evidence for scoped statements.

Likely input boundary: Semantic IR to constraint-style formal statement.

Can prove: scoped constraint semantics, witness or lookup properties where supported.

Cannot prove: runtime backend behavior or official benchmark validity.

Claim boundary: Level 4 for formal statement; Level 5 only after checked proof.

Adapter risks: conversion trust boundary and mismatch between source DSL and formal encoding.

## formal-land/garden

Expected role: Rocq trace/property proof lane for generated FSM/loop traces.

Evidence type: future trace validity or property proof evidence.

Likely input boundary: finite trace model, transition relation, invariants, and mutation verdicts.

Can prove: determinism, functional correctness, and scoped trace properties for tiny cases.

Cannot prove: full zkVM behavior, external benchmark correctness, or recursive proof semantics.

Claim boundary: Level 5 only for scoped machine-checked properties.

Adapter risks: proof engineering cost, WIP assumptions, and trace model drift.

## Shared Formal Lane Rules

- A formal proof about one layer is not a formal proof about the full system.
- A successful proof is not automatically evidence that the source spec was meaningful.
- Formal lanes must name property, scope, source spec hash, lowering assumptions, and claim boundary.

