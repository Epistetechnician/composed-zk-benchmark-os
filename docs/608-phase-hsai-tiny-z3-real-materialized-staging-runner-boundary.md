# Phase 608 HSAI Tiny Z3 Real Materialized Staging Runner Boundary

State slice: `Phase 608 HSAI tiny Z3 real materialized staging runner boundary`.

Phase 608 defines the docs-first boundary for a narrow local staging runner over
the Phase 607 capture materializer:

```text
operator invokes exact Phase 604 focused command
  -> bounded in-memory transcript digests
  -> Phase 607 quarantined capture output root
```

This phase does not implement Rust code, change Cargo metadata, add
dependencies, add package runtime files, call a network service, read
credentials, import external results, mutate the accepted Evidence Ledger,
accept independent external reproduction, create accepted formal evidence,
create Level2+ evidence, populate score axes, run Lean, run COBALT, run
Rust-to-Lean extraction, create proof artifacts, create checker transcripts,
create solver certificates, create benchmark evidence, record human-review
acceptance, claim semantic correctness, claim production readiness, claim SOTA,
claim breakthrough status, claim full security, claim external audit status, or
grant authority to execute an action.

## Future Runner Meaning

A future implementation may provide an operator-facing local example that:

- requires an explicit acknowledgement environment variable;
- constrains output to the ignored `.gateway-demo-runs/` root;
- executes only the exact Phase 604 focused command:

```text
cargo test -p hsai-agent-admission phase604_real_z3_unsat_result_materializes_accepted_ledger_artifact_without_claim_escalation -- --nocapture
```

- records repository commit, branch, dirty-status class, Rust version, Z3 path,
  Z3 version, start/finish timestamps, process status, stdout digest, and
  stderr digest;
- keeps raw stdout and stderr in memory only;
- maps the observation into the Phase 607 materializer;
- reads the materialized bundle back before reporting success.

The output remains a quarantined local capture packet. It is not external result
import, accepted evidence, accepted formal evidence, independent external
reproduction accepted by the repo, Level2+ evidence, score-axis evidence, Lean
proof, COBALT containment evidence, Rust-to-Lean proof, checker transcript
authority, solver certificate authority, benchmark evidence, external audit,
semantic correctness, production readiness, SOTA, full security, or action
authority.

## Required Future Validation Rules

A future implementation must fail closed if:

- the acknowledgement is absent or does not match the literal contract;
- the output root is not under `.gateway-demo-runs/`;
- the run id or operator id is not a single-segment identifier;
- the repository commit is not a full SHA-1 hex commit;
- the command differs from the exact Phase 604 focused command;
- Z3 version output does not identify Z3;
- the process exit status is nonzero;
- the expected Phase 604 focused result line is absent;
- the run skipped because Z3 was unavailable;
- transcript bytes exceed the bounded in-memory cap;
- the Phase 607 materializer rejects the normalized packet;
- readback differs from the materialized manifest.

## Phase 609 Implementation Exit Criteria

A future Phase 609 may implement the staging runner only if it:

- touches only `crates/hsai-agent-admission/src/lib.rs`,
  `crates/hsai-agent-admission/examples/`, focused tests under
  `crates/hsai-agent-admission/tests/`, future phase notes under `docs/`, and
  navigation/status updates under `README.md`, `docs/12-task-list.md`,
  `docs/90-whole-codebase-validation-report.md`, and `AGENTS.md`;
- adds no dependencies and no Cargo metadata changes;
- uses no shell and no network calls;
- reads no credentials;
- writes only the existing Phase 607 quarantined capture packet files under a
  caller-selected ignored output root;
- retains no raw stdout or stderr files;
- creates no accepted evidence files;
- creates no Level2 or score-axis files;
- records only local staging capture metadata;
- rejects any claim that external result import, accepted independent external
  reproduction, accepted formal evidence, Level2+ evidence, score-axis
  population, benchmark evidence, external audit, strong public claim,
  human-review acceptance, or action authority exists.
