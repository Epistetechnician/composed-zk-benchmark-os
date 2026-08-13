# V29 replay-anchored temporal replication protocol

State slice: `continual-learning-protocol-v29-replay-anchored-temporal-replication`.

Source slice: `continual-learning-protocol-v29-replay-anchored-temporal-confirmation-preflight`.

## Purpose

The V29 anchor and its confirmation both passed on the two pre-identified
`20260812` V27 tie cells. This protocol tests the unchanged V29 mechanism on
the seven remaining cells of the original three-seed by three-order matrix.
The two V29 executions are retained as validated anchors and are not rerun.

## Frozen matrix

- Seeds: `20260811`, `20260812`, `20260813`.
- Orders: `0,1,2,3`; `0,2,3,1`; `0,3,1,2`.
- Excluded validated V29 anchor cells: `20260812 / 0,3,1,2` and
  `20260812 / 0,2,3,1`.
- Fresh cells: exactly seven, each run once.
- Same cached Qwen2.5-0.5B-Instruct-4bit model, fact IDs, replay policy,
  temporal batch policy, shared adapter, optimizer, seed stream, budgets,
  prompts, and assessment.
- No adaptive tuning, favorable-cell selection, second model, or H100.

## Strict gate

All seven fresh cells plus the two validated V29 anchors must pass acquisition,
replay exposure, optimizer-state custody, exact examples and steps, matched
adapter bytes, temporal audits, and replay retention strictly above no-replay.
Failure of any cell rejects robust V29 replication and requires a new protocol
decision. Passing the matrix remains a local benchmark result until external
review and independent replication.

Pure-data matrix plan:

`/tmp/continual-learning-model-v29-replay-anchored-temporal-replication-plan.json`
