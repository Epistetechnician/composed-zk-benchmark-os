# V2 Qwen inference-time recirculation broader-feasibility boundary

Date: 2026-08-26

State slice: `continual-learning-qwen-inference-recirculation-v2`

Claim ceiling: `LocalDevelopmentQwenInferenceRecirculationBroaderFeasibility`

## Purpose

V2 extends the V1 local feasibility check to a larger, document-disjoint
repository-owned text surface. It keeps the V1 manual Qwen layer/KV-cache seam
and normalized deep-to-shallow residual recurrence unchanged. The checkpoint
remains frozen, and this is not a paper replication: the local checkpoint is
Qwen2.5-0.5B-Instruct rather than the Gemma3 family used by the source paper.

The source mechanism is [Recirculation, arXiv:2608.17981](https://arxiv.org/abs/2608.17981).

## Frozen protocol

- Model: the already-cached
  `/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit`.
- Fit sources: `docs/03-sota-architecture.md`,
  `docs/05-adapter-roadmap.md`, and `docs/07-rust-module-layout.md`.
- Assessment sources: `docs/08-benchmark-taxonomy.md`,
  `docs/09-mutation-engine.md`, and `docs/10-scoring-rubric.md`.
- The extractor takes the first four prose blocks from each source, excluding
  headings, tables, blank lines, and fenced code. This yields 12 fit and 12
  assessment sequences with disjoint source files.
- Every source file and extracted text unit is represented by a digest and
  length in the corpus manifest; raw corpus text is not written to the
  external artifact.
- The candidate grid remains `(7,2)`, `(9,3)`, `(11,4)`, and `(12,5)` with
  `alpha=0.10`. The lowest fit mean NLL is selected before assessment.
- Assessment is executed once and repeated deterministically with the locked
  configuration. The primary metric is selected-minus-baseline assessment
  mean NLL.

## Gates and custody

The manual layer path must match the native cached-token path at `alpha=0`
within `1e-5` for every fit and assessment sequence. The model manifest,
corpus manifest, configuration, results, and receipt are digest-bound. The
independent validator recomputes the corpus from the current repository,
rechecks every binding, and rejects source drift, parity failure, or a
non-deterministic repeat.

The campaign writes only to a new repository-external immutable artifact root.
No V1 artifact is mutated or pooled with V2. No model download, network call,
training, adapter update, adaptive assessment tuning, provider call,
production traffic, accepted Evidence Ledger mutation, or benchmark claim is
allowed.

## Boundary

Even a valid positive result is only broader local feasibility evidence. It
cannot establish a general Qwen result, a Gemma3 replication, a generally
viable continual-learning candidate, accepted scientific evidence, provider
readiness, or production readiness. A later cross-model or paper-comparable
claim requires a separately frozen successor with a second eligible model and
disjoint comparable data.
