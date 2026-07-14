# Phase 791 HSAI Native Transcript Descriptor-Relative Collector Boundary

## Status

Complete as a documentation-first safety and implementation boundary.

State slice:
`phase-791-hsai-native-transcript-descriptor-relative-collector-boundary`.

Classification: `DescriptorRelativeCollectorContractResolved`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Verdict

Phase 791 defines the only authorized Phase 792 path for collecting host
executable identity facts. It does not implement or run that collector.

Terminal `O_NOFOLLOW` is insufficient because an ancestor component can be
replaced between pathname checks. Phase 792 must traverse from an opened root
directory with retained directory descriptors, no-follow every component,
hash only through the accepted terminal descriptor, and recheck every retained
object before returning a fact.

No Phase 780 lane closes. `P01B` materialization remains stopped. Resolved
lanes remain `L01-L04,L09`; open lanes remain `L05-L08,L10-L11`. Historical
Phase 779 remains 102 blocked rows and 1,469 blockers without a source-ledger
digest.

## Authorized Phase 792 Surface

Phase 792 may change only:

```text
crates/hsai-native-transcript-preparation/Cargo.toml
crates/hsai-native-transcript-preparation/src/lib.rs
crates/hsai-native-transcript-preparation/src/collector.rs
crates/hsai-native-transcript-preparation/tests/descriptor_relative_collector.rs
Cargo.lock
docs/792-phase-hsai-native-transcript-descriptor-relative-collector-implementation.md
README.md
docs/12-task-list.md
docs/90-whole-codebase-validation-report.md
AGENTS.md
```

The implementation dependencies are exactly:

```toml
rustix = { version = "=1.1.4", features = ["fs"] }
libc = "=0.2.186"
```

Both versions are already present in `Cargo.lock`. `rustix 1.1.4` exposes
`openat`, `statat`, `readlinkat`, `fstat`, and `fstatfs` and declares Rust 1.63
compatibility. `libc 0.2.186` declares Rust 1.65 compatibility and is authorized
only for the macOS `MNT_LOCAL` constant. Phase 792 must also compile and test
with the installed `1.74.0-aarch64-apple-darwin` toolchain. No `libc` function
call or unsafe block is authorized.

Phase 792 is macOS-only. Other targets must return a typed
`UnsupportedPlatform` result and must not emulate weaker semantics.

## Input Contract

The collector accepts one already structurally valid Phase 790
`MachinePolicyCandidate`, one exact `HostExecutableRole`, and fixed limits:

```text
max_symlink_hops=32
max_executable_bytes=1073741824
hash_chunk_bytes=65536
```

The collector must recompute the machine-policy digest internally. It may not
accept a caller-supplied digest, observed owner, observed executable digest,
canonical path, symlink chain, metadata snapshot, platform tuple, or decision.

Before any file open it rejects:

- a policy that fails Phase 790 structural validation;
- a missing or duplicate role entry;
- empty, relative, non-normalized, NUL-bearing, dot, dot-dot, repeated-root,
  or trailing-slash requested paths;
- empty, non-normalized, or pairwise-overlapping allowed roots;
- a requested path not contained by exactly one allowed root; and
- any unsupported or unclassifiable nonlocal filesystem.

Overlapping roots are rejected rather than resolved by first-match or
longest-prefix behavior. Phase 792 may tighten the Phase 790 pure-data
validator to enforce this rule.

## Descriptor-Relative Algorithm

Phase 792 must implement this order without pathname fallback:

1. Open `/` read-only as a directory with close-on-exec and no-follow flags.
   Apply `rustix::fs::fstatfs` and require `f_flags & libc::MNT_LOCAL != 0`.
2. Walk the selected allowed-root components from that descriptor. For every
   component, use no-follow metadata, open it as a no-follow directory, compare
   descriptor metadata with the preceding directory-entry metadata, and retain
   both the parent and opened descriptor.
3. Walk the requested path relative to the retained allowed-root descriptor.
   Every nonterminal directory receives the same metadata/open/compare and
   retention treatment.
4. Inspect each possible symlink with no-follow entry metadata and
   `readlinkat`. Record the containing directory, link path, raw UTF-8 link
   text, and normalized resolved path. Resolve relative link text only against
   its containing directory. Absolute links restart from the retained `/`
   descriptor but must remain inside the same selected allowed root.
5. Track complete resolution states and reject a repeated state as a cycle.
   Accept at most 32 followed links; reject the 33rd.
6. Open the terminal with read-only, no-follow, nonblocking, no-controlling-TTY,
   and close-on-exec flags. Compare terminal entry and descriptor device/inode.
   Reapply the same `MNT_LOCAL` test to the selected allowed-root and terminal
   descriptors.
7. Require a regular nonempty file no larger than 1 GiB. Reject setuid, setgid,
   sticky, group-write, other-write, and no-execute modes. Require the numeric
   owner in the exact policy allowlist.
8. Record pre-read descriptor metadata. Hash exactly the recorded byte length
   in 64 KiB chunks, reject early EOF, and probe one additional byte to reject
   growth.
9. Record post-read descriptor metadata and require equality for device, inode,
   mode, owner, link count, length, modification time, and change time. Access
   time is excluded.
10. Re-read every recorded symlink through its retained containing-directory
    descriptor. Recheck every retained directory entry and terminal entry
    against its original object identity and metadata.
11. Require the computed SHA-256 in the policy entry's admitted sorted set.
12. Return one generated local fact with `decision=accepted`. Any failed step
    returns one typed error and no accepted fact.

The resolved path is a normalized path label. Device and inode identify the
observed object; Phase 792 must not claim path uniqueness because hard links
and filesystem aliases can exist.

## Stable Metadata

The Phase 792 fact must extend the Phase 790 metadata declaration with:

```text
device
inode
mode
owner_uid
link_count
byte_length
modified_seconds
modified_nanoseconds
changed_seconds
changed_nanoseconds
```

Negative timestamps are represented without lossy unsigned conversion. The
pre/post comparison is exact over this field set.

## Failure Taxonomy

Phase 792 must expose a closed non-authoritative error enum covering:

```text
UnsupportedPlatform
UnsupportedFilesystem
InvalidPolicy
MissingRole
InvalidRequestedPath
InvalidAllowedRoot
OverlappingAllowedRoots
OutsideAllowedRoot
Io
NotDirectory
NotSymlink
NonUtf8Symlink
SymlinkCycle
TooManySymlinkHops
RootEscape
EntryIdentityDrift
NotRegularFile
EmptyFile
FileTooLarge
UnsafeMode
OwnerRejected
EarlyEof
ContentGrowth
MetadataDrift
SymlinkDrift
DirectoryDrift
DigestRejected
```

OS error text is diagnostic only. Tests and future callers match typed classes,
not localized strings or raw errno values.

## Deterministic Adversarial Tests

Phase 792 must add private test-only checkpoints after entry metadata, after
directory open, after symlink read, after terminal open, during hashing, after
post-read metadata, and before final recheck. Tests coordinate mutations with
barriers or channels; sleeps and probabilistic races are forbidden.

The required test matrix includes:

- direct regular-file acceptance for a declared-path role and fixed-path role
  mismatch rejection;
- relative and absolute terminal and ancestor symlinks;
- exactly 32 links, 33 links, direct cycles, indirect cycles, and repeated
  finite resolution states;
- relative, dot, dot-dot, NUL, trailing-slash, root-escape, and overlapping-root
  rejection;
- directory, FIFO, socket, device, empty, oversized, no-execute, privileged,
  group-writable, other-writable, and owner-rejected terminals;
- ancestor replacement after entry metadata and after directory open;
- symlink-text replacement, terminal rename/replacement, unlink while open,
  truncation, growth, mode/owner drift, and modification/change-time drift;
- admitted and rejected digest sets;
- exact fact-to-policy digest and platform binding;
- source scan proving no process, network, environment, shell, helper, or
  pathname-canonicalization API; and
- `cargo +1.74.0 test -p hsai-native-transcript-preparation`.

Filesystem-specific tests may skip only with a typed unsupported-filesystem
result and an explicit test reason. They may not silently weaken assertions.

## Non-Authority Boundary

Even a successful Phase 792 fact is a local observation-window record. It does
not authenticate the policy reviewer, make the file immutable, authorize a
later launch, or substitute for immediate pre-use and post-use campaign
identity rechecks. Phase 795 must recollect and bind any fact it consumes.

Phase 791 and Phase 792 do not authorize network access, archive acquisition,
Rustup, Cargo, Git, extraction, compilation, target copying, root
materialization, native transcript capture, `codesign`, `spctl`, `otool`, Lean,
Lake, SMT, Z3, COBALT, a proof backend, or a kernel checker.

## Claim Boundary

Phase 791 is a collector design boundary. It is not collector execution, a
machine observation, an authenticated policy, target materialization, build
acceptance, reviewer approval, a handoff, native transcript capture, fixture
authority, a grammar, plan v2, executor binding, backend execution, a proof
artifact, checker transcript, accepted evidence, Level2+, a score axis,
semantic correctness, production readiness, SOTA, breakthrough, full security,
external audit, or action authority.
