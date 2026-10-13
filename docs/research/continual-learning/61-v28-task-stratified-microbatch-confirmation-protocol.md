# V28 task-stratified microbatch confirmation protocol

State slice: `continual-learning-protocol-v28-task-stratified-microbatch-confirmation`.

Source slice: `continual-learning-protocol-v28-task-stratified-microbatch`.

## Purpose

The first V28 targeted preflight changed the first V27 `20260812` tie cell
(`0,2,3,1`) into a positive local signal. This confirmation applies the same
single changed variable to the second pre-identified V27 tie cell
(`20260812`, order `0,3,1,2`). It is not a new favorable-cell search and does
not expand the V27 matrix.

## Frozen contract

- Same cached Qwen2.5-0.5B-Instruct-4bit model and V28 batch policy.
- Same seed `20260812` and selected fact IDs derived from V26.
- Order `0,3,1,2`, fixed before this run because V27 recorded a tie there.
- Thirty-two actual rows and 160 optimizer iterations per update.
- 128 actual examples and 640 optimizer iterations per arm.
- One shared eight-layer adapter and one persistent AdamW state.
- Same replay selection, prompts, wrappers, learning rate, batch size, and
  sequence length as V28.
- No adaptive tuning, matrix expansion, second model, or H100.

## Decision gate

The confirmation is valid only if replay exposure, optimizer-state custody,
exact budgets, task-stratified batch audits, and matched adapter bytes pass.
The changed design is retained as a candidate only if replay acquisition is at
least `6/8` and replay retention is strictly above no-replay in this frozen
confirmation cell. A positive cell remains local confirmation evidence, not a
replication, SOTA result, breakthrough claim, or H100 authorization.

Pure-data plan output:

`/tmp/continual-learning-model-v28-task-stratified-microbatch-confirmation-plan.json`
