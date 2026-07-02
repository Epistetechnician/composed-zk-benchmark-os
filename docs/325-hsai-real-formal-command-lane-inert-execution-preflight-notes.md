# Phase 325 HSAI Real Formal Command Lane Inert Execution Preflight Notes

State slice: `Phase 325 HSAI real formal command lane inert execution-preflight metadata and source-scan exception`.

## Scope

Phase 325 implements the inert execution-preflight metadata authorized by Phase
324 for the Phase 321-323 real formal command lane.

This phase adds Rust data types, validation, focused tests, and a source-scan
exception shape for one future fixed local SMT-LIB2 process invocation. It does
not spawn a process, execute SMT, Z3, Lean, COBALT, Rust-to-Lean, Aeneas, Hax,
Coq, TLA+, CBMC, or any model checker, create proof artifacts, create checker
transcripts, create solver certificates, create accepted evidence, create
Level2+ evidence, populate score axes, prove semantic correctness, establish
production readiness, establish SOTA, establish breakthrough status, establish
full security, or grant authority to execute an action.

## Implemented Surface

Phase 325 adds these local Rust surfaces under
`crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalRealCommandLaneExecutionPreflightInput`;
- `GatewayFormalRealCommandLaneExecutionPreflight`;
- `GatewayFormalRealCommandLaneExecutionPreflightIssue`;
- `GatewayFormalRealCommandLaneExecutionPreflightValidation`;
- `GatewayFormalRealCommandLaneFixedSmtProcessPlan`;
- `build_gateway_formal_real_command_lane_execution_preflight`;
- `validate_gateway_formal_real_command_lane_execution_preflight_input`;
- `validate_gateway_formal_real_command_lane_execution_preflight`;
- `gateway_formal_real_command_lane_fixed_smt_process_plan`.

The `gateway_formal_real_command_lane_fixed_smt_process_plan` function is a
blocked Phase 325 plan surface. It returns `process_spawned = false` and
`backend_executed = false`; Phase 325 does not call `std::process::Command`,
does not construct a solver command, and does not read or write solver
artifacts.

## Preflight Rejections

The preflight validator rejects:

- missing Phase 323 readback;
- Phase 323 manifest digest drift;
- command request digest drift;
- command descriptor digest drift;
- obligation digest drift;
- expected-output grammar digest drift;
- missing operator acknowledgement;
- missing executable digest;
- executable policy mismatch;
- fixed executable label mismatch;
- caller executable path enablement;
- caller argv enablement;
- shell fragments;
- inherited environment;
- stdin;
- network access;
- protected output-root labels;
- accepted-evidence paths;
- Level2+ evidence paths;
- score-axis paths;
- benchmark-output paths;
- proof-promotion paths;
- missing nonclaims;
- claim-boundary drift;
- any process/backend/proof/evidence/score/authority promotion flag.

## Source-Scan Exception

Phase 325 updates
`crates/hsai-e2e-harness/tests/claim_boundary_source_scan.rs` with a
single-function exception shape for a future direct process API line:

```text
function: run_gateway_formal_real_command_lane_fixed_smt_process
allowed line: let mut command = std::process::Command::new(fixed_executable);
```

No such process API line exists in the implementation in this phase. The
exception is constrained so an arbitrary backend runner, caller-controlled
command, shell command, or unrelated process API remains forbidden by the
source scan.

## Validation

Phase 325 adds focused tests for:

- valid preflight construction from a read back Phase 323 bundle;
- blocked fixed-SMT process-plan behavior with no spawn and no execution;
- missing Phase 323 readback rejection;
- missing operator acknowledgement rejection;
- missing executable digest rejection;
- manifest/request/descriptor/obligation/grammar digest drift rejection;
- caller executable path rejection;
- caller argv rejection;
- shell fragment rejection;
- inherited environment rejection;
- stdin rejection;
- network rejection;
- protected output-root rejection;
- accepted-evidence, Level2+, score-axis, benchmark-output, and proof-promotion path rejection;
- preflight promotion flag rejection;
- source-scan single-function exception enforcement.

Required validation:

```text
cargo fmt --all -- --check
cargo test -p hsai-agent-admission gateway_formal_real_command_lane --quiet
cargo test -p hsai-e2e-harness --test claim_boundary_source_scan
cargo test -p zkbench-core --test repo_claim_boundary_docs --test repo_hygiene
git diff --check
find README.md AGENTS.md docs crates -type f -empty
pnpm run lint, if package.json exists
cargo test --workspace --quiet
```

## Evidence Meaning

This phase supports only this claim:

```text
HSAI has a local inert execution-preflight lane for one future fixed local SMT-LIB2 command invocation over one tiny gateway invariant.
```

It does not support SOTA, full security, semantic correctness, production
readiness, accepted formal evidence, Level2+ formal evidence, backend score
axes, a real SMT/Z3 run, a Lean proof, a COBALT containment proof,
Rust-to-Lean extraction, proof artifacts as accepted evidence, checker
transcripts as accepted evidence, solver certificates as accepted evidence,
source correspondence proof, accepted Evidence Ledger mutation, or authority to
execute an action.

## Next Slice

Phase 326 implements the first quarantined fixed local SMT-LIB2 process
execution over this exact preflight lane. It remains nonpromoting: no accepted
evidence, no Level2+ evidence, no score axes, no semantic-correctness claim, no
production-readiness claim, no SOTA claim, no full-security claim, and no action
authority.
