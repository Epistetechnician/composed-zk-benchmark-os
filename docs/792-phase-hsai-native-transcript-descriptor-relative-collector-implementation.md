# Phase 792 HSAI Native Transcript Descriptor-Relative Collector Implementation

## Status

Complete for the bounded local collector implementation.

State slice:
`phase-792-hsai-native-transcript-descriptor-relative-collector`.

Classification: `DescriptorRelativeCollectorImplementedLocalValidationOnly`.

Execution status: `LocalValidationOnly`. Evidence ceiling:
`Level1LocalReplayOrLower`.

## Verdict

Phase 792 implements the macOS-only descriptor-relative collector authorized by
Phase 791. A successful call creates one local observation-window
`ExecutableIdentityFact` for one accepted machine-policy role. It does not
materialize a preparation root, authorize capture, or create evidence.

`P01B` remains stopped. No Phase 780 lane closes. Resolved lanes remain
`L01-L04,L09`; open lanes remain `L05-L08,L10-L11`. Historical Phase 779
remains 102 blocked rows and 1,469 blockers without a source-ledger digest.

## Implemented Surface

The `hsai-native-transcript-preparation` crate now provides:

```rust
pub fn collect_executable_identity_fact(
    policy: &MachinePolicyCandidate,
    role: HostExecutableRole,
) -> Result<ExecutableIdentityFact, CollectorError>;
```

The implementation:

- fails with `UnsupportedPlatform` outside macOS;
- validates exactly one role, one normalized non-overlapping allowed root, the
  reviewed policy shape, and the compiled macOS architecture before opening;
- opens `/` and the selected root with retained read-only no-follow directory
  descriptors and requires macOS `MNT_LOCAL` classification;
- uses `statat`, `openat`, `readlinkat`, `fstat`, and `fstatfs` from locked
  `rustix 1.1.4`, with `libc 0.2.186` used only for `MNT_LOCAL`;
- resolves relative and absolute symlinks only inside the selected root, records
  their containing directory and exact UTF-8 text, rejects repeated resolution
  states, and accepts at most 32 hops;
- opens the terminal read-only, no-follow, nonblocking, no-controlling-TTY, and
  close-on-exec, then requires the entry and descriptor to identify the same
  regular file;
- rejects empty, over-1-GiB, non-executable, privileged, group-writable,
  other-writable, and owner-disallowed files;
- hashes the exact pre-read length through the terminal descriptor in 64-KiB
  chunks, rejects early EOF and growth, and compares complete pre/post stable
  metadata; and
- rechecks every retained directory entry, symlink, and terminal entry before
  returning a policy-, entry-, registry-, platform-, and decision-bound fact.

The fact schema now carries registry id, machine-policy id and digest,
domain-separated policy-entry digest, acceptance-policy id, accepted decision,
link count, and signed modification/change timestamps. Policy product/build
versions are labeled `declared_platform`; only compile-time macOS and
architecture are labeled `observed_platform`. Its resolved path is a label for
the observed device/inode object, not a path-uniqueness claim.

Because these are required wire-shape changes, the preparation candidate,
executable fact, candidate digest domain, and state-slice identity advance to
v2/Phase 792. Explicit v1 constants remain exported only to identify the
superseded Phase 790 wire contract; v1 bytes are not silently accepted as v2.

No unsafe block or libc function call exists. The collector has no process,
environment-variable, network, shell, helper, or pathname-canonicalization
path.

## Deterministic Adversarial Validation

Private checkpoints cover entry metadata, directory open, symlink read,
terminal open, hashing, post-read metadata, and final recheck. Tests use scoped
threads with zero-capacity trigger and acknowledgement channels rather than
sleeps or probabilistic races.

The focused suite covers:

- direct declared-path acceptance and exact policy/fact correspondence;
- relative, absolute, terminal, and ancestor symlinks;
- 32-hop acceptance, 33-hop rejection, direct and indirect cycles, repeated
  resolution-state rejection, root escape, and non-UTF-8 symlink rejection;
- relative, dot-dot, NUL, trailing-slash, invalid-root, overlapping-root,
  outside-root, missing-role, and fixed-role drift rejection;
- directory, socket, device, empty, oversized, unsafe-mode, owner, and digest
  rejection, including a real FIFO created by the exact test-only
  `/usr/bin/mkfifo` exception and synthetic privileged-mode classification;
- deterministic ancestor replacement after metadata and directory open;
- deterministic symlink-text replacement, terminal replacement, unlink,
  truncation, growth, and mode/metadata drift; and
- production-source scans for forbidden process, network, environment, shell,
  canonicalization, unsafe, and libc-call surfaces.

Validated commands:

```text
cargo test -p hsai-native-transcript-preparation
cargo clippy -p hsai-native-transcript-preparation --all-targets -- -D warnings
cargo +1.74.0 test -p hsai-native-transcript-preparation --locked
```

All passed. The focused crate result is 28 tests: 11 private collector and
mutation tests, 9 public collector tests, and 8 preparation-candidate tests.

## Next Boundary

Phase 793 is documentation-first for the operator preparation driver and source
receipt boundary. It must define how externally reviewed policy and source
objects are authenticated, how collector facts are immediately recollected,
and how any future materializer consumes them without converting a stale local
observation into launch authority.

Conditional Phase 794 may implement only the resulting hermetic driver.
Conditional Phase 795 remains the earliest `P01B` materialization phase. Phase
796 remains the earliest native transcript capture phase. Phase 806 remains the
earliest plan-v2 boundary.

## Claim Boundary

Phase 792 is a local descriptor-relative collector implementation and test
result. It is not an authenticated machine policy, immutable executable
identity, preparation handoff, target materialization, build acceptance,
reviewer approval, native transcript capture, fixture authority, grammar,
source-ledger digest, plan v2, executor binding, backend execution, Lean/SMT/Z3
or COBALT run, proof artifact, checker transcript, accepted evidence, Level2+,
score axis, semantic correctness, production readiness, SOTA, breakthrough,
full security, external audit, or action authority.
