# Qwen inference-time recirculation alpha-sweep feasibility

Date: 2026-08-26

State slice: `continual-learning-qwen-inference-recirculation-v3`

Claim ceiling: `LocalDevelopmentQwenInferenceRecirculationAlphaSweepFeasibility`

## Purpose

V3 is the single-factor successor to V2. It tests whether the V2 local signal
is sensitive to the source paper's reported alpha values while preserving the
Qwen checkpoint, manual inference seam, source/destination pairs, corpus,
assessment split, and no-training boundary. The source mechanism is described
in [Recirculation, arXiv:2608.17981](https://arxiv.org/abs/2608.17981).

This is not a reproduction of the source paper: the local model is the cached
Qwen2.5-0.5B-Instruct checkpoint, while the paper uses a different model family
and evaluation setting.

## Frozen protocol

- Model: the already-cached Qwen2.5-0.5B-Instruct-4bit checkpoint.
- Corpus: the unchanged V2 corpus of 12 fit and 12 document-disjoint
  assessment sequences from six repository-owned Markdown sources. Source-byte
  and extracted-unit digests are retained; raw corpus text is not written to
  the external artifact.
- Mechanism: frozen token-by-token MLX inference with normalized deep-source
  feedback into a shallower destination at the next token step.
- Candidate grid: source/destination pairs `(7,2)`, `(9,3)`, `(11,4)`, and
  `(12,5)`, crossed with alpha values `0.04`, `0.07`, `0.10`, and `0.16`.
- Selection: the minimum mean fit NLL is selected before any assessment
  execution. The locked assessment is then run twice.

## Validation and custody

All 24 fit/assessment sequences passed manual/native zero-alpha parity with
maximum logit delta `0.0`. The assessment repeat maximum metric delta was
`0.0`. The model manifest, corpus manifest, configuration, results, and
receipt are digest-bound, and the independent validator recomputes the corpus
manifest against the current repository. The model remained weight-frozen;
network access and training were false.

Canonical external artifact:

`/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-qwen-inference-recirculation-v3-20260826-r1`

Receipt hashes:

- `config.json`: `efb90c6b409f5480e3d73de337624a4f1f1939f997b98e8868e5daaf136b795e`
- `results.json`: `50b1f320cf3a5f010b80cd84f767d43877a3e02a240955c2b53e36984e7d375c`
- `receipt.json`: `d99f08dfdac6b25f816b66056c147bb7379ed6b85c0eea10a29420b20c1cab45`
- `corpus-manifest.json`: `3eb8428a79cbde5d032a2bacfc825d0d141576c5554df8c621214ff4d1b861e1`
- `model-manifest.json`: `0aaa27ea97be0c050fa54231418191e197dd33e5f051828aea7d92d39c9b959a`

## Result

Fit selected `source=12`, `destination=5`, `alpha=0.04`. On 575 locked
assessment target tokens:

- baseline mean NLL: `5.238627717`
- selected mean NLL: `5.237328535`
- selected-minus-baseline NLL: `-0.001299182`
- baseline perplexity: `188.411371272`
- selected perplexity: `188.166749505`
- selected-minus-baseline perplexity: `-0.244621767` (approximately `0.13%`)

Six assessment sequences improved and six worsened. The aggregate change is
therefore small and mixed. It is a local alpha-sweep feasibility signal, not
proof that recirculation is established, not a generalization claim, and not
accepted scientific or production evidence.

## Boundary and next gate

V3 does not authorize model downloads, network access, training, adapter
updates, adaptive assessment tuning, provider execution, production traffic,
Evidence Ledger mutation, or benchmark claims. A stronger claim requires a
freshly frozen, paper-comparable evaluation with eligible models, larger
disjoint data, and independent validation. The V2 negative result remains a
separate immutable predecessor; V3 was not tuned on its assessment outcome.
