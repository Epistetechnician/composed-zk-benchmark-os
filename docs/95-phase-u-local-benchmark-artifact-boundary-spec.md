# Phase U Local Benchmark Artifact Boundary Spec

Status: docs-first boundary only.

Phase U defines the next benchmark OS boundary before any generated local
benchmark artifacts are created. It does not authorize Rust implementation
code, generated artifact files, command-line tools, UI dashboards, package
runtime files, external replay, live backend execution, official benchmark
submission, accepted Evidence Ledger mutation, ZK backend performance claims,
score-axis population from local-only evidence, Level2+ promotion, or treating
local generated artifacts as official benchmark evidence.

## State Slice

This phase is limited to Markdown specification and navigation updates under:

- `docs/95-phase-u-local-benchmark-artifact-boundary-spec.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`
- `docs/90-whole-codebase-validation-report.md`

No crate, test fixture, generated benchmark artifact, benchmark pack, readiness
output, report bundle, audit-index output, ergonomics output, cross-bundle
output, local replay result, Evidence Record, Score Report, accepted Evidence
Ledger, package runtime file, command-line surface, or UI artifact is changed
by this docs-first phase.

## Purpose

The current codebase can generate local packs, local readiness metadata, report
bundles, audit indexes, ergonomics views, and cross-bundle views. The remaining
gap is not a lack of individual local metadata surfaces. The gap is the absence
of a named local artifact boundary that says which existing local outputs may
be assembled into a generated benchmark artifact bundle, which files must be
digest-covered, and which claims must remain blocked.

Phase U is that boundary. It prepares a future implementation that may create a
portable local benchmark artifact bundle from already-valid local inputs while
preserving the existing claim ceiling.

The future bundle is a local reproducibility artifact only. It is not official
benchmark evidence, not accepted evidence, not ZK backend performance evidence,
not Level2+ evidence, not a leaderboard submission, and not proof.

## Authorized Future Inputs

A future implementation may accept only already-valid local inputs:

- one or more valid `BenchmarkPackManifest` values and their digest-covered
  local pack files;
- optional valid `PackReadinessReport` and `PackReadinessValidation` values;
- optional valid local report-bundle metadata;
- optional valid local audit-index metadata;
- optional valid Phase S audit-index ergonomics metadata;
- optional valid Phase T cross-bundle audit-index metadata;
- local replay manifests, local replay results, local evidence ledgers, and
  local score reports only when they are already referenced by a valid local
  pack;
- caller-supplied logical source ids and protected source paths;
- a caller-selected output root outside all protected paths;
- an explicit overwrite policy.

Every supplied input must be validated before it contributes to the future
artifact bundle. Invalid inputs must fail closed or be explicitly excluded with
a local warning. Exclusion is never evidence improvement.

## Forbidden Future Inputs

A future implementation must not consume:

- live backend output;
- external replay output;
- official benchmark submissions;
- accepted Evidence Ledger entries as mutable targets;
- network resources;
- credentials or secrets;
- shell commands or executable replay steps;
- undeclared filesystem paths discovered by scanning;
- package runtime files;
- source repositories cloned during artifact generation.

## Authorized Future Output Shape

A future implementation may define a declared-file-only artifact root such as
`local-benchmark-artifact/`. The exact implementation phase must name concrete
paths, but the output contract must include:

- one canonical artifact manifest JSON file;
- one deterministic rendered Markdown summary;
- digest sidecars for every materialized payload;
- a source-input digest summary;
- a claim-boundary summary capped at the weakest supplied local input;
- a limitations section containing the required labels from this spec;
- explicit references to any included local pack, readiness, report-bundle,
  audit-index, ergonomics, or cross-bundle payloads;
- a machine-checkable statement that no accepted Evidence Ledger was mutated.

The future output files must remain outside source packs, source reports,
report bundles, audit-index outputs, Phase S ergonomics outputs, Phase T
cross-bundle outputs, score reports, accepted Evidence Ledgers, and package
runtime trees.

## Protected Path Policy

A future implementation must treat all supplied source paths as protected:

- source pack locations;
- local replay artifact locations;
- local evidence ledger locations;
- score report locations;
- pack-readiness output locations;
- report-bundle locations;
- audit-index output locations;
- Phase S ergonomics output locations;
- Phase T cross-bundle output locations;
- accepted Evidence Ledger locations;
- existing local benchmark artifact roots.

The output root must be rejected when it is equal to, nested under, or a parent
of any protected path. Relative and absolute representations of the same
location must overlap. Path checks must use structured normalization where
available, not string-prefix checks alone.

## Output Root Policy

A future implementation must reject:

- empty output-root declarations;
- output roots that are existing files;
- output roots containing unexpected files;
- output roots containing symlinks;
- output roots with parent-directory components;
- output roots with URL-like content or shell-like fragments;
- output roots that overlap protected source or evidence paths;
- overwrite attempts unless the caller explicitly permits overwrite;
- overwrite attempts where existing bytes do not match the supplied contract.

Corrupted output roots are not repair inputs. Explicit overwrite may replace
only declared local benchmark artifact files after validation proves the
existing root is a complete, digest-consistent bundle for the same contract.
Partial, unexpected, symlinked, stale-digest, or drifted roots must be
rejected.

## Required Limitation Labels

Every future materialized local benchmark artifact must visibly include:

- Local benchmark artifacts are not official benchmark evidence.
- Local benchmark artifacts are not accepted Evidence Ledger entries.
- Local benchmark artifacts do not create Level2+ evidence.
- Local benchmark artifacts do not prove ZK backend performance.
- Local benchmark artifacts do not prove semantic correctness.
- Local replay artifacts are not official benchmark evidence.
- Internal timing telemetry is not ZK backend performance.
- Score axes remain unpopulated for local-only evidence.
- Acceptance requires a separate reviewed promotion phase.

## Required Future Validation

A future implementation phase must include hermetic tests for:

- invalid local pack rejection;
- missing digest sidecar rejection;
- stale manifest summary rejection;
- stale source-input digest rejection;
- invalid readiness/report-bundle/audit-index/cross-bundle input rejection;
- claim-boundary ceiling preservation across mixed local inputs;
- required limitation-label preservation in JSON and Markdown outputs;
- score-axis non-population from local-only evidence;
- accepted Evidence Ledger non-mutation;
- protected-path overlap rejection across every protected input class;
- relative and absolute protected-path overlap equivalence;
- output-root parent/child overlap rejection;
- non-overwrite rejection;
- explicit overwrite that is not a repair path;
- partial-bundle rejection;
- unexpected-file rejection;
- stale-digest rejection;
- rendered Markdown drift rejection;
- symlink rejection;
- source immutability;
- source scan proving no process, network, package runtime, CLI, or UI hooks
  were added.

## Promotion Boundary

Phase U does not promote any artifact to Level2 evidence. A later reviewed
promotion phase would still need, at minimum:

- external replay authority;
- independently reproduced output capture;
- replay environment provenance;
- result import and quarantine handling;
- manual review approval;
- an explicit accepted-evidence mutation policy;
- rule separation between local oracle output and external backend output;
- rule separation between rendered reports and accepted Evidence Records;
- validation proving no official, formal, soundness, or performance claim text
  enters accepted evidence without review.

Until those preconditions are implemented in a separate reviewed phase, local
benchmark artifacts remain local reproducibility packaging only.

## Non-Goals

This docs-first phase does not permit:

- Rust source or test changes;
- generated benchmark artifact files;
- command-line tools;
- browser or UI dashboard work;
- JavaScript, TypeScript, package scripts, lockfiles, or node dependencies;
- source pack mutation;
- source report mutation;
- report-bundle mutation;
- audit-index output mutation;
- Phase S ergonomics output mutation;
- Phase T cross-bundle output mutation;
- accepted Evidence Ledger mutation;
- replay-command execution;
- external replay;
- live backend execution;
- external repo clones;
- vendored source;
- external result import;
- official benchmark evidence;
- ZK backend performance claims;
- score-axis population from local-only evidence;
- Level2+ evidence creation;
- broad leaderboard claims.
