# Phase 322 HSAI Real Formal Command Lane Inert Data Model Notes

State slice: `Phase 322 HSAI real formal command lane inert data model`.

## Scope

Phase 322 implements the inert Rust data model and declared output contract for
the Phase 321 real formal command lane.

This phase is implemented in `crates/hsai-agent-admission/src/lib.rs`.

It does not add package runtime files, solver scripts, checker scripts, proof
assistant setup files, command execution, process spawning, filesystem
materialization for the new lane, proof artifacts, generated checker
transcripts, solver certificates, accepted evidence, Level2+ evidence, score
axes, benchmark evidence, or proof-authority claims.

## Implemented Surface

Phase 322 adds:

- `GATEWAY_FORMAL_REAL_COMMAND_LANE_*` schema, state-slice, and claim-boundary
  constants.
- `GatewayFormalRealCommandLaneRequest`.
- `GatewayFormalRealCommandLaneCommandDescriptor`.
- `GatewayFormalRealCommandLaneObligation`.
- `GatewayFormalRealCommandLaneObligationBinding`.
- `GatewayFormalRealCommandLaneBoundedSummary`.
- `GatewayFormalRealCommandLaneSolverVerdict`.
- `GatewayFormalRealCommandLaneTranscript`.
- `GatewayFormalRealCommandLaneNonpromotionReport`.
- `GatewayFormalRealCommandLaneValidation`.
- `GatewayFormalRealCommandLaneValidationReport`.
- `GatewayFormalRealCommandLaneOutputManifest`.
- `GatewayFormalRealCommandLaneOutputContract`.
- declared `gateway-formal-real-command-lane/*` file and sidecar lists.
- in-memory contract construction through
  `build_gateway_formal_real_command_lane_output_contract`.
- fail-closed validation through `validate_gateway_formal_real_command_lane`.

The output contract is in memory only. It declares the future artifact grammar
and digest bindings but does not write the bundle to disk.

## Source Wiring

The contract binds the Phase 317 and Phase 319 source surfaces:

- Phase 317 source adapter output manifest.
- Phase 319 tiny hermetic execution output manifest.
- Phase 317 adapter request digest.
- Phase 317 fixture input digest.
- Phase 317 source command descriptor digest.
- one static SMT-LIB2 obligation digest.
- one expected-output grammar digest.

The validator rejects source drift when either source manifest no longer
matches the declared digests or when the source manifests attempt evidence,
score, semantic-correctness, production-readiness, SOTA, breakthrough,
full-security, or authority escalation.

## Command Contract

The command descriptor is metadata only. It requires:

- `backend_id = local_smt_tiny_gateway_invariant`;
- `backend_mode = smt-lib2-offline-command`;
- `command_kind = direct_process_no_shell`;
- `input_kind = static_non_secret_smt2_obligation`;
- `output_kind = bounded_solver_stdout_stderr`;
- fixed executable policy;
- fixed argv template;
- no shell;
- no stdin;
- no inherited environment;
- no environment values;
- no network;
- no caller executable path;
- no caller argv;
- ignored output root only;
- digest binding for the source execution manifest;
- digest binding for the SMT-LIB2 obligation;
- digest binding for the expected-output grammar.

The validator rejects shell fragments, inherited environment, stdin, network,
caller executable paths, caller argv, and digest drift.

## Solver Verdict Boundary

The solver verdict enum includes only the Phase 321 labels:

- `not_run`;
- `process_exited`;
- `process_failed`;
- `process_timed_out`;
- `solver_unsat_without_certificate`;
- `solver_sat_witness_without_certificate`;
- `solver_unknown`;
- `output_unparseable`.

Phase 322 permits only `not_run` as a valid contract state. All real solver
labels remain reserved for a future execution phase.

## Tests

Phase 322 adds focused tests:

```text
cargo test -p hsai-agent-admission gateway_formal_real_command_lane --quiet
```

The tests verify:

- valid in-memory contract construction from real Phase 317/319 source
  manifests;
- exact declared file and sidecar grammar;
- no process spawn;
- no backend execution;
- no proof artifact;
- no checker transcript promotion;
- no solver certificate promotion;
- no accepted evidence;
- no Level2+ evidence;
- no score-axis population;
- no semantic-correctness claim;
- no production-readiness claim;
- no SOTA claim;
- no breakthrough claim;
- no full-security claim;
- no authority grant;
- missing operator acknowledgement rejection;
- unsafe command-policy rejection;
- source execution manifest drift rejection;
- transcript promotion rejection.

## Claim Boundary

This phase supports only this claim:

```text
HSAI has an inert Rust data model and declared output contract for one future local SMT-LIB2 command lane over one tiny gateway invariant.
```

It does not support:

- HSAI is SOTA;
- HSAI is fully secure;
- HSAI proves semantic correctness;
- HSAI is production ready;
- HSAI has accepted formal evidence;
- HSAI has Level2+ formal evidence;
- HSAI has backend score axes;
- a real SMT/Z3 run exists;
- a Lean proof exists;
- a COBALT containment proof exists;
- Rust-to-Lean extraction succeeded;
- proof artifacts are accepted evidence;
- checker transcripts are accepted evidence;
- solver certificates are accepted evidence;
- source correspondence is proven;
- accepted Evidence Ledger state changed;
- authority to execute an action exists.

## Validation

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

## Next Slice

Phase 323 implemented local filesystem materialization and readback for the
declared `gateway-formal-real-command-lane/*` output contract.

Phase 324 may define the source-scan exception and execution preflight boundary
for one fixed local SMT-LIB2 command invocation. Phase 324 still must not run
SMT, Z3, Lean, COBALT, Aeneas, Hax, rust-lean, Coq, TLA+, CBMC, or any model
checker.
