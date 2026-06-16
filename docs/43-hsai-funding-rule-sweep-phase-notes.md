# HSAI Funding-Rule Sweep Phase Notes

## Status

Complete and locally verified on Rust 1.74.

This explicit Hyper Sacred AI implementation phase extends only
`crates/hsai-economy-sim` with the funding-rule sweep API from
`docs/41-funding-rule-sweep-spec.md`. It is a backward-compatible simulation
extension: `run(config)` remains the `Even` funding rule and the Rust-confirmed
A5 grid remains unchanged.

## Built

- `FundingRule::{None, Even, ProportionalToBalance}`.
- `run_with_funding(config, rule)`, with `run(config)` defined as
  `run_with_funding(config, FundingRule::Even)`.
- Snapshot-based funding dispatch so the proportional rule is deterministic and
  order-independent.
- `SweepCell` and `sweep(base, policies, rules, seeds)`.
- FS-1..4 unit tests, FSP-1..3 proptests, and a regression test for the recorded
  funding-rule sweep.

## Verification

Commands run:

```sh
rustup run 1.74.0 cargo test -p hsai-economy-sim
rustup run 1.74.0 cargo fmt --all --check
rustup run 1.74.0 cargo clippy -p hsai-economy-sim --all-targets -- -D warnings
```

All passed. `cargo test -p hsai-economy-sim` ran 19 unit/property tests plus
doc-tests.

## A5 Refinement

The sweep confirms that terminal-Gini movement is dominated by the funding rule,
not the currency choice, within this model. Funding-rule spread is 481 per-mille
for demurrage and 474 per-mille for mutual credit, while the largest same-rule
currency spread is 135 per-mille.

## Claim Boundary

Funding rules are probes, not proposals. `ProportionalToBalance` is a deliberately
regressive bracket. The sweep isolates model behavior only; it is not empirical
economic evidence and does not establish that a real economy is regenerative.
