# Independent review r2: information-budget frontier v1

State slice: `continual-learning-information-budget-frontier-v1`.

Review date: `2026-08-29`.

Review mode: read-only. No assessment, provider, or model work was performed.

## Files reviewed

- `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/docs/research/continual-learning/124-information-budget-frontier-v1-protocol.md`
- `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/docs/research/continual-learning/125-information-budget-frontier-v1-independent-review-packet.md`
- `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/docs/research/continual-learning/126-information-budget-frontier-v1-independent-review-2026-08-29.md`
- `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/.autoresearch/continual-learning-information-budget-frontier-v1/contract.md`
- `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py`
- `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/autoresearch_information_budget_frontier_v1.py`
- `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/validate_information_budget_frontier_v1.py`
- `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/tests/test_information_budget_frontier_v1.py`

## Ten-item review matrix

| # | Required finding | Result | Exact evidence |
|---:|---|---|---|
| 1 | CPSP is materially distinct from the closed replay, reinitialization, and plasticity-guard family. | PASS | The separate geometry-based theory is declared at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/docs/research/continual-learning/124-information-budget-frontier-v1-protocol.md:7-23`; implementation is at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py:272-306`. This establishes distinction from the closed family, not novelty relative to existing orthogonal-gradient methods. |
| 2 | AFFU is a fixed, reproducible estimand that explicitly prices positive protected forgetting. | PASS | The endpoint formula and fixed risk prices are declared at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/docs/research/continual-learning/124-information-budget-frontier-v1-protocol.md:25-38` and `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py:34-52`. |
| 3 | Candidate selection uses fit/tune only and a prediction lock precedes assessment. | FAIL | Assessment now requires receipt and lock arguments at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py:475-490`, but the driver hardcodes the prior rejected review artifact at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/autoresearch_information_budget_frontier_v1.py:120-126`; that artifact ends with `REJECTED_PENDING_REPAIR` at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/docs/research/continual-learning/126-information-budget-frontier-v1-independent-review-2026-08-29.md:52`. The lock validator checks only state/type/candidate name/split at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py:319-327`, not the exact fit/tune artifact or full candidate configuration. |
| 4 | Assessment data cannot affect candidate selection, risk prices, seeds, orders, or hard guards. | PASS with gate caveat | Candidate scoring occurs on fit/tune before assessment at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/autoresearch_information_budget_frontier_v1.py:64-98`; assessment is invoked afterward at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/autoresearch_information_budget_frontier_v1.py:120-130`; fixed protocol values are emitted at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py:512-537`. The broken receipt/lock gate prevents a valid assessment rather than leaking assessment data. |
| 5 | Untouched, fixed-adapter, and random-projection controls are meaningful. | PASS | Arm declarations and candidate controls are fixed at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py:34-52`; distinct arm behavior is implemented at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py:283-306` and `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py:330-369`. |
| 6 | Gradient and shadow compute accounting is equalized across arms. | PASS | The runner fixes gradient and shadow counts at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py:399-435`; the independent recomputation binds the same counts at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/validate_information_budget_frontier_v1.py:161-254` and `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/validate_information_budget_frontier_v1.py:301-324`. |
| 7 | Rollback, order stability, calibration, custody, and validator checks are executable and not placeholder booleans. | FAIL | The rollback inverse and order/AFFU comparison are now implemented at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py:399-403` and `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py:441-470`. The independent validator now recomputes trials and enforces observed-split coverage at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/validate_information_budget_frontier_v1.py:161-324` and `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/validate_information_budget_frontier_v1.py:387-430`. However, review/lock hashes are only shape-checked at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/validate_information_budget_frontier_v1.py:431-435`, the receipt gate is text-based at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py:309-316`, candidate selection checks tune guards but not fit guards at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/autoresearch_information_budget_frontier_v1.py:71-74`, and the standalone result writer still accepts an arbitrary path at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/information_budget_frontier_v1.py:623-626`. |
| 8 | The output claim ceiling excludes model, provider, Astral, ZK/PQC, benchmark, and production claims. | PASS | The ceiling and exclusions are declared at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/docs/research/continual-learning/124-information-budget-frontier-v1-protocol.md:67-80` and emitted by the driver at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/autoresearch_information_budget_frontier_v1.py:152-157`. |
| 9 | The implementation does not mutate closed records or reuse closed scientific artifacts as data. | PASS | The new lane remains explicitly separate from the closed family at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/docs/research/continual-learning/124-information-budget-frontier-v1-protocol.md:7-10`; the contract forbids closed-record mutation and historical scientific inputs at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/.autoresearch/continual-learning-information-budget-frontier-v1/contract.md:11-18`. |
| 10 | The bounded search has a finite candidate and assessment budget. | PASS | The five-candidate/one-assessment bound is declared at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/.autoresearch/continual-learning-information-budget-frontier-v1/contract.md:37-45` and enforced at `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/autoresearch_information_budget_frontier_v1.py:24-53` and `/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/autoresearch_information_budget_frontier_v1.py:64-101`. |

## Blocking defects

1. The driver points assessment at the rejected r1 review artifact. It must
   reference a separately approved r2 receipt after that receipt exists.
2. Review and prediction-lock validation must bind exact artifact digests,
   packet identity, reviewer disposition, full candidate configuration, and
   the fit/tune result artifact. Text presence and 64-character strings are
   insufficient.
3. Candidate selection must enforce hard guards over both fit and tune, not
   tune only.
4. The standalone writer/CLI must either enforce the declared custody root or
   be removed from the protocol surface; otherwise artifacts can be emitted
   outside the custody boundary.
5. Tests must exercise rejected/approved receipt binding, tampered lock
   contents, fit-guard failure, rollback after a nonzero update, complete
   coverage rejection, and custody-path rejection.

Required disposition remains blocked until these repairs pass a fresh
independent review. No assessment, provider, model, GiveMeANode, Astral, or
ZK/PQC execution is authorized.

Final disposition: `REJECTED_PENDING_REPAIR`

Every mutation in this review artifact touches state slice
`continual-learning-information-budget-frontier-v1`.
