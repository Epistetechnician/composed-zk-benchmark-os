# Phase 741 HSAI Gateway Threat Ordinal Archive Profile Discovery Report

## Status

Complete as one cleaned acquisition-only raw archive-profile discovery run.

State slice:
`phase-741-hsai-gateway-threat-ordinal-archive-profile-discovery`.

Classification: `RawArchiveProfileDiscoveredNotAccepted`.

Execution status: `Succeeded` for parser self-tests, both asset acquisitions,
and raw profile discovery; `NotRun` for archive extraction, Rust, Charon, Lean,
Cargo, Lake, sandbox attribution, backend extraction, and kernel checking.
Evidence ceiling: `Level1LocalReplayOrLower`.

## Observed Profile

The bounded raw-aware parser self-test exited zero with empty stderr. Both
Aeneas assets matched their exact size and SHA-256 pins. The bounded discovery
producer then exited zero with empty stderr, validated raw names, direct member
types, counts, roots, aliases, duplicates, ancestors, stable file descriptors,
and embedded Lean-build byte equality, while intentionally omitting top-level
profile acceptance.

Observed main archive:

```text
logical_members = 2471
root_count = 0
regular_members = 2305
directory_members = 166
top_level = [aeneas, backends, charon, charon-driver, libs, rust-toolchain]
inventory_sha256 = 26c0f52d30c7fd254ec76f3ee796a769c51eda9fbd72b0f9592e4b70d665539e
```

Observed Lean-build archive:

```text
logical_members = 2125
root_count = 1
regular_members = 2021
directory_members = 104
top_level = [ir, lib]
inventory_sha256 = 8242938ad079bf2ee9359b29f8c7a257c88b27d4efac8d67ba167b6730999ff4
```

The embedded Lean-build asset was byte-identical to the separate 50,447,755
byte asset with SHA-256
`f1771437f16e5e34135719ff467b32ecda101cc215dc411741cd098732916f59`.
The discovery helper SHA-256 was
`1ed1388e6b8836b9d1330926c2ab8632748f3ac9c5765e4527f0a463923243fb`.

## Transcript Digests

```text
discovery.status.json = 5f044c4e19f1d291ce501a8ad554f2152181b106516b0552e8612e1ac00ec446
discovery.stdout = 390043ed937b0b0eb9a0f558a2aed3602fb79aa7a93fac9b8d4ab4b250072b92
discovery.stderr = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
selftest.status.json = 9de6dadd4fdd76e012fa90b9561828fd2009d0d1c7162c8a7acabe66f39c51bf
selftest.stdout = 4b9ffe5cd09e3b2368e7ae5e99bbabd2819f5893701336be09391503e216a73a
selftest.stderr = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

## Cleanup and Claims

The mode-0700 run root and both downloaded assets were removed. No persistent
tool root, detached execution worktree, archive extraction, or generated source
was created. Repository state remained clean.

Phase 741 discovers but does not accept the observed profile. It creates no
materialized external tool, backend result, kernel result, proof artifact,
accepted evidence, Level2+, score axis, semantic correctness, production
readiness, SOTA, breakthrough, or full-security claim.
