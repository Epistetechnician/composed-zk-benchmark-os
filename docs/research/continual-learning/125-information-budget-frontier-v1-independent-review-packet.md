# Independent review packet: information-budget frontier v1

State slice: `continual-learning-information-budget-frontier-v1`.

Review status: `PENDING_INDEPENDENT_REVIEW`.

An approval must be emitted as structured JSON, not as text presence in a
Markdown report. The receipt schema is
`continual-learning-information-budget-frontier-review-receipt-v1` and must
contain this exact state slice, this packet's SHA-256 digest, reviewer role
`independent`, all ten check keys with value `PASS`, an empty
`blocking_defects` array, and disposition `APPROVED_FOR_SYNTHETIC_RUN`.

## Review scope

The reviewer must inspect the following files without changing them:

- `docs/research/continual-learning/124-information-budget-frontier-v1-protocol.md`
- `.autoresearch/continual-learning-information-budget-frontier-v1/contract.md`
- `experiments/continual_learning/information_budget_frontier_v1.py`
- `experiments/continual_learning/autoresearch_information_budget_frontier_v1.py`
- `experiments/continual_learning/validate_information_budget_frontier_v1.py`
- `experiments/continual_learning/tests/test_information_budget_frontier_v1.py`

## Required findings

The review must state pass or fail for each item:

1. The CPSP mechanism is materially distinct from the closed replay,
   reinitialization, and plasticity-guard family.
2. AFFU is a fixed, reproducible estimand that explicitly prices positive
   protected forgetting.
3. Candidate selection uses fit/tune only and a prediction lock precedes
   assessment.
4. Assessment data cannot affect candidate selection, risk prices, seeds,
   orders, or hard guards.
5. Untouched, fixed-adapter, and random-projection controls are meaningful.
6. Gradient and shadow compute accounting is equalized across arms.
7. Rollback, order stability, calibration, custody, and validator checks are
   executable and not represented by placeholder booleans.
8. The output claim ceiling excludes model, provider, Astral, ZK/PQC,
   benchmark, and production claims.
9. The implementation does not mutate closed records or reuse closed
   scientific artifacts as data.
10. The bounded search has a finite candidate and assessment budget.

## Decision rule

No synthetic assessment run may begin unless every item passes or the review
records a concrete blocking defect. A local test pass is not independent
review. The reviewer must include exact file and line references for every
finding in the review report and emit the structured receipt only when every
check passes. The final disposition is `APPROVED_FOR_SYNTHETIC_RUN` or
`REJECTED_PENDING_REPAIR`.

This packet itself is only review infrastructure. It does not authorize model
loading, provider execution, GiveMeANode, Astral integration, ZK/PQC work, or
promotion beyond `LocalDevelopmentInformationBudgetFrontierSyntheticOnly`.

Every mutation in this packet touches state slice
`continual-learning-information-budget-frontier-v1`.
