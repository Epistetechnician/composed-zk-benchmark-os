# Phase 774 HSAI Formal Execution Command Family Resolution

## Status

Complete as a documentation-first command-cardinality and shared-profile
resolution.

State slice: `phase-774-hsai-formal-execution-command-family-resolution`.

Classification: `FormalCommandCardinalityResolved`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Resolution Verdict

Phase 774 replaces the four unresolved Phase 773 command families with exact
design choices. The normalized plan has exactly 84 ordinary bounded command
obligations, plus one dedicated controlled-loopback lifecycle and closed
in-process acceptance/materialization/cleanup operations.

These are new HSAI execution-contract decisions where inherited documents were
silent. They are not observations from a backend run.

## Repository And Cleanup Resolution

The six Phase 773 primary/detached rows remain and use the following Git
executable, identity-pinned before future use:

```text
/opt/homebrew/bin/git
```

Every Git argv starts with this exact prefix:

```text
/opt/homebrew/bin/git
-c core.fsmonitor=false
-c core.untrackedCache=false
-c core.hooksPath=/dev/null
-c submodule.recurse=false
```

Exact worktree suffixes are:

```text
-C ${PRIMARY_ROOT} worktree add --detach ${DETACHED_ROOT} ${SOURCE_HEAD}
-C ${PRIMARY_ROOT} worktree remove --force ${DETACHED_ROOT}
```

Initial and final primary snapshots each use separate bounded `rev-parse HEAD`
and `status --porcelain=v1 -z --untracked-files=all` commands. Final acceptance
compares byte-for-byte with the initial Phase 753 snapshot; it never assumes a
clean primary checkout.

The hidden repository/worktree lifecycle adds exactly four bounded rows:

```text
list-worktrees-before:
  -C ${PRIMARY_ROOT} worktree list --porcelain -z
capture-detached-head:
  -C ${DETACHED_ROOT} rev-parse --verify HEAD^{commit}
capture-detached-status:
  -C ${DETACHED_ROOT} status --porcelain=v1 -z --untracked-files=all --ignore-submodules=none
list-worktrees-after:
  -C ${PRIMARY_ROOT} worktree list --porcelain -z
```

Frozen file hashes, path types, root absence, executable identity, canonical
path containment, ordinal inventory, and disk reserve are pure operations over
bounded transcripts or descriptor-relative standard-library filesystem
observations. They may not spawn children. The detached worktree is accepted
only when its HEAD equals `${SOURCE_HEAD}`, status is empty, and registration
appears only between the two worktree-list transcripts.

Cleanup process-group termination, owned-root deletion, symlink rejection,
retention planning, and final snapshot comparison use in-process
standard-library operations. The already-counted `remove-detached-worktree`
Git row is the only cleanup child command. Cleanup preserves the first
operational failure, records every step result, attempts all independently safe
steps, and performs final primary verification last.

## Lean Extraction Resolution

The single Phase 773 `extract-lean` placeholder becomes two `host-offline`
bounded commands with no shell or pipeline:

```text
decompress-lean-archive:
  /opt/homebrew/bin/zstd -d --force -o ${ATTEMPT_TMP}/lean.tar ${DOWNLOAD_ROOT}/lean-4.31.0-darwin_aarch64.tar.zst
extract-lean-tar:
  /usr/bin/tar -x -f ${ATTEMPT_TMP}/lean.tar -C ${LEAN_ROOT}
```

`/opt/homebrew/bin/zstd` is a Phase 774 host-path observation that must be
regular, non-symlink, and SHA-256 pinned in a later hermetic implementation.
The intermediate tar is attempt-owned, mode `0600`, stable between commands,
and removed in-process after extraction acceptance. Extraction paths must pass
the existing archive-safety and containment rules before either command runs.

## Native Audit Resolution

The five Phase 773 native-audit placeholders become ten `sandbox-closed`
bounded commands:

```text
lipo-charon:
  /usr/bin/lipo -archs ${CHARON_BIN}
lipo-charon-driver:
  /usr/bin/lipo -archs ${CHARON_DRIVER}
codesign-verify-charon:
  /usr/bin/codesign --verify --strict --verbose=4 ${CHARON_BIN}
codesign-verify-charon-driver:
  /usr/bin/codesign --verify --strict --verbose=4 ${CHARON_DRIVER}
codesign-display-charon:
  /usr/bin/codesign --display --verbose=4 ${CHARON_BIN}
codesign-display-charon-driver:
  /usr/bin/codesign --display --verbose=4 ${CHARON_DRIVER}
spctl-charon:
  /usr/sbin/spctl --assess --type execute --verbose=4 ${CHARON_BIN}
otool-libraries-charon:
  /usr/bin/otool -L ${CHARON_BIN}
otool-libraries-charon-driver:
  /usr/bin/otool -L ${CHARON_DRIVER}
otool-load-commands-charon:
  /usr/bin/otool -l ${CHARON_BIN}
```

Adjacency, non-symlink identity, canonical-parent equality, Mach-O type,
architecture acceptance, signature disclosure, and loader-path resolution are
pure acceptances over these transcripts and descriptor-relative observations.

The inherited assets are ad-hoc signed and historically fail Gatekeeper.
`spctl-charon` therefore records an expected rejection; it is not a production
trust gate. Its exact return code remains a row-level blocked field until a
hermetic fixture freezes it. A later implementation must not normalize any
nonzero code into success or claim notarization.

## Exact Count

```text
Phase 773 identifiable obligations                     74
four new frozen-repository rows                        +4
Lean extraction: replace one placeholder with two      +1
native audit: replace five placeholders with ten       +5
cleanup: no new child beyond counted worktree removal  +0
ordinary bounded command total                         84
dedicated controlled-loopback lifecycle                 1
```

## Typed Placeholder Registry

Only single-pass `${NAME}` placeholders are permitted:

```text
PRIMARY_ROOT DETACHED_ROOT SOURCE_HEAD ATTEMPT_ROOT TRANSCRIPT_ROOT
ATTEMPT_TMP DOWNLOAD_ROOT CHARON_SOURCE CHARON_TARGET CHARON_BIN
CHARON_DRIVER CLIENT_ROOT MATHLIB_CACHE_ROOT HOME_ROOT RUSTUP_ROOT
CHARON_CARGO_HOME AENEAS_ROOT LEAN_ROOT CHECKER_CARGO_HOME TOOLCHAIN_ROOT
ORDINAL_3 OPERATION_ID
```

Unknown, unresolved, recursive, repeated-brace, relative, noncanonical,
owner-escaping, or symlink-ancestor resolutions fail before mutation.
Machine-resolved values never enter a path-normalized contract digest.

## Transcript Convention

Every ordinary command row receives three distinct paths:

```text
${TRANSCRIPT_ROOT}/${ORDINAL_3}-${OPERATION_ID}/status.json
${TRANSCRIPT_ROOT}/${ORDINAL_3}-${OPERATION_ID}/stdout.bin
${TRANSCRIPT_ROOT}/${ORDINAL_3}-${OPERATION_ID}/stderr.bin
```

Directories are mode `0700`; files are mode `0600`. Paths must be absent,
canonical, owner-contained, and free of symlink ancestors. Files are created
exclusively. Status is written last after both streams are flushed and the
complete process group is reaped. No path may be reused by another row.

## Fully Expanded Row Profiles

Profiles are authoring rules only. A future ledger must expand every field into
every row before hashing; runtime profile inheritance is prohibited.

| Profile | Cwd | Timeout | Stdout cap | Stderr cap |
|---|---|---:|---:|---:|
| `primary-git` | `${PRIMARY_ROOT}` | 30s | 64 KiB | 64 KiB |
| `local-preflight` | `${DETACHED_ROOT}` | 120s | 1 MiB | 256 KiB |
| `fixture-exact` | `${DETACHED_ROOT}` | inherited | 1,024 B | 1,024 B |
| `external-acquisition` | owning root | 900s | 1 MiB | 1 MiB |
| `extract-materialize` | `${ATTEMPT_ROOT}` | 600s | 1 MiB | 1 MiB |
| `native-audit` | `${ATTEMPT_ROOT}` | 120s | 1 MiB | 1 MiB |
| `sandbox-build-backend` | owning source/client root | inherited, otherwise 1,800s | inherited, otherwise 4 MiB | inherited, otherwise 4 MiB |
| `direct-lean` | `${CLIENT_ROOT}` | 120s | 256 KiB | 256 KiB |

The exact fixture, Charon extraction, pretty-print, Aeneas generation, direct
Lean, and Lake-build bounds from controlling phases override shared authoring
defaults.

Every expanded replacement environment includes only declared entries. The
base is:

```text
HOME=${HOME_ROOT}
LANG=C
LC_ALL=C
TZ=UTC
TMPDIR=${ATTEMPT_TMP}
TERM=dumb
NO_COLOR=1
PATH=/usr/bin:/bin:/usr/sbin:/sbin
GIT_CONFIG_NOSYSTEM=1
GIT_CONFIG_GLOBAL=/dev/null
GIT_TERMINAL_PROMPT=0
```

Git rows add `GIT_OPTIONAL_LOCKS=0` and `GIT_LFS_SKIP_SMUDGE=1`. Rust, Cargo,
Lean, and Lake rows add only their exact roots and tool paths. Offline rows add
`CARGO_NET_OFFLINE=true` where applicable. The timeout fixture alone adds
`RUN=${ATTEMPT_ROOT}`. Proxy, askpass, SSH, token, resolver override, and
credential variables remain absent.

The default expected result is `exit`, return code `0`, signal `null`.
Phase 732 timeout/stdout-limit/stderr-limit outcomes retain their exact reasons
and signal `15`. `spctl-charon` remains explicitly blocked until its exact
expected nonzero return code is frozen.

## Network Closure

The exact `external-acquisition` set is:

```text
download-rust-manifest
install-rust-toolchain
fetch-charon-source
download-aeneas-main
download-aeneas-lean
download-lean
fetch-charon-dependencies
lake-update
lake-cache-get
resolve-hostname-before-closure
```

An in-process `external-network-closed` barrier follows
`resolve-hostname-before-closure`. Every later ordinary child is
`sandbox-closed`. The dedicated loopback controller alone may declare
`controlled-loopback`; it does not reopen external networking.

## Resolution Contract Identity

The following canonical JSON has no trailing newline and is not an executable
source ledger:

```json
{"exact_command_count":84,"external_acquisition_ids":["download-rust-manifest","install-rust-toolchain","fetch-charon-source","download-aeneas-main","download-aeneas-lean","download-lean","fetch-charon-dependencies","lake-update","lake-cache-get","resolve-hostname-before-closure"],"network_closure_after":"resolve-hostname-before-closure","replacements":{"cleanup_external":["remove-detached-worktree"],"frozen-repository":["list-worktrees-before","capture-detached-head","capture-detached-status","list-worktrees-after"],"lean-extraction":["decompress-lean-archive","extract-lean-tar"],"native-audit":["lipo-charon","lipo-charon-driver","codesign-verify-charon","codesign-verify-charon-driver","codesign-display-charon","codesign-display-charon-driver","spctl-charon","otool-libraries-charon","otool-libraries-charon-driver","otool-load-commands-charon"]},"schema":"hsai-formal-command-family-resolution-v1","transcript_template":"${TRANSCRIPT_ROOT}/${ORDINAL_3}-${OPERATION_ID}/{status.json,stdout.bin,stderr.bin}"}
```

SHA-256:

```text
d6117ddd618fde5369f109bc73487c5aa210d6b4c6adcc9039fc70f998dee3ae
```

This digest binds Phase 774 cardinality and shared resolution decisions only.
It is not the missing fully expanded 84-row source-ledger digest.

## Phase 775 Gate

Phase 775 must remain documentation-first. It may add one fully expanded
84-row source ledger and standard mirrors. Every row must contain exact argv,
cwd, replacement environment, capability, timeout, caps, transcript paths,
expected reason/return/signal, typed inputs/outputs, acceptance id, and
resolution status. Shared profiles must be expanded, not referenced.

Rows with unresolved exact executable identities, asset commands, artifact
inventories, or `spctl` outcome remain `blocked`. Phase 775 may publish the
canonical `hsai-formal-source-ledger-v1` digest only if all 84 rows are fully
resolved. It may not modify source or run any producer.

Phase 774 creates no executable plan, source-ledger digest, backend result,
proof artifact, checker transcript, accepted evidence, Level2+, score axis,
semantic correctness, production readiness, SOTA, breakthrough, full-security
claim, external audit, or action authority.
