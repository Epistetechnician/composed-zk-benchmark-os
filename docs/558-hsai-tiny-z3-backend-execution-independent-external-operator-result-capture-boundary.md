# Phase 558 HSAI Tiny Z3 Backend Execution Independent External Operator Result Capture Boundary

State slice: `Phase 558 HSAI tiny Z3 backend execution independent external operator result capture boundary`.

Phase 558 defines the docs-first boundary for a future local capture packet
that an independent external operator could return after receiving the Phase
557 handoff packet:

```text
Phase 557 digest-checked handoff packet
  + future external operator result declaration
  -> future local capture packet boundary
```

This phase does not implement Rust code, change Cargo metadata, add
dependencies, add binaries, add scripts, write filesystem artifacts, run an
external replay, run a backend, run Lean, run SMT/Z3, run COBALT, run
Rust-to-Lean extraction, create proof artifacts, create checker transcripts,
create solver certificates, import external results, mutate the accepted
Evidence Ledger, create accepted formal evidence, create Level2+ evidence,
populate score axes, submit benchmarks, claim semantic correctness, claim
production readiness, claim SOTA, claim breakthrough status, claim full
security, claim external audit status, claim independent external
reproduction, or grant authority to execute an action.

## Future Capture Meaning

A future implementation may validate and materialize a local capture packet
under this namespace:

```text
gateway-formal-tiny-z3-independent-external-operator-result/
  manifest.json
  phase557-handoff-packet-manifest.json
  operator-provenance.json
  execution-observation.json
  captured-artifact-index.json
  redaction-report.json
  nonpromotion-report.json
  digests.json
```

Those files would be local `Level0DesignNote` capture metadata only. They
would not be accepted evidence, Level2+ evidence, score-axis evidence, a Lean
proof, COBALT containment evidence, Rust-to-Lean proof, checker transcript
authority, solver certificate authority, benchmark evidence, or production
evidence.

## Required Future Bindings

A future implementation must bind:

- one Phase 557 packet manifest digest;
- the Phase 557 readback validation digest;
- the Phase 557 nonpromotion report digest;
- the Phase 557 Phase 555 handoff digest;
- the Phase 555 manual handoff bundle digest;
- the Phase 555 manual handoff validation digest and zero issue count;
- the Phase 553 blocked import-review digest;
- inherited Phase 551/549/547/545/543/541/535/533/531/529/527 digests;
- an operator-declared environment identifier;
- a provenance record with operator id, run timestamp, workspace digest,
  source revision, toolchain declaration, command descriptor digest, and
  redaction policy digest;
- an execution observation with bounded exit status, normalized stdout/stderr
  summary digests, elapsed-time metadata, and explicit raw-log retention flags;
- an artifact index with declared logical roles, relative paths, byte lengths,
  SHA-256 digests, and redaction flags;
- a redaction report that proves no secrets, credentials, raw provider
  responses, raw stdout/stderr, or undeclared files are retained;
- a nonpromotion report that keeps external result import, accepted formal
  evidence, Level2+ evidence, score axes, proof/checker/solver artifacts, Lean,
  COBALT, Rust-to-Lean, benchmark evidence, external audit, SOTA, semantic
  correctness, production readiness, full security, and action authority false.

## Required Future Validation Rules

A future implementation must fail closed if:

- the Phase 557 packet manifest is missing, stale, malformed, or not exact;
- the Phase 557 packet claims any run, result import, accepted evidence, Level2+
  evidence, score-axis population, proof artifact, checker transcript, solver
  certificate, Lean execution, COBALT execution, Rust-to-Lean execution,
  benchmark evidence, external audit, strong public claim, or action authority;
- the Phase 555 handoff validation is invalid or has any issue;
- the operator provenance is incomplete, non-deterministic, or does not bind the
  command descriptor and source revision;
- any artifact path is absolute, traverses parent directories, is duplicated,
  is undeclared, or has a mismatched digest;
- any raw stdout/stderr, secret, credential, provider response, accepted
  evidence artifact, Level2 artifact, score-axis artifact, proof artifact,
  checker transcript, solver certificate, benchmark artifact, or production
  deployment artifact is present;
- any capture metadata claims independent external reproduction as accepted,
  imports an external result, populates score axes, creates Level2+ evidence,
  or makes SOTA, full-security, semantic-correctness, production-readiness, or
  breakthrough claims.

## Evidence Meaning

If a future capture packet succeeds under this boundary, it may support this
claim only:

```text
HSAI can locally validate and package an operator-declared external execution
observation as quarantined capture metadata for future review.
```

That still would not be accepted evidence, independent external reproduction
accepted by the repo, external result import, Level2+ evidence, score-axis
evidence, Lean proof, SMT proof authority, COBALT containment evidence,
Rust-to-Lean proof, checker transcript authority, solver certificate authority,
benchmark evidence, external audit, SOTA, semantic correctness, production
readiness, full security, or authority to execute an action.

## Phase 559 Implementation Exit Criteria

A future Phase 559 may implement local capture metadata only if it:

- touches only `crates/hsai-agent-admission/src/lib.rs`, focused tests in that
  file, future phase notes under `docs/`, and navigation/status updates under
  `README.md`, `docs/12-task-list.md`,
  `docs/90-whole-codebase-validation-report.md`, this boundary, and
  `AGENTS.md`;
- performs no process or network calls;
- reads no credentials;
- writes only caller-selected local capture packet files under the declared
  namespace;
- writes no accepted-evidence files;
- writes no Level2 or score-axis files;
- validates one exact Phase 557 handoff packet manifest;
- validates one exact Phase 555 handoff record through the Phase 557 manifest;
- validates materialized file digests on readback;
- records only quarantined `Level0DesignNote` capture metadata;
- rejects any claim that external result import, accepted formal evidence,
  Level2+ evidence, score-axis population, benchmark evidence, external audit,
  strong public claim, or action authority exists.
