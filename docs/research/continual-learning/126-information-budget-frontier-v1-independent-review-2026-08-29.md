# Independent review: information-budget frontier v1

State slice: `continual-learning-information-budget-frontier-v1`.

Review date: `2026-08-29`.

Review constraint: read-only review; no assessment, provider, or model work was
performed.

## Files reviewed

- `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/docs/research/continual-learning/124-information-budget-frontier-v1-protocol.md`
- `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/docs/research/continual-learning/125-information-budget-frontier-v1-independent-review-packet.md`
- `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/.autoresearch/continual-learning-information-budget-frontier-v1/contract.md`
- `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py`
- `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/autoresearch_information_budget_frontier_v1.py`
- `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/validate_information_budget_frontier_v1.py`
- `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/tests/test_information_budget_frontier_v1.py`

## Ten-item review matrix

| # | Required finding | Result | Exact evidence |
|---:|---|---|---|
| 1 | CPSP is materially distinct from the closed replay, reinitialization, and plasticity-guard family. | PASS | Protocol `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/docs/research/continual-learning/124-information-budget-frontier-v1-protocol.md:7-23`; runner `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py:271-305`. This establishes distinction from the closed family, not novelty relative to orthogonal-gradient literature. |
| 2 | AFFU is a fixed, reproducible estimand that explicitly prices positive protected forgetting. | PASS | Protocol `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/docs/research/continual-learning/124-information-budget-frontier-v1-protocol.md:25-38`; fixed prices are declared at runner `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py:34-52`. |
| 3 | Candidate selection uses fit/tune only and a prediction lock precedes assessment. | FAIL | The driver writes a lock and then invokes assessment without reading or verifying it at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/autoresearch_information_budget_frontier_v1.py:112-119`. The standalone runner permits assessment directly without a lock or review receipt at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py:575-582`. |
| 4 | Assessment data cannot affect candidate selection, risk prices, seeds, orders, or hard guards. | PASS with lock caveat | Fit/tune selection precedes assessment at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/autoresearch_information_budget_frontier_v1.py:59-93`; fixed protocol values are emitted at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py:470-486`. The missing lock enforcement remains a separate blocker. |
| 5 | Untouched, fixed-adapter, and random-projection controls are meaningful. | PASS | Arm declarations at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py:34-52`; arm behavior at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py:283-305` and `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py:324-347`. |
| 6 | Gradient and shadow compute accounting is equalized across arms. | PASS in the runner | Counts are fixed from adaptation length and alpha-grid length at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py:380-412`. The independent validator does not independently recompute the shadow count; that defect is recorded under item 7. |
| 7 | Rollback, order stability, calibration, custody, and validator checks are executable and not placeholder booleans. | FAIL | Rollback compares a snapshot with itself at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py:377-379`. Order stability covers adaptation gain only, not forgetting or AFFU, at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py:417-438`. The validator checks supplied arithmetic and self-authored digests but does not recompute synthetic dynamics or enforce complete coverage at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/validate_information_budget_frontier_v1.py:110-165`. The output path is unrestricted despite the external custody declaration at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/autoresearch_information_budget_frontier_v1.py:40-49`. |
| 8 | The output claim ceiling excludes model, provider, Astral, ZK/PQC, benchmark, and production claims. | PASS | Protocol `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/docs/research/continual-learning/124-information-budget-frontier-v1-protocol.md:67-80`; driver summary `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/autoresearch_information_budget_frontier_v1.py:141-146`. |
| 9 | The implementation does not mutate closed records or reuse closed scientific artifacts as data. | PASS | The new lane is declared separate from the closed family at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/docs/research/continual-learning/124-information-budget-frontier-v1-protocol.md:7-10`; contract scope forbids closed-record mutation and historical scientific inputs at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/.autoresearch/continual-learning-information-budget-frontier-v1/contract.md:11-18`. |
| 10 | The bounded search has a finite candidate and assessment budget. | PASS | Contract `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/.autoresearch/continual-learning-information-budget-frontier-v1/contract.md:37-45`; driver cap and loop `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/autoresearch_information_budget_frontier_v1.py:24-47` and `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/autoresearch_information_budget_frontier_v1.py:59-95`. |

## Blocking defects

1. Assessment is not mechanically gated on an independent review receipt and
   verified prediction lock.
2. Rollback fidelity is a placeholder calculation and can pass without a
   restore operation.
3. Order stability omits protected forgetting and the primary AFFU endpoint.
4. The independent validator does not independently recompute the exact
   synthetic learner, does not require complete trial coverage, and does not
   recompute exact candidate/configuration and shadow-compute bindings.
5. The runner accepts arbitrary output paths, so the declared external custody
   boundary is not enforced.

Required repair is to implement and test each gate, then repeat independent
review before any synthetic assessment. No model, provider, GiveMeANode,
Astral, or ZK/PQC execution is authorized by this review.

Final disposition: `REJECTED_PENDING_REPAIR`

Every mutation in this review artifact touches state slice
`continual-learning-information-budget-frontier-v1`.
