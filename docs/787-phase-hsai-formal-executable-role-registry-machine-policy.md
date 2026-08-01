# Phase 787 HSAI Formal Executable Role Registry And Machine Policy

## Status

Complete as a documentation-first Phase 780 lane `L09` contract closure.

State slice: `phase-787-hsai-formal-executable-role-registry-machine-policy`.

Classification: `ExecutableRoleRegistryAndMachinePolicyResolved`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Resolution Verdict

Phase 787 resolves Phase 780 lane `L09` at the immutable contract-input level.
It publishes:

1. one closed 26-role executable registry;
2. four exact executable acceptance-policy classes;
3. one external machine-policy schema;
4. one attempt-specific executable identity-observation schema;
5. exact complete role bindings for all 83 `E83` operations; and
6. exact native grammar-selector inputs for `codesign`, `spctl`, and `otool`.

It does not resolve any executable on the current host or publish an observed
path, symlink chain, device, inode, owner, mode, SHA-256, host identifier, or
policy instance. Those values remain external machine observations.

Historical Phase 779 JSONL remains unchanged. Its 1,469 blocker objects and
102 blocked rows remain historical facts, and no source-ledger digest exists.
The successor ledger may consume this registry during Phase 795-797 expansion.

Resolved lanes are now `L01` through `L04` and `L09`. Open lanes are `L05`
through `L08`, `L10`, and `L11`.

## Registry Schema

The immutable registry schema is
`hsai-formal-executable-role-registry-v1`. It contains exactly:

```text
schema
registry_id
base_operation_order_sha256
base_row_count
scope_id
scope_ordinals
roles
consumer_bindings
acceptance_policy_classes
machine_policy_schema
identity_observation_schema
native_grammar_selector_schema
source_anchors
```

The fixed header values are:

```text
registry_id=phase787-e83-executable-role-registry
base_operation_order_sha256=490c30a8098214754d20e4025696e2e3c702df8d4f7114a611157653ea7a4464
base_row_count=102
scope_id=E83
scope_ordinals=007-022,028-058,061-082,085-098
scope_ordinal_count=83
role_count=26
acceptance_policy_class_count=4
```

Every role record has these exact fields:

```text
role_id
requested_path_template
requested_path_kind
identity_class
resolver_id
producer_or_external_authority
acceptance_policy_id
grammar_selector_id
consumer_operation_ids
source_anchors
```

Every consumer binding names one exact Phase 778 ordinal and operation ID plus
the complete ordered set of executable roles required by that operation.
Roles are not inferred from capability, path spelling, imports, descendants,
or a shared runtime profile.

## Closed Role Registry

`machine-policy-path:<ROLE>` means that the immutable registry names the role
and machine-policy key while the approved absolute requested path exists only
in a later machine-policy instance. It is not a path placeholder and may not be
expanded through environment variables or `PATH`.

| Role ID | Requested path template | Kind | Identity class | Resolver | Policy | Grammar selector |
|---|---|---|---|---|---|---|
| `GIT_EXE` | `machine-policy-path:GIT_EXE` | machine-policy absolute | host | `resolve-host-executable-v1` | `host-declared-sha256-v1` | none |
| `ZSTD_EXE` | `machine-policy-path:ZSTD_EXE` | machine-policy absolute | host | `resolve-host-executable-v1` | `host-declared-sha256-v1` | none |
| `TAR_EXE` | `/usr/bin/tar` | fixed absolute | host | `resolve-host-executable-v1` | `host-fixed-sha256-v1` | none |
| `SANDBOX_EXEC_EXE` | `/usr/bin/sandbox-exec` | fixed absolute | host wrapper | `resolve-host-executable-v1` | `host-fixed-sha256-v1` | none |
| `PYTHON3_EXE` | `/usr/bin/python3` | fixed absolute | host | `resolve-host-executable-v1` | `host-fixed-sha256-v1` | none |
| `ECHO_EXE` | `/bin/echo` | fixed absolute | host fixture | `resolve-host-executable-v1` | `host-fixed-sha256-v1` | none |
| `SH_EXE` | `/bin/sh` | fixed absolute | host fixture | `resolve-host-executable-v1` | `host-fixed-sha256-v1` | none |
| `SLEEP_EXE` | `/bin/sleep` | fixed absolute | host fixture | `resolve-host-executable-v1` | `host-fixed-sha256-v1` | none |
| `YES_EXE` | `/usr/bin/yes` | fixed absolute | host fixture | `resolve-host-executable-v1` | `host-fixed-sha256-v1` | none |
| `CURL_EXE` | `/usr/bin/curl` | fixed absolute | host acquisition | `resolve-host-executable-v1` | `host-fixed-sha256-v1` | none |
| `RUSTUP_EXE` | `machine-policy-path:RUSTUP_EXE` | machine-policy absolute | host acquisition | `resolve-host-executable-v1` | `host-declared-sha256-v1` | none |
| `RUSTC_EXE` | `${TOOLCHAIN_ROOT}/bin/rustc` | owned-root template | extracted toolchain | `resolve-owned-executable-v1` | `owned-extracted-sha256-v1` | none |
| `CARGO_EXE` | `${TOOLCHAIN_ROOT}/bin/cargo` | owned-root template | extracted toolchain | `resolve-owned-executable-v1` | `owned-extracted-sha256-v1` | none |
| `SHASUM_EXE` | `/usr/bin/shasum` | fixed absolute | host | `resolve-host-executable-v1` | `host-fixed-sha256-v1` | none |
| `FILE_EXE` | `/usr/bin/file` | fixed absolute | host | `resolve-host-executable-v1` | `host-fixed-sha256-v1` | none |
| `LIPO_EXE` | `/usr/bin/lipo` | fixed absolute | host native audit | `resolve-host-executable-v1` | `host-fixed-sha256-v1` | none |
| `CODESIGN_EXE` | `/usr/bin/codesign` | fixed absolute | host native audit | `resolve-host-executable-v1` | `host-fixed-sha256-v1` | `darwin-native-v1` |
| `SPCTL_EXE` | `/usr/sbin/spctl` | fixed absolute | host native audit | `resolve-host-executable-v1` | `host-fixed-sha256-v1` | `darwin-native-v1` |
| `OTOOL_EXE` | `/usr/bin/otool` | fixed absolute | host native audit | `resolve-host-executable-v1` | `host-fixed-sha256-v1` | `darwin-native-v1` |
| `AENEAS_EXE` | `${AENEAS_ROOT}/aeneas` | owned-root template | extracted artifact | `resolve-owned-executable-v1` | `owned-extracted-sha256-v1` | none |
| `LEAN_EXE` | `${LEAN_ROOT}/bin/lean` | owned-root template | extracted artifact | `resolve-owned-executable-v1` | `owned-extracted-sha256-v1` | none |
| `LAKE_EXE` | `${LEAN_ROOT}/bin/lake` | owned-root template | extracted artifact | `resolve-owned-executable-v1` | `owned-extracted-sha256-v1` | none |
| `TRUE_EXE` | `/usr/bin/true` | fixed absolute | host control | `resolve-host-executable-v1` | `host-fixed-sha256-v1` | none |
| `NC_EXE` | `/usr/bin/nc` | fixed absolute | host control | `resolve-host-executable-v1` | `host-fixed-sha256-v1` | none |
| `CHARON_EXE` | `${CHARON_BIN}` | producer-artifact template | source-built artifact | `resolve-owned-built-executable-v1` | `owned-built-receipt-sha256-v1` | none |
| `CHARON_DRIVER_EXE` | `${CHARON_DRIVER}` | producer-artifact template | source-built artifact | `resolve-owned-built-executable-v1` | `owned-built-receipt-sha256-v1` | none |

`producer_or_external_authority` is fixed by identity class:

- host roles use an accepted external machine-policy instance;
- extracted toolchain roles use ordinal 016 plus toolchain inventory and
  identity acceptance;
- Aeneas roles use ordinals 033-038 plus accepted extraction identities;
- Lean/Lake roles use ordinals 058-064 plus accepted extraction identities;
  and
- source-built roles use ordinal 073 plus static native and source-stability
  acceptance before first execution.

## Acceptance Policy Classes

### `host-fixed-sha256-v1`

The requested path is the literal fixed absolute path in the registry. The
machine-policy entry must carry the same path and at least one admitted
SHA-256. Path-only or platform-signature-only acceptance is forbidden.

### `host-declared-sha256-v1`

The requested path is one explicit absolute path from the machine-policy entry
for that exact role. An empty path, relative path, path list, fallback path,
`PATH` search, `command -v`, shell discovery, or child-process discovery fails.

### `owned-extracted-sha256-v1`

The requested path expands below an already accepted attempt-owned root. The
root producer, archive identity, extraction inventory, exact relative path,
and executable SHA-256 receipt must all be accepted before use. No component
below the owned root may be a symlink.

### `owned-built-receipt-sha256-v1`

The requested path expands to one exact ordinal-073 build output. The build
receipt, exact relative path, regular-file identity, architecture, signature,
source stability, pre-use SHA-256, and post-use SHA-256 must agree. There is no
predeclared universal Charon binary digest and no path-only acceptance.

## Common Resolver Rules

Every resolver is in-process and read-only. It may not call a shell, helper,
executable locator, hash command, or subprocess.

For host roles, resolution must:

1. require an absolute requested path;
2. follow at most 32 symlink hops with cycle detection;
3. record every hop in order, including link text and containing directory;
4. resolve relative link text only against its containing directory;
5. require every resolved hop and final target to remain inside one
   machine-policy-declared allowed root;
6. require a final absolute regular file;
7. reject setuid, setgid, and sticky bits;
8. require at least one execute bit and reject group/other write bits;
9. require the numeric owner UID to appear in the entry's nonempty owner
   allowlist;
10. read and hash through a no-follow descriptor while recording stable
    pre-read and post-read metadata; and
11. require the observed SHA-256 in the entry's nonempty admitted digest set.

For owned roles, every component below the accepted root must be non-symlink.
The final file must be regular, owned by the root receipt's accepted effective
UID, free of setuid/setgid/sticky and group/other-write bits, owner-executable,
and stable across descriptor read. Its SHA-256 must equal the accepted producer
receipt and the immediate post-use recheck.

Unknown policy, missing policy, duplicate role entry, duplicate digest, empty
digest set, empty owner allowlist, excessive or cyclic symlink chain, root
escape, replacement, metadata drift, digest drift, or ambiguous ownership
fails before command launch.

## External Machine Policy Schema

The external schema is `hsai-formal-machine-executable-policy-v1`. A concrete
policy instance is operator-reviewed input to a future machine-resolved plan;
it is not created by Phase 787.

```text
schema
policy_id
registry_id
registry_document_sha256
operation_order_sha256
platform_os
platform_arch
platform_product_version
platform_build_version
allowed_roots
entries
reviewer_id
reviewed_at_utc
```

Each `entries` element contains exactly:

```text
role_id
requested_path
allowed_owner_uids
admitted_sha256
acceptance_policy_id
platform_build_selector
```

The policy must contain exactly one entry for every host role used by the
future plan. `admitted_sha256` and `allowed_owner_uids` are nonempty sorted
unique arrays. Wildcards, prefixes, regexes, semantic-version ranges, signer
substitution, latest-version selection, and unknown-role fallback are
forbidden. The complete policy bytes receive one SHA-256 that the future plan
and machine-resolved attempt must bind.

No serial number, hardware UUID, username, home path, network address, or
other private machine identifier is permitted. Platform product/build version
and architecture are compatibility selectors, not claims of machine identity.

## Identity Observation Schema

The attempt-specific schema is
`hsai-formal-executable-identity-observation-v1`:

```text
schema
registry_id
machine_policy_id
machine_policy_sha256
role_id
requested_path
requested_path_kind
ordered_symlink_hops
canonical_regular_file_path
canonical_device
canonical_inode
byte_length
observed_sha256
observed_mode
observed_owner_uid
pre_read_metadata
post_read_metadata
platform_product_version
platform_build_version
platform_arch
acceptance_policy_id
policy_entry_sha256
decision
```

`decision` is exactly `accepted` or `rejected`. A rejection carries one typed
reason and cannot be used by a command. Device, inode, observed path, observed
digest, observed owner, platform values, and policy-instance digest remain
outside the immutable source-ledger digest.

## Native Grammar Selector

The `darwin-native-v1` selector contains exactly:

```text
role_id
acceptance_policy_id
machine_policy_id
machine_policy_sha256
observed_executable_sha256
platform_product_version
platform_build_version
platform_arch
```

It applies only to `CODESIGN_EXE`, `SPCTL_EXE`, and `OTOOL_EXE`. The selector
is the executable-version binding required by `L05`; the executable digest and
platform build replace any unbounded version-probe subprocess.

An `L05` grammar and a fixture may match only by byte-identical selector.
Path-only, role-only, signer-only, version-range, platform-range, wildcard,
default, closest-version, and unknown-version fallback are forbidden. Phase
787 defines selector inputs only. It creates no grammar, parser output,
acceptance operation ID, or fixture.

## Exact E83 Consumer Bindings

Binding scope is every executable token present in the executor-submitted argv
after sandbox-wrapper expansion, plus the exact nested fixture argv frozen by
Phase 732. Tool-internal descendants created by Cargo, Charon, Lake, or another
accepted command are bounded process-group behavior, not additional source-row
role references. Their environment, artifact, transcript, and acceptance
constraints remain `L11` work. Phase 787 does not claim a complete inventory of
all runtime descendant processes.

Role order is wrapper first, direct command executable second, then declared
fixture descendants in launch order. The exact bindings are:

| Ordinal | Operation ID | Ordered role IDs |
|---:|---|---|
| 007 | `compile-helper-sources` | `PYTHON3_EXE` |
| 008 | `run-helper-tests` | `PYTHON3_EXE` |
| 009 | `run-raw-parser-self-test` | `PYTHON3_EXE` |
| 010 | `fixture-normal-exit` | `PYTHON3_EXE`, `ECHO_EXE` |
| 011 | `fixture-process-timeout` | `PYTHON3_EXE`, `SH_EXE`, `SLEEP_EXE` |
| 012 | `fixture-stdout-limit` | `PYTHON3_EXE`, `YES_EXE` |
| 013 | `fixture-stderr-limit` | `PYTHON3_EXE`, `SH_EXE`, `YES_EXE` |
| 014 | `validate-process-fixtures` | `PYTHON3_EXE` |
| 015 | `download-rust-manifest` | `CURL_EXE` |
| 016 | `install-rust-toolchain` | `RUSTUP_EXE` |
| 017 | `capture-rust-components-before` | `RUSTUP_EXE` |
| 018 | `capture-rustup-version` | `RUSTUP_EXE` |
| 019 | `capture-rust-components-identity` | `RUSTUP_EXE` |
| 020 | `capture-rustc-identity` | `RUSTC_EXE` |
| 021 | `capture-cargo-identity` | `CARGO_EXE` |
| 022 | `capture-rust-components-after` | `RUSTUP_EXE` |
| 028 | `hash-charon-license-md-initial` | `SHASUM_EXE` |
| 029 | `hash-charon-readme-md-initial` | `SHASUM_EXE` |
| 030 | `hash-charon-cargo-toml-initial` | `SHASUM_EXE` |
| 031 | `hash-charon-cargo-lock-initial` | `SHASUM_EXE` |
| 032 | `hash-charon-rust-toolchain-initial` | `SHASUM_EXE` |
| 033 | `download-aeneas-main` | `CURL_EXE` |
| 034 | `download-aeneas-lean` | `CURL_EXE` |
| 035 | `validate-aeneas-archives` | `PYTHON3_EXE` |
| 036 | `extract-aeneas-main` | `TAR_EXE` |
| 037 | `extract-aeneas-lean-staging` | `TAR_EXE` |
| 038 | `capture-aeneas-file` | `FILE_EXE` |
| 039 | `lipo-packaged-aeneas` | `LIPO_EXE` |
| 040 | `lipo-packaged-charon` | `LIPO_EXE` |
| 041 | `lipo-packaged-charon-driver` | `LIPO_EXE` |
| 042 | `lipo-packaged-libgmp` | `LIPO_EXE` |
| 043 | `codesign-verify-packaged-aeneas` | `CODESIGN_EXE` |
| 044 | `codesign-verify-packaged-charon` | `CODESIGN_EXE` |
| 045 | `codesign-verify-packaged-charon-driver` | `CODESIGN_EXE` |
| 046 | `codesign-display-packaged-aeneas` | `CODESIGN_EXE` |
| 047 | `codesign-display-packaged-charon` | `CODESIGN_EXE` |
| 048 | `codesign-display-packaged-charon-driver` | `CODESIGN_EXE` |
| 049 | `spctl-packaged-aeneas` | `SPCTL_EXE` |
| 050 | `spctl-packaged-charon` | `SPCTL_EXE` |
| 051 | `spctl-packaged-charon-driver` | `SPCTL_EXE` |
| 052 | `otool-libraries-packaged-aeneas` | `OTOOL_EXE` |
| 053 | `otool-libraries-packaged-charon` | `OTOOL_EXE` |
| 054 | `otool-libraries-packaged-charon-driver` | `OTOOL_EXE` |
| 055 | `otool-libraries-packaged-libgmp` | `OTOOL_EXE` |
| 056 | `otool-load-commands-packaged-charon-driver` | `OTOOL_EXE` |
| 057 | `capture-aeneas-version` | `AENEAS_EXE` |
| 058 | `download-lean` | `CURL_EXE` |
| 061 | `capture-lean-version` | `LEAN_EXE` |
| 062 | `capture-lake-version` | `LAKE_EXE` |
| 063 | `capture-lean-prefix` | `LEAN_EXE` |
| 064 | `capture-leantar-file` | `FILE_EXE` |
| 065 | `compile-rustc-private-probe` | `RUSTC_EXE` |
| 066 | `fetch-charon-dependencies` | `CARGO_EXE` |
| 067 | `lake-update` | `LAKE_EXE` |
| 068 | `lake-cache-get` | `LAKE_EXE` |
| 069 | `resolve-hostname-before-closure` | `PYTHON3_EXE` |
| 070 | `sandbox-process-positive` | `SANDBOX_EXEC_EXE`, `TRUE_EXE` |
| 071 | `sandbox-hostname-negative` | `SANDBOX_EXEC_EXE`, `PYTHON3_EXE` |
| 072 | `sandbox-direct-ip-negative` | `SANDBOX_EXEC_EXE`, `NC_EXE` |
| 073 | `build-charon` | `SANDBOX_EXEC_EXE`, `CARGO_EXE` |
| 074 | `lipo-built-charon` | `SANDBOX_EXEC_EXE`, `LIPO_EXE` |
| 075 | `lipo-built-charon-driver` | `SANDBOX_EXEC_EXE`, `LIPO_EXE` |
| 076 | `codesign-verify-built-charon` | `SANDBOX_EXEC_EXE`, `CODESIGN_EXE` |
| 077 | `codesign-verify-built-charon-driver` | `SANDBOX_EXEC_EXE`, `CODESIGN_EXE` |
| 078 | `codesign-display-built-charon` | `SANDBOX_EXEC_EXE`, `CODESIGN_EXE` |
| 079 | `codesign-display-built-charon-driver` | `SANDBOX_EXEC_EXE`, `CODESIGN_EXE` |
| 080 | `otool-libraries-built-charon` | `SANDBOX_EXEC_EXE`, `OTOOL_EXE` |
| 081 | `otool-libraries-built-charon-driver` | `SANDBOX_EXEC_EXE`, `OTOOL_EXE` |
| 082 | `otool-load-commands-built-charon-driver` | `SANDBOX_EXEC_EXE`, `OTOOL_EXE` |
| 085 | `hash-charon-license-md-final` | `SANDBOX_EXEC_EXE`, `SHASUM_EXE` |
| 086 | `hash-charon-readme-md-final` | `SANDBOX_EXEC_EXE`, `SHASUM_EXE` |
| 087 | `hash-charon-cargo-toml-final` | `SANDBOX_EXEC_EXE`, `SHASUM_EXE` |
| 088 | `hash-charon-cargo-lock-final` | `SANDBOX_EXEC_EXE`, `SHASUM_EXE` |
| 089 | `hash-charon-rust-toolchain-final` | `SANDBOX_EXEC_EXE`, `SHASUM_EXE` |
| 090 | `capture-charon-version` | `SANDBOX_EXEC_EXE`, `CHARON_EXE` |
| 091 | `preflight-built-charon-driver-load` | `SANDBOX_EXEC_EXE`, `CHARON_DRIVER_EXE` |
| 092 | `extract-checker-llbc` | `SANDBOX_EXEC_EXE`, `CHARON_EXE` |
| 093 | `pretty-print-checker-llbc` | `SANDBOX_EXEC_EXE`, `CHARON_EXE` |
| 094 | `generate-aeneas-lean` | `SANDBOX_EXEC_EXE`, `AENEAS_EXE` |
| 095 | `check-types-olean` | `SANDBOX_EXEC_EXE`, `LAKE_EXE`, `LEAN_EXE` |
| 096 | `check-funs-olean` | `SANDBOX_EXEC_EXE`, `LAKE_EXE`, `LEAN_EXE` |
| 097 | `check-witness-olean` | `SANDBOX_EXEC_EXE`, `LAKE_EXE`, `LEAN_EXE` |
| 098 | `lake-build` | `SANDBOX_EXEC_EXE`, `LAKE_EXE` |

The exact Phase 787 design decisions for previously ambiguous direct roles are:

- `CURL_EXE` is fixed to `/usr/bin/curl`, while the non-system Git, zstd, and
  Rustup requested paths remain explicit machine-policy inputs;
- ordinals 009-014 and 035 use the accepted `PYTHON3_EXE` interpreter for the
  committed helper scripts;
- fixture child and grandchild binaries are explicit roles on 010-013;
- ordinals 017-019 and 022 use the same accepted `RUSTUP_EXE` as ordinal 016;
- ordinals 036 and 037 use `TAR_EXE` without a sandbox wrapper, consistent with
  the Phase 781 host-offline correction;
- ordinals 069 and 071 use the same `PYTHON3_EXE` and future byte-identical
  standard-library hostname-probe program, with only the sandbox prefix
  differing; and
- every sandbox row binds both `SANDBOX_EXEC_EXE` and its wrapped executable.

These choices resolve only executable-role membership and identity policy.
They do not resolve the remaining exact argv, environment, bounds, outcome,
artifact, acceptance-ID, or placeholder fields.

## Preserved Non-E83 Bindings

The successor registry preserves the already resolved 19-row complement with
the Phase 781 sandbox corrections applied:

```text
001-006  GIT_EXE
023-027  GIT_EXE
059      ZSTD_EXE
060      TAR_EXE
083-084  SANDBOX_EXEC_EXE, GIT_EXE
099-102  GIT_EXE
```

The `E83` set and this 19-row complement are disjoint and cover all 102 Phase
778 ordinary operations. Historical Phase 779 rows 059 and 060 still display
the old sandbox role; Phase 781 and this successor mapping remove it without
rewriting history.

## Closure Checks

Lane `L09` is closed only under all of these conditions:

- the registry has exactly 26 unique role IDs;
- the `E83` binding table has exactly 83 unique ordinal/operation pairs;
- the pairs exactly equal the Phase 780 `E83` set and Phase 778 names;
- every role reference resolves to one registry entry;
- every sandboxed `E83` row in 070-082 and 085-098 contains the wrapper first;
- no host role accepts an empty digest or owner allowlist;
- no owned role accepts a path outside its accepted producer root;
- native grammar selector inputs exist only on the three `N21` tool roles;
- no machine observation is embedded in the immutable registry; and
- no unresolved role is inferred from a row's capability or operation name.

Missing, extra, duplicate, reordered, unknown, ambiguous, fallback, or
policy-free bindings fail successor-ledger expansion.

## Phase 788 Gate

Phase 788 remains documentation-first. It may implement only Phase 786
prerequisite `P01`: the native transcript fixture-acquisition protocol and
readiness audit.

It must consume this registry's exact `darwin-native-v1` selector, identify
non-secret target sources for every required semantic shape, freeze exact
capture argv and process bounds, define raw-byte ownership and redaction,
define deterministic synthetic-negative derivations, and stop if any target,
tool identity, stream grammar input, or provenance field is unavailable.

Phase 788 may not resolve a host executable, create a machine-policy instance,
publish an observed executable digest, run native tools, capture transcripts,
create fixtures, close `L05`, modify Python or Rust source, create an attempt
root, publish a source-ledger digest, or run any helper, test, producer,
network, Rustup, Cargo, Charon, Aeneas, Lean, Lake, sandbox, SMT, Z3, COBALT,
or kernel command.

## State Preserved

```text
Phase 778 ordinary operation count     102
Phase 778 operation-order digest       490c30a8098214754d20e4025696e2e3c702df8d4f7114a611157653ea7a4464
historical Phase 779 blocker count     1469
historical Phase 779 blocked rows      102
historical Phase 779 source digest     absent
resolved Phase 780 lanes               L01-L04,L09
open Phase 780 lanes                   L05-L08,L10-L11
```

Phase 787 creates no concrete machine policy, identity observation, fixture,
transcript grammar, parser, acceptance operation ID, executable plan, executor
binding, machine-resolved attempt, source-ledger digest, or evidence record.

## Source Correspondence

| Contract fact | Controlling source |
|---|---|
| Exact 102-operation order and digest | Phase 778 operation-order correction |
| Exact `E83` and `N21` sets and `L09` exit gate | Phase 780 resolution matrix |
| Host identity record and safe symlink boundary | Phase 776 executable identity contract |
| Curl and Rustup role references | Phase 782 acquisition and installer contracts |
| Python helper argv | Phase 784 helper route correction |
| Native audit executable paths and cardinality | Phases 774 and 776 |
| Host-offline extraction and sandbox corrections | Phase 781 capability correction |
| Fixture descendant executable argv | Phase 732 fixture closure |
| Toolchain, Aeneas, Lean, Lake, and Charon paths | Phases 668 and 678 |
| Driver pre-use ordering | Phases 777 and 778 |
| Identity-before-fixture dependency route | Phase 786 route correction |

## Claim Boundary

Phase 787 is an immutable role and policy-schema contract. It is not a machine
policy instance, machine identity, executable digest observation, fixture
capture, fixture corpus, native transcript grammar, parser, transcript,
executable plan, executor binding, backend result, generated Lean, retained
kernel result, proof artifact, checker transcript, accepted evidence, Level2+,
score axis, semantic correctness, production readiness, SOTA, breakthrough,
full security, external audit, or action authority.

## Phase 788 Forward Result

Phase 788 subsequently freezes the documentation-first `P01` protocol in
`docs/788-phase-hsai-formal-native-transcript-fixture-acquisition-readiness-audit.md`.
Its readiness decision is `not-ready` because accepted native-tool identity
observations, retained target bytes, an ordinal-073 build receipt, raw corpus,
manifest, and named independent reviewers are absent. Phase 789 `P02` capture
is not authorized. No Phase 780 lane closes; resolved lanes remain
`L01-L04,L09`, open lanes remain `L05-L08,L10-L11`, and the historical Phase
779 blocker state and absent source-ledger digest remain unchanged.
