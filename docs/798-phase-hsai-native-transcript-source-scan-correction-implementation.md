# Phase 798 HSAI Native-Transcript Source-Scan Correction Implementation

Date: 16 July 2026.

Named state slice:
`hsai-native-transcript-source-scan-authorized-test-exceptions`.

## Outcome

The HSAI claim-boundary scanner now recognizes only the already committed Phase
792/794 integration-test references authorized by Phase 797. The helper binds
the two exact test paths, exact source lines, and exact enclosing functions.
The single process construction remains fixed to `/usr/bin/mkfifo` inside
`rejects_non_utf8_symlink_and_terminal_kind_and_size_boundaries`.

The same helper recognizes forbidden-pattern literals only inside
`collector_source_has_no_process_network_shell_or_canonicalization_path` and
`driver_source_has_no_forbidden_execution_or_io_surface`. The production source
scan continues to cover every HSAI Rust source, test, example, and binary.

## Adversarial coverage

Focused tests accept the exact authorized import, process-id call, fixed FIFO
construction, and test literals. They reject a different file, function,
executable, import shape, and literal outside the named regression test.

## Validation

- exact and full HSAI claim-boundary scanner: pass, 7 tests;
- native-transcript package: pass, 50 tests;
- clean-tree focused warning-denied Clippy: pass;
- clean-tree workspace tests across all targets and features: pass;
- repository docs and hygiene checks: pass;
- clean-tree workspace warning-denied Clippy: one unrelated committed failure in
  `zkbench-core/tests/operator_soak_campaign_contract.rs` because the current
  toolchain classifies `!EXAMPLE_SOURCE.is_empty()` as `const_is_empty`.

The final workspace Clippy finding is outside Phase 798 and is not waived,
suppressed, or changed here.

## Claim boundary

This is scanner correctness evidence only. It creates no new process or network
authority, runtime behavior, capture, materialization, backend execution,
benchmark evidence, accepted evidence, semantic-correctness claim, proof,
production-readiness claim, SOTA claim, or full-security claim.
