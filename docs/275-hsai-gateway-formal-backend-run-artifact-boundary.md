# Phase 275 HSAI Gateway Formal Backend Run Artifact Boundary

State slice: `Phase 275 HSAI gateway formal backend-run artifact boundary`.

## Status

Complete for the docs-first backend-run artifact boundary.

## Purpose

Phase 273 created inert backend-adapter metadata for a future `RustToLean`
gateway formal lane. Phase 274 added drift coverage for that metadata. Phase
275 defines the future artifact boundary for a hermetic backend run before any
proof tool setup or execution is allowed.

This phase does not implement a runner and does not run a backend.

## Future Artifact Root

A future implementation may read or write only under a caller-selected
artifact root. The artifact root must be outside protected repository roots
unless a test tempdir is used.

The implementation must reject:

- empty artifact roots;
- repository roots;
- file roots;
- symlink roots;
- existing roots unless explicit overwrite is set;
- path traversal;
- absolute declared paths;
- undeclared files;
- missing declared files;
- stale sidecars;
- malformed declared JSON;
- raw secret material;
- raw external repository source;
- raw unbounded prover logs;
- raw unbounded checker transcripts;
- accepted Evidence Ledger files.

## Declared Candidate Files

A future `RustToLean` backend-run artifact bundle should use this logical
layout:

```text
gateway-formal-backend-run/
  adapter-request.json
  adapter-report.json
  correspondence-certificate-digest.json
  correspondence-output-manifest-digest.json
  source-digests.json
  toolchain-lock.json
  model-assumptions.json
  unsupported-rust-features.json
  proof-obligations.json
  run-summary.json
  redaction-report.json
  nonclaims.md
  manifest.json
```

Each declared file must have a matching `.sha256` sidecar.

No raw proof assistant cache, raw build directory, raw external repository
checkout, credential file, accepted Evidence Ledger file, benchmark result file,
or live-provider response may be written by this bundle.

## Optional Candidate Attachments

A later implementation may support optional declared attachments only when they
are digest-bound and explicitly redacted:

- `candidate-proof-artifact.ref.json`
- `candidate-checker-transcript.ref.json`
- `candidate-tool-log-summary.md`

The optional attachments may contain paths or digests to operator-held external
artifacts, but they must not contain raw proof scripts, raw full checker logs,
credentials, secrets, raw external source trees, or accepted Evidence Ledger
material.

The presence of a candidate proof artifact reference must not change evidence
maturity above candidate status.

## Run Summary Contract

The future `run-summary.json` must include:

- schema version;
- run id;
- adapter request digest;
- adapter report digest;
- correspondence certificate digest;
- output manifest digest;
- backend kind;
- tool name and version;
- toolchain lock digest;
- execution mode;
- started-at and finished-at timestamps if provided by the caller;
- exit status;
- checker status;
- proof obligation ids requested;
- proof obligation ids discharged;
- proof obligation ids not discharged;
- modeled assumptions digest;
- unsupported Rust features digest;
- candidate proof artifact reference digest, if present;
- candidate checker transcript reference digest, if present;
- claim boundary;
- `creates_accepted_evidence = false`;
- `creates_level2_evidence = false`;
- `populates_score_axes = false`;
- `grants_authority = false`.

## Execution Mode Contract

Future code must distinguish:

- `NotRun`;
- `HermeticFixtureOnly`;
- `OperatorProvidedLocalRun`;
- `ExternalRunReferenceOnly`.

Normal automated tests may use only `NotRun` or `HermeticFixtureOnly`. Any
operator-provided local run must require explicit operator acknowledgement and
must not require credentials or network access in normal test paths.

## Review Gate

A future candidate backend run is not accepted evidence until a later explicit
promotion phase validates:

- source correspondence;
- output-bundle readback;
- adapter metadata;
- toolchain lock;
- run-summary digest;
- proof artifact reference digest, if present;
- checker transcript reference digest, if present;
- redaction report;
- nonclaims;
- reviewer decision;
- accepted-evidence nonpromotion flags.

The reviewer decision for this artifact boundary may be candidate-only. It must
not be accepted-evidence approval.

## Benchmark Hooks

Repository-scale benchmark hooks are allowed only as metadata references:

- benchmark suite name;
- benchmark suite version;
- benchmark case ids;
- benchmark harness digest;
- benchmark result reference digest.

Benchmark hooks must not populate score axes, create benchmark evidence, or
claim SOTA unless a later explicit benchmark-evidence phase validates the run
against its own acceptance policy.

## Required Future Tests

A future implementation phase must add tests for:

- declared-file materialization;
- readback of a valid hermetic fixture bundle;
- protected root rejection;
- symlink root rejection;
- symlink declared-file rejection;
- symlink sidecar rejection;
- undeclared file rejection;
- missing declared file rejection;
- stale sidecar rejection;
- malformed adapter request rejection;
- malformed adapter report rejection;
- malformed run summary rejection;
- redaction-report drift rejection;
- nonclaim drift rejection;
- proof artifact reference drift rejection;
- checker transcript reference drift rejection;
- accepted Evidence Ledger retention rejection;
- raw proof log retention rejection;
- score-axis population rejection;
- Level2+ evidence escalation rejection;
- authority grant rejection;
- forbidden public claim text rejection.

## Anti-Goals

This phase does not permit:

- Rust implementation changes;
- Cargo metadata changes;
- package runtime files;
- proof assistant setup files;
- external repo clones;
- vendored source;
- Lean, Coq, TLA+, SMT, Z3, CBMC, model-checker, Aeneas, Hax, rust-lean, or
  COBALT execution;
- generated proof artifacts;
- generated checker transcripts;
- raw prover logs;
- raw checker logs;
- accepted Evidence Ledger mutation;
- Level2+ evidence;
- score-axis population;
- benchmark evidence;
- official benchmark submission;
- live provider calls;
- credential handling;
- semantic-correctness claims;
- production-readiness claims;
- SOTA claims;
- breakthrough claims;
- full-security claims;
- global software-agent uniqueness claims;
- authority to execute an action.

## Next Slice

The next implementation slice was completed as Phase 276. It added inert
backend-run artifact metadata and validation in `hsai-agent-admission` without
running a backend. It only models declared candidate artifact metadata,
redaction, digest binding, nonclaims, and fail-closed escalation checks.

The next responsible slice should be docs-first materialized bundle planning for
the backend-run artifact root. It should not write files or run a backend until
that boundary is explicit.
