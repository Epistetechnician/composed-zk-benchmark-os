# HSAI Economy Simulation Phase Notes

## Status

Complete and locally verified on Rust 1.74.

This explicit Hyper Sacred AI implementation phase adds only the standalone
`hsai-economy-sim` crate. The crate is a deterministic integer simulation
harness over the shipped HSAI economy; it adds no protocol primitive and makes no
empirical economic claim.

## Built

- `crates/hsai-economy-sim/` — new crate, path-depending on the shipped
  `hsai-claim-envelope`, `hsai-agent-case`, `hsai-distinct-agent`, and
  `hsai-economy` crates.
- Inline splitmix64 PRNG (`next_u64`).
- Fixed-point per-mille metrics: `gini_permille`, `velocity_permille`, and
  `active_permille`.
- `PolicyChoice`, `SimConfig`, `TickMetrics`, `SimReport`, and
  `run(config) -> SimReport`.
- Deterministic simulation order: earn -> gift -> fund -> decay, using the
  shipped `Economy` API.
- S1-S6 unit tests, SP-1..4 proptests, and an A5 grid regression test tying the
  ledger measurements to the Rust `run` path.

## Verification

Commands run:

```sh
rustup run 1.74.0 cargo test -p hsai-economy-sim
rustup run 1.74.0 cargo fmt --all --check
rustup run 1.74.0 cargo clippy -p hsai-economy-sim --all-targets -- -D warnings
```

All passed. `cargo test -p hsai-economy-sim` ran 11 unit/property tests plus
doc-tests.

## A5 Measurement

The small grid from `docs/38-economy-simulation-spec.md` is recorded in
`docs/research/assumption-ledger.md` as a Rust-confirmed A5 simulation update.
The result is model behavior only: "regenerative" remains an operational
threshold chosen by the experimenter, not a claim made by the harness.

## Claim Boundary

A simulation outcome is model behavior, not empirical evidence. This phase does
not modify `hsai-economy`, does not add pool demurrage, does not connect external
rails, does not produce benchmark output, and does not claim a real economy is
regenerative.
