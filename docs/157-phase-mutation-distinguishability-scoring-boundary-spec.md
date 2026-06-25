# Phase 157 — Mutation Distinguishability Scoring Boundary Spec

## Status

Allowed, not yet implemented.

## Purpose

Today, mutation scoring is binary: `score_report_from_local_mutation_evidence`
counts `local_accepted_traces`, `local_rejected_traces`,
`mutation_variants_generated`, `outcome_changes_observed`, and
`unsound_acceptance_candidates`. It does not classify *how* each mutation
distinguishes itself. The SOTA-wedge rule in `AGENTS.md` names
"adversarial mutation scoring" — without a distinguishability matrix, the
adversarial framing is a label, not analysis.

This phase adds a local distinguishability matrix that composes each mutation's
declared `ExpectedVerdict` with a hypothetical `BackendOutcome` and returns the
existing `ResultClassification`, plus a derived severity bucket. This is the
analytical lens Phase 156's wider mutation surface needs to mean anything.

The matrix is **pure metadata analysis over existing types**. No new backend
execution, no new evidence, no new claim boundary. It classifies what each
mutation *would* mean if a backend produced a given outcome — useful for
prioritizing which mutations to send to a real backend later.

## State Slice

This phase is limited to:

- Additive Rust source under `crates/zkbench-core/src/scoring/` introducing:
  - `MutationDistinguishabilityAxis` enum
  - `MutationDistinguishabilityCell` struct
  - `MutationDistinguishabilityMatrix` struct
  - `classify_mutation_distinguishability` function
  - `summarize_mutation_distinguishability` function
- Re-exports from `crates/zkbench-core/src/scoring/mod.rs`,
  `crates/zkbench-core/src/prelude.rs`, and `crates/zkbench-core/src/lib.rs`.
- Additive integration tests under `crates/zkbench-core/tests/`.
- Phase notes under `docs/` and navigation updates under `README.md`,
  `docs/12-task-list.md`, `docs/90-whole-codebase-validation-report.md`, and
  `AGENTS.md`.

It does **not** permit:

- Changes to `ExpectedVerdict`, `BackendOutcome`, `ResultClassification`,
  `classify_result`, `ScoreReport`, `LocalMutationEvidenceSummary`,
  `score_report_from_evidence`, `score_report_from_local_mutation_evidence`,
  or `validate_score_report`.
- Changes to `MutationClass`, `MutationKind`, `MutationSafetyClass`,
  `MutationSpec`, `MutationVariant`, `MutationProvenance`,
  `MutatedBenchmarkInstance`, the `MutationPass` trait, or any mutation pass.
- Changes to the DSL, oracle, evidence ledgers, accepted-ledger append,
  promotion preflight, official-submission package, external replay preflight,
  pack readiness, report bundle, audit index, local benchmark artifact, local
  artifact campaign, zk-Harness adapter, or any HSAI crate.
- New Cargo dependencies, `Cargo.toml`, or `Cargo.lock` changes.
- External execution, external repo clones, vendored source, network access,
  credentials, command-line tools, UI dashboards, browser apps, JavaScript or
  TypeScript runtime files, package runtime files, or committed generated
  benchmark artifact files.
- Level2+ evidence, formal evidence, accepted Evidence Ledger mutation,
  official benchmark submission, score-axis population on `ScoreReport`,
  ZK backend performance claims, SOTA claims, broad leaderboard claims,
  production-readiness claims, semantic-correctness claims, proof claims,
  benchmark-evidence claims, or global software-agent uniqueness claims.

## Distinguishability Axis

Each mutation has a declared `ExpectedVerdict`. When paired with a hypothetical
`BackendOutcome`, the existing `classify_result` produces a
`ResultClassification`. Phase 157 buckets each cell of this matrix into one of
five distinguishability axes:

```rust
pub enum MutationDistinguishabilityAxis {
    /// Oracle says accept, backend accepts. Not a mutation signal.
    TruePositive,
    /// Oracle says reject, backend rejects. The mutation is detected.
    DetectedRejection,
    /// Oracle says reject, backend accepts. Unsound acceptance candidate —
    /// the highest-value mutation signal.
    UnsoundAcceptanceCandidate,
    /// Oracle says accept, backend rejects. False rejection candidate.
    FalseRejectionCandidate,
    /// Outcome was inconclusive, capability gap, timeout, error, or otherwise
    /// not classifiable as a clean signal.
    Inconclusive,
}
```

## Cell And Matrix

```rust
pub struct MutationDistinguishabilityCell {
    pub expected_verdict: ExpectedVerdict,
    pub backend_outcome: BackendOutcome,
    pub classification: ResultClassification,
    pub axis: MutationDistinguishabilityAxis,
}

pub struct MutationDistinguishabilityMatrix {
    pub mutation_class: MutationClass,
    pub cells: Vec<MutationDistinguishabilityCell>,
}
```

`classify_mutation_distinguishability(mutation_class, expected_verdict)
-> MutationDistinguishabilityMatrix` iterates over every `BackendOutcome`
variant and returns one cell per pairing. This produces a deterministic,
complete matrix — no sampling, no randomness.

`summarize_mutation_distinguishability(matrices: &[MutationDistinguishabilityMatrix])
-> MutationDistinguishabilitySummary` counts cells per axis across all
supplied matrices, producing the aggregate local-only signal.

## Severity Buckets

Each axis carries an implicit priority for downstream triage:

- `UnsoundAcceptanceCandidate` — highest priority (potential soundness finding)
- `DetectedRejection` — high (mutation is detectable)
- `FalseRejectionCandidate` — medium (potential completeness issue)
- `Inconclusive` — low (needs more evidence)
- `TruePositive` — informational (not a mutation signal)

These buckets are exposed via `axis_severity(&self) -> u8` on
`MutationDistinguishabilityAxis`, returning 4/3/2/1/0 respectively. They are
local-only priority hints, not benchmark scores.

## Required Tests

- One test per `ExpectedVerdict` × `BackendOutcome` pairing showing the
  classification and axis are computed correctly.
- One test showing `classify_mutation_distinguishability` produces a complete
  matrix (one cell per `BackendOutcome` variant) for a given mutation class.
- One test showing `summarize_mutation_distinguishability` aggregates counts
  correctly across multiple matrices.
- One test showing `axis_severity` returns the documented priority values.
- One test showing the matrix is deterministic (same inputs produce same
  outputs).
- One test asserting no new `ExpectedVerdict`, `BackendOutcome`, or
  `ResultClassification` variants were added (scope guard).
- One test asserting the summary carries `Level1LocalReplay` nonclaim language.

## Claim Boundary

Every distinguishability matrix produced by this phase is local metadata
analysis only, capped at `Level1LocalReplay`. A cell classifying as
`UnsoundAcceptanceCandidate` is a *hypothetical* unsound acceptance candidate
under a *hypothetical* backend outcome — it is not proof, not benchmark
evidence, not accepted evidence, not formal evidence, not ZK backend
performance evidence, not semantic correctness, not global software-agent
uniqueness, and not evidence that any real backend would produce that outcome.
The matrix does not populate any `ScoreReport` axis; it is reported separately
as local analysis metadata.

## Non-Goals

- Calling any real backend.
- Producing the first Level2 evidence, the first accepted Evidence Ledger
  entry, the first formal property statement, the first machine-checked proof,
  or the first independently reproduced evidence.
- Changing any existing scoring, evidence, mutation, DSL, or oracle surface.
- Adding new verdicts, outcomes, classifications, or mutation classes.
- Any external execution, network access, or credential use.
