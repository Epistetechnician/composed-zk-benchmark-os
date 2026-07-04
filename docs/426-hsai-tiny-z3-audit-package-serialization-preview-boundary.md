# Phase 426 HSAI Tiny Z3 Audit Package Serialization Preview Boundary

State slice: `Phase 426 HSAI tiny Z3 audit package serialization preview boundary`.

Phase 426 defines a docs-first boundary for a future deterministic in-memory
serialization preview of the Phase 425 local tiny-Z3 review audit package. The
future preview may show exactly what would be exported for human review, but it
must remain local, non-accepted, non-authoritative, and non-mutating.

This phase does not implement serialization code, write filesystem artifacts,
create package files, create archives, mutate the accepted Evidence Ledger,
change accepted append policy, create accepted formal evidence, create Level2+
evidence, populate score axes, generate proof artifacts, generate checker
transcripts, generate solver certificates, execute Lean, execute SMT, execute
COBALT, run Rust-to-Lean extraction, submit benchmarks, deploy to production,
claim semantic correctness, claim production readiness, claim SOTA, claim
breakthrough status, claim full security, or grant action authority.

## Future Preview Purpose

The future serialization preview may convert one valid Phase 425 audit package
record into deterministic pure data for local review. The preview may help a
reviewer inspect the audit package shape before any later handoff or artifact
plumbing phase is authorized.

The preview must be treated as metadata only. It is not accepted evidence, not
Level2+ evidence, not score-axis evidence, not a proof artifact, not a checker
transcript, not a solver certificate, not a benchmark result, and not a backend
execution result.

## Allowed Future Preview Fields

A future implementation may expose these in-memory fields:

- preview schema version;
- preview state slice;
- preview id;
- preview created-at timestamp supplied by the caller;
- source Phase 425 audit package id;
- source Phase 425 audit package digest;
- source Phase 423 review digest;
- source Phase 421 metadata digest;
- source Phase 405 local Z3 output-manifest digest;
- source Phase 404 local Z3 execution digest;
- accepted append blocker digest;
- package manifest digest;
- canonical JSON payload digest;
- redaction policy digest;
- explicit nonclaim digest;
- portable logical preview path string, if any, under
  `local-preview/tiny-z3/`;
- preview summary string that contains no promotional claim language;
- boolean flags proving that no raw proof, checker, solver, backend stdout,
  backend stderr, benchmark, secret, credential, accepted-ledger mutation, or
  score-axis payload is included.

The future preview may include deterministic JSON bytes in memory only. It must
not write those bytes to disk in the implementation slice unless a later phase
explicitly authorizes output plumbing.

## Required Future Validation

A future implementation must reject a preview request if:

- the source Phase 425 audit package is invalid;
- the source audit package digest is zero or missing;
- the source review digest is zero, missing, or drifted;
- the source metadata digest is zero, missing, or drifted;
- the Phase 405 output-manifest digest is zero, missing, or drifted;
- the Phase 404 execution digest is zero, missing, or drifted;
- the accepted append blocker digest is zero, missing, or drifted;
- the package manifest digest is zero, missing, or drifted;
- the canonical JSON payload digest is zero, missing, or inconsistent with the
  in-memory payload;
- the redaction policy digest is zero, missing, or inconsistent with the
  declared redaction policy;
- a logical path is absolute, contains `..`, contains empty path segments,
  contains platform separators outside `/`, or falls outside
  `local-preview/tiny-z3/`;
- the preview text claims accepted evidence, Level2+ evidence, score-axis
  evidence, proof authority, checker authority, solver-certificate authority,
  benchmark evidence, semantic correctness, production readiness, SOTA,
  breakthrough status, full security, or action authority;
- raw backend stdout or stderr is included;
- raw proof artifacts are included;
- raw checker transcripts are included;
- raw solver certificates are included;
- benchmark outputs are included;
- secrets, provider credentials, private keys, or mutable accepted-ledger state
  are included;
- the preview attempts to mutate the accepted Evidence Ledger;
- the preview attempts to change accepted append policy;
- the preview attempts to create accepted formal evidence.

## Serialization Rules

A future implementation must make the preview reproducible by:

- using a fixed schema version;
- using stable field names;
- sorting object keys or otherwise proving canonical order;
- serializing booleans and digests without environment-dependent formatting;
- excluding process ids, machine paths, hostnames, usernames, wall-clock reads,
  random numbers, backend process output, network responses, and live solver
  output;
- taking caller-supplied timestamps instead of reading time inside the builder;
- deriving every digest from explicit input bytes or already validated source
  metadata;
- exposing validation issues instead of partially accepting malformed input.

## Evidence Meaning

The maximum claim after Phase 426 is:

```text
HSAI has a boundary for a deterministic local serialization preview of one
non-accepted tiny-Z3 audit package while accepted formal evidence remains
blocked.
```

That still is not:

- implemented serialization;
- filesystem artifact output;
- accepted formal evidence;
- accepted Evidence Ledger mutation;
- accepted append policy change;
- Level2+ evidence;
- score-axis evidence;
- a Lean proof;
- an SMT proof beyond the referenced local Phase 404/405 replay metadata;
- a COBALT containment proof;
- a Rust-to-Lean proof;
- a proof artifact;
- a checker transcript;
- a solver certificate;
- benchmark evidence;
- whole-system proof;
- semantic correctness;
- production readiness;
- SOTA;
- breakthrough status;
- full security;
- authority to execute an action.

## Phase 427 Implementation Exit Criteria

Phase 427 may implement the local in-memory serialization preview only if it:

- stays inside `crates/hsai-agent-admission/src/lib.rs`;
- adds no Cargo metadata;
- writes no filesystem artifacts;
- creates no archives or package files;
- performs no process or network calls;
- accepts only one valid Phase 425 audit package;
- emits deterministic in-memory preview data only;
- binds the source Phase 425 audit package digest;
- binds the Phase 423 review digest;
- binds the Phase 421 metadata digest;
- binds Phase 404/405 local Z3 backend replay digests through the audit
  package;
- binds the current accepted append blocker digest;
- validates canonical JSON payload digest consistency;
- validates redaction policy digest consistency;
- rejects non-portable logical paths;
- rejects raw backend/proof/checker/solver/benchmark/secret-bearing payloads;
- rejects promotional preview text;
- rejects all promotion attempts listed in this boundary;
- does not mutate the accepted Evidence Ledger;
- does not change accepted append policy;
- does not create accepted formal evidence;
- does not create Level2+ evidence;
- does not populate score axes;
- does not generate or promote proof artifacts, checker transcripts, or solver
  certificates;
- does not run Lean, SMT, COBALT, or Rust-to-Lean extraction;
- does not submit benchmarks;
- does not claim semantic correctness, production readiness, SOTA, breakthrough
  status, full security, or action authority.
