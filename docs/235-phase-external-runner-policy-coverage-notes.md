# Phase 235 External Runner Policy Coverage Notes

## State Slice

Phase 235 is the external-runner policy coverage tranche for
`crates/zkbench-core/src/external_runner/policy.rs`.

This slice is limited to additive Rust tests under `crates/zkbench-core/tests/`
and navigation/status updates under `docs/`, `README.md`, and `AGENTS.md`.

## Purpose

Phase 234 routed the next local coverage target to
`external_runner/policy.rs` after `mutation/invariant_weakening.rs` reached
`100.00%` line coverage.

The Phase 235 missing-line audit found uncovered reachable paths in:

- the public Phase H policy constructor helper;
- empty policy id validation;
- elevated policy claim-boundary validation;
- claim-boundary-policy mismatch validation;
- missing manual-review gate validation;
- absolute-path flag validation.

## Implemented Coverage

Phase 235 adds focused tests to
`crates/zkbench-core/tests/external_runner_policy.rs`:

- `phase_h_default_and_manual_handoff_policy_helpers_are_bounded`;
- `policy_validation_reports_identity_boundary_gate_and_path_flags`.

The tests keep the external-runner policy surface hermetic and assert that the
manual-handoff helper remains non-live, that the Phase H default helper matches
the default builder, and that reachable validator rejection paths report their
documented issue paths.

## Coverage Result

Baseline before Phase 235:

- `external_runner/policy.rs`: `91.18%` region / `93.75%` function /
  `85.78%` line coverage.
- `zkbench-core` package total: `91.67%` region / `87.59%` function /
  `93.37%` line coverage.

Measured after Phase 235:

- `external_runner/policy.rs`: `98.82%` region / `100.00%` function /
  `97.63%` line coverage.
- `zkbench-core` package total: `91.72%` region / `87.64%` function /
  `93.47%` line coverage.

## Remaining Cap

The local missing-line report still lists `external_runner/policy.rs` lines
417-421. Those lines are the explicit Level2+ actual-claim rejection branch in
`validate_external_runner_policy`.

This branch is structurally capped by
`ExternalClaimBoundaryPolicy::permits_actual_claim_boundary`, which already
rejects Level2+ actual claim boundaries through the Phase H
`phase_h_actual_claim_allowed` guard before the validator can reach the nested
Level2+ branch. Phase 235 does not force that branch by weakening the public
guard or adding test-only entry points.

## Claim Boundary

This phase proves only that the local Rust test suite now exercises the
reachable external-runner policy constructor and validation rejection paths
listed above.

It does not prove semantic correctness, production readiness, live external
runner safety, benchmark performance, official benchmark evidence, accepted
Evidence Ledger mutation, formal evidence, score-axis population, live provider
evidence, or Level2+ evidence.

## Validation Commands

The following commands passed locally:

```sh
cargo fmt --all --check
git diff --check
cargo test -p zkbench-core --test external_runner_policy
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
cargo llvm-cov -p zkbench-core --all-features --summary-only --no-run
```

## Next Coverage Candidate

After Phase 235, `external_runner/policy.rs` has only the structurally capped
Level2+ rejection branch remaining in the local missing-line report. The lowest
remaining non-serializer line-coverage candidate in the current package summary
is `soak/campaign.rs` at `85.79%`, subject to a fresh missing-line audit before
any mutation.
