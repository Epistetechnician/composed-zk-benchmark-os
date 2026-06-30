# Phase 239 Evidence Ledger Coverage Notes

## State Slice

Phase 239 is the evidence-ledger coverage tranche for
`crates/zkbench-core/src/evidence/ledger.rs`.

This slice is limited to additive Rust tests under `crates/zkbench-core/tests/`
and navigation/status updates under `docs/`, `README.md`, and `AGENTS.md`.

## Purpose

Phase 238 routed the next local coverage target to `evidence/ledger.rs` after
`mutation/recursion_envelope_mismatch.rs` reached `100.00%` line coverage.

The Phase 239 missing-line audit found uncovered reachable paths in:

- `EvidenceLedger::default()`;
- filesystem error wrapping in `save_json` and `load_json`;
- malformed JSON deserialization in `load_json`;
- sequence-number, previous-digest, and cached-summary validation drift;
- explicit nonclaim language that must not be treated as forbidden claim text.

## Implemented Coverage

Phase 239 adds focused tests to `crates/zkbench-core/tests/evidence_ledger.rs`:

- `default_evidence_ledger_matches_new`;
- `evidence_ledger_json_file_errors_are_reported`;
- `evidence_ledger_detects_sequence_previous_digest_and_summary_drift`;
- `evidence_ledger_allows_explicit_nonclaim_language`.

The tests exercise reachable ledger construction, read/write error context,
validation drift reporting, and safe negative claim-boundary phrasing without
creating accepted evidence or changing ledger policy.

## Coverage Result

Baseline before Phase 239:

- `evidence/ledger.rs`: `84.73%` region / `76.19%` function / `86.78%` line
  coverage.
- `zkbench-core` package total: `91.90%` region / `88.00%` function /
  `93.62%` line coverage.

Measured after Phase 239:

- `evidence/ledger.rs`: `94.27%` region / `90.48%` function / `96.04%` line
  coverage.
- `zkbench-core` package total: `91.99%` region / `88.17%` function /
  `93.71%` line coverage.

## Remaining Cap

`evidence/ledger.rs` retains uncovered lines for serialization-error branches
inside digest/save helpers and the private docs-only `_class_is_used_for_docs`
marker. This tranche does not introduce fake non-serializable data, test-only
production hooks, or dead-code forcing to cover those lines.

## Claim Boundary

This phase proves only that the local Rust test suite now exercises reachable
Evidence Ledger defaulting, filesystem/deserialization error reporting,
validation drift reporting, and safe nonclaim text handling.

It does not prove semantic correctness, production readiness, accepted Evidence
Ledger mutation, accepted evidence policy correctness, benchmark performance,
official benchmark evidence, formal evidence, score-axis population, live
provider evidence, Level2+ evidence, SOTA status, or breakthrough status.

## Validation Commands

The following commands passed locally:

```sh
cargo fmt --all --check
cargo test -p zkbench-core --test evidence_ledger
cargo llvm-cov -p zkbench-core --all-features --summary-only
```

The final Phase 239 gate also ran:

```sh
git diff --check
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
```

## Next Coverage Candidate

After Phase 239, `evidence/ledger.rs` has no remaining reachable missed lines
worth forcing in this local tranche. The lowest remaining non-serializer
line-coverage candidate in the current package summary is
`adapters/zk_harness/export.rs` at `86.96%`, subject to a fresh missing-line
audit before any mutation.
