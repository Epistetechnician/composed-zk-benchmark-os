# Continual-learning activation-shape diagnostic — docs-first boundary

State slice: `continual-learning-activation-shape-diagnostic-boundary`
Claim ceiling: `Level0DesignNote`.

## Purpose

Add a descriptive, non-selective diagnostic: record raw activation shape
(per-unit percentile profile) before and after a bounded local update, plus a
matched-random-unit comparison of update-induced change. Source idea is the
Goodfire essay (informal, unreviewed, no code or data); here it is a
diagnostic only.

## Rules

- Diagnostic is read-only with respect to update decisions: it may not select,
  gate, retune, or promote any update, threshold, seed, or policy.
- Reported as aggregates with digests; no raw activations retained in the
  repository.
- Applies only to already-authorized local frozen experiments; it adds no new
  experiment, model, corpus, or training.
- Closed families (plasticity-recovery V1/V2, recursive-update-policy V1/V2,
  prior Qwen/Llama V-series) stay closed and are not reopened.

## Gate

Any implementation needs its own state slice. Model-bearing or gman execution
needs an independent signed ACCEPT, hard USD ceiling, and allocation receipt
(absent), so nothing runs under this document.

## Nonclaims

No result, accepted evidence, benchmark, SOTA, proof, mechanistic-feature, or
production claim.
