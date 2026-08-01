# Phase 797 HSAI Native-Transcript Source-Scan Correction Boundary

Date: 16 July 2026.

Status: documentation-first boundary complete; implementation not yet authorized
by this commit.

Named boundary state slice:
`hsai-native-transcript-source-scan-correction-boundary`.

Future implementation state slice:
`hsai-native-transcript-source-scan-authorized-test-exceptions`.

## Problem

The repository-wide HSAI process/network source scan predates the Phase 792 and
Phase 794 native-transcript security tests. It currently reports eleven
violations in already committed test sources:

- three real test-only process references in
  `hsai-native-transcript-preparation/tests/descriptor_relative_collector.rs`;
- eight forbidden-pattern string literals used to test rejection in that file
  and in
  `hsai-native-transcript-preparation/tests/operator_preparation_driver.rs`.

Phase 792 explicitly authorized one fixed `/usr/bin/mkfifo` invocation inside a
single security-test function. The other two real references are the matching
test-only `Command` import and process-id use. The scanner was not updated when
those tests landed. Its line-oriented matching also treats its test inputs as
runtime use. This is a gate defect, not authority for broader process execution.

## Exact future mutation surface

The future implementation may change only:

- `crates/hsai-e2e-harness/tests/claim_boundary_source_scan.rs`;
- `docs/798-phase-hsai-native-transcript-source-scan-correction-implementation.md`;
- `README.md`;
- `AGENTS.md`;
- `docs/12-task-list.md`;
- `docs/90-whole-codebase-validation-report.md`.

It may not change either native-transcript integration test, any production
source, Cargo metadata, package runtime file, Statebook file, admission source,
benchmark code, or generated artifact.

## Closed exception contract

The corrected scan must remain fail closed. It may recognize only:

1. the exact test file
   `hsai-native-transcript-preparation/tests/descriptor_relative_collector.rs`;
2. the exact import `use std::process::Command;`;
3. the exact test-only call `std::process::id()`;
4. the exact fixed command construction
   `Command::new("/usr/bin/mkfifo")` only inside
   `rejects_non_utf8_symlink_and_terminal_kind_and_size_boundaries`;
5. forbidden-pattern literals only inside the two named source-scan regression
   tests:
   `collector_source_has_no_process_network_shell_or_canonicalization_path`
   and `driver_source_has_no_forbidden_execution_or_io_surface`.

The exception must bind file, exact source line, and enclosing function where a
function boundary applies. It must reject near misses involving another file,
another function, another executable, another command construction, altered
source text, or a forbidden literal outside the two named regression tests.

## Required verification

The implementation must add positive and near-miss negative tests for the
exception helper, then pass:

- the exact `hsai_crates_do_not_use_process_or_network_apis` test;
- the full `claim_boundary_source_scan` integration test;
- `cargo test -p hsai-native-transcript-preparation --all-features`;
- formatting and warning-denied focused Clippy;
- repository documentation and hygiene checks;
- a clean-tree full workspace gate, with any independent dirty-worktree failure
  reported separately.

## Nonclaims

This boundary and its future implementation do not authorize general process
execution, shell execution, PATH lookup, variable executables, network access,
capture, P01B materialization, formal backend execution, external rails,
accepted Evidence Ledger mutation, benchmark evidence, Level2+ evidence,
semantic correctness, production readiness, SOTA, proof, or full security.
