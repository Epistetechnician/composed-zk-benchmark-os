# Phase 238 Recursion Envelope Mismatch Coverage Notes

## State Slice

Phase 238 is the recursion-envelope-mismatch mutation coverage tranche for
`crates/zkbench-core/src/mutation/recursion_envelope_mismatch.rs`.

This slice is limited to additive Rust tests under `crates/zkbench-core/tests/`
and navigation/status updates under `docs/`, `README.md`, and `AGENTS.md`.

## Purpose

Phase 237 routed the next local coverage target to
`mutation/recursion_envelope_mismatch.rs` after
`mutation/invariant_strengthening.rs` reached `100.00%` line coverage.

The Phase 238 missing-line audit found uncovered reachable paths in:

- the public `RecursionEnvelopeMismatchPass::mutation_class()` method;
- the no-declared-trace failure path before loop selection;
- the no-loop failure path after trace selection;
- the prior-envelope-digest metadata fallback when `max_unroll` is absent.

## Implemented Coverage

Phase 238 adds focused tests to
`crates/zkbench-core/tests/phase_161_mutation_completion.rs`:

- `recursion_envelope_mismatch_reports_its_mutation_class`;
- `recursion_envelope_mismatch_fails_without_declared_trace`;
- `recursion_envelope_mismatch_fails_without_loop_after_trace_selection`;
- `recursion_envelope_mismatch_records_prior_digest_when_max_unroll_is_absent`.

The tests cover both fail-closed target-selection paths without weakening the
generated-instance invariants, and they exercise the fallback metadata record
when the source loop has an `envelope_digest` but no `max_unroll`.

## Coverage Result

Baseline before Phase 238:

- `mutation/recursion_envelope_mismatch.rs`: `84.00%` region / `50.00%`
  function / `86.44%` line coverage.
- `zkbench-core` package total: `91.86%` region / `87.83%` function /
  `93.59%` line coverage.

Measured after Phase 238:

- `mutation/recursion_envelope_mismatch.rs`: `98.67%` region / `100.00%`
  function / `100.00%` line coverage.
- `zkbench-core` package total: `91.90%` region / `88.00%` function /
  `93.62%` line coverage.

## Remaining Cap

`mutation/recursion_envelope_mismatch.rs` has no remaining missed lines or
missed functions in the local coverage report. One defensive region remains
unexecuted: the `loop_mut` error edge after `loop_id` has already been selected
from the same surface spec. This tranche does not corrupt that internal
post-selection invariant to force the branch.

## Claim Boundary

This phase proves only that the local Rust test suite now exercises
`RecursionEnvelopeMismatchPass::mutation_class()`, both reachable target-
selection failure paths, and the digest fallback metadata path.

It does not prove semantic correctness, production readiness, complete mutation
engine correctness, benchmark performance, official benchmark evidence,
accepted Evidence Ledger mutation, formal evidence, score-axis population, live
provider evidence, Level2+ evidence, SOTA status, or breakthrough status.

## Validation Commands

The following commands passed locally:

```sh
cargo fmt --all --check
cargo test -p zkbench-core --test phase_161_mutation_completion
cargo llvm-cov -p zkbench-core --all-features --summary-only
```

The final Phase 238 gate also ran:

```sh
git diff --check
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
```

## Next Coverage Candidate

After Phase 238, `mutation/recursion_envelope_mismatch.rs` has no missed lines
or missed functions in the local coverage report. The lowest remaining
non-serializer line-coverage candidate in the current package summary is
`evidence/ledger.rs` at `86.78%`, subject to a fresh missing-line audit before
any mutation.
