# Statebook P2 Payoff And Residual Engine Implementation Notes

Date: 16 July 2026.

Status: implemented locally.

Named state slice: `statebook-p2-payoff-residual-engine`.

## Outcome

`statebook-core` now evaluates only P1-validated terminal indicator contracts
over an explicit finite scalar state domain. It composes exact rational target
and candidate quantities, applies contract unit scale and contract-level exact
rounding, and returns target-minus-candidate residuals as non-netted
settlement-asset vectors.

The output status is deliberately scoped to `ExactOnDeclaredDomain`,
`ApproximateOnDeclaredDomain`, or `Incomplete`. It is not a claim of global
economic equivalence and does not populate execution, capital, settlement,
assurance, or recovery completeness.

## Implemented surface

- checked rational negation, absolute value, addition, subtraction,
  multiplication, division, scaled-integer conversion, and exact quantization;
- GCD reduction before denominator products and cross-cancellation before
  numerator and denominator multiplication;
- exact `toward_zero`, `floor`, `ceiling`, and `half_even` quantization,
  including symmetric negative ties;
- bounded domains of one through 256 uniquely named exact scalar states;
- at most 64 candidate legs, deterministic StateKey aggregation, exact
  duplicate quantity addition through canonical exact-opposite cancellation
  and a fixed-width checked fold, zero-aggregate removal, and retained source
  receipt digests;
- strict target/candidate observation-coordinate comparison over all fourteen
  P1 reference and observation fields;
- exact indicator evaluation for every P1 comparator and range endpoint rule;
- non-netted residual maps by settlement asset and per-asset worst absolute
  residuals with every tying state id;
- typed whole-report fail closure for coordinate mismatch, aggregation
  overflow, evaluation overflow, quantization overflow, or unrepresentable
  worst-case comparison;
- fixed finite-domain, normalized-observation, rounding-order, and no-conversion
  assumptions plus all eight P2 unmodeled residual classes.

Any incompatible coordinate or material arithmetic failure makes every state
unsupported and removes all numeric residual and worst-case output. A partial
portfolio is never presented as a valid approximation.

Same-StateKey quantities are collected before arithmetic. Canonical rationals
with equal denominator and magnitude cancel across opposite signs first. The
remaining terms sort by denominator, unsigned numerator magnitude, and sign,
then fold through checked `i128`/`u128` addition. This representation-defined
order makes every caller permutation produce the same result while preserving
the P2 fixed-width failure boundary. `i128::MAX + 1 - 1` and
`i128::MIN - 1 + 1` succeed because the exact opposites cancel; a genuine final
overflow or a canonical unrepresentable intermediate returns `Incomplete`.
Domain construction consumes incrementally and rejects on the 257th item
without pulling a 258th item from the caller's iterator.

## Deterministic fixture

`payoff_residual_vectors_v1.json` freezes the baseline P1 indicator payout,
three-state domain, exact decompositions, boundary residual, non-netted USD and
USDC residual, coordinate mismatch, and positive and negative rounding ties.

The sorted declared-domain digest is:

```text
67cb8e1807cd3e619f73d569f70de494ef60610f4d44acea236b0ee006e45e6a
```

The P1 identity remains unchanged:

```text
StateKeyV1 = f1662f3fb5a10c074680c0baf76ba488b7230337456358be92f3127d8a632c08
canonical preimage length = 701 bytes
```

No P1 fixture, canonical tag, field ordering, source schema, normalization
profile, StateKey preimage, or validated-contract digest algorithm changed.

## Focused validation

```text
CARGO_INCREMENTAL=0 cargo test -p statebook-core --all-features
CARGO_INCREMENTAL=0 cargo clippy -p statebook-core --all-targets --all-features -- -D warnings
cargo fmt --all -- --check
```

The package test surface covers exact arithmetic, rounding ties, all comparator
and range boundaries, exact and approximate decompositions, duplicate and
signed positions, order invariance, additive cancellation, resource limits,
multi-asset non-netting, coordinate mismatch, four arithmetic failure classes,
bounded implementation-diverse reference arithmetic, claim-boundary scanning,
and the unchanged P1 golden vectors.

## Claim ceiling

This is local fixture-backed payoff regression evidence over finite declared
states. It creates no other payoff form, order book, price, fill, optimization,
routing, execution, margin, collateral, liquidation, funding, fee, custody,
signing, pause, external value movement, legal enforcement, default
realization, oracle-truth, live-source, filesystem-write, process, network,
HSAI, zkbench, accepted Evidence Ledger, benchmark, proof, independent audit,
semantic-correctness, production-readiness, SOTA, or full-security capability or
claim.
