# Phase 623 PCSM Clean-Source Operator Replay Boundary

State slice: `phase-623-pcsm-clean-source-operator-replay-boundary`.

## Purpose

Define the docs-first boundary for a future quarantined local packet returned
by an external operator after replaying the clean recoverable-ghost-states
PCSM source coordinate outside this repository.

The source coordinate remains:

```text
repo=recoverable-ghost-states
commit=8b342fe159324395174a149052b9ea1d937a50ce
path=docs/pcsm-cl12-bounded-proof-handoff.md
sha256=93e07a250c9a6a5f530d02f07095074e7df8a5b5ce7e8e2dfa6e5feb376ea149
state_slice=pcsm-cl12-bounded-proof-package
schema=pcsm-cl12-bounded-proof-handoff-v1
```

The current local chain is:

```text
Phase 616 clean-source reconciliation boundary
  -> Phase 617 local reconciliation
  -> Phase 618 materialization boundary
  -> Phase 619 local materialized bundle/readback
  -> Phase 620 audit boundary
  -> Phase 621 local audit summary
  -> Phase 622 local closure report
```

Phase 623 does not execute the source repository. It only defines the future
shape of a quarantined operator replay packet that HSAI may later validate
locally. That packet may describe what an operator did in
recoverable-ghost-states, but it may not become accepted evidence or a PCSM
semantic claim by itself.

## Future Packet Namespace

A future implementation may validate a local returned packet under this
namespace:

```text
phase623-pcsm-clean-source-operator-replay/
  manifest.json
  phase622-closure-report-binding.json
  clean-source-coordinate.json
  operator-provenance.json
  source-repository-observation.json
  replay-command-observation.json
  transcript-digests.json
  artifact-retention-declaration.json
  redaction-report.json
  nonpromotion-report.json
  digests.json
```

Those files would be quarantined local metadata only. They would not be PCSM
runtime import, recoverable-ghost artifact import, accepted evidence, accepted
independent external reproduction, Level2+ evidence, score-axis evidence,
proof, checker transcript authority, solver certificate authority, benchmark
evidence, production evidence, external-audit evidence, or action authority.

## Authorized Future Implementation

A following implementation slice may add local Rust source and focused tests
under `crates/hsai-agent-admission/src/lib.rs` only if it remains limited to:

- one operator replay packet type over the clean source coordinate;
- one manifest type for the declared packet files;
- one source-repository observation type for repository URL or source-bundle
  identifier, commit, branch, dirty status, handoff path, and handoff digest;
- one replay-command observation type for operator-declared command lines,
  UTC start/finish timestamps, exit statuses, and focused result summaries;
- transcript SHA-256 digest records for stdout and stderr, including explicit
  empty-transcript handling;
- artifact-retention declarations that list only non-secret, declared,
  quarantined metadata artifacts;
- a redaction report proving no secrets, credentials, private machine
  identifiers, raw provider responses, undeclared files, raw logs, accepted
  evidence artifacts, Level2 artifacts, score-axis artifacts, proof artifacts,
  checker transcripts, solver certificates, benchmark artifacts, or production
  deployment artifacts are included;
- a nonpromotion report preserving:
  `pcsm_runtime_imported=false`,
  `recoverable_artifacts_imported=false`,
  `accepted_evidence_created=false`,
  `accepted_independent_external_reproduction=false`,
  `level2_evidence_created=false`, and
  `score_axes_populated=false`;
- deterministic digesting of every declared file and fail-closed readback
  validation.

The future implementation may reuse the existing local output-root,
declared-file, digest, sidecar, duplicate-JSON, and nonpromotion conventions
already used by the Phase 619 materialization path. It must not add new
dependencies, command runners, network APIs, process-spawn APIs, source-repo
parsers, or accepted-evidence append paths.

## Required Future Bindings

A future implementation must bind:

- the Phase 622 closure report path and digest;
- the clean source coordinate fields listed in this document;
- one Phase 621 local audit summary digest or an explicit explanation that no
  durable audit summary was materialized;
- the operator-declared repository remote URL or source-bundle identifier;
- the operator-declared repository commit hash;
- the operator-declared pre-run branch name;
- the operator-declared pre-run dirty status;
- the operator operating system and architecture;
- the toolchain versions relevant to the replay commands;
- each operator-declared command line;
- each command UTC start and finish timestamp;
- each command exit status;
- each command focused result summary;
- stdout and stderr transcript SHA-256 digests for every command;
- artifact-retention declaration digest;
- redaction-report digest;
- nonpromotion-report digest;
- packet manifest digest.

## Required Future Validation Rules

A future implementation must fail closed if:

- the Phase 622 closure report binding is missing, stale, malformed, or
  digest-mismatched;
- the clean source coordinate differs from the coordinate in this boundary;
- the operator packet omits repository commit, branch, dirty status, handoff
  path, handoff digest, command line, timestamps, exit status, focused result
  summary, or transcript digests;
- the operator-declared source status is dirty, staged, uncommitted, or
  digest-mismatched;
- the handoff digest does not match
  `93e07a250c9a6a5f530d02f07095074e7df8a5b5ce7e8e2dfa6e5feb376ea149`;
- any declared command failed or is reported as skipped;
- any stdout or stderr digest does not match the supplied transcript digest
  record;
- any retained artifact path is absolute, traverses parent directories,
  duplicates another path, is undeclared, or has a mismatched digest;
- any raw stdout/stderr, secret, credential, private machine identifier, raw
  provider response, accepted-evidence artifact, Level2 artifact, score-axis
  artifact, proof artifact, checker transcript, solver certificate, benchmark
  artifact, or production deployment artifact is present;
- any packet metadata claims PCSM runtime import, recoverable artifact import,
  external result import, accepted evidence, accepted independent external
  reproduction, accepted formal evidence, Level2+ evidence, score-axis
  population, benchmark evidence, external audit status, SOTA, semantic
  correctness, production readiness, full security, breakthrough status,
  human-review acceptance, or action authority.

## Evidence Meaning

If a future packet succeeds under this boundary, it may support only:

```text
HSAI can locally validate and quarantine an operator-declared replay packet for
the clean recoverable-ghost-states PCSM source coordinate.
```

That still would not be PCSM runtime import, recoverable-ghost artifact import,
external result import, accepted evidence, accepted formal evidence,
independent external reproduction accepted by the repo, Level2+ evidence,
score-axis evidence, proof authority, checker transcript authority, solver
certificate authority, benchmark evidence, external audit, SOTA, semantic
correctness, production readiness, full security, or authority to execute an
action.

## Nonclaims

Phase 623 does not permit Rust implementation code in this slice, Cargo
metadata changes, new dependencies, source-repo parsing, source-repo command
execution by HSAI, filesystem reads from recoverable-ghost-states, PCSM
runtime import or vendoring, recoverable-ghost artifact import, generated
committed bundles, package runtime additions, command-line tools, network
access, credential reads, external result import, accepted Evidence Ledger
mutation, accepted external evidence, accepted formal evidence, accepted
independent external reproduction, Level2+ evidence, score-axis population,
proof artifact generation or promotion, checker transcript generation or
promotion, solver certificate generation or promotion, Lean execution, SMT/Z3
execution, COBALT execution, Rust-to-Lean extraction, benchmark submission,
production deployment, external-audit claims, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, global software-agent uniqueness claims, human-review acceptance
claims, or authority to execute an action.

## Exit Criteria

Phase 623 is complete when this boundary is documented and referenced from the
repo navigation/status files. Any implementation remains blocked until a
separate explicit implementation phase names the exact state slice it mutates.
