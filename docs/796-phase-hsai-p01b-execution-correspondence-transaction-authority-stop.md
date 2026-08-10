# Phase 796 HSAI P01B Execution Correspondence and Transaction Authority Stop

Status: complete documentation-only audit; `P01B` materialization remains
stopped.

State slice:
`phase-796-hsai-p01b-execution-correspondence-transaction-authority-stop`.

Classification:
`P01BExecutionCorrespondenceTransactionAuthorityNotReady`.

Execution status: `StoppedDocumentationOnly`.

Evidence ceiling: `Level1LocalReplayOrLower`.

## Verdict

Phase 796 does not satisfy the Phase 795 exit criteria. The repository can
derive the required operation families and their order, but it cannot construct
byte-complete executable contracts for them. Five independent blockers remain:

1. documented macOS interfaces do not provide the required verified-descriptor
   executable launch primitive;
2. the exact gzip/TAR header ledger and ordered member inventory for the pinned
   Aeneas archive were not retained and cannot be reconstructed from their
   aggregate digest;
3. the complete Cargo, Rustc, build-script, native-tool, linker, SDK, loader,
   and dynamic-library trust-root census has not been observed and accepted;
4. no concrete trusted-time or authenticated anti-rollback compare-and-swap
   authority has been provisioned; and
5. the exact per-operation argv, environment, input/output, timeout, stream,
   network, and accepted-outcome wires remain incomplete.

Consequently:

```text
preparation_contract_sha256 = absent
phase_797_authorized = false
materialization_authorized = false
capture_authorized = false
```

The conditional Phase 797 authorization in Phase 795 is not activated. No
static authorization validator or deterministic plan template may be
implemented from incomplete inputs.

## Audit Scope

This phase audits only whether the Phase 795 `P01B` transaction can be made
byte-complete without execution. It does not acquire source, inspect a live
machine, materialize an archive, compile Charon, reserve an attempt, mutate a
journal, or create an executable plan.

The audit reviewed:

- the Phase 778 fixed 102-operation order;
- the Phase 779 blocked source ledger;
- the Phase 780 blocker-resolution lanes;
- the Phase 787 executable-role and machine-policy contracts;
- the Phase 788 capture-prerequisite protocol;
- the Phase 789 route correction;
- the Phase 792 descriptor-relative collector;
- the Phase 793 source-receipt boundary;
- the Phase 794 hermetic preparation driver; and
- the Phase 795 external authorization and transaction boundary.

Resolved Phase 780 lanes remain `L01-L04,L09`. Open lanes remain
`L05-L08,L10-L11`. The historical Phase 779 ledger remains 102 blocked rows
with 1,469 blockers and no published source-ledger digest.

## Exact Inputs Already Available

The following values are stable inputs to a future closure attempt. They are
not enough to authorize one.

### Operation topology

Phase 795 fixes:

- seven bootstrap operations;
- 33 success-path runtime operations, global ordinals `008-040`;
- eight failure operations; and
- eight idempotent recovery operations.

The ordering, transaction states, root roles, and acceptance conjunction are
known. Their operation names do not define executable commands.

### Aeneas archive identity

The pinned main archive is:

```text
url = https://github.com/AeneasVerif/aeneas/releases/download/nightly-2026.07.10-c2015b8/aeneas-macos-aarch64.tar.gz
release_id = 351909376
asset_id = 472143319
tag_commit = c2015b8668ba6d5b41f5f19d00a881c12bbb0b5d
byte_length = 123234656
sha256 = fe706e847b01d83178e703898006bf372c5fcac007942b280efce776f5c35d45
release_immutable = false
```

The public [Aeneas release](https://github.com/AeneasVerif/aeneas/releases/tag/nightly-2026.07.10-c2015b8)
and [GitHub release API](https://api.github.com/repos/AeneasVerif/aeneas/releases/tags/nightly-2026.07.10-c2015b8)
provide release and asset metadata. They do not provide the archive's gzip
headers, TAR headers, or member ledger.

Phase 741 historically observed 2,471 logical members: 2,305 regular files and
166 directories. The top-level names were `aeneas`, `backends`, `charon`,
`charon-driver`, `libs`, and `rust-toolchain`. Its ordered logical-inventory
commitment was:

```text
26c0f52d30c7fd254ec76f3ee796a769c51eda9fbd72b0f9592e4b70d665539e
```

That SHA-256 commitment binds the historical compact JSON-LF rows, but cannot
reconstruct the rows.

### Charon source and intended build

The source commit is:

```text
909ff09ad0f144f83d354f2c3d26f631fb9f8e9a
```

The intended direct build is historically described as:

```text
cargo build --verbose --locked --offline --release \
  --manifest-path <pinned-charon-source>/Cargo.toml \
  --bin charon --bin charon-driver
```

with Rust channel `nightly-2026-06-01` under the Phase 776 deny-network sandbox.
This is an intended build family, not a complete accepted operation contract or
child-process census.

## Blocker Ledger

### P796-01 Verified-object launch unavailable

Required property: the executable object accepted by descriptor-relative
collection must be the same object the kernel launches, without a second
pathname lookup that can select a replacement object.

The Phase 792 collector retains descriptors during traversal and hashing but
returns an identity fact and closes those descriptors. The later launch surface
is not descriptor-bound.

The reviewed public macOS interfaces expose pathname-based `execve` and
`posix_spawn`. Apple's archived [`execve(2)` documentation](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/execve.2.html)
takes a pathname. The public [XNU syscall table](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/syscalls.master)
and [Libc `unistd.h`](https://github.com/apple-oss-distributions/Libc/blob/main/include/unistd.h)
do not expose a public `fexecve`- or `execveat`-style API. XNU's
[`kern_exec.c`](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/kern/kern_exec.c)
performs pathname lookup for execution.

This is evidence that the required mechanism is not available through the
reviewed documented interfaces. It is not a claim about private or undisclosed
kernel interfaces.

`/dev/fd/N`, `F_GETPATH`, directory-relative paths, `fork` plus `execve`, and a
suspended pathname spawn do not establish the required same-object property.

Closure requires one explicit architecture decision:

1. move the strict launch lane to a platform with an accepted descriptor-bound
   execution primitive and freeze that platform contract; or
2. weaken the macOS property to a precisely specified controlled-pathname
   launch only through a separately authorized contract-correction phase that
   explicitly supersedes the incompatible Phase 795 requirement, revises the
   threat model and claim ceiling, receives independent approval, and
   reschedules Phase 797 and every dependent successor.

Phase 796 does neither. The original strict property remains authoritative and
open. A controlled-pathname launch cannot close the current Phase 795 exit gate
or activate the current Phase 797 schedule.

### P796-02 Archive ledger bytes absent

Required artifacts:

1. `archive-source-manifest-v1`, binding release, tag, commit, asset, URL,
   filename, length, SHA-256, timestamps, and mutability;
2. `gzip-tar-header-ledger-v1`, binding every gzip member and physical 512-byte
   TAR header, extension payload, trailer, terminator, and trailing padding; and
3. `ordered-logical-member-inventory-v1`, binding contiguous logical order,
   physical-header references, effective names, collision keys, kinds, sizes,
   extension references, and regular-file content digests.

The accepted archive contract must also freeze finite values for compressed
bytes, uncompressed TAR bytes, physical headers, logical members, extension
payload bytes, per-member expanded bytes, aggregate regular-file expanded bytes,
and total extraction output bytes. Validation must reject every bound before
writing an extracted member. An inventory without these exact aggregate and
per-member limits is incomplete.

The current validator delegates gzip decoding and retains only selected TAR
fields. The repository retained aggregate counts and an inventory digest, not
the canonical 2,471 rows or complete raw headers. GitHub asset metadata cannot
fill those fields. The pinned upstream
[release workflow](https://github.com/AeneasVerif/aeneas/blob/c2015b8668ba6d5b41f5f19d00a881c12bbb0b5d/.github/workflows/release.yml#L145-L184)
also does not publish that ledger.

Closure requires a separately authorized acquisition-only pass that streams the
SHA-256-pinned archive bytes into the three canonical artifacts before any
extraction. The pass must retain the rows, reject digest or length mismatch,
write no extracted member, and receive independent review. Phase 796 performs
no acquisition.

### P796-03 Build-descendant trust census absent

Required process identities include, at minimum:

- pinned Cargo;
- every Rustc child, including build-script compilation;
- every generated `build-script-build` executable in the selected unit graph;
- native compiler and archiver children such as `cc`, `clang`, and `ar`;
- the selected Apple linker driver and actual linker;
- SDK-discovery children such as `xcrun`;
- the produced `charon` and `charon-driver`; and
- any wrapper selected by Cargo, Rustc, the linker, `CC`, or `AR` configuration.

Cargo documents that package [build scripts](https://doc.rust-lang.org/cargo/reference/build-scripts.html)
are compiled and executed. Its [environment-variable](https://doc.rust-lang.org/cargo/reference/environment-variables.html)
and [configuration](https://doc.rust-lang.org/cargo/reference/config.html)
surfaces can select compilers, wrappers, linkers, flags, and configuration
hierarchies. Therefore `Cargo.lock` and the top-level build argv do not define
the complete child set.

Required non-process trust roots include the Rust sysroot and rustc-private
libraries, dependency sources and proc-macro dylibs, generated native archives,
selected Xcode developer directory, SDK inputs, Clang resources, linker inputs,
Mach-O loader and library resolution, dyld shared-cache/OS identity, and a
closed replacement environment.

Closure requires an independently authorized offline discovery build against
the pinned source and toolchain. It must record the selected Cargo unit graph,
every descendant executable, every generated executable, actual linker and SDK
selection, and recursive produced-binary loader roots. A later accepted contract
must prohibit all unlisted descendants and wrappers. Phase 796 runs no build.

### P796-04 Transaction authority unprovisioned

Phase 795 defines the transaction invariants but not their concrete authority.
A local file, wall clock, or hash chain alone does not satisfy authenticated
trusted time or anti-rollback compare-and-swap across host rollback.

Closure requires a provisioned authority contract that fixes:

- authority and key identities;
- authenticated trusted-time response bytes and freshness rules;
- journal namespace and checkpoint storage identity;
- atomic compare-and-swap request, response, and conflict semantics;
- one-shot nonce reservation and terminal-consumption transitions;
- anti-rollback and recovery guarantees;
- transport and outage behavior;
- durable audit receipt bytes; and
- independent reviewer policy.

No such authority, endpoint, key, storage instance, or accepted transcript is
present. Phase 796 does not invent one in documentation.

### P796-05 Operation wires incomplete

The seven bootstrap, 33 runtime, eight failure, and eight recovery operations
have exact relative order. The following fields are not complete for every row:

- closed operation kind;
- executable role and child identity set;
- exact argv bytes;
- descriptor-relative cwd identity;
- ordered replacement environment;
- stdin policy;
- network state and transition;
- typed input and output artifact identities;
- timeout and termination policy;
- stdout and stderr retention/caps;
- accepted exit, signal, and semantic outcome; and
- cleanup and durability effect.

The Phase 788 `P02` capture defaults cannot be copied into `P01B`: they apply to
a different operation family and threat boundary. Closure requires a
field-complete canonical row for all 56 Phase 795 operations after blockers
`P796-01` through `P796-04` are resolved.

## Required Remediation Sequence

The Phase 796 documentation audit is complete, but the Phase 795 materialization
exit gate remains open. Remediation must occur through separately authorized
sub-slices, each preserving this stop until independently reviewed:

```text
796-A  acquire ledgers and freeze per-member plus aggregate extraction limits
796-B  decide and validate the verified-object launch architecture
796-C  perform the pinned offline build-child and loader trust-root census
796-D  provision trusted-time and anti-rollback transaction authority
796-E  freeze all 56 byte-complete operation rows and their aggregate digest
796-F  independently audit A-E and publish preparation_contract_sha256
```

The labels are remediation identifiers, not new completed phases. Their
sequence may not be collapsed by substituting documentation for observed bytes,
machine facts, or provisioned authority.

## Phase 797 Gate

Phase 797 remains blocked until all of the following are true:

- every blocker in this report is closed by retained evidence;
- all 56 operation rows are complete and canonically serialized;
- the exact archive artifacts are retained and independently reviewed;
- exact per-member and aggregate archive extraction limits are reviewed;
- the launch mechanism satisfies the strict Phase 795 same-object property;
- the build descendant and trust-root census is complete;
- the trusted-time and journal authorities are provisioned;
- the transaction and recovery operations are complete;
- an independent audit finds zero unresolved fields; and
- `preparation_contract_sha256` is published from those reviewed bytes.

Until then, Phase 797 may not add Rust or Cargo changes or construct a plan
template.

## Mutation and Execution Record

Phase 796 changes Markdown only. It performs no source acquisition, archive
read, extraction, build, process spawn, environment inspection, network action,
filesystem materialization, attempt reservation, journal mutation, trusted-time
request, target production, handoff creation, native transcript capture, fixture
acceptance, grammar closure, source-ledger publication, plan construction,
executor binding, or backend execution.

The pre-existing unrelated mutation under
`crates/hsai-agent-admission/src/lib.rs` is outside this state slice and is not
modified or staged by Phase 796.

## Claim Boundary

Phase 796 is a stopped documentation audit. It is not an archive safety result,
verified build, same-object launch proof, provisioned authorization authority,
accepted external authorization, replay journal, materialization plan, target,
handoff, native transcript corpus, Phase 780 lane closure, zero-blocker source
ledger, plan v2, executor, retention result, dry preflight, live-attempt
authorization, backend execution, Lean/SMT/Z3/COBALT run, proof artifact, checker
transcript, accepted evidence, Level2+ evidence, populated score axis, semantic
correctness, production readiness, SOTA, breakthrough, full security, external
audit, or action authority.

## Phase 796-A Forward Route

Phase 796-A records the documentation-first parser and acquisition-separation
boundary for blocker `P796-02`. It treats `796-A` as an umbrella workstream:
hermetic parser implementation and a two-reviewer audit must precede a
separately authorized acquisition-only run and candidate-ledger review. No
parser or acquisition runs in Phase 796-A, and no proposal accepts itself. A
later separately authorized local repository two-reviewer decision is required to
close `P796-02`; it remains Level 1 local evidence and does not close the live
anti-rollback blocker. The Phase 796 stop and every other blocker remain
unchanged; Phase 797 stays unauthorized. See
`docs/796a-phase-hsai-p01b-archive-ledger-parser-and-acquisition-separation-boundary.md`.
