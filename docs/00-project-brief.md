# Project Brief

## Mission

Composed ZK Benchmark OS creates a professional foundation for benchmarks generated from explicit control-flow semantics. It turns machine specifications into benchmark families, mutation variants, replay artifacts, evidence records, and score reports.

## Thesis

ZK verifier and proof-system benchmarks should be generated from explicit semantic machine specifications, not only selected from hand-authored circuits or workload examples.

## Problem Statement

Existing benchmark systems are valuable but often start from fixed circuits, fixed workloads, or backend-specific examples. That misses a class of failures around state transitions, loops, witness boundaries, recursion envelopes, stale reads, invalid counters, and adversarial near-valid traces. The project addresses that gap by making semantics and expected verdicts first-class.

## Target User

- ZK systems researchers comparing verifier behavior across backends.
- Benchmark maintainers designing replayable workload suites.
- Formal-methods engineers defining scoped proof obligations.
- zkVM and proof-system teams looking for negative tests and adversarial control-flow stress cases.
- Open-source maintainers who need evidence-bound claims rather than hype.

## Research Motivation

The useful research artifact is not another collection of circuits. It is a repeatable system for deriving benchmark cases from semantic families, mutating them with known expected verdicts, and measuring both speed and soundness-failure coverage.

## What Counts As Success

- A clear Surface DSL and Semantic IR contract.
- Benchmark families generated from state and loop semantics.
- Mutation variants with explicit expected verdicts.
- Backend adapters that report capability-scoped evidence.
- A scoring model that separates performance from soundness.
- Claim boundaries that prevent benchmark, recursion, or local replay evidence from being overstated.

## What Does Not Count As Success

- Copying existing benchmark repos.
- Generating a dashboard before the evidence model exists.
- Reporting one composite score without exposing weak evidence axes.
- Treating backend acceptance as semantic proof.
- Claiming SOTA benchmark results without reproducible artifacts.

## First Milestone

Complete this documentation-only scaffold with implementation-grade architecture, DSL, module layout, mutation, scoring, validation, and adapter plans.

## First Non-Doc Implementation Milestone

Implement the Rust DSL/core schema:

```text
Surface DSL -> Parsed AST -> canonical Semantic IR
```

The first implementation milestone should include validation of schema entities, oracle declarations, mutation declarations, and evidence metadata. It should not include external adapters.

## Risks

| Risk | Mitigation |
|---|---|
| Adapter sprawl replaces core research. | Build DSL/core schema first. |
| Performance scores hide weak soundness evidence. | Keep separate score axes and claim boundaries. |
| Formal lanes overclaim full-system proof. | Scope every formal claim to a property and layer. |
| Existing repos become copied feature sets. | Wrap or reference by default. |
| Negative tests are misclassified. | Require Oracle, Expected Verdict, Backend Outcome, and result triage. |

## Project Vocabulary

- Surface DSL: Human-authored benchmark specification.
- Parsed AST: Syntactic representation before semantic lowering.
- Semantic IR: Canonical machine semantics and oracle declarations.
- Benchmark Family: Parameterized set of generated machines.
- Benchmark Instance: Concrete generated case.
- Mutation Variant: Valid, near-valid, malicious, or invalid variant.
- Oracle: Semantic evaluator that defines expected verdicts.
- Expected Verdict: What the semantic model says should happen.
- Backend Outcome: What an adapter reports happened.
- Evidence Record: Normalized replay/proof/formal/benchmark evidence.
- Claim Boundary: Maximum claim justified by evidence.
- Score Report: Multi-axis report separating speed and soundness.

