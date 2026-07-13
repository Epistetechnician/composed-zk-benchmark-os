# Phase 776 HSAI Formal Execution Contract Correction

## Status

Complete as a documentation-first executable-identity, sandbox-binding,
producer-cardinality, environment, and retention-schema correction.

State slice: `phase-776-hsai-formal-execution-contract-correction`.

Classification: `FormalExecutionContractsCorrected`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Correction Verdict

Phase 776 supersedes the incomplete Phase 774 command-family details without
changing the historical Phase 774 resolution digest. The corrected plan has
exactly 102 ordinary bounded commands plus one dedicated controlled-loopback
lifecycle. The increase from 84 is the addition of 18 packaged-Aeneas native
asset audits that Phase 774 omitted.

This is an authoring contract for a later fully expanded source ledger. It is
not an executable plan, executor binding, machine-resolved attempt, or backend
run.

## Executable Identity Contract

The immutable ledger binds executable roles, not a machine-specific Homebrew
Cellar path. The following placeholders replace hard-coded paths whose entry
may be a symlink:

| Placeholder | Type | Producer | Allowed consumers | Resolved-root class |
|---|---|---|---|---|
| `${GIT_EXE}` | canonical executable identity | `resolve-git-executable` | Git rows only | `host-executable` |
| `${ZSTD_EXE}` | canonical executable identity | `resolve-zstd-executable` | `decompress-lean-archive` | `host-executable` |
| `${TAR_EXE}` | canonical executable identity | `resolve-tar-executable` | `extract-lean-tar` | `host-executable` |
| `${SANDBOX_EXEC_EXE}` | canonical executable identity | `resolve-sandbox-executable` | every `sandbox-closed` row | `host-executable` |

Each identity resolution is an in-process, read-only precondition. It records:

```text
requested_path
requested_path_kind
ordered_symlink_hops
canonical_regular_file_path
canonical_device_and_inode
sha256
mode
owner
```

Acceptance requires an absolute requested path, a finite symlink chain with no
relative escape, a canonical absolute regular-file target, no writable target
by group or other, an executable mode, and a SHA-256 admitted by the later
machine policy. The immutable source ledger contains the executable role and
these acceptance rules. Only the machine-resolved attempt digest contains the
resolved path, link facts, device/inode, and observed digest.

The current host observation that Git, zstd, and tar entry paths are symlinks
does not fail this corrected contract. It does prevent those entry paths from
being described as canonical regular files.

All other absolute native-audit executable paths remain subject to the same
identity record. A later ledger may spell their immutable requested paths
directly only when the entry itself is a regular file; the resolved attempt
still records its digest.

## Typed Placeholder Registry

Every placeholder belongs to exactly one of these closed groups. A group row
defines the type, producer, allowed consumer set, and resolved-root class for
each listed name; no name inherits semantics from its spelling.

| Names | Type | Producer | Allowed consumers | Resolved-root class |
|---|---|---|---|---|
| `PRIMARY_ROOT` | existing canonical directory | operator input acceptance | primary Git and final verification rows | `primary-repository` |
| `DETACHED_ROOT` | owned canonical directory | `create-detached-worktree` | detached Git, preflight, source, and cleanup rows | `attempt-owned` |
| `ATTEMPT_ROOT` | owned canonical directory | `materialize-attempt-root` | all attempt-owned descendants | `attempt-owned` |
| `ATTEMPT_TMP` | owned canonical directory | `materialize-attempt-tmp` | bounded temporary-output rows | `attempt-owned` |
| `TRANSCRIPT_ROOT` | owned canonical directory | `materialize-transcript-root` | every ordinary command row | `attempt-owned` |
| `DOWNLOAD_ROOT` | owned canonical directory | `materialize-download-root` | acquisition, validation, and extraction rows | `attempt-owned` |
| `HOME_ROOT` | owned canonical directory | `materialize-home-root` | every replacement environment | `attempt-owned` |
| `RUSTUP_ROOT` | owned canonical directory | `materialize-rustup-root` | Rust acquisition, identity, build, and driver rows | `attempt-owned` |
| `CHARON_CARGO_HOME` | owned canonical directory | `materialize-charon-cargo-home` | Charon fetch and build rows | `attempt-owned` |
| `AENEAS_ROOT` | owned canonical directory | `extract-aeneas-main` | packaged audits, generation, and Lean rows | `attempt-owned` |
| `LEAN_ROOT` | owned canonical directory | `extract-lean-tar` | Lean/Lake identity, dependency, and kernel rows | `attempt-owned` |
| `CHECKER_CARGO_HOME` | borrowed cache with bounded mutable metadata | operator input acceptance | Charon extraction only | `borrowed-cache` |
| `TOOLCHAIN_ROOT` | owned canonical directory | `install-rust-toolchain` | Rust identity, Charon build, and driver rows | `attempt-owned` |
| `CHARON_TARGET` | owned canonical directory | `materialize-charon-target` | Charon build and source-built audit rows | `attempt-owned` |
| `CLIENT_ROOT` | owned canonical directory | `materialize-client-root` | Lake, Aeneas generation, kernel, and retention rows | `attempt-owned` |
| `MATHLIB_CACHE_ROOT` | owned canonical directory | `materialize-mathlib-cache-root` | Lake cache acquisition and freeze rows | `attempt-owned` |
| `CHARON_SOURCE` | owned canonical source directory | `initialize-charon-source` | Charon source, dependency, build, and stability rows | `attempt-owned` |
| `CHARON_BIN`, `CHARON_DRIVER` | canonical regular executable path | `build-charon` plus binary acceptance | source-built Charon audits and backend rows | `charon-target-owned` |
| `SOURCE_HEAD` | 40-hex commit scalar | primary snapshot acceptance | detached creation and HEAD equality consumers | `scalar` |
| `ORDINAL_3` | three-digit ordinal scalar | source-ledger row | that row's three transcript paths only | `scalar` |
| `OPERATION_ID` | operation-id scalar | source-ledger row | that row's three transcript paths only | `scalar` |
| `SANDBOX_PROFILE` | canonical regular-file path | `materialize-sandbox-profile` | every `sandbox-closed` row | `attempt-owned` |
| `GIT_EXE`, `ZSTD_EXE`, `TAR_EXE`, `SANDBOX_EXEC_EXE` | canonical executable identity | named identity resolver | consumers in the executable table | `host-executable` |

Unknown, unresolved, recursive, NUL-bearing, repeated-brace, relative,
noncanonical, owner-escaping, or symlink-ancestor path resolutions fail before
mutation. A future ledger must expand each row's allowed placeholders; group
membership is not runtime profile inheritance.

`CHECKER_CARGO_HOME` is pre-existing and never receives an ownership receipt.
Only `registry/index`, `.package-cache`, and `.global-cache` may change during
the exact locked/offline Cargo consumer. Immutable-cache digest acceptance
excludes only those three roots, and cleanup may never remove or rewrite any
part of the borrowed cache.

## Lean Extraction Correction

The two pipeline-free commands remain, but overwrite authority is removed:

```text
decompress-lean-archive:
  ${ZSTD_EXE} -d -o ${ATTEMPT_TMP}/lean.tar ${DOWNLOAD_ROOT}/lean-4.31.0-darwin_aarch64.tar.zst

extract-lean-tar:
  ${TAR_EXE} -x -f ${ATTEMPT_TMP}/lean.tar -C ${LEAN_ROOT}
```

Before decompression, `${ATTEMPT_TMP}` must carry a successful owned-root
receipt, be mode `0700`, and contain no `lean.tar`. `--force` is forbidden.
After zero exit, the adapter accepts exactly one regular, non-symlink,
owner-contained `lean.tar`, changes its mode to `0600` in-process if needed,
records its digest and size, and freezes those facts for the tar consumer. Any
pre-existing output, replacement, extra output, wrong owner, or path change
fails. The intermediate is removed in-process only after extraction acceptance.

## Sandbox Binding

Phase 776 chooses an argv-bound wrapper. Every `sandbox-closed` command has the
literal prefix:

```text
${SANDBOX_EXEC_EXE} -f ${SANDBOX_PROFILE}
```

The wrapped executable and its arguments follow in the same argv array. The
executor may not add, remove, or rewrite the prefix. Source-ledger argv,
executor-binding identity, transcript status, and machine-resolved attempt
digest therefore cover the same process invocation.

The sandbox profile is materialized from committed byte-exact content beneath
an owned attempt root, mode `0600`, and SHA-256 pinned before any wrapped row.
The committed source is the following UTF-8 byte sequence with one LF after
each line, including the final line:

```text
(version 1)
(allow default)
(deny network*)
```

Its SHA-256 is
`5c358b8d847211333e7ba22df82d84f796b5f30a41a2682209a949d783adbd08`.
`materialize-sandbox-profile` is the sole producer and must create the absent
file exclusively; no placeholder substitution occurs inside the profile.
Its accepted policy denies external IPv4, external IPv6, DNS, proxy use, and
new network connection creation while retaining the exact filesystem and local
process permissions needed by the named row. Independently, the bounded
executor must spawn with `close_fds=true`, preserve only file descriptors 0,
1, and 2 plus its private status channel, mark that channel close-on-exec, and
prove through a committed fixture that no inherited socket or extra descriptor
is visible after exec. The three sandbox controls and
the dedicated loopback lifecycle must pass before any build or backend row.
An unavailable or rejected `sandbox-exec` identity stops the future attempt;
there is no unsandboxed fallback.

## Corrected Native-Audit Cardinality

### Packaged Aeneas assets: 18 host-offline rows

These audits occur after archive materialization and before irreversible
network closure. Adjacency, exact path identity, digest equality, and absolute
dependency existence are pure acceptances over the resulting transcripts and
descriptor-relative filesystem observations.

```text
lipo-packaged-aeneas
lipo-packaged-charon
lipo-packaged-charon-driver
lipo-packaged-libgmp
codesign-verify-packaged-aeneas
codesign-verify-packaged-charon
codesign-verify-packaged-charon-driver
codesign-display-packaged-aeneas
codesign-display-packaged-charon
codesign-display-packaged-charon-driver
spctl-packaged-aeneas
spctl-packaged-charon
spctl-packaged-charon-driver
otool-libraries-packaged-aeneas
otool-libraries-packaged-charon
otool-libraries-packaged-charon-driver
otool-libraries-packaged-libgmp
otool-load-commands-packaged-charon-driver
```

Each `lipo` row targets one asset and must exit 0 with exactly `arm64` after
normalized whitespace. Each `codesign --verify --strict --verbose=4` and
`codesign --display --verbose=4` row must exit 0 and disclose ad-hoc signing
with no Team ID. Each `otool` row must exit 0. The driver load-command row must
show no usable `LC_RPATH`; dependency acceptance must reproduce the pinned
historical dependency set and stop if an absolute dependency is unavailable.

The three `spctl --assess --type execute --verbose=4` rows have the normative
admission result `reason=exit`, `return_code=3`, `signal=null`. Phase 776 sets
that result as a new future-run policy; the older observations establish only
rejection, not the numeric code. Their stderr must
classify the asset as rejected. This is a negative Gatekeeper observation for
the pinned research assets, not a production trust result. A Darwin/tool
identity drift that changes the return code blocks the attempt instead of
being normalized.

### Source-built Charon assets: 10 sandbox-closed rows

```text
lipo-built-charon
lipo-built-charon-driver
codesign-verify-built-charon
codesign-verify-built-charon-driver
codesign-display-built-charon
codesign-display-built-charon-driver
otool-libraries-built-charon
otool-libraries-built-charon-driver
otool-load-commands-built-charon-driver
preflight-built-charon-driver-load
```

All ten use the sandbox prefix and have the normative admission result
`reason=exit`, `return_code=0`, and `signal=null`. These are Phase 776 policy
choices, not inherited observations. The architecture rows require `arm64`.
Signature rows require a valid ad-hoc signature with no Team ID; an unsigned,
invalidly signed, or differently identified local build stops. They may not
import the packaged-asset Gatekeeper rejection. Library rows reject unavailable
absolute dependencies.
The load-command row targets `${CHARON_DRIVER}`, requires the expected
`@rpath/librustc_driver-cddc585b497d1e17.dylib` identity resolved to the
regular file of that name below `${TOOLCHAIN_ROOT}`, and the final non-mutating
preflight proves that the driver loads under `${TOOLCHAIN_ROOT}` without
invoking extraction.

Native status outcomes are exact, but transcript acceptance remains fail-closed.
The future ledger must freeze parser grammars for the `codesign`, `spctl`, and
`otool` versions bound by each executable identity. Until those grammars are
committed, all affected rows remain `blocked`; no substring-only acceptance or
return-code-only promotion is permitted.

### Corrected total

```text
Phase 774 ordinary command total                         84
remove Phase 774 mixed native-audit rows                -10
add corrected source-built Charon audit rows            +10
add omitted packaged-Aeneas asset audit rows            +18
corrected ordinary bounded command total                102
dedicated controlled-loopback lifecycle                   1
```

The ten external-acquisition ids and the irreversible closure position remain
unchanged. The 18 packaged rows are inserted after `capture-aeneas-version`
and before `download-lean`. The ten source-built rows remain after
`capture-charon-version` and before `extract-checker-llbc`. All later ordinals
shift deterministically in the future expanded ledger.

## Transcript Fields

Every ordinary row expands three independent templates, never a brace-based
pseudo-template:

```text
status_path_template=${TRANSCRIPT_ROOT}/${ORDINAL_3}-${OPERATION_ID}/status.json
stdout_path_template=${TRANSCRIPT_ROOT}/${ORDINAL_3}-${OPERATION_ID}/stdout.bin
stderr_path_template=${TRANSCRIPT_ROOT}/${ORDINAL_3}-${OPERATION_ID}/stderr.bin
```

The paths are distinct, absent, exclusively created, mode `0600`, and owned by
the attempt. Status is written last after stream flush and process-group reap.

## Replacement Environment Vocabulary

Plan v2 must replace the current source allowlist with this closed vocabulary:

```text
CARGO_HOME CARGO_NET_OFFLINE CARGO_TARGET_DIR
GIT_CONFIG_GLOBAL GIT_CONFIG_NOSYSTEM GIT_LFS_SKIP_SMUDGE
GIT_OPTIONAL_LOCKS GIT_TERMINAL_PROMPT
HOME HSAI_AENEAS_LEAN_ROOT LANG LC_ALL
MATHLIB_CACHE_DIR MATHLIB_NO_CACHE_ON_UPDATE
NO_COLOR PATH RUN RUST_BACKTRACE RUSTC RUSTDOC
RUSTUP_HOME RUSTUP_TOOLCHAIN TERM TMPDIR TZ
```

Every row carries a complete replacement environment rather than inheriting
the parent. The base is exactly:

```text
HOME=${HOME_ROOT}
LANG=C
LC_ALL=C
TZ=UTC
TMPDIR=${ATTEMPT_TMP}
TERM=dumb
NO_COLOR=1
PATH=/usr/bin:/bin:/usr/sbin:/sbin
```

Git, Rust/Cargo, timeout-fixture, and Lean/Lake additions are limited to the
keys above and only where the expanded row requires them. Proxy, credential,
askpass, SSH, token, dynamic-loader override, resolver override, and inherited
environment variables are absent. Executable selection is carried by exact
argv placeholders, not by `PATH` lookup.

## Path-Free Retained Kernel Evidence

On complete future success, the retention transaction may create exactly this
tree under the committed formal evidence location:

```text
HsaiGatewayThreatOrdinalAeneas/Extracted/Types.lean
HsaiGatewayThreatOrdinalAeneas/Extracted/Funs.lean
HsaiGatewayThreatOrdinalAeneas/Witnesses.lean
client-metadata.json
provenance.json
kernel-results.json
statuses/check-types.json
statuses/check-funs.json
statuses/check-witness.json
statuses/lake-build.json
README.md
```

No `.olean`, machine-local Lake manifest, absolute path, username, hostname,
device/inode, attempt-root name, cache path, raw environment, or secret is
retained. The `.olean` files remain attempt-local; their SHA-256 and producing
status identities are retained in `kernel-results.json`.

`client-metadata.json` binds schema, namespace, module order, pinned package
commits, Lean toolchain identity, and relative module paths.

`provenance.json` binds schema, state slice, source HEAD, frozen checker file
digests, generated-source digests, witness digest, Aeneas/Charon/Lean tool
identity digests, source-ledger digest, plan-v2 digest, executor-binding digest,
and the machine-resolved attempt digest without resolved paths.

The four status files are byte-identical path-free projections of the accepted
bounded-runner status records. They retain operation id, reason, return code,
signal, timeout and caps, stream sizes and SHA-256 values, input/output digest
bindings, executable-role identity digest, and sandbox-profile digest, but no
absolute path or wall-clock timestamp. `kernel-results.json` binds:

```text
schema
ordered_check_ids
check_types_status_sha256
check_funs_status_sha256
check_witness_status_sha256
lake_build_status_sha256
types_olean_sha256
funs_olean_sha256
witnesses_olean_sha256
lake_build_inventory_sha256
all_expected_zero_exit
all_inputs_digest_matched
green_kernel_result
```

`green_kernel_result` is true only when the three direct Lean checks and final
Lake build have accepted zero-exit statuses, every input digest matches, every
expected `.olean` exists below the allowed build root, and the final mutable
inventory is exact. It means only that the pinned Lean kernel accepted the
retained modules under the recorded tool and dependency identities.

The exact consumers are the retention transaction, retained-tree verifier,
local report renderer, and a future evidence-append proposal builder. No
consumer may mutate an accepted Evidence Ledger in this phase. Generated
sources, witness, metadata, provenance, and results must be byte-identical to
the accepted attempt inputs before atomic publication. Each recorded status
SHA-256 must recompute from its retained status preimage. Partial retention is
removed; a failure retains only the separately authorized bounded failure note.

## Correction Contract Identity

Canonical JSON, with no trailing newline:

```json
{"corrected_command_count":102,"inherited_fd_policy":"close-all-except-stdio","packaged_aeneas_audit_count":18,"retained_file_count":11,"sandbox_binding":"argv-prefix","sandbox_profile_sha256":"5c358b8d847211333e7ba22df82d84f796b5f30a41a2682209a949d783adbd08","schema":"hsai-formal-execution-contract-correction-v1","source_built_charon_audit_count":10,"spctl_expected_return_code":3}
```

SHA-256:

```text
7cbd663038029a293866687c5750e0c523fe33bdef2aa7855a5f63fd7896a72f
```

This digest identifies the correction decisions only. It is not the future
102-row source-ledger digest.

## Phase 777 Gate

Phase 777 must remain documentation-first. It may add one fully expanded,
ordered 102-row `hsai-formal-source-ledger-v1` document plus standard mirrors.
Every row must contain exact argv, cwd, complete replacement environment,
capability, timeout, caps, three transcript templates, exact expected outcome,
typed inputs and outputs, acceptance id, executable roles, and resolution
status. Shared profiles and grouped placeholder rules must be expanded into
each row.

Rows whose exact downloader, installer, helper file order, native transcript
grammar, driver-preflight argv, archive inventory, or machine executable digest
remains unresolved must stay `blocked`. Phase 777 may publish a source-ledger
digest only if all path-normalized row fields are complete; machine-specific
identity observations remain outside that digest. It may not modify Python or
Rust source or run any producer.

Phase 776 creates no executable plan, source-ledger digest, executor binding,
machine-resolved attempt, backend result, generated Lean, retained kernel
result, proof artifact, checker transcript, accepted evidence, Level2+, score
axis, semantic correctness, production readiness, SOTA, breakthrough, full
security, external audit, or action authority.

Phase 777 subsequently stops before ledger expansion because the packaged and
source-built version producers precede their required native acceptance. See
`docs/777-phase-hsai-formal-execution-pre-use-ordering-stop.md`. Phase 778 must
correct the exact 102-command order before any row expansion.
