# Phase 263 External Runner Validation Coverage Notes

Status: complete for a bounded local coverage tranche.

## Scope

Phase 263 continues the `zkbench-core` coverage lane. The target is:

```text
crates/zkbench-core/src/external_runner/validation.rs
```

The previous recorded coverage-route floor for this file was `88.16%` line
coverage. The missing-line audit found only two reachable gaps: the shared
warning issue constructor and Windows absolute-path edge detection.

## Added Coverage

Added:

```text
crates/zkbench-core/tests/phase_263_external_runner_validation_coverage.rs
```

The tests cover:

- `ExternalValidationIssue::warning` preserving path, message, and warning
  severity;
- Windows-style absolute paths with `/` and `\` separators;
- non-drive prefixes, drive-relative paths, short drive strings, and portable
  relative paths staying non-rejected.

## Coverage Result

Measured with:

```sh
cargo llvm-cov -p zkbench-core --all-features --json --summary-only
```

Result:

```text
external_runner/validation.rs:
89.36% region -> 100.00% region
90.91% function -> 100.00% function
88.16% line -> 100.00% line

zkbench-core:
92.80% region -> 92.83% region
89.48% function -> 89.53% function
94.57% line -> 94.60% line
```

## Next Coverage Target

The fresh coverage table still shows `adapters/zk_harness/export.rs` at
`86.96%`, but Phase 240 already audited that surface and classified the
remaining misses as serializer-wrapper paths not worth forcing under the
current public data model. The next reachable non-serializer candidate is:

```text
crates/zkbench-core/src/evidence/external_submission_preflight_output.rs
```

Current line coverage:

```text
88.60%
```

Audit missing lines before mutation.

## Nonclaims

This phase does not claim:

- production source behavior changes;
- external-runner behavior changes;
- external execution;
- endpoint submission behavior;
- credential handling;
- generated artifact materialization;
- accepted Evidence Ledger mutation;
- benchmark evidence;
- score-axis population;
- Level2+ evidence;
- semantic correctness;
- production readiness;
- SOTA status;
- breakthrough status;
- whole-workspace 100% coverage.
