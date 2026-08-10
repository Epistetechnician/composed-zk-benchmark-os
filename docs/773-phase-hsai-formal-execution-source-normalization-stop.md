# Phase 773 HSAI Formal Execution Source Normalization Stop

## Status

Stopped because inherited command-family cardinality remains unresolved.

State slice: `phase-773-hsai-formal-execution-source-normalization-stop`.

Classification: `SourceNormalizationCardinalityIncomplete`.

Execution status: `StoppedDocumentationOnly`. Evidence ceiling:
`Level1LocalReplayOrLower`.

## Result

Phase 773 decomposed 74 identifiable command obligations without running any
of them. It could not publish the Phase 772-required exact producer count or a
canonical executable source-ledger digest because several inherited command
families do not freeze their own child cardinality.

Every identifiable row remains `blocked`. All 74 lack exact absolute
status/stdout/stderr artifact templates. Many also lack exact argv, cwd,
replacement environment, timeout, caps, outcome, or input/output identities.
An operation id is not an executable contract.

## Normalized Identifiable Obligations

The following ids are stable Phase 773 normalization ids. They are not plan-v2
operation ids and do not authorize execution.

### Primary and detached execution: 6

```text
snapshot-primary-head
snapshot-primary-status
create-detached-worktree
remove-detached-worktree
verify-primary-head-final
verify-primary-status-final
```

Controlling sources: Phases 753 and 766. Exact Git argv, cwd, environment,
bounds, transcript paths, worktree mutation contract, and cleanup failure
behavior remain unresolved.

### Helper and fixture preflight: 8

```text
compile-helper-sources
run-helper-tests
run-raw-parser-self-test
fixture-normal-exit
fixture-process-timeout
fixture-stdout-limit
fixture-stderr-limit
validate-process-fixtures
```

Controlling sources: Phases 732, 749, and 761. The raw self-test and four
fixture argv/bounds/outcomes are substantially specified. Exact helper file
order, test discovery argv, validator input argv, cwd, replacement
environments, remaining bounds, and transcript paths are not. The timeout
fixture's `$RUN` dependency conflicts with the current command environment
allowlist.

### Rust acquisition and identity: 8

```text
download-rust-manifest
install-rust-toolchain
capture-rust-components-before
capture-rustup-version
capture-rust-components-identity
capture-rustc-identity
capture-cargo-identity
capture-rust-components-after
```

Controlling sources: Phases 668, 680, 718, 751, and 763. The first two require
`external-acquisition`; the six identities require `host-offline`. Downloader
and installer argv, absolute Rustup resolution, timeouts, exact Cargo stdout,
complete environments, and transcript paths remain unresolved.

### Charon source acquisition and stability: 17

```text
initialize-charon-source
fetch-charon-source
checkout-charon-source
capture-charon-head-initial
capture-charon-status-initial
hash-charon-license-md-initial
hash-charon-readme-md-initial
hash-charon-cargo-toml-initial
hash-charon-cargo-lock-initial
hash-charon-rust-toolchain-initial
capture-charon-head-final
capture-charon-status-final
hash-charon-license-md-final
hash-charon-readme-md-final
hash-charon-cargo-toml-final
hash-charon-cargo-lock-final
hash-charon-rust-toolchain-final
```

Controlling sources: Phases 718, 744, 755, and 757. Only
`fetch-charon-source` requires `external-acquisition`; the other rows require
`host-offline`. Commit and five path digests are frozen. Exact Git init/fetch/
checkout argv, absolute Git and `shasum` identities, path forms, environments,
bounds, and transcript paths remain unresolved.

### Aeneas and Lean materialization/identity: 13

```text
download-aeneas-main
download-aeneas-lean
validate-aeneas-archives
extract-aeneas-main
extract-aeneas-lean-staging
capture-aeneas-file
capture-aeneas-version
download-lean
extract-lean
capture-lean-version
capture-lake-version
capture-lean-prefix
capture-leantar-file
```

Controlling sources: Phases 668, 684, 686, 690, 718, 742, 744, and 749. The
three downloads require `external-acquisition`; all other rows require
`host-offline`. Asset identities and several acceptance facts are frozen.
Downloader argv, absolute extractor argv, extraction timeouts, complete
environments, transcript paths, and the exact Lean `.tar.zst` child-command
sequence remain unresolved.

### Dependency acquisition: 4

```text
compile-rustc-private-probe
fetch-charon-dependencies
lake-update
lake-cache-get
```

Controlling sources: Phases 672, 678, and 718. The latter three require
`external-acquisition`; the probe requires `host-offline`. Core Cargo/Lake argv
are known. Probe source and flags, complete environments, timeouts, transcript
paths, and some artifact identities remain unresolved.

### Network transition and controls: 4

```text
resolve-hostname-before-closure
sandbox-process-positive
sandbox-hostname-negative
sandbox-direct-ip-negative
```

Controlling sources: Phases 678 and 696. The hostname-positive row is the last
`external-acquisition` control. It is followed by the irreversible
`external-network-closed` barrier. The three later rows require
`sandbox-closed`. Exact hostname argv, per-command bounds, transcript paths,
and exact negative outcomes remain unresolved.

The Phase 732 persistent loopback controller remains a separate closed
`controlled-loopback` lifecycle, not one of these ordinary command rows.

### Sandboxed build, backend, and kernel checks: 14

```text
build-charon
capture-charon-version
inspect-charon-architecture
inspect-charon-signature
inspect-charon-dependencies
inspect-charon-adjacency
inspect-charon-driver-binding
extract-checker-llbc
pretty-print-checker-llbc
generate-aeneas-lean
check-types-olean
check-funs-olean
check-witness-olean
lake-build
```

Controlling sources: Phases 668, 678, 716, and 720. Every row requires
`sandbox-closed`. Core build/extraction/generation/check argv and process bounds
are partly frozen. Exact native-inspection child cardinality, wrapper argv,
complete environments, direct Lean `-o` argv, transcript paths, and final
mutable artifact inventory remain unresolved.

## Count Reconciliation

```text
primary/detached                         6
helper/fixture                           8
Rust acquisition/identity               8
Charon source/stability                 17
Aeneas/Lean materialization/identity    13
dependency acquisition                   4
network transition/controls              4
sandboxed build/backend/checks           14
identifiable obligations total          74
exact child-command total               unknown
```

The exact total remains unknown because:

1. `verify-frozen-repository` still compresses an unspecified number of Git,
   scanner, disk, executable, and root probes;
2. Lean extraction is described historically as a `zstd | tar` pipeline but
   no controlling direct-child replacement is frozen;
3. Charon architecture, signature, dependency, adjacency, and driver-binding
   audits do not freeze command count and target cardinality; and
4. cleanup does not yet specify whether process inspection, termination, and
   worktree removal are in-process actions or bounded child commands.

No source-ledger SHA-256 is published because hashing an incomplete ledger as
if it were complete would create a false executable identity. The Phase 770 v1
conceptual digest remains unchanged:

```text
1644a895733d769fbe89795cc3fc7d4886d71b03c8c28b9f1866f5a075a1db14
```

## Closed Capability Order

The normalized capability order is:

```text
host-offline preflight
explicit external-acquisition rows only
resolve-hostname-before-closure
external-network-closed
controlled-loopback lifecycle
sandbox-closed controls
sandbox-closed build, backend, and kernel checks
aggregate cleanup and final primary verification
```

No operation after `external-network-closed` may declare
`external-acquisition`. Controlled loopback does not reopen DNS, public IPv4,
public IPv6, proxy inheritance, or inherited network descriptors.

## Pure Non-Producer Inventory

The following remain closed in-process operation families when supplied only
with prior typed artifacts or immutable constants:

```text
canonical JSON parsing and schema acceptance
digest and byte comparison
path normalization and containment checks
regular-file, mode, and non-symlink checks
archive summary/profile acceptance
component-set and identity acceptance
generated-source and ordinal-body scans
artifact producer/consumer closure checks
cleanup planning and ownership-receipt acceptance
```

Any subprocess call moves an operation out of this list and requires a
separate bounded command row.

## Phase 774 Resolution Boundary

Phase 774 must be documentation-first and may add one command-family
resolution document plus standard mirrors. It must resolve the four unknown
cardinality families above, define a global transcript template convention,
and freeze missing shared cwd/environment/timeout/outcome rules. Every design
choice must be explicit; it may supersede missing older details but may not
pretend they were inherited facts.

Only after the exact count and every row are complete may Phase 774 publish a
canonical path-normalized ledger digest and authorize a later hermetic plan-v2
implementation. Phase 774 may not modify source or run a producer.

Phase 773 creates no executable plan, ledger digest, backend result, proof
artifact, checker transcript, accepted evidence, Level2+, score axis, semantic
correctness, production readiness, SOTA, breakthrough, full-security claim,
external audit, or action authority.

Phase 774 subsequently resolves the four unknown command families to exactly
84 ordinary bounded commands, freezes shared profiles and transcript paths,
and publishes a non-executable resolution-contract digest. Phase 775 must
expand all 84 rows under
`docs/774-phase-hsai-formal-execution-command-family-resolution.md`.
