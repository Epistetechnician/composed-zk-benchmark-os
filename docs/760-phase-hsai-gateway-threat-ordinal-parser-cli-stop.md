# Phase 760 HSAI Gateway Threat Ordinal Parser CLI Stop

## Status

Complete as one cleaned pre-parser-execution stop.

State slice: `phase-760-hsai-gateway-threat-ordinal-parser-cli-stop`.

Classification: `RawParserSelfTestInvocationMismatch`.

Diagnostic: `UnsupportedOutputOption`.

Execution status: `Succeeded` for root, disk, preservation, detached source,
all frozen repository identities, three independent helper hashes, helper
compilation, and 30 focused helper tests; `Failed` before parser self-test
execution because the invocation supplied an unsupported `--output` option;
and `NotRun` for parser acceptance, client metadata, fixtures, network, Rust,
Charon, Aeneas, Lean, Cargo, Lake, sandbox controls, backend extraction,
generated source, or kernel checking. Evidence ceiling:
`Level1LocalReplayOrLower`.

## First Failure

The committed `raw_archive_validator.py self-test` command takes no option and
writes one canonical JSON summary to stdout. Phase 760 supplied `--output`, so
argparse returned nonzero before `run_self_test()` executed. No same-phase
repair or replay occurred.

## Cleanup And Claims

The run root and detached worktree were removed. All four attempt-owned
persistent roots remained absent. The primary checkout exactly matched its
pre-attempt HEAD, porcelain bytes, dirty-file set, and recorded file hashes;
the preservation record was then removed.

Phase 760 creates focused local helper-test evidence only. It creates no parser
self-test result, fixture result, acquired asset, backend result, generated
source, kernel result, proof, accepted evidence, Level2+, score axis, semantic
correctness, production readiness, SOTA, breakthrough, full-security claim,
external audit, or action authority.
