# Phase O Local Reproducible-Pack Readiness Spec

## Status And Claim Boundary

Phase O-B implements the inert local reproducible-pack readiness contract.

This phase corrects the Phase O target and adds local readiness metadata: the
current repository may define and validate local reproducible-pack readiness,
but it must not create Level2+ evidence, official benchmark evidence, external
replay evidence, ZK backend performance claims, or broad leaderboard claims.

The current authorized state slice is:

```text
crates/zkbench-core/src/pack/readiness.rs
crates/zkbench-core/src/pack/mod.rs
crates/zkbench-core/src/lib.rs
crates/zkbench-core/src/prelude.rs
crates/zkbench-core/tests/phase_o_pack_readiness.rs
docs/65-phase-o-local-reproducible-pack-readiness-spec.md
docs/12-task-list.md
README.md
AGENTS.md
```

All Phase O-B readiness artifacts remain `Level0DesignNote`. Existing local benchmark
packs remain local pack artifacts at `Level1LocalReplay` or lower. A local
pack-readiness statement is not Level2 evidence.

## Purpose

Phase O should make local packs easier to reproduce and audit without
overclaiming. The useful question is:

```text
Can a local benchmark pack prove that its own local artifacts are complete,
portable, digest-covered, replay-described, and claim-capped?
```

The answer is a local readiness statement only. It does not prove that another
backend replayed the pack, does not prove semantic soundness, and does not make
the pack official benchmark evidence.

## Local Readiness Contract

The local pack-readiness implementation may inspect:

- `BenchmarkPackManifest`;
- pack file entries and SHA-256 artifact digests;
- local replay manifests;
- local replay results;
- local evidence ledgers;
- local `ScoreReport` artifacts;
- local soak report bundles;
- failure corpus and reproduction bundle metadata;
- explicit `ClaimBoundary` labels.

The readiness contract requires:

- every pack file has a stable relative path;
- every pack file has a SHA-256 digest;
- manifest summary counts match referenced artifacts;
- replay manifests and replay results round-trip deterministically;
- evidence ledger digest chains validate;
- score reports validate and keep local score axes unpopulated when claim
  boundaries are local;
- replay command metadata is inert/non-shell data;
- sampled pack validation is reproducible from the committed local code;
- all output claims remain at or below the weakest local input boundary.

## Replay Command Metadata

Phase O describes replay commands as inert metadata only. A replay command
record may name an intended local verification action, expected input artifact,
and expected output artifact, but it must not contain shell payloads, absolute
paths, environment secrets, network endpoints, or external backend invocation.

Replay command metadata is not execution evidence.

## Future Promotion Preconditions

True Level2 promotion requires a separate reviewed phase. Before any future
agent may claim Level2 reproducible benchmark artifacts, the repo must define:

- explicit external replay authority;
- artifact capture contract for independently reproduced outputs;
- provenance requirements for the replay environment;
- result import and quarantine rules;
- manual review policy for claim-boundary elevation;
- rule separating local oracle output from external backend output;
- rule separating Score Report rendering from accepted Evidence Record
  mutation;
- validation proving no official, formal, or performance claim text enters
  accepted evidence without review.

Until those preconditions exist, Phase O must stop at local readiness.

## Required Negative Tests

The Phase O tests reject:

- pack-readiness output claiming Level2 evidence;
- local replay treated as official benchmark evidence;
- local soak telemetry treated as ZK backend performance;
- replay command metadata containing shell payloads or absolute paths;
- missing digest coverage for referenced pack files;
- stale manifest summary counts;
- digest-consistent but invalid score reports;
- append previews treated as accepted evidence;
- Level2 eligibility reports treated as Level2 evidence;
- external replay results imported without provenance and quarantine review.

## Non-Goals

- No external replay.
- No live zk-Harness, gnark, zkML, clean, zkLean, or Garden execution.
- No official benchmark evidence.
- No Level2+ evidence creation.
- No ZK backend performance claims.
- No broad leaderboard claim.
- No accepted Evidence Ledger mutation from readiness metadata.
- No dashboard work.

## Implemented Slice

The implemented Phase O-B slice is inert readiness metadata only:

```text
local pack-readiness target
PackReadinessReport data model
PackReadinessInputRef data model
PackReadinessReplayCommandMetadata data model
PackReadinessCheck data model
pack-readiness report digest helper
JSON serialization helpers
local readiness contract
inert replay-command metadata rules
future Level2 promotion preconditions
required negative tests
non-goals
claim-boundary restrictions
```

This slice does not create pack outputs, benchmark results, or Level2 evidence.
