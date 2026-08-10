# Model adapter pilot v2 execution record

State slice: `continual-learning-model-adapter-v2`.

Status: `RetiredPromptMismatchDiagnostic`.

## Execution boundary

- Runtime: local MLX `mlx_lm` 0.31.3.
- Network: offline flags set; no downloads or provider calls.
- Task protocol: four disjoint task families, eight facts per task, balanced
  four-choice labels, target task `0` first, interference order `0,1,2,3`.
- Update budget: sixteen examples per task for both trainable strategies.
- Training: eight LoRA updates per run including recovery, forty iterations per
  sequential update and twenty for recovery.
- Assessment: source context removed for acquisition, retention, and recovery;
  evaluation used frozen A/B/C/D next-token likelihoods.

## Runs

| Run | Model | Manifest | No-update acquisition | Naive retention | Replay retention | Retrieval retention | Validator |
|---|---|---|---:|---:|---:|---:|---|
| Qwen r4 | `Qwen2.5-0.5B-Instruct-4bit` | `45a059a0f58b9c88bff0746de8f9422a315572d431848368d0af86eec38a4df6` | 0.375 | 0.250 | 0.250 | 0.875 | valid |
| Llama | `Llama-3.2-1B-Instruct-4bit` | `47e19a5853c6e49a5344554ed7005a2b03cf260a41cf04afd461943ea1c4326a` | 0.250 | 0.250 | 0.250 | 0.250 | valid |

Qwen naive and replay acquisition were both `0.375`; Llama naive and replay
acquisition were both `0.250`. No trainable strategy exceeded its frozen
no-update baseline on the primary acquisition endpoint. Replay did not exceed
naive sequential retention on either model.

## Preserved diagnostics

- The first Qwen run used a different training prefix and was retained as a
  prompt-transfer diagnostic, not pooled evidence.
- The aligned six-fact Qwen run reached `0.500` acquisition and `0.500`
  retention for both trainable strategies; it was superseded by the balanced
  eight-fact protocol and is not pooled.
- The first balanced eight-fact run stopped before evaluation because the
  full-context control exceeded the initial 128-token bound. The bound was
  corrected to 192 before the valid Qwen r4 run.

## Decision

Retire this pilot as scientific evidence. The structural validator was valid,
but V2 trained after an `Answer:` suffix while assessing before that suffix.
The result is therefore a prompt-transfer diagnostic, not a valid negative
continual-learning result. V3 repairs this boundary in a new state slice.

External artifacts:

- `/tmp/continual-learning-model-v2-seed20260810-order0123-r4`
- `/tmp/continual-learning-model-v2-llama1b-seed20260810-order0123`
