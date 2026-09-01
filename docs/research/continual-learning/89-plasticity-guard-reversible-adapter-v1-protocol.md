# Plasticity guard with reversible adapters V1

Date: 2026-08-28.

State slice: `continual-learning-plasticity-guard-reversible-adapter-v1`.

Claim ceiling: `LocalDevelopmentPlasticityGuardReversibleAdapterFeasibility`.

## Scope

This is the separately authorized cached-model follow-up to the validated
exact synthetic factorial. It tests only the surviving `plasticity_guard`
mechanism. It does not reopen the rejected adaptive-verification slice, add a
wave schedule, add stochastic scheduling, use ZK/PQC evidence, or create an
Astral introspection/self-modeling result.

The base model is loaded offline and remains byte-identical. Every learner
update is a reversible LoRA adapter subprocess. A candidate adapter is either
committed by changing the active adapter pointer or retained as a rejected
candidate; the base checkpoint is never updated or merged.

## Fixed model and corpus contract

- Model: already-cached `/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16`.
- Runtime: cached MLX `0.31.2` and MLX-LM `0.31.3` with the model-bound
  tokenizer policy.
- Network: `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`; no download or
  provider call.
- Source: the already operator-supplied NEWSROOM `test.jsonl.gz`, copied and
  digest-bound into the external result root. This is a new document cohort,
  not reuse of V1/V2 local-pilot windows or result artifacts.
- Selection: after skipping the first eight source-order eligible documents
  used by the prior local pilots, select the next twelve eligible documents.
  Eligibility is at least 256 model tokens. The selection policy and every
  source line, URL, and text digest are recorded before adapter training.
- Splits: six fit documents, three tune documents, and three assessment
  documents. Document identities are disjoint across all splits.
- Window: the first exactly 256 model tokens from each selected document,
  decoded and re-encoded with exact token identity.

The source file is reused only as an immutable, digest-bound operator input.
Prior V1/V2 corpus files, metrics, adapters, and results are not inputs.

## Learner and case design

The preregistered cases are two seeds (`1739`, `1741`) crossed with forward and
reverse fit orders. Each case runs two arms: `fixed_cadence` and
`plasticity_guard`. Both arms attempt the same six updates, with four copies
of the current 256-token window, three LoRA iterations, batch size one, four
trainable layers, AdamW, learning rate `1e-4`, and the same seed plus step.
The fixed arm commits every candidate. The guarded arm evaluates every
candidate with the same compute and commits only when the fixed guard passes.

The guard is frozen before execution:

```text
current_gain = active_current_nll - candidate_current_nll
protected_delta = candidate_protected_nll - active_protected_nll
commit iff step == 0 OR
  (current_gain >= 0.001 AND protected_delta <= 0.010)
```

The protected buffer contains only previously committed fit windows. A failed
guard rolls back by leaving the active adapter pointer unchanged. Candidate
training and guard measurements are still retained in the external artifact,
so a rollback does not hide compute or erase a failure.

## Endpoint and hard guards

The sole primary endpoint is held-out adaptation improvement after the fixed
six-update budget:

```text
assessment_adaptation_improvement = base_assessment_mean_nll - final_mean_nll
primary_delta = guarded_improvement - fixed_improvement
```

The primary result is a `DevelopmentCandidate` only when the mean paired delta
is at least `0.010` NLL/token, the deterministic 10,000-resample case-level
95% bootstrap lower bound is at least zero, the guarded arm wins at least
three of four paired cases, and every hard guard passes. Otherwise it is
`DevelopmentNoCandidate`.

Hard guards are fixed and non-rescuable:

- final fit forgetting fraction is at most `0.05` relative to frozen-base fit
  loss;
- tune expected calibration error (ECE) change is at most `0.05` absolute;
- assessment repeat mean-NLL difference is at most `1e-8`;
- native reload logit parity is at most `1e-5`;
- zero-adapter logit parity is at most `1e-5`;
- candidate adapter save/restore logit difference is at most `1e-6`;
- every candidate has finite metrics and a complete adapter file;
- base-model file manifest before and after the campaign is identical;
- PrimaryED and DAed artifact manifests are byte-identical;
- the independent validator passes.

The unit for the primary bootstrap is the case, not a token or training row.
No parameter, threshold, split, seed, order, or arm is selected from
assessment data. Tune data does not select a hyperparameter.

## Locking, custody, and Astral boundary

The prediction lock is written after all fit updates and guard decisions but
before any final adapter or base assessment metric is computed. It contains
configuration, qualification, case identities, update decisions, and adapter
digests, but no assessment result. The lock is immutable thereafter.

Raw text, adapter tensors, and training logs remain only in the external
PrimaryED root and its DAed mirror. Repository records retain protocol,
execution status, digests, aggregate metrics, and the narrow claim ceiling.

Astral integration is `not_run` in this slice. If a future separately opened
integration is proposed, it may test only causal-effect prediction,
calibration, or instrumental correction. It may not be described as
introspection, self-modeling, Stage 0C, Stage 1, or V48 evidence. Real ZK/PQC
backends remain a later independent proof-and-overhead experiment; fixture
receipts and booleans are not cryptographic evidence.

## Terminal rules

Qualification failure, base-manifest drift, split leakage, lock drift,
validator failure, missingness, or a failed hard guard closes this execution
as invalid or `DevelopmentNoCandidate`. No adaptive retry, threshold change,
model shopping, provider escalation, adapter merge, base-weight update, or
Astral claim expansion is allowed.
