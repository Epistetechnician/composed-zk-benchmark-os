# Functional-plasticity frontier V1 execution record

Date: 2026-08-30.

State slice: `continual-learning-functional-plasticity-frontier-v1`.

## Disposition

The fixed exact-synthetic campaign is `NoCandidate`. The function-space
projection treatment did not beat the fixed-update control on the locked
post-adaptation fresh-task plasticity estimand. All hard guards and the
independent aggregate validator passed. This result closes this protocol
identity and is not a tuning prompt.

## Bound protocol and custody

- Protocol: `functional-plasticity-frontier-v1-protocol.md`
- Protocol SHA-256: `e80cd2c5997352f6362556ff274ed65e64dfb4301b51cef62787be40f36dba2e`
- Contract: `.autoresearch/continual-learning-functional-plasticity-frontier-v1/contract.md`
- Contract SHA-256: `32eb94cbd481d3d0699fc45ce3466f864efb5ef43562511ff65b75a5e87dfa87`
- Review packet SHA-256: `8e328e40a647dc5543ad9df88436ee25cae5d4d9ad9ffaa228af0a5508c60a8b`
- Review receipt: `functional-plasticity-frontier-v1-independent-review-2026-08-30.json`
- Review verdict: `ACCEPT`; execution authorization field: `false`
- Result root: `/Users/shaanp/Documents/research-artifacts/continual-learning-functional-plasticity-frontier-v1-20260830-r1`
- Result SHA-256: `4a83a60a2f18e50d8249439d21c3b6da832c7974bef2db566b353f6d97e9f723`
- Root contents: `result.json` only

The root was absent before execution, was created at the declared path, was
not a symlink, and contains no raw vectors, targets, features, or intermediate
state.

## Locked campaign result

- Case groups: `32`
- Case-arm records: `96`
- Arms: `untouched_base`, `fixed_adapter`, `function_projected`
- Primary estimand `G_FP`: `-0.0004941255812591174`
- Bootstrap 95% interval: `[-0.0015933699393070782, 0.0005462313554810875]`
- Function-projected wins: `16/32`
- Mean probe gain, untouched base: `0.013317529322043387`
- Mean probe gain, fixed adapter: `0.013811654903302507`
- Mean probe gain, function projected: `0.013317529322043388`
- Mean assessment gain, function projected: `4.87890977618477e-19`
- Mean fit adaptation gain, function projected: `-1.0733601507606494e-17`
- Mean protected forgetting, function projected: `8.131516293641283e-18`
- Primary gate: `false`
- All hard guards: `true`

The treatment tied the untouched base at floating-point precision on the
primary probe mean and lost to fixed updates. The negative primary effect,
non-positive bootstrap lower bound, and `16/32` win count fail the fixed
decision rule. No threshold, seed, order, split, endpoint, or guard was
changed after the result.

## Verification

- Focused tests: `8 passed`
- Contract check: `PASS`
- Independent validator: `PASS`
- Fast gate: `pnpm --ignore-workspace run lint:fast` `PASS`
- Base-state digest: invariant across all records
- Rollback: measured error within `1e-12` in every record
- Function-preservation guard: passed for every treatment record
- Astral integration: `not_run`
- GiveMeANode/provider/model-bearing execution: `not_run`
- Base-weight or adapter update: `not_run`
- ZK/PQC custody proof: `not_run`

This is bounded exact-synthetic infrastructure evidence only. It does not
establish model-scale continual-learning superiority, recursive
self-improvement, AGI, introspection, causal self-modeling, truth, safety,
production readiness, or benchmark superiority. Any future continuation
requires a materially new theory and estimand, a new state slice, fresh guards,
and independent review. The closed Astral V48, GiveMeANode, base-weight, and
ZK/PQC boundaries remain unchanged.

Every mutation governed by this record touches state slice
`continual-learning-functional-plasticity-frontier-v1`.
