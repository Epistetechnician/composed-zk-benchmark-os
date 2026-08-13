# V29 replay-anchored temporal confirmation protocol

State slice: `continual-learning-protocol-v29-replay-anchored-temporal-confirmation`.

Source slice: `continual-learning-protocol-v29-replay-anchored-temporal-microbatch`.

## Purpose

V29 produced a positive local signal on the frozen V28 tie cell
`20260812 / 0,3,1,2`. This confirmation applies the identical V29 temporal
schedule to the other V27 `20260812` tie cell, order `0,2,3,1`, which was
fixed before this run. It is a two-cell robustness check, not a favorable-cell
selection or matrix expansion.

## Frozen contract

- Same cached Qwen2.5-0.5B-Instruct-4bit model and V29 temporal policy.
- Same seed `20260812`, selected fact IDs, prompts, and balanced replay policy.
- Order `0,2,3,1`, fixed by the prior V27 tie result.
- Thirty-two actual rows and 160 optimizer iterations per update.
- 128 actual examples and 640 optimizer iterations per arm.
- One shared eight-layer adapter and one persistent AdamW state.
- Same learning rate, batch size, sequence length, and no random batch
  permutation as V29.
- No adaptive tuning, matrix expansion, second model, or H100.

## Decision gate

The confirmation is valid only if temporal batch audits, replay exposure,
optimizer-state custody, exact budgets, matched adapter bytes, and acquisition
pass. Replay retention must be strictly above no-replay to confirm the V29
candidate. Even if positive, this confirms only the two pre-identified local
tie cells; it does not authorize a general claim or H100.
