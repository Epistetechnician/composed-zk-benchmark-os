# Phase 318 HSAI Tiny Hermetic Formal-Backend Execution Readiness Boundary

State slice: `Phase 318 HSAI tiny hermetic formal-backend execution readiness boundary`.

## Scope

Phase 318 defines the readiness contract that must be satisfied before any
later phase may add code that runs the Phase 317 tiny hermetic formal-backend
adapter command. This is a documentation-only boundary. It does not add Rust
implementation code, process APIs, package runtime files, solver scripts,
checker scripts, proof artifacts, checker transcripts, solver certificates, or
accepted evidence.

The target remains exactly one property:

```text
attestation_challenge_binding_deterministic_input_sensitive
```

The intended backend lane remains:

```text
local_smt_tiny_gateway_invariant
```

## Required Preconditions

A later execution implementation phase must fail closed unless all of these are
true before process spawn:

- The Phase 317 adapter bundle readback succeeds.
- The Phase 317 request, fixture input, command descriptor, transcript summary,
  nonpromotion report, validation report, manifest, sidecars, and nonclaims all
  validate without drift.
- The source-correspondence certificate digest is nonzero and bound into the
  adapter request and transcript summary.
- The descriptor-report manifest digest is nonzero and bound into the adapter
  request.
- The process-spawn interface digest is nonzero and bound into the adapter
  request.
- The command descriptor digest is computed from the exact fixed argv template.
- The fixture input digest is computed from the exact non-secret fixture.
- The expected transcript schema digest is nonzero and operator-acknowledged.
- The imported `report_data_binding` assumption remains explicit.
- All required nonclaims are present before execution and after quarantine
  readback.

## Execution Contract For A Future Phase

A future implementation may only run one direct process if it preserves these
constraints:

- Fixed executable label from the Phase 317 command descriptor.
- Fixed argv template from the Phase 317 command descriptor.
- No caller-supplied executable path.
- No caller-supplied argv.
- No shell.
- No stdin.
- No inherited environment.
- Empty or explicitly allowlisted environment only.
- No network.
- Fixed timeout.
- Bounded stdout.
- Bounded stderr.
- Output root treated as quarantine-only, never as accepted-evidence or score
  authority.

The future runner must not interpret process success as proof. A zero exit code
may only mean the tiny local backend process completed according to the local
runner contract.

## Transcript Contract

A future executed transcript must materialize only redacted metadata:

- Schema version.
- Adapter id.
- Backend id.
- Property id.
- Source-correspondence certificate digest.
- Descriptor-report manifest digest.
- Process-spawn interface digest.
- Command descriptor digest.
- Fixture input digest.
- Expected transcript schema digest.
- Process exit label.
- Timeout flag.
- Solver/checker status label.
- Invariant verdict label.
- Bounded stdout summary digest.
- Bounded stderr summary digest.
- Redaction report digest.
- Nonpromotion report digest.
- Imported assumptions.
- Required nonclaims.

The transcript must not retain raw stdout, raw stderr, raw solver traces, raw
prover logs, raw checker logs, proof artifacts, checker transcripts, solver
certificates, provider responses, credentials, secrets, benchmark outputs,
score-axis outputs, accepted evidence files, or Level2+ evidence files.

## Quarantine Readback Requirements

A later readback implementation must reject:

- Missing declared files.
- Missing sidecars.
- Stale sidecars.
- Symlinked roots, bundle directories, declared files, or sidecars.
- Undeclared raw logs.
- Undeclared proof artifacts.
- Undeclared checker transcripts.
- Undeclared solver certificates.
- Undeclared accepted-evidence files.
- Undeclared Level2+ files.
- Undeclared benchmark or score-axis files.
- Manifest escalation flags.
- Nonpromotion-report escalation flags.
- Transcript claims of semantic correctness, production readiness, SOTA,
  breakthrough status, full security, or authority.
- Any drift in source-correspondence, descriptor-report, process-interface,
  command, fixture, transcript, validation, nonclaim, or nonpromotion digests.

## Claim Boundary

Phase 318 can support only this claim:

```text
HSAI has a documented readiness boundary for a future tiny hermetic local formal-backend execution experiment.
```

It cannot support:

- `HSAI is SOTA.`
- `HSAI is fully secure.`
- `HSAI proves semantic correctness.`
- `HSAI is production ready.`
- `HSAI has accepted formal evidence.`
- `HSAI has Level2+ formal evidence.`
- `HSAI has backend score axes.`
- `HSAI has executed Lean/SMT/COBALT in this phase.`

## Anti-Goals

This phase does not permit:

- Rust implementation code.
- Process spawning.
- Backend execution.
- Lean execution.
- SMT/Z3 execution.
- COBALT execution.
- Aeneas/Hax/rust-lean execution.
- Coq/TLA+/CBMC/model-checker execution.
- Solver scripts.
- Checker scripts.
- Package runtime files.
- External repo clones.
- Vendored source.
- Network access.
- Credentials or secrets.
- Proof artifact creation.
- Checker transcript creation.
- Solver-certificate creation.
- Accepted Evidence Ledger mutation.
- Level2+ evidence.
- Score-axis population.
- Benchmark evidence.
- Official benchmark submission.
- Semantic-correctness claims.
- Production-readiness claims.
- SOTA claims.
- Breakthrough claims.
- Full-security claims.
- Authority to execute an action.

## Validation

Required validation for this docs-first boundary:

```text
cargo fmt --all -- --check
cargo test -p hsai-e2e-harness --test claim_boundary_source_scan
cargo test -p zkbench-core --test repo_claim_boundary_docs --test repo_hygiene
git diff --check
find README.md AGENTS.md docs crates -type f -empty
pnpm run lint, if package.json exists
cargo test --workspace
```

## Next Slice

Phase 319 may implement a tiny local fixture execution readback contract only if
it stays within this Phase 318 boundary. It must still treat the run as a local
execution experiment, not proof authority, accepted evidence, Level2+ evidence,
score-axis evidence, semantic correctness, production readiness, SOTA,
breakthrough status, full security, or action authority.
