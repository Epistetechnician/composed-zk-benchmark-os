# Phase 796-A1 HSAI P01B Archive Ledger Parser Implementation

## Status

Complete as a committed-candidate hermetic implementation. Phase 796-A2
clean-commit audit remains required before any separately authorized Phase
796-A3 acquisition-only attempt.

State slice: `phase-796a1-hsai-p01b-archive-ledger-helper`.

Classification: `P01BArchiveLedgerParserImplementedAuditPending`.

Execution status: `LocalValidationOnly`.

Evidence ceiling: `Level1LocalReplayOrLower`.

## Implemented Surface

Phase 796-A1 adds exactly the implementation surface conditionally authorized
by the immutable Phase 796-A boundary:

| File | SHA-256 |
|---|---|
| `tools/hsai-formal-preflight/p01b_archive_ledger.py` | `ab7c3da98d995997fba1bd2d2d865257c9f99dfefb4ce82b815cceacd92df45f` |
| `tools/hsai-formal-preflight/tests/test_p01b_archive_ledger.py` | `0ae3a2b348e491af7d2b362272255b0bd278961f4a4b7ca24718a4470692f81b` |

The helper uses only the Python 3.9.6 standard library. It directly parses one
RFC 1952 member, raw DEFLATE, and strict 512-byte ustar records. It does not
use `gzip.GzipFile`, `tarfile`, subprocess, shell, environment lookup, dynamic
imports, package installation, or network access. It never extracts a member.

The implementation includes:

- descriptor-relative canonical input and output traversal with retained
  entry/open identity checks;
- pinned production asset and profile authority;
- finite gzip, TAR, extension, path, member, aggregate, compression-ratio,
  candidate-byte, process, and terminal-record bounds;
- exact physical-header and ordered logical-member ledgers;
- independent candidate reconstruction, including asset/profile authority,
  optional gzip framing, TAR bindings, all fixed limits, and authority fields;
- exclusive mode-0700 candidate creation and mode-0600 artifact writes;
- final-status hard-link commit semantics, directory durability operations,
  replacement detection, and fail-closed cleanup; and
- one atomic `PIPE_BUF`-bounded terminal record on the bounded runner's stdout
  or stderr pipe, with stdin closed before process setup or argv parsing.

The immutable Phase 796-A boundary remains:

```text
sha256 = 2b52a3b24d94b565434dc341d808fe7ee3ad44757ea5ff8365f8dc88aefe1ba0
contract_digest = 9a85d6b33f31ee3e78d6176da9208753bc5c244c4fecc44ab29efc265b4f7bd1
```

The historical helper remains unchanged:

```text
tools/hsai-formal-preflight/raw_archive_validator.py
sha256 = 31fa2450fe7e3ce87c13dd844ac6fde1cde0a4a81e7d351276e5dd2a4ba32692
```

## Hermetic Validation

Observed locally with `/usr/bin/python3` 3.9.6:

```text
focused Phase 796-A1 suite: 68 passed, 0 failed
complete formal-preflight suite: 151 passed, 0 failed
ruff check: passed
cargo fmt --all -- --check: passed
git diff --check: passed
pnpm run lint: unavailable; pnpm reports that the project is configured for Yarn
invalid CLI: exit 1 with one canonical InvalidCli stderr line
independent implementation review: READY
independent test-completeness review: READY
```

The tests cover literal contract and authority pins, golden candidate bytes,
all schema field types, signed and unsigned integer boundaries, gzip optional
fields and checksums, strict TAR numeric and type families, PAX/GNU name rules,
path collisions in both ancestor orders, descriptor replacement races, every
declared-artifact stat/open race, resource-limit setup, terminal FD ownership,
partial writes, cleanup, every publication checkpoint, and fail-stop states on
both sides of the final status link.

`cargo check --workspace --all-targets` remains blocked outside this state
slice by the preserved user-owned mutation in
`crates/hsai-agent-admission/src/lib.rs`. The missing admission exports break
the Phase 609 example and gateway digest checker integration test. Phase
796-A1 does not modify or stage that file.

The repository has no root `package.json`; the root `pnpm run lint` gate is not
an available repository command. Python, Rust formatting, and diff hygiene are
the applicable local gates for this slice.

## Authority Boundary

All candidates produced by synthetic tests existed only in test-owned
temporary directories and were removed by test cleanup. No real Aeneas archive
was read or downloaded. No durable candidate ledger was generated.

This phase does not publish or accept `preparation_contract_sha256`. It does
not authorize Phase 797, P01B materialization, transcript capture, backend,
Lean, SMT, Z3, or COBALT execution, proof artifacts, accepted evidence,
Level2+, score axes, semantic correctness, production readiness, SOTA,
breakthrough, full security, external audit, or action authority.

## Next Gate

Phase 796-A2 must review the clean committed implementation and tests against
the immutable contract and return a retained zero-gap decision. The two READY
development reviews above are implementation hardening evidence; they do not
replace that clean-commit audit.

Phase 796-A3 remains separately blocked by explicit acquisition authority and
an accepted supervisor enforcing `max_resident_bytes=536870912`. A1 completion
alone cannot authorize network access or archive inspection.
