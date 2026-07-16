# Statebook P2 Payoff And Residual Engine Boundary

Date: 16 July 2026.

Status: documentation-first boundary complete; implementation requires a
separate commit.

Named boundary state slice:
`statebook-p2-payoff-residual-engine-boundary`.

Future implementation state slice:
`statebook-p2-payoff-residual-engine`.

## Objective

Evaluate only P1-validated terminal indicator contracts over one explicit finite
scalar state domain, compose exact rational positions into settlement-asset
vectors, and report target-minus-candidate residuals for every declared state.

P2 addresses payoff completeness on a declared domain. It does not address
semantic completeness beyond P1, execution completeness, capital completeness,
settlement completeness, assurance completeness, recovery completeness, or
global economic equivalence.

## Frozen payoff order

For a contract and declared observation:

```text
raw_contract_payoff =
  indicator(comparator, observation)
  * payoff_amount
  * settlement_unit_scale

rounded_contract_payoff =
  quantize(raw_contract_payoff, rounding_quantum, rounding_mode)

position_payoff =
  position_quantity * rounded_contract_payoff
```

`payoff_amount` counts settlement units. `settlement_unit_scale` converts one
unit into settlement-asset units. Contract rounding occurs before an external
portfolio coefficient is applied. Every operation is checked exact rational
arithmetic; floating point, saturation, silent truncation, and implicit asset
conversion are forbidden.

## Closed supported domain

P2 may support only:

- opaque P1 `ValidatedContract` inputs;
- the P1 indicator payoff form;
- `<`, `<=`, `=`, `>=`, `>`, and bounded ranges with all four endpoint rules;
- one exact scalar observation per uniquely named state;
- exact signed rational target and candidate quantities;
- at most 256 declared states and 64 input candidate legs;
- deterministic duplicate-leg aggregation by `StateKeyV1`;
- negative, zero, and positive portfolio coefficients;
- multiple settlement assets as a non-netted asset vector;
- `toward_zero`, `floor`, `ceiling`, and `half_even` exact quantization.

P2 may not add fixed, linear, option, perpetual, barrier, path-dependent,
physical-delivery, basket, exercise, discretionary-resolution, lifecycle, or
default-contingent cashflow forms.

## Observation-coordinate compatibility

A candidate leg may share the target's declared observation only when all of
these P1-normalized fields match exactly:

- reference namespace, identifier, and unit;
- benchmark administrator;
- methodology version and SHA-256;
- fallback rule;
- calendar and timezone;
- observation start and end;
- sampling rule;
- disruption rule;
- correction rule.

Comparator, payoff amount, settlement asset, unit scale, rounding quantum, and
rounding mode may differ because they define the payoff algebra being compared.
Any coordinate mismatch makes every declared state unsupported for that leg.
The engine must return `Incomplete`; it must not omit the leg or emit a plausible
partial numeric residual.

## Exact arithmetic contract

P2 may add checked rational negation, addition, subtraction, multiplication,
division, absolute value, zero testing, scaled-integer conversion, and exact
quantization to `SignedRational`.

Multiplication must cross-cancel before checked products. Addition must reduce
denominator factors before checked products. Division by zero and every
unrepresentable `i128`/`u128` intermediate must fail closed as
`ExactError::Overflow` or the existing exact error appropriate to the input.
Zero remains canonical `0/1`; denominators remain positive and reduced.

Half-even quantization must treat positive and negative ties symmetrically and
must compare remainder with `denominator - remainder` rather than multiplying
the remainder by two.

## Public result vocabulary

The implementation may add opaque, `Serialize`-only V1 types for:

- a declared terminal state and bounded declared state domain;
- a borrowed contract position;
- an aggregated position receipt retaining every contributing validated
  contract digest;
- per-state evaluated or unsupported status;
- per-asset exact residuals;
- per-asset worst absolute residual and every tying state id;
- payoff assumptions and unmodeled residual classes;
- the report status `ExactOnDeclaredDomain`,
  `ApproximateOnDeclaredDomain`, or `Incomplete`.

`ExactOnDeclaredDomain` requires every state to evaluate and every asset
residual to equal zero. `ApproximateOnDeclaredDomain` requires every state to
evaluate and at least one nonzero asset residual. `Incomplete` is mandatory for
any incompatible coordinate, unsupported state, or exact arithmetic failure.

The report must always disclose finite-domain, final-corrected-observation,
rounding-order, and no-asset-conversion assumptions. It must disclose unmodeled
basis, timing, FX, default, legal, liquidity, between-state jump, and
outside-domain residual classes. Zero residual on the declared states cannot
remove these disclosures.

## Determinism and identity

Candidate legs aggregate by `StateKeyV1`, not by source lineage. Exact
quantities add, zero aggregates disappear, and all contributing validated
contract digests remain in a sorted set. Candidate order and state insertion
order must not affect the report.

The declared-state-domain digest uses a new domain separator:

```text
statebook:declared-state-domain:v1\0
```

Its preimage binds schema version, sorted ASCII state ids, and canonical signed
numerator/unsigned denominator bytes. It does not change or extend the P1
`StateKeyV1` preimage. The frozen P1 701-byte preimage, StateKey digest, validated
contract digest, schema, and fixture files must remain byte-identical.

## Frozen scenarios

The implementation must cover:

1. `>= threshold` equals `= threshold + > threshold` on below/equal/above states;
2. `>= threshold` versus `> threshold` leaves one unit at equality;
3. two half-quantity duplicate target legs aggregate to one exact leg;
4. `= threshold` equals `>= threshold - > threshold`;
5. USD versus USDC remains two non-netted residual entries and discloses FX;
6. a reference-coordinate mismatch yields only unsupported states and
   `Incomplete`;
7. positive and negative exact rounding ties for all four modes;
8. every comparator and range endpoint boundary;
9. candidate aggregation, payoff multiplication, denominator, and quantization
   overflow paths;
10. 256-state/64-leg acceptance and 257-state/65-leg rejection;
11. candidate permutation, state insertion, split/merge, and additive-inverse
    invariance;
12. unchanged P1 StateKey and validated-contract golden vectors.

## Authorized future implementation paths

The future implementation may change only:

- `crates/statebook-core/src/lib.rs`;
- `crates/statebook-core/src/exact.rs`;
- `crates/statebook-core/src/model.rs`, only for additive internal accessors or
  ordering derives needed by P2, never P1 schema or identity changes;
- new `crates/statebook-core/src/payoff.rs`;
- `crates/statebook-core/tests/claim_boundary.rs`;
- new `crates/statebook-core/tests/payoff_residual.rs`;
- new small synthetic fixtures under
  `crates/statebook-core/tests/fixtures/payoff_residual_vectors_v1.json`;
- `docs/statebook-p2-payoff-residual-engine-implementation-notes.md`;
- `README.md`;
- `AGENTS.md`;
- `docs/12-task-list.md`;
- `docs/90-whole-codebase-validation-report.md`.

No dependency or Cargo metadata change is authorized.

## Acceptance gates

- P1 fixtures and golden bytes remain unchanged;
- exact arithmetic and rounding fail closed on every overflow;
- all frozen payoff scenarios pass;
- unsupported states cannot produce exact or approximate status;
- incompatible legs emit no partial residual;
- multi-asset residuals never net through an implicit numeraire;
- package formatting, tests, and warning-denied Clippy pass;
- Statebook claim-boundary and repository docs/hygiene tests pass;
- clean-tree workspace tests run;
- clean-tree workspace Clippy findings outside P2 are reported, not absorbed;
- independent exact-arithmetic and scope/claim-boundary reviews complete.

## Nonclaims

P2 creates no order book, price, fill, slippage, optimization, ranking, routing,
execution, margin, collateral, liquidation, funding, fee, custody, signing,
pause, withdrawal, transfer, settlement, legal enforceability, default
realization, oracle truth, live source, filesystem write, process, network,
HSAI, zkbench, accepted Evidence Ledger, benchmark, Level2+, proof,
semantic-correctness, production-readiness, SOTA, independent-verification,
external-audit, or full-security capability or claim.
