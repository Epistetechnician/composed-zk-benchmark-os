# V39 fixed-optimizer task-order retention replication

State slice: `continual-learning-qwen25-fixed-optimizer-order-replication-v39`.

V39 tests whether the V38 retention result survives noncanonical task orders.
It crosses all three V38 task seeds with three orders frozen before execution:
`0,2,1,3`; `0,3,1,2`; and `0,1,3,2`. Task 0 remains first so acquisition and
post-interference retention remain separated. Tasks 1–3 are the interference
updates in the declared order.

The V37 acquisition campaign remains the immutable source of task manifests
and task-routed adapters. V39 independently re-executes the V38 naive and
bounded-replay sequential controls, recovery, and fresh readout for each
seed/order arm. Model, raw-text serialization, optimizer settings, fixed
optimizer seeds, update budget, replay capacity, and assessment gates remain
unchanged.

Primary metric: replay retention minus naive retention.

Claim ceiling: `LocalDevelopmentOrderReplicationPreflight`.

This phase can support only order-replication evidence for the local mechanism.
It does not establish a general continual-learning result, second-model
replication, provider delivery, production readiness, or accepted scientific
evidence.

## Execution record

The campaign artifact, exact seed/order metrics, hashes, and durable custody
path will be appended only after all nine cases and the independent campaign
validator complete. A failed arm remains a recorded negative result; no
adaptive order or seed selection is permitted.

## Executed result

The first V39 attempt was quarantined at
`/private/tmp/continual-learning-qwen25-fixed-optimizer-order-replication-v39-20260824-r1-incomplete`
after a reusable V38 manifest guard incorrectly required manifest order to
equal execution order. No model result was emitted. The guard was corrected
to validate task identity independently of update order before the sealed r2
campaign.

Campaign root:
`/private/tmp/continual-learning-qwen25-fixed-optimizer-order-replication-v39-20260824-r2`.

Durable custody:
`/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-qwen25-fixed-optimizer-order-replication-v39-20260824-r2`.

The independent campaign validator returned `valid: true`,
`case_count: 9`, and `campaign_eligible: true`. All nine arms passed the
source-acquisition, bank-retention-floor, sequential-acquisition-floor, and
strict replay-over-naive retention gates.

The exact Task 0 results, shown as
`naive acquisition / retention / recovery`, `replay acquisition / retention /
recovery`, and retention delta, are:

- Seed `20260856`: order `0213` = `1.00 / 0.00 / 0.75`, `1.00 / 0.25 / 0.25`, `+0.25`; order `0312` = `1.00 / 0.00 / 0.25`, `1.00 / 0.25 / 0.25`, `+0.25`; order `0132` = `1.00 / 0.00 / 0.25`, `1.00 / 1.00 / 1.00`, `+1.00`.
- Seed `20260857`: order `0213` = `1.00 / 0.00 / 0.75`, `1.00 / 0.25 / 0.25`, `+0.25`; order `0312` = `1.00 / 0.00 / 0.25`, `1.00 / 0.25 / 0.25`, `+0.25`; order `0132` = `1.00 / 0.00 / 0.25`, `1.00 / 1.00 / 0.75`, `+1.00`.
- Seed `20260858`: order `0213` = `1.00 / 0.00 / 0.75`, `1.00 / 0.25 / 0.25`, `+0.25`; order `0312` = `1.00 / 0.00 / 0.25`, `1.00 / 0.25 / 0.25`, `+0.25`; order `0132` = `1.00 / 0.00 / 0.25`, `1.00 / 0.25 / 0.25`, `+0.25`.

Immutable adapter-bank retention was `1.00` in every arm. The replication
supports a robust positive replay-over-naive retention direction across all
orders, while also showing order/seed heterogeneity in effect magnitude and
recovery. The result remains local mechanism replication evidence; it is not
a general continual-learning claim or a single-model scientific confirmation.

The campaign report's internal digest is
`4cc1e0d5b9acae474722dc07906d5f8123e8363a808b00b2a0ab738516b31801`.
The report file SHA-256 is
`3222db7a0cf42fb573d981046d014100df3313f45f9a86c3b3607a3dcd5e91e2` in both
temporary and durable custody.

Provider execution, production operation, network access, second-model
replication, accepted scientific-evidence mutation, and promotion beyond
`LocalDevelopmentOrderReplicationPreflight` were not performed.
