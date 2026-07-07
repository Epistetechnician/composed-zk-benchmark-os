# Phase 606 HSAI Tiny Z3 Real Materialized External Operator Capture Boundary

State slice: `Phase 606 HSAI tiny Z3 real materialized external operator capture boundary`.

Phase 606 defines the docs-first boundary for a future local capture packet
returned by an external operator after following the Phase 605 handoff packet:

```text
Phase 605 external-review handoff packet
  + external operator transcript and provenance declaration
  -> future quarantined local operator-capture packet
```

This phase does not implement Rust code, change Cargo metadata, add
dependencies, add binaries, add scripts, write filesystem artifacts, retain
generated ledgers, run an external replay, run a backend, run Lean, run SMT/Z3,
run COBALT, run Rust-to-Lean extraction, create proof artifacts, create checker
transcripts, create solver certificates, import external results, mutate the
accepted Evidence Ledger, create accepted formal evidence, create Level2+
evidence, populate score axes, submit benchmarks, claim semantic correctness,
claim production readiness, claim SOTA, claim breakthrough status, claim full
security, claim external audit status, accept independent external
reproduction, record a human-review acceptance, or grant authority to execute
an action.

## Future Capture Meaning

A future implementation may validate a local returned packet under this
namespace:

```text
phase605-real-z3-materialized-operator-capture/
  manifest.json
  phase605-handoff-packet.json
  operator-provenance.json
  execution-observation.json
  transcript-digests.json
  artifact-retention-declaration.json
  reviewer-routing.json
  redaction-report.json
  nonpromotion-report.json
  digests.json
```

Those files would be local quarantined capture metadata only. They would not
be accepted evidence, accepted independent external reproduction, Level2+
evidence, score-axis evidence, Lean proof, COBALT containment evidence,
Rust-to-Lean proof, checker transcript authority, solver certificate authority,
benchmark evidence, production evidence, or action authority.

## Required Future Bindings

A future implementation must bind:

- one exact Phase 605 handoff packet document path and digest;
- the Phase 604 focused command;
- the Phase 604 local materialized path documentation digest;
- the Phase 603 real-Z3 crossing documentation digest;
- the repository remote URL or source bundle identifier;
- the repository commit hash;
- the pre-run branch name;
- the pre-run dirty status;
- operator operating system and architecture;
- Rust toolchain version;
- Z3 executable path;
- `z3 --version` output;
- UTC start and finish timestamps;
- process exit status;
- focused Phase 604 test result line;
- stdout transcript SHA-256 digest;
- stderr transcript SHA-256 digest, including explicit empty-stderr digest
  handling;
- nonsecret operator identifier;
- raw-log retention flag;
- artifact-retention declaration;
- reviewer routing metadata;
- redaction report proving no secrets, credentials, private machine
  identifiers, raw provider responses, undeclared files, or raw retained logs
  are included;
- nonpromotion report keeping external result import, accepted formal evidence,
  accepted independent external reproduction, Level2+ evidence, score axes,
  proof/checker/solver artifacts, Lean, COBALT, Rust-to-Lean, benchmark
  evidence, external audit, SOTA, semantic correctness, production readiness,
  full security, global uniqueness, human-review acceptance, and action
  authority false.

## Required Future Validation Rules

A future implementation must fail closed if:

- the Phase 605 packet is missing, stale, malformed, or not exact;
- the command differs from the Phase 604 focused command;
- the operator packet omits the repository commit, branch, dirty status, Z3
  path, Z3 version, command line, timestamps, exit status, test-result line, or
  transcript digests;
- the run skipped because Z3 was not available;
- the focused Phase 604 test failed;
- stdout or stderr digests do not match the supplied transcript records;
- any retained artifact is not explicitly quarantined;
- any artifact path is absolute, traverses parent directories, is duplicated,
  is undeclared, or has a mismatched digest;
- any raw stdout/stderr, secret, credential, private machine identifier,
  provider response, accepted-evidence artifact, Level2 artifact, score-axis
  artifact, proof artifact, checker transcript, solver certificate, benchmark
  artifact, or production deployment artifact is present;
- any capture metadata claims external result import, accepted independent
  external reproduction, accepted formal evidence, Level2+ evidence,
  score-axis population, benchmark evidence, external audit status, SOTA,
  semantic correctness, production readiness, full security, breakthrough
  status, human-review acceptance, or action authority.

## Evidence Meaning

If a future capture packet succeeds under this boundary, it may support only:

```text
HSAI can locally validate and quarantine an operator-declared reproduction
attempt for the Phase 604 real-Z3 materialized local replay path.
```

That still would not be external result import, accepted evidence, accepted
formal evidence, independent external reproduction accepted by the repo,
Level2+ evidence, score-axis evidence, Lean proof, SMT proof authority, COBALT
containment evidence, Rust-to-Lean proof, checker transcript authority, solver
certificate authority, benchmark evidence, external audit, SOTA, semantic
correctness, production readiness, full security, or authority to execute an
action.

## Phase 607 Implementation Exit Criteria

A future Phase 607 may implement local capture metadata only if it:

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
- validates one exact Phase 605 handoff packet;
- validates one operator-declared transcript/provenance packet;
- validates materialized file digests on readback if any artifact retention is
  authorized by that implementation phase;
- records only quarantined `Level0DesignNote` capture metadata;
- rejects any claim that external result import, accepted independent external
  reproduction, accepted formal evidence, Level2+ evidence, score-axis
  population, benchmark evidence, external audit, strong public claim,
  human-review acceptance, or action authority exists.
