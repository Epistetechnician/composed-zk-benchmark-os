# Qwen inference-time recirculation feasibility

Date: 2026-08-26

State slice: `continual-learning-qwen-inference-recirculation-v1`

Claim ceiling: `LocalDevelopmentQwenInferenceRecirculationFeasibility`

Source mechanism: [Recirculation, arXiv:2608.17981](https://arxiv.org/abs/2608.17981)

## Scope

This slice tests the paper's inference-time mechanism against the already
cached `Qwen2.5-0.5B-Instruct-4bit` MLX checkpoint. It is not a replication of
the paper's Gemma3 experiments. The model, tokenizer, text inputs, runtime,
and evaluation scale differ from the paper.

The implementation runs the Qwen stack token by token with a fresh KV cache.
After source layer `s` completes at input step `t`, its residual stream is
normalized to the destination norm and mixed into destination layer `d` at
step `t+1`:

`z_next,d = alpha * normalize(z_source) + (1 - alpha) * z_destination`.

The checkpoint is frozen. No LoRA adapter, weight update, download, network
call, provider call, or production operation is involved.

## Frozen campaign

- Model: `Qwen2.5-0.5B-Instruct-4bit`, Qwen2 architecture, 24 layers.
- Runtime: MLX `0.31.2`, mlx-lm `0.31.3`, offline flags enabled.
- Fit set: four fixed repository-owned text strings.
- Assessment set: four different fixed repository-owned text strings, held
  out before source/destination selection.
- Candidate grid: `(s,d) = (7,2), (9,3), (11,4), (12,5)` with `alpha=0.10`.
- Selection: lowest fit mean token NLL, then one locked assessment evaluation
  and one deterministic repeat.
- Artifact root:
  `/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-qwen-inference-recirculation-v1-20260826-r3`

## Result

The independent validator returned `valid=true`.

- Manual layer-by-layer `alpha=0` versus native cached-token parity:
  `max_abs_logit_delta=0.0`; gate passed.
- Fit-selected configuration: `s=7`, `d=2`, `alpha=0.10`.
- Assessment mean NLL: `5.932926829` baseline versus `5.893055695` with
  recirculation, delta `-0.039871134`.
- Assessment perplexity: `377.257066570` baseline versus `362.511317631`
  with recirculation, delta `-14.745748939` (approximately `3.91%` lower).
- Deterministic assessment repeat: exact at the recorded metric precision.
- Training: `false`; network access: `false`; weights frozen: `true`.

The result is a local feasibility signal on 82 assessment target tokens. It is
not accepted scientific evidence, a Gemma3 replication, a general Qwen claim,
a production result, or proof that recirculation improves language modeling
outside this fixed fixture.

## Custody and correction record

The first `r1` artifact is superseded and must not be used: its zero-alpha
parity check accidentally routed through the native path and was therefore
tautological. The manual path was corrected to bypass zero-weight intervention
arithmetic while still executing every Qwen layer, then the parity gate passed
on an isolated retest and the canonical `r3` campaign was run. All roots are
immutable; only `r3` is the valid campaign root.

The producer and independent validator are:

- `experiments/continual_learning/qwen_inference_recirculation_v1.py`
- `experiments/continual_learning/validate_qwen_inference_recirculation_v1.py`
- `experiments/continual_learning/tests/test_qwen_inference_recirculation_v1.py`

## Next evidence gate

Before any stronger claim, freeze a larger disjoint natural-text corpus and a
preregistered Qwen assessment, compare against native Qwen on multiple fresh
sequences, and independently repeat the locked source/destination choice. A
second eligible model and paper-comparable datasets would be required for a
cross-model or paper-replication claim. Provider, production, and accepted
Evidence Ledger lanes remain closed.
