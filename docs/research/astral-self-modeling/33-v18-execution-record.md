# V18 Execution Record

State slice: `astral-trained-lm-explainer-feasibility-v18`.

Execution: `TrainedSameModelDevelopmentCandidate`. Confirmation:
`NotAuthorized`. Stage 1: `BlockedByStage0C`.

## Integrity and ordering

V18 used only the cached local Qwen2.5-0.5B and Llama-3.2-1B 4-bit
conversions. The target Qwen weights remained frozen. Six final LoRA adapters
were trained offline over the final eight layers using the three preregistered
seeds per explainer model.

The new 256-family arithmetic-hint corpus had no overlap with V17. Fit and tune
target labels were balanced enough to proceed:

| Split | Changed | Unchanged | Minority fraction |
|---|---:|---:|---:|
| Fit | 114 | 78 | 40.625% |
| Tune | 22 | 10 | 31.25% |

Target repeat error was exactly zero. The 20-update Qwen smoke test completed,
and peak reported training memory was approximately 1.4 GB for Qwen and 2.2 GB
for Llama.

Assessment processing followed the locked order:

1. only hinted assessment target outputs were collected;
2. all trained, untrained, constant, and rule predictions were written;
3. the independent lock validator confirmed that no assessment ablation output
   existed;
4. prediction lock
   `e98419bdcbf4aac60e4b03a5f0ce8e7ffac79ae0d521c9d9eaebd4c7b2eeda64`
   was sealed;
5. the 32 target ablations were executed once;
6. deterministic scoring and balanced-accuracy bootstrap were finalized;
7. the complete bundle independently validated.

Final manifest SHA-256:
`a1710a217452fd74312fef171d0986a9c4e27c6f353d442943420bd5f315cc33`.

Validated repository-external bundle:
`/tmp/astral-lm-v18-20260727-run1`.

## Primary result

The sealed assessment split contained 16 changed and 16 unchanged target
answers.

| Method | Accuracy | Balanced accuracy | F1 | Brier |
|---|---:|---:|---:|---:|
| Trained Qwen ensemble | 1.0000 | 1.0000 | 1.0000 | 0.0337 |
| Trained Llama ensemble | 0.5000 | 0.5000 | 0.0000 | 0.2115 |
| Untrained Qwen | 0.5000 | 0.5000 | 0.0000 | 0.3575 |
| Majority constant | 0.5000 | 0.5000 | 0.6667 | 0.5000 |
| Hint-disagreement rule | 0.5000 | 0.5000 | 0.5000 | 0.5000 |

The Qwen ensemble's balanced-accuracy advantage was 50 percentage points over
every primary comparator. The preregistered stratified paired-bootstrap lower
bounds were:

- `0.5000` versus trained Llama ensemble;
- `0.5000` versus untrained Qwen;
- `0.5000` versus majority constant;
- `0.3125` versus hint-disagreement.

Qwen seed balanced accuracies were `1.0000`, `0.90625`, and `1.0000`, so the
result was not rescued by one Qwen seed.

## Critical limitation

The Llama control was highly seed-unstable: its individual balanced accuracies
were `0.5000`, `0.5000`, and `1.0000`. The preregistered probability ensemble
scored `0.5000` because two members collapsed toward opposing constant
decisions. The Qwen-versus-Llama ensemble comparison therefore passes the
literal development gate but does not isolate privileged self-access. It mixes
architecture, tokenizer, model size, quantization, optimization stability, and
arithmetic competence.

The task can also be solved by reasoning about the visible arithmetic, hint,
and target answer. No internal activation is supplied to either explainer.
Accordingly, the result is evidence for reliable local supervised
input-ablation prediction by the trained Qwen configuration, not evidence that
Qwen introspected its hidden computation.

## Disposition

V18 supplies one development candidate. It does not confirm Stage 0C and does
not authorize Stage 1. The exposed corpus, adapters, seeds, and thresholds are
closed.

The next admissible step is a preregistered replication with new sealed
families, a task whose labels cannot be recovered by elementary arithmetic
alone, and stronger cross-model controls that address seed instability. The
replication must preserve prediction locking and must not tune against this
assessment split.

Claim ceiling:
`LocalDevelopmentTrainedLmInputAblationExplainerPilot`. This is not
introspection, self-modeling, faithful natural-language explanation, activation
access, semantic self-knowledge, consciousness, benchmark evidence, production
readiness, Stage 0C confirmation, or Stage 1 authorization.
