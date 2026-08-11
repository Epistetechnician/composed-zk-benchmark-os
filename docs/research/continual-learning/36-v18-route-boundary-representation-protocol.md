# V18 route-boundary representation protocol

State slice: `continual-learning-protocol-v18-route-boundary-representation`.

Source slice: `continual-learning-protocol-v17-task-keyed-readout-feasibility`.

## Question

Does repeating the exact task route marker immediately before the answer boundary
preserve task identity in the learned shared representation, while all data,
optimizer, seed, order, model, and update budgets remain fixed?

V17 showed that a task-keyed readout cannot recover information absent from the
shared representation. V18 therefore changes the representation interface at
the prompt boundary, not the readout after training.

## Fixed contract

- Model: cached Qwen2.5-0.5B-Instruct-4bit.
- Seed: `20260810`.
- Task order: `0,1,2,3`; target task remains task `0`.
- Eight train and eight held-out facts per task.
- Thirty-two examples per update; 160 objective iterations.
- AdamW, learning rate `0.0001`, batch size `2`, eight layers, LoRA, maximum
  sequence length `192`.
- Naive, balanced replay, immutable task-adapter bank, no-update, context-only,
  and retrieval controls are retained.

## Sole changed variable

The residue-only prompt keeps the task token and derived residue visible and
adds the exact route marker immediately before `Answer:`:

```text
Use the task's residue-to-option codebook and return only the option letter.
Task route binding: T0.
Answer:
```

Training and assessment use byte-identical prompt construction. Raw compositional
pairs remain absent. The validator checks every emitted training row for route
binding and checks replay audit IDs/counts and target-task accuracy after every
update.

## Advancement gates

The run is a local pilot only. Candidate advancement requires the solvability
floor (`naive` acquisition at least `0.75`) and replay retention strictly above
naive retention. The adapter bank is reported as a positive control, not as
evidence that replay works. Any tied or negative replay result stops the line;
the next change must be a task/update protocol redesign. No H100 is authorized
unless a corrected local protocol first passes replay retention and runtime or
memory is then the measured bottleneck.

## One-run command

```bash
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python experiments/continual_learning/route_boundary_representation_preflight.py \
  --model /Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit \
  --output /tmp/continual-learning-model-v18-qwen-seed20260810-order0123 \
  --iters 160
```
