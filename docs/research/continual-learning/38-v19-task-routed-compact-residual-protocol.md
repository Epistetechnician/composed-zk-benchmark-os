# V19 task-routed compact residual protocol

State slice: `continual-learning-protocol-v19-task-routed-compact-residual`.

Source slice: `continual-learning-protocol-v18-route-boundary-representation`.

## Question

Can task-routed parameter state preserve a learned task without paying the
four-full-adapter cost of the positive V14 adapter-bank control?

V18 showed that repeating a route marker in the prompt did not change shared
replay retention. V19 therefore changes the parameter update path: each task is
trained into its own compact two-layer residual slot, and evaluation routes the
task token to the corresponding slot.

## Fixed contract

- Cached Qwen2.5-0.5B-Instruct-4bit model.
- Seed `20260810`, order `0,1,2,3`, target task `0`.
- Eight training and eight held-out facts per task.
- Thirty-two examples per task update and 160 optimizer iterations.
- AdamW, learning rate `0.0001`, batch size `2`, LoRA, maximum sequence length
  `192`.
- Four compact slots at two layers each: `4 * 2 = 8` layers, matching one
  eight-layer shared adapter in total layer budget.
- Route-boundary prompt contract from V18 remains fixed.

The candidate consumes 128 examples and 640 optimizer iterations across its
four slots, matching the four-update shared panel. The validator measures
actual adapter bytes and requires the compact total to remain within 25% of the
single shared-adapter reference.

## Gates

Candidate advancement requires all of:

```text
task_routed_solvability_floor: acquisition >= 0.75
task_routed_retention_above_naive: routed retention > naive retention
parameter_budget_matched: compact total within 0.75..1.25 of one shared adapter
```

The result remains a local pilot even if all gates pass. The adapter bank is a
positive control, not a breakthrough claim. H100 provisioning is unauthorized
unless a corrected local protocol passes and runtime or memory is then the
demonstrated bottleneck.

## One-run command

```bash
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python experiments/continual_learning/task_routed_compact_residual_preflight.py \
  --model /Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit \
  --output /tmp/continual-learning-model-v19-qwen-seed20260810-order0123 \
  --iters 160
```
