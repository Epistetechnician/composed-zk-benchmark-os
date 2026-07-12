# Phase 736 HSAI Gateway Threat Ordinal Structured Archive Validator Closure

## Status

Complete as a documentation-first structured archive-validation correction.

State slice:
`phase-736-hsai-gateway-threat-ordinal-structured-archive-validator-closure`.

Classification: `StructuredTarMemberValidationSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Canonical Attempt Identity

Phase 737 uses canonical run root `hsai-phase737-efa3782c`, canonical detached
repository root `hsai-phase737-repo-efa3782c`, and witness
`phase737ExtractedThreatOrdinalWitnesses`.

## Structured Validator

After both exact Aeneas asset hashes pass, Phase 737 must run one temporary
Python-standard-library `tarfile` validator as a bounded producer over both
archives. It replaces text and verbose inventory producers. The validator must
open each archive in gzip-read mode, call `getmembers()` once, and emit one
deterministic structured inventory from those same members.

The main archive must contain exactly 2,471 members and no root marker. Its
declared top-level extraction keys are exactly:

```text
aeneas
backends
charon
charon-driver
libs
```

The Lean-build archive must contain exactly 2,125 members, exactly one root
marker, and top-level extraction keys exactly `ir` and `lib`. The root marker
must be raw `.` or `./` and must be a directory. No second root marker is
allowed.

For every non-root member, the validator must:

1. require the structured member type to be only regular file or directory;
2. reject absolute names;
3. remove at most one leading `./`;
4. remove exactly one trailing `/` only for a directory;
5. split on `/` and reject every empty, `.`, or `..` component;
6. join the remaining components as the extraction-equivalent collision key;
7. reject duplicate raw names and duplicate collision keys across files and
   directories; and
8. require the first collision-key component to belong to the archive's exact
   declared top-level set.

This allowlist rejects symlinks, hard links, character/block devices, FIFOs,
sockets, sparse/unknown types, and metadata-only extraction aliases. The
validator must also locate the regular member
`backends/lean/.lake/lean-build-aeneas-arm64-apple-darwin24.6.0.tar.gz`, stream
it through SHA-256, and require exact size `50447755`, digest
`f1771437f16e5e34135719ff467b32ecda101cc215dc411741cd098732916f59`,
and byte equality with the separately downloaded Lean-build asset.

The validator runs under the bounded process-group runner with 120 seconds,
1 MiB stdout, and 256 KiB stderr. The runner's status JSON is the sole child
status authority. The next top-level command must require `reason=exit`,
`returncode=0`, regular bounded streams, exact member counts, exact top-level
sets, and the embedded-asset equality record before any extraction command.
No shell `$?`, display command, or later process may replace that result.

## Extraction Binding

Immediately after structured validation and again immediately before each
separate extraction producer, Phase 737 must recheck both outer archive byte
counts and SHA-256 values. Any drift stops before extraction. Main Aeneas and
Lean-build staging extraction remain separate top-level producers with numeric
statuses, bounded streams, and checkpoints. The inherited 2,021-file,
104-directory, zero-link, equal-path, equal-file-digest, and equal-inventory
rules remain mandatory before staging deletion.

The pinned upstream release workflow copies the Nix release output into a
staging directory, precompiles the Lean support tree, and packages top-level
entries with `tar -- *`; it is source context, not evidence authority:
[Aeneas release workflow](https://github.com/AeneasVerif/aeneas/blob/c2015b8668ba6d5b41f5f19d00a881c12bbb0b5d/.github/workflows/release.yml).

After commit and detached-worktree gates, Phase 737 may make one attempt. The
Phase 732 exact fixtures and loopback controls plus every inherited identity,
independent acquisition/materialization, exact version, token, client, scanner,
component, source, cache, rfl witness, direct `.olean`, cleanup, evidence, and
claim rule remain.

Phase 736 runs no tool or backend and creates no proof, accepted evidence,
Level2+, score axis, semantic correctness, production readiness, SOTA,
breakthrough, or full-security claim.
