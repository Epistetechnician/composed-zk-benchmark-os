# Phase 740 HSAI Gateway Threat Ordinal Archive Profile Discovery Boundary

## Status

Complete as a documentation-first, acquisition-only profile-discovery boundary.

State slice:
`phase-740-hsai-gateway-threat-ordinal-archive-profile-discovery-boundary`.

Classification: `RawArchiveProfileDiscoverySpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Narrow Phase 741 Scope

Phase 741 uses canonical run root
`hsai-phase741-archive-profile-efa3782c`. It is not a backend attempt and does
not create a detached Charon execution worktree. It may materialize only the
Phase 739 raw-aware parser, its bounded adversarial self-test, its bounded
runner, the two exact Aeneas release assets, and run-local transcripts.

Phase 741 must:

1. prove the canonical run root absent, create it with mode `0700`, and preserve
   a clean repository;
2. pass the exact Phase 738 parser self-test before network access;
3. download the two Aeneas assets as separate producers with numeric statuses,
   bounded streams, checkpoints, exact sizes, and exact SHA-256 values;
4. open regular non-symlink descriptors and validate raw names, direct member
   types, logical counts, root rules, path aliases, duplicate keys, ancestor
   collisions, and embedded Lean-asset byte equality exactly as Phase 738;
5. omit only the expected top-level-set equality assertion; and
6. emit one canonical discovery summary containing the observed main and Lean
   top-level sets, counts, roots, type counts, inventory digests, helper digest,
   outer archive identities, and embedded-asset equality.

Discovery success does not accept the observed set. It supplies bounded local
input for one later docs-first profile closure. No archive may be extracted,
and no Rust toolchain, Charon source, Lean toolchain, Cargo home, Lake client,
sandbox backend, generated source, or kernel process may be created.

## Acceptance Command Separation

The bounded discovery producer writes status JSON, stdout, and stderr. The next
top-level command may contain only the duplicate-key-safe status and summary
parser. It must propagate nonzero directly. It may not print diagnostics, hash
files, write a checkpoint, change shell error mode, or execute a later command.

Only after that top-level parser itself exits zero may one separate top-level
command write the discovery checkpoint and transcript hashes. A failed parser,
masked status, premature checkpoint, or output outside the declared summary
stops Phase 741 and removes the entire run root.

## Output and Claims

On complete discovery success, Phase 741 may retain only a Markdown report with
the observed sets and bounded transcript digests plus standard mirrors. It must
remove the run root and both downloaded assets. The report is local profile
discovery, not archive acceptance, tool materialization, backend evidence,
proof, or production input.

After commit and clean-tree gates, Phase 741 may make one discovery attempt.
Phase 740 runs no network, archive, backend, or kernel command and creates no
proof, accepted evidence, Level2+, score axis, semantic correctness, production
readiness, SOTA, breakthrough, or full-security claim.
