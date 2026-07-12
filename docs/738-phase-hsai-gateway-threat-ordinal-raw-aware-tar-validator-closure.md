# Phase 738 HSAI Gateway Threat Ordinal Raw-Aware Tar Validator Closure

## Status

Complete as a documentation-first raw-member validation correction.

State slice:
`phase-738-hsai-gateway-threat-ordinal-raw-aware-tar-validator-closure`.

Classification: `RawAwareTarParserAndSelfTestsSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Canonical Attempt Identity

Phase 739 uses canonical run root `hsai-phase739-efa3782c`, canonical detached
repository root `hsai-phase739-repo-efa3782c`, and witness
`phase739ExtractedThreatOrdinalWitnesses`.

## Raw-Name Authority

Phase 739 must use a temporary `tarfile.TarInfo` subclass that captures the raw
USTAR name, prefix, and type fields in `frombuf()` before superclass
normalization. PAX `path` or `GNU.sparse.name` values and GNU long-name values
must replace the captured effective raw name before ordinary member validation.
UTF-8 decoding is strict. Missing raw-name metadata, malformed headers, invalid
checksums, conflicting path extensions, or unsupported extension semantics stop
validation.

The only accepted final logical member types are `REGTYPE`, `AREGTYPE`, and
`DIRTYPE`, tested through `member.type` directly. `CONTTYPE`, GNU sparse,
links, devices, FIFOs, and every other type are rejected even if a convenience
predicate classifies them as file-like. Member counts are logical members after
PAX/GNU extension processing and remain exactly 2,471 and 2,125.

All Phase 736 raw-name, root, component, extraction-key, top-level, embedded
asset, status, output, and rehash rules remain. In addition, for every key,
each present ancestor key must be a directory. A regular-file ancestor of
another member is rejected. Archive file descriptors must be regular,
non-symlink files with exact size and SHA-256 before opening and unchanged
device, inode, size, mtime, and digest after validation.

## Mandatory Self-Tests

Before the canonical client hash gate and before any network or persistent-root
producer, the exact raw-aware parser must pass bounded local in-memory fixtures
covering:

- safe regular-file and directory members;
- exact permitted root behavior;
- absolute, `..`, empty, internal `.`, repeated-leading-`./`, repeated
  separator, and trailing-separator aliases;
- duplicate raw names and duplicate extraction keys;
- regular-file ancestor collisions;
- symlink, hard link, character/block device, FIFO, contiguous, sparse, and
  unknown member types;
- invalid root type/count;
- unexpected top-level keys and wrong logical member counts;
- PAX path and GNU long-name raw preservation; and
- malformed checksum/header rejection.

The self-test producer uses the bounded runner, emits one canonical summary,
and must exit zero with empty stderr. The next top-level command must parse the
runner status and summary before canonical client hashes. Failed, skipped,
weakened, or alternate self-tests stop before acquisition.

The real validator then emits stdout only after every archive and embedded
asset check succeeds. Its one canonical JSON summary must bind schema, helper
SHA-256, archive identities, logical counts, root counts, top-level sets,
member-type counts, extraction-tree inventory digests, and embedded-asset byte
equality. Failure stdout is empty and stderr contains one bounded canonical
error record without a traceback. The following top-level command remains the
sole acceptance point for runner status and summary.

Python 3.9's public `tarfile` documentation and pinned implementation source are
imported parser trust roots, not proof authority:
[Python 3.9 tarfile documentation](https://docs.python.org/3.9/library/tarfile.html),
[CPython 3.9.6 tarfile source](https://github.com/python/cpython/blob/v3.9.6/Lib/tarfile.py).

After commit and detached-worktree gates, Phase 739 may make one attempt. The
Phase 732 exact fixtures and loopback controls, Phase 736 archive profiles, and
every inherited identity, independent acquisition/materialization, exact
version, token, client, scanner, component, source, cache, rfl witness, direct
`.olean`, cleanup, evidence, and claim rule remain.

Phase 738 runs no tool or backend and creates no proof, accepted evidence,
Level2+, score axis, semantic correctness, production readiness, SOTA,
breakthrough, or full-security claim.
