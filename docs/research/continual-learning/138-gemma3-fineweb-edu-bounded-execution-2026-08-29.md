# Gemma3 FineWeb-Edu bounded recirculation execution record

State slice: `continual-learning-gemma3-fineweb-edu-bounded-v1`

Date: 2026-08-29

Disposition: `BoundedPilotSignalObserved`

## Receipts

- Source manifest SHA256:
  `9e6311b8a88b879c2b8d102cc1b1d4093312c796633571d00c928738327b33d3`
- Corpus manifest SHA256:
  `e06941cd85b4b2c3e75ba0561f9980a63cb74f7c708f30acb80510a4869fee85`
- Model manifest SHA256:
  `69f078b42d4521d3e53f0c388a20fa6cf32b4df7ea6535b0eb9da6ccef75c256`
- Configuration SHA256:
  `89dc928e78c7b18fc6f1a8a59608dff1e584e1c2b9231890446fb533443725c2`
- Results SHA256:
  `151d56568a6c90b3c1b090a3cdb2c571e046abb2f497b87306df27430e472f68`
- Receipt SHA256:
  `58764e9dd927eea2f2eb3539a29020f62ec6813bffa8b8a73656f20ac05083da`

The raw source validator, corpus validator, result validator, and the
runner's pre-publication validator all returned `valid: true`.

## Outcome

- Paper expected pair `(11 -> 4)`: recovered by the locked fit selection.
- Fit selected alpha: `0.10`.
- Locked assessment alpha: `0.15`.
- Assessment baseline mean NLL: `2.538428641`.
- Assessment selected mean NLL: `2.460517272`.
- Assessment delta, selected minus baseline: `-0.077911369`.
- Assessment perplexity delta, selected minus baseline: `-0.948894631`.
- Assessment deterministic repeat: passed.
- Maximum repeat metric delta: `0.0`.
- Native/MLX parity: passed; max absolute logit delta `0.0` across 32
  sequences.
- Zero-alpha parity: passed.
- Network access during model execution: false.
- Training: false.
- Weights frozen: true.
- Evidence Ledger mutation: false.

## Interpretation

This bounded, cross-crawl FineWeb-Edu pilot observed an assessment improvement
under the locked protocol and recovered the paper's expected layer pair
without forcing the pair. That is evidence for a local replication signal in
this exact artifact set. It is not proof of general recirculation, exact
paper replication, causal mechanism, benchmark superiority, or production
readiness. The panel is only 16 fit and 16 assessment windows, and the source
is a bounded sample rather than the full paper-shaped corpus.

## Remaining gate

The next scientific gate is independent human review of the immutable source,
corpus, model, locked configuration, controls, and receipts. A stronger claim
requires a fresh disjoint cohort, predeclared uncertainty and multiplicity
rules, and independent reproduction. No provider/H100 execution, GiveMeANode
submission, Evidence Ledger mutation, or production action is authorized by
this result.
