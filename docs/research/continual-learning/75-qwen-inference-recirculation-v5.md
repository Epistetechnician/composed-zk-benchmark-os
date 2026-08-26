# Qwen inference-time recirculation fixed-transfer feasibility

Date: 2026-08-26

State slice: `continual-learning-qwen-inference-recirculation-v5`

Claim ceiling: `LocalDevelopmentQwenInferenceRecirculationFixedTransferFeasibility`

## Purpose

V5 is an out-of-sample transfer holdout from V4. It carries V4's fit-selected
configuration into a new corpus without selecting or tuning a configuration on
V5 data. The Qwen checkpoint, inference-time recurrence, source/destination
pair, alpha, assessment procedure, and no-training boundary are fixed. The
source mechanism is described in
[Recirculation, arXiv:2608.17981](https://arxiv.org/abs/2608.17981).

This is not a reproduction of the source paper: the local model is the cached
Qwen2.5-0.5B-Instruct checkpoint, while the paper uses a different model family
and evaluation setting.

## Frozen protocol

- Model: the already-cached Qwen2.5-0.5B-Instruct-4bit checkpoint.
- Transfer source: V4's sealed fit-selected configuration
  `(source=12, destination=5, alpha=0.07)`, bound to V4 config digest
  `5ebd7e72ddf6bff5fff19103172e80f6ac73f3bc7c7da158d1b469c5c2017029` and
  receipt digest
  `aeec8b111d67e38b25e68b17fda03aae84a37067e4bb3eec1016b272dc4820a9`.
- Fit sources: `docs/18-phase-h-external-runner-boundary-notes.md`,
  `docs/19-phase-i-synthetic-result-import-notes.md`,
  `docs/20-phase-j-reviewed-proposal-acceptance-notes.md`, and
  `docs/21-phase-k-local-soak-runner-telemetry-notes.md`.
- Assessment sources: `docs/22-hyper-sacred-ai-architecture.md`,
  `docs/23-claim-envelope-implementation-spec.md`,
  `docs/24-hsai-implementation-handoff.md`, and
  `docs/26-agent-case-evidence-lane-spec.md`.
- The extractor takes the first four prose blocks from each source, excluding
  headings, tables, blank lines, and fenced code. This yields 16 fit and 16
  assessment sequences with disjoint source files, and all eight sources are
  fresh relative to V2, V3, and V4.
- The V5 corpus is not used to search the layer grid or alpha grid. The fit
  transfer metric is diagnostic; the primary outcome is the locked assessment
  selected-minus-baseline mean NLL.

## Validation and custody

All 32 fit/assessment sequences passed manual/native zero-alpha parity with
maximum logit delta `0.0`. The assessment repeat maximum metric delta was
`0.0`. The model manifest, corpus manifest, configuration, results, receipt,
and V4 transfer-source binding are digest-bound, and the independent validator
recomputes the corpus from current repository bytes. The model remained
weight-frozen; network access and training were false.

Canonical external artifact:

`/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-qwen-inference-recirculation-v5-20260826-r1`

Receipt hashes:

- `config.json`: `e75475bad40ea7a0c527cbcf7c414e946350c88d67ef40311e842bc17eb815d4`
- `results.json`: `3f17a9de7358877123aeba051cc6644b81d23337e7135221fc241b19247b1771`
- `receipt.json`: `79f925a10a39ee6681d90bc30d7a79be1e69276eda34206029916e9e1245a23f`
- `corpus-manifest.json`: `012afb75f44a10b80f76122db85ec7d462f91f1f13727527ee85b594ef313b59`
- `model-manifest.json`: `0aaa27ea97be0c050fa54231418191e197dd33e5f051828aea7d92d39c9b959a`

## Result

The fixed transfer configuration was `source=12`, `destination=5`,
`alpha=0.07`. On 1,355 locked assessment target tokens:

- baseline mean NLL: `5.012090637`
- transferred mean NLL: `5.019982755`
- transferred-minus-baseline NLL: `+0.007892118`
- baseline perplexity: `150.218460294`
- transferred perplexity: `151.408692670`
- transferred-minus-baseline perplexity: `+1.190232376`

Five assessment sequences improved and eleven worsened. The fixed-transfer gate
is therefore negative on this fresh holdout. It is valid local transfer
evidence, not proof that recirculation is established, not a generalization
claim, and not accepted scientific or production evidence.

## Boundary and next gate

V5 does not authorize model downloads, network access, training, adapter
updates, configuration search on V5 data, adaptive assessment tuning, provider
execution, production traffic, Evidence Ledger mutation, or benchmark claims.
The V2 negative result and V5 negative transfer result prevent promotion of the
small V3/V4 positives. A stronger claim requires a freshly frozen,
paper-comparable evaluation with eligible models, independently sourced data,
and independent validation.
