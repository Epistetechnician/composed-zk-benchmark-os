# Sequential retention and recovery protocol v1

Status: `LocalDevelopmentProtocolHarnessOnly`

State slice: `continual-learning-sequential-retention-recovery-v1`.

## Purpose

Create a measurable continual-learning endpoint before introducing a model,
training method, GPU allocation, or external data. The protocol must separate
knowledge acquisition from retention, source-context dependence, and recovery
after forgetting.

## Locked design

- Four deterministic, disjoint fact families are generated from a pinned seed.
- Task 0 is acquired first; its source context is removed before evaluation.
- Tasks 1–3 are then applied as interference updates.
- Task 0 is evaluated again with no source context.
- Task 0 is explicitly reacquired and evaluated a third time.
- Every endpoint uses a fresh pure evaluator over exact key/value answers.
- Controls are `no_update`, `context_only`, `naive_sequential`, `replay`, and
  `retrieval`.
- Replay is bounded by a pinned capacity; retrieval is an intentionally strong
  non-parametric upper control, not a neural-learning claim.

## Primary metrics

- Acquisition accuracy after the first update with context removed.
- Retention accuracy after interference with context removed.
- Forgetting delta: acquisition minus retention.
- Recovery accuracy after explicit reacquisition.
- Context dependence: acquisition with context minus acquisition without context.

## Advancement gates

1. The task manifest, strategy panel, denominators, and context-removal list
   validate mechanically.
2. The harness is deterministic for a repeated configuration.
3. The context-only control scores zero after source removal.
4. The naive sequential control forgets Task 0 and recovers after reacquisition.
5. Replay never exceeds its declared memory capacity.

Passing these gates authorizes only a future model-specific benchmark design.
It does not establish neural continual learning, transfer, SOTA, production
readiness, profitability, or a breakthrough.

## Next bounded experiment

Replace the deterministic learner with one locally cached model and a frozen
update interface. Keep the same task manifest, source-removal boundary,
fresh-evaluator restart, strategy labels, and three independent update-order
seeds. No adaptive tuning on the assessment split is permitted.
