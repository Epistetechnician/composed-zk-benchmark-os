# Phase B Implementation Notes

## Implemented

The Level 1 local Rust foundation creates `crates/zkbench-core` with:

- Surface DSL data structures.
- YAML parsing into `SurfaceSpec`.
- `ParsedAst` validation.
- Deterministic lowering into canonical `SemanticIr`.
- Static validation for ids, state references, field references, trace transitions, targets, mutations, and Level 1 claim caps.
- A small local oracle for integer, boolean, and text values; guard comparisons; boolean guard composition; assignment; integer add/sub assignment; trace final-state and final-field checks.
- `ExpectedVerdict`, `BackendOutcome`, and `ResultClassification`.
- `EvidenceRecord`, `ClaimBoundary`, provenance, and artifact digest primitives.
- `BenchmarkFamily` and `BenchmarkInstance` primitives.
- Mutation taxonomy and mutation variant metadata.
- Replay manifest and backend adapter trait definitions only.
- Score report primitives with missing-data handling.

## Deliberately Unimplemented

The crate does not implement external adapters, backend artifact generation, zk-Harness integration, clean, zkLean, Garden, gnark, zkML execution, dashboards, benchmark packs, formal proofs, or generated benchmark results.

## Why Adapters Are Deferred

Adapters can only produce meaningful evidence after the local generator and mutation engine can produce concrete Benchmark Instances with Expected Verdicts. Backends consume Semantic IR-derived instances; they do not define the semantics.

## Evidence Boundary

This phase remains Level 1 local foundation at most. A benchmark pass is not proof. A local replay is not official benchmark evidence. A recursion proof is not semantic proof. No fixture or test is a real benchmark result, reproducible benchmark artifact, formal statement, or machine-checked proof.

## Known v0 Oracle Limits

The local oracle supports only a small executable subset. Raw-text guards/actions return capability gaps. Recursion metadata, zkML metadata, formal semantics, witness aliasing, and public/private boundary checks are represented as metadata but are not fully executed.

