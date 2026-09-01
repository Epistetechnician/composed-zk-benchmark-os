# Recursive update-policy V2 execution record

Date: 2026-08-29.

State slice: `continual-learning-recursive-update-policy-v2`.

## Disposition

The fixed bounded synthetic campaign is `NoCandidate`. All hard guards and the
independent validator passed, but recursive policy selection did not beat the
random policy on the primary selection estimand and did not satisfy the
predeclared compounding rule. This protocol identity is closed. The result does
not support recursive self-improvement or RSI claims.

## Review and custody

- Protocol: `139-recursive-update-policy-v2-protocol.md`
- Protocol SHA-256: `3ce96aad7c0cf570f569556b78c705de0c98d48f489b549aba282e73d9a26e39`
- Contract SHA-256: `5d255d64037f8481b9c4d7ea6288976bcad8da1426e116aeea5c10e4a04a7b76`
- Accepted review receipt:
  `/Users/shaanp/Documents/research-artifacts/continual-learning-recursive-update-policy-v2-review-receipt-20260829.json`
- Review receipt SHA-256: `7218b36a2635a2c06ae94978f95f0d2dc5af6074906976ec52e164f60b254a32`
- Result root:
  `/Users/shaanp/Documents/research-artifacts/continual-learning-recursive-update-policy-v2-20260829`
- Result SHA-256: `3bd854c24bd25b40e4f22f8f8b74bea11a5c2ed35a3887e5708a2844ac2bbc00`
- Result digest field: `0585fb791c50f77afe5d15dd529f1a5a841efeb736355ed5a61f45c59f9efaaf`
- Root contents: `result.json` only.

The root was absent before the accepted receipt was validated, was created at
the declared path, and was not a symlink. No repository result artifact was
written.

## Locked synthetic result

- Factorial: `64` cases, `4` generations, `4` arms, `256` generation rows.
- Classification: `NoCandidate`.
- Cases with hard guards passing: `64/64`.
- Selection advantage `U`: `-0.0011354145513036448`.
- Compounding advantage `G`: `0.004179722339390019`.
- Deterministic bootstrap 95% interval for `G`:
  `[-0.00017505128430102423, 0.00892036498278542]`.
- Mean recursive adaptation slope: `0.013048574489406451`.
- Recursive versus fixed mean adaptation: `-0.0013010966229894086`.
- Primary gate: `false`.
- All hard guards: `true`.

The result fails the random-selection requirement (`U < 0.005`), the
compounding threshold (`G < 0.005`), the bootstrap lower-bound requirement, and
the all-recursive-slopes condition. Under the fixed decision rules this is a
closure, not a tuning prompt.

## Verification and boundaries

- Accepted review receipt validation: pass.
- Contract-check: pass.
- V2 focused tests: `9/9` pass.
- `pnpm --ignore-workspace run lint:fast`: pass.
- Independent validator:
  `python -B experiments/continual_learning/validate_recursive_update_policy_v2.py <root>/result.json`: pass.
- Base state: unchanged; the immutable base digest is retained in every row.
- Rollback: all actual restore-and-compare checks pass at `0.0` error.
- Astral integration: `not_run`.
- GiveMeANode/provider/model-bearing execution: `not_run`.
- ZK/PQC custody proof: `not_run`.

This negative result does not justify a cached-model reversible-adapter run,
Astral integration, GiveMeANode, or ZK/PQC work. Any future continual-learning
work requires a materially new theory and estimand, a new state slice and
protocol, fresh guards, independent review, and separate authorization.

Every mutation in this execution record names state slice
`continual-learning-recursive-update-policy-v2`.
