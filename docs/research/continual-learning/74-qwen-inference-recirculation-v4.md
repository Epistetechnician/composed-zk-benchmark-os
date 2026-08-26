# Qwen inference-time recirculation fresh-corpus feasibility

Date: 2026-08-26

State slice: `continual-learning-qwen-inference-recirculation-v4`

Claim ceiling: `LocalDevelopmentQwenInferenceRecirculationFreshCorpusFeasibility`

## Purpose

V4 is the single-factor successor to V3. It changes only the evaluation corpus
to test whether the V3 alpha-sweep signal survives fresh repository-owned
documents. The Qwen checkpoint, inference-time recurrence, layer-pair grid,
alpha grid, fit-only selection, assessment lock, and no-training boundary are
unchanged. The source mechanism is described in
[Recirculation, arXiv:2608.17981](https://arxiv.org/abs/2608.17981).

This is not a reproduction of the source paper: the local model is the cached
Qwen2.5-0.5B-Instruct checkpoint, while the paper uses a different model family
and evaluation setting.

## Frozen protocol

- Model: the already-cached Qwen2.5-0.5B-Instruct-4bit checkpoint.
- Fit sources: `docs/00-project-brief.md`,
  `docs/04-fork-wrap-ignore-decisions.md`, `docs/06-dsl-schema.md`, and
  `docs/13-semantics-oracles-and-claim-boundaries.md`.
- Assessment sources: `docs/14-phase-b-implementation-notes.md`,
  `docs/15-phase-d-e-generator-mutation-notes.md`,
  `docs/16-phase-f-local-replay-evidence-ledger-notes.md`, and
  `docs/17-phase-g-zk-harness-dry-run-adapter-notes.md`.
- The extractor takes the first four prose blocks from each source, excluding
  headings, tables, blank lines, and fenced code. This yields 16 fit and 16
  assessment sequences with disjoint source files.
- Every source file and extracted text unit is represented by a digest and
  length in the corpus manifest; raw corpus text is not written to the external
  artifact.
- The candidate grid is the V3 grid: source/destination pairs `(7,2)`,
  `(9,3)`, `(11,4)`, and `(12,5)`, crossed with alphas `0.04`, `0.07`,
  `0.10`, and `0.16`. The lowest fit mean NLL is selected before assessment.
- The assessment is executed once and repeated with the locked configuration.
  The primary metric is selected-minus-baseline assessment mean NLL.

## Validation and custody

All 32 fit/assessment sequences passed manual/native zero-alpha parity with
maximum logit delta `0.0`. The assessment repeat maximum metric delta was
`0.0`. The model manifest, corpus manifest, configuration, results, and
receipt are digest-bound, and the independent validator independently
recomputes the corpus from current repository bytes. The model remained
weight-frozen; network access and training were false.

Canonical external artifact:

`/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-qwen-inference-recirculation-v4-20260826-r1`

Receipt hashes:

- `config.json`: `5ebd7e72ddf6bff5fff19103172e80f6ac73f3bc7c7da158d1b469c5c2017029`
- `results.json`: `1dce237ba270d24c9da3743faee769d804ce37b3c78c5a5a89ebf70d83f3b259`
- `receipt.json`: `aeec8b111d67e38b25e68b17fda03aae84a37067e4bb3eec1016b272dc4820a9`
- `corpus-manifest.json`: `ac15c6aa7ec70320d5a1ebc33a446aaf1ab2f7b393df98b900940bad58e36b93`
- `model-manifest.json`: `0aaa27ea97be0c050fa54231418191e197dd33e5f051828aea7d92d39c9b959a`

## Result

Fit selected `source=12`, `destination=5`, `alpha=0.07`. On 860 locked
assessment target tokens:

- baseline mean NLL: `4.995389717`
- selected mean NLL: `4.994936018`
- selected-minus-baseline NLL: `-0.000453699`
- baseline perplexity: `147.730507193`
- selected perplexity: `147.663497307`
- selected-minus-baseline perplexity: `-0.067009886`

Ten assessment sequences improved and six worsened. The aggregate improvement
is smaller than V3 and remains mixed. V4 is directional local feasibility
evidence, not proof that recirculation is established, not a generalization
claim, and not accepted scientific or production evidence.

## Boundary and next gate

V4 does not authorize model downloads, network access, training, adapter
updates, adaptive assessment tuning, provider execution, production traffic,
Evidence Ledger mutation, or benchmark claims. A stronger claim requires a
freshly frozen paper-comparable evaluation with eligible models, a larger
independent corpus, and independent validation. V3 and V4 are separate
immutable local runs; V4 changes no assessment-selected configuration based on
the V3 assessment result.
