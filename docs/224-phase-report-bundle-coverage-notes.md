# Phase 224 Report Bundle Coverage Notes

Status: complete for local coverage hardening.

## State Slice

This phase touched only:

- `crates/zkbench-core/tests/phase_q_report_bundle.rs`
- `docs/224-phase-report-bundle-coverage-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No production Rust source, Cargo metadata, generated artifacts, accepted
Evidence Ledger state, benchmark output, score-axis state, report-bundle
semantics, or external replay behavior changed.

## Purpose

After Phase 223, the next visible low non-serializer public surface in the
`zkbench-core` package coverage table was
`crates/zkbench-core/src/report_bundle.rs` at `82.30%` line coverage.

This tranche adds focused regression coverage for reachable local
report-bundle validation, rendered payload validation, output-root rejection,
and manifest readback failure behavior.

## Coverage Added

The added tests cover:

- empty bundle, version, input, and rendered-report identities;
- duplicate input identifiers;
- unsupported digest algorithms and zero-length digest metadata;
- claim-boundary escalation in report-bundle inputs and rendered reports;
- missing source references and missing required local-only limitations;
- missing inputs and missing rendered reports;
- shell-like artifact references rejected by manifest validation;
- empty rendered Markdown payload identifiers;
- empty rendered Markdown payload bodies;
- duplicate rendered Markdown payload identifiers;
- extra rendered Markdown payloads not declared by the manifest;
- output roots that are regular files rather than directories;
- syntactically invalid output-root strings;
- non-UTF-8 manifest digest sidecars;
- non-UTF-8 manifest JSON with a matching digest sidecar.

These paths are exercised through the public local manifest, output, and
readback APIs. They do not generate benchmark results, mutate accepted ledgers,
run external replay, or populate score axes.

## Coverage Measurement

Before this tranche, the full local package coverage run reported:

- `zkbench-core`: `90.64%` region coverage, `86.16%` function execution, and
  `91.93%` line coverage;
- `report_bundle.rs`: `86.84%` region coverage, `79.37%` function execution,
  and `82.30%` line coverage.

After this tranche, the full local package coverage run reported:

- `zkbench-core`: `90.82%` region coverage, `86.28%` function execution, and
  `92.33%` line coverage;
- `report_bundle.rs`: `91.35%` region coverage, `82.54%` function execution,
  and `92.90%` line coverage.

Remaining misses are mostly filesystem error closures, serde serialization
error closures for infallible in-memory structs, digest computation error
closures, and platform-specific path component branches. They are not forced in
this tranche.

After ignoring serializer-wrapper floors already audited in Phases 217 and
218, the next visible low non-serializer public surface is
`soak/artifact_layout.rs` at `83.81%` line coverage.

## Claim Boundary

This is local regression coverage only. It does not change production source,
report-bundle semantics, external replay behavior, endpoint submission
behavior, credential handling, accepted Evidence Ledger policy, formal
evidence, benchmark evidence, score-axis population, generated artifact
materialization, Level2+ evidence, semantic-correctness claims,
production-readiness claims, unsafe coverage forcing, coverage suppression,
structurally unreachable branch forcing, or whole-workspace 100% coverage
claims.

## Validation

Validation passed for this tranche:

```sh
cargo fmt --all --check
git diff --check
cargo test -p zkbench-core --test phase_q_report_bundle
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
cargo llvm-cov -p zkbench-core --all-features --summary-only
```
