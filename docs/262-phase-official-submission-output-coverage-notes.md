# Phase 262 Official Submission Output Coverage Notes

Status: complete for a bounded local coverage tranche.

## Scope

Phase 262 returns from the gateway public-packet lane to the `zkbench-core`
coverage lane. The target is:

```text
crates/zkbench-core/src/evidence/official_submission_output.rs
```

The previous recorded coverage-route floor for this file was `87.45%` line
coverage. The tranche is limited to reachable local output-plumbing behavior.

## Added Coverage

Updated:

```text
crates/zkbench-core/tests/phase_186_official_submission_output_coverage.rs
```

The tests now cover:

- explicit overwrite of an already valid matching package output root;
- digest preservation across matching overwrite;
- non-UTF-8 digest sidecar rejection;
- invalid validation-report JSON rejection with a matching digest sidecar;
- unexpected declared-root child rejection.

## Coverage Result

Measured with:

```sh
cargo llvm-cov -p zkbench-core --all-features --json --summary-only
```

Result:

```text
evidence/official_submission_output.rs:
82.12% region -> 84.22% region
70.45% function -> 75.00% function
87.45% line -> 90.04% line

zkbench-core:
92.74% region -> 92.80% region
89.36% function -> 89.48% function
94.51% line -> 94.57% line
```

## Residual Cap

Remaining misses are mostly low-level filesystem error wrappers, private
relative-path validation branches reached only by fixed internal constants,
unreachable parent-component fallback arms after public prevalidation, and
serialization-error wrappers for concrete serializable data.

## Next Coverage Target

The fresh coverage table still shows `adapters/zk_harness/export.rs` at
`86.96%`, but Phase 240 already audited that surface and classified the
remaining misses as serializer-wrapper paths not worth forcing under the
current public data model. The next reachable non-serializer candidate is:

```text
crates/zkbench-core/src/external_runner/validation.rs
```

Current line coverage:

```text
88.16%
```

Audit missing lines before mutation.

## Nonclaims

This phase does not claim:

- production source behavior changes;
- official submission behavior;
- endpoint submission behavior;
- credential handling;
- generated artifact materialization outside test tempdirs;
- accepted Evidence Ledger mutation;
- benchmark evidence;
- score-axis population;
- Level2+ evidence;
- semantic correctness;
- production readiness;
- SOTA status;
- breakthrough status;
- whole-workspace 100% coverage.
