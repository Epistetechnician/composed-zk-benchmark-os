# Phase 778 HSAI Formal Execution Operation Order Correction

## Status

Complete as a documentation-first exact operation-order correction.

State slice: `phase-778-hsai-formal-execution-operation-order-correction`.

Classification: `FormalOperationOrderCorrected`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Verdict

Phase 778 preserves the Phase 776 cardinality of exactly 102 ordinary bounded
commands plus one dedicated controlled-loopback lifecycle and corrects the
Phase 777 pre-use ordering defect. Static native inspection and acceptance now
precede every executable version or driver-load producer.

This order is an immutable documentation contract. It does not expand row
fields, bind executors, resolve a machine, or authorize execution.

## Exact Ordered Command IDs

```text
001 snapshot-primary-head
002 snapshot-primary-status
003 list-worktrees-before
004 create-detached-worktree
005 capture-detached-head
006 capture-detached-status
007 compile-helper-sources
008 run-helper-tests
009 run-raw-parser-self-test
010 fixture-normal-exit
011 fixture-process-timeout
012 fixture-stdout-limit
013 fixture-stderr-limit
014 validate-process-fixtures
015 download-rust-manifest
016 install-rust-toolchain
017 capture-rust-components-before
018 capture-rustup-version
019 capture-rust-components-identity
020 capture-rustc-identity
021 capture-cargo-identity
022 capture-rust-components-after
023 initialize-charon-source
024 fetch-charon-source
025 checkout-charon-source
026 capture-charon-head-initial
027 capture-charon-status-initial
028 hash-charon-license-md-initial
029 hash-charon-readme-md-initial
030 hash-charon-cargo-toml-initial
031 hash-charon-cargo-lock-initial
032 hash-charon-rust-toolchain-initial
033 download-aeneas-main
034 download-aeneas-lean
035 validate-aeneas-archives
036 extract-aeneas-main
037 extract-aeneas-lean-staging
038 capture-aeneas-file
039 lipo-packaged-aeneas
040 lipo-packaged-charon
041 lipo-packaged-charon-driver
042 lipo-packaged-libgmp
043 codesign-verify-packaged-aeneas
044 codesign-verify-packaged-charon
045 codesign-verify-packaged-charon-driver
046 codesign-display-packaged-aeneas
047 codesign-display-packaged-charon
048 codesign-display-packaged-charon-driver
049 spctl-packaged-aeneas
050 spctl-packaged-charon
051 spctl-packaged-charon-driver
052 otool-libraries-packaged-aeneas
053 otool-libraries-packaged-charon
054 otool-libraries-packaged-charon-driver
055 otool-libraries-packaged-libgmp
056 otool-load-commands-packaged-charon-driver
057 capture-aeneas-version
058 download-lean
059 decompress-lean-archive
060 extract-lean-tar
061 capture-lean-version
062 capture-lake-version
063 capture-lean-prefix
064 capture-leantar-file
065 compile-rustc-private-probe
066 fetch-charon-dependencies
067 lake-update
068 lake-cache-get
069 resolve-hostname-before-closure
070 sandbox-process-positive
071 sandbox-hostname-negative
072 sandbox-direct-ip-negative
073 build-charon
074 lipo-built-charon
075 lipo-built-charon-driver
076 codesign-verify-built-charon
077 codesign-verify-built-charon-driver
078 codesign-display-built-charon
079 codesign-display-built-charon-driver
080 otool-libraries-built-charon
081 otool-libraries-built-charon-driver
082 otool-load-commands-built-charon-driver
083 capture-charon-head-final
084 capture-charon-status-final
085 hash-charon-license-md-final
086 hash-charon-readme-md-final
087 hash-charon-cargo-toml-final
088 hash-charon-cargo-lock-final
089 hash-charon-rust-toolchain-final
090 capture-charon-version
091 preflight-built-charon-driver-load
092 extract-checker-llbc
093 pretty-print-checker-llbc
094 generate-aeneas-lean
095 check-types-olean
096 check-funs-olean
097 check-witness-olean
098 lake-build
099 remove-detached-worktree
100 list-worktrees-after
101 verify-primary-head-final
102 verify-primary-status-final
```

## Pre-Use Acceptance Order

For packaged assets, ordinal 038 is a non-executing file-identity producer.
Ordinals 039 through 056 are static native inspections. Their pure transcript,
path, digest, adjacency, support-library, and dependency acceptance must finish
before ordinal 057 executes packaged Aeneas for its version identity.

For source-built Charon, ordinal 073 builds both binaries. Ordinals 074 through
082 inspect them without executing either target. Ordinals 083 through 089
freshly reproduce the Charon commit, status, and five frozen source hashes
after dependency fetch and build. Static binary and post-build source-stability
acceptance must finish
before ordinal 090 executes Charon for its version identity. Version acceptance
and exact `librustc_driver-cddc585b497d1e17.dylib` resolution must finish
before ordinal 091 executes the non-mutating driver-load preflight. Driver
preflight acceptance must finish before ordinal 092 begins extraction.

No acceptance operation in these intervals may spawn a child. Each consumes
only prior typed transcripts, immutable constants, and descriptor-relative
filesystem observations.

## Network And Loopback Order

The external-acquisition commands remain exactly:

```text
015 download-rust-manifest
016 install-rust-toolchain
024 fetch-charon-source
033 download-aeneas-main
034 download-aeneas-lean
058 download-lean
066 fetch-charon-dependencies
067 lake-update
068 lake-cache-get
069 resolve-hostname-before-closure
```

The irreversible `external-network-closed` barrier follows ordinal 069. The
dedicated controlled-loopback lifecycle follows that barrier and precedes
ordinal 070; it receives no ordinary-command ordinal. Every command from 070
through 098 is `sandbox-closed`. Cleanup commands 099 through 102 cannot reopen
network access.

## Set And Cardinality Proof

The list contains 102 entries and 102 unique IDs. It equals the Phase 774
84-ID set after replacing the mixed ten-row native family with the corrected
ten source-built rows and adding the 18 packaged-asset rows. No Phase 773
superseded placeholder is present. The controlled-loopback lifecycle is
separate and counted once outside the ordinary list.

The order also preserves:

```text
initial primary snapshot before detached creation
detached identity before helper or source work
all acquisition before irreversible closure
all sandbox controls before build or backend work
fresh Charon commit, status, and path hashes after build and before extraction
generated Types before Funs before Witnesses
three direct Lean checks before final Lake build
worktree removal before final worktree and primary verification
primary HEAD and status verification as the final two commands
```

## Order Contract Identity

The canonical JSON object uses sorted keys, compact separators, the exact
102-element `operation_ids` array above, and these remaining fields:

```json
{"controlled_loopback_after":"resolve-hostname-before-closure","external_network_closed_after":"resolve-hostname-before-closure","schema":"hsai-formal-operation-order-v1"}
```

SHA-256 of the complete canonical object, including `operation_ids`:

```text
490c30a8098214754d20e4025696e2e3c702df8d4f7114a611157653ea7a4464
```

This digest binds command membership and order only. It is not a source-ledger,
plan-v2, executor-binding, or machine-resolved-attempt digest.

## Remaining Blockers

The Phase 777 ledger blockers remain unchanged: exact downloader and installer
argv, helper file order, native transcript grammars, driver-preflight argv,
archive and mutable-output inventories, machine executable identity acceptance,
and fully expanded per-row fields.

## Phase 779 Gate

Phase 779 must remain documentation-first. It may expand the 102 ordered rows
into `hsai-formal-source-ledger-v1` plus standard mirrors. Every required field
must be present in each row. Unsupported values remain explicit typed blockers;
profiles, grouped defaults, and inferred values are prohibited. A ledger digest
may be published only if every path-normalized field is complete and no row is
blocked.

Phase 779 may not modify Python or Rust source, create attempt roots, resolve
machine identities, or run any producer. Plan-v2 and executor implementation
remain later phases after a complete ledger is committed and independently
audited.

Phase 778 creates no source ledger, executable plan, executor binding,
machine-resolved attempt, backend result, generated Lean, retained kernel
result, proof artifact, checker transcript, accepted evidence, Level2+, score
axis, semantic correctness, production readiness, SOTA, breakthrough, full
security, external audit, or action authority.
