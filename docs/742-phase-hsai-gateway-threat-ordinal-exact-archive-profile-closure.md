# Phase 742 HSAI Gateway Threat Ordinal Exact Archive Profile Closure

## Status

Complete as a documentation-first exact archive-profile correction.

State slice:
`phase-742-hsai-gateway-threat-ordinal-exact-archive-profile-closure`.

Classification: `ExactPinnedArchiveProfilesSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Canonical Phase 743 Profiles

Phase 743 uses canonical run root `hsai-phase743-efa3782c`, canonical detached
repository root `hsai-phase743-repo-efa3782c`, and witness
`phase743ExtractedThreatOrdinalWitnesses`.

The exact accepted pre-extraction profile assertions are now:

```text
main.logical_members = 2471
main.root_count = 0
main.regular_members = 2305
main.directory_members = 166
main.top_level = [aeneas, backends, charon, charon-driver, libs, rust-toolchain]
main.inventory_sha256 = 26c0f52d30c7fd254ec76f3ee796a769c51eda9fbd72b0f9592e4b70d665539e

lean.logical_members = 2125
lean.root_count = 1
lean.regular_members = 2021
lean.directory_members = 104
lean.top_level = [ir, lib]
lean.inventory_sha256 = 8242938ad079bf2ee9359b29f8c7a257c88b27d4efac8d67ba167b6730999ff4
```

The main profile adds the previously omitted `rust-toolchain` top-level regular
file. Every Phase 738 raw-name, direct-type, path, duplicate, ancestor,
self-test, stable-descriptor, embedded-asset, summary, and error rule remains.
Profile equality is required only after all structural safety checks pass.

The real validator acceptance command must be the only command in its top-level
shell. It must propagate nonzero directly. Only a later top-level command may
write a checkpoint or transcript hash after acceptance exits zero. Phase 739's
masked checkpoint pattern is prohibited.

After commit and detached-worktree gates, Phase 743 may make one full attempt.
The Phase 732 exact fixtures and loopback controls, Phase 726 separate
materialization producers, Phase 728 exact identity transcripts, Phase 724 rfl
witness, Phase 720 direct `.olean` sequence, and every inherited acquisition,
version, token, client, scanner, component, source, cache, sandbox, cleanup,
evidence, and claim rule remain.

Phase 742 runs no tool or backend and creates no proof, accepted evidence,
Level2+, score axis, semantic correctness, production readiness, SOTA,
breakthrough, or full-security claim.
