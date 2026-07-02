# Phase 324 HSAI Real Formal Command Lane Execution Preflight Boundary

State slice: `Phase 324 HSAI real formal command lane execution preflight boundary`.

## Scope

Phase 324 defines the docs-first boundary for the execution preflight that must
exist before the Phase 321-323 real formal command lane may cross into a fixed
local SMT-LIB2 process invocation.

This phase does not add Rust implementation code, Cargo metadata changes,
package runtime files, source-scan exceptions, process APIs, process spawning,
solver scripts, checker scripts, proof assistant setup files, command
execution, generated proof artifacts, generated checker transcripts, generated
solver certificates, accepted evidence, Level2+ evidence, score axes, benchmark
evidence, or proof-authority claims.

## Preflight Goal

The future execution preflight must answer one question before any process can
run:

```text
Is this exact local command invocation eligible to run as a quarantined,
nonpromoting SMT-LIB2 output producer for the already materialized Phase 323
bundle?
```

The only eligible lane remains:

```text
backend_id = local_smt_tiny_gateway_invariant
backend_mode = smt-lib2-offline-command
property_id = attestation_challenge_binding_deterministic_input_sensitive
```

No other solver, prover, model checker, theorem-prover extraction path, or
certificate checker is in scope.

## Required Future Inputs

A future preflight implementation may consume only:

- a successfully read back Phase 323 `GatewayFormalRealCommandLaneOutputManifest`;
- the Phase 323 command request;
- the Phase 323 command descriptor;
- the Phase 323 obligation file digest;
- the Phase 323 expected-output grammar digest;
- a caller-supplied run id;
- a caller-supplied created-at timestamp;
- an explicit operator acknowledgement;
- an explicit local executable policy identifier;
- an explicit local executable digest supplied by the operator;
- an explicit timeout and bounded stdout/stderr policy already matching the
  Phase 323 command descriptor.

The future preflight implementation must reject:

- missing Phase 323 readback;
- stale Phase 323 sidecars;
- Phase 323 manifest drift;
- command descriptor drift;
- obligation digest drift;
- expected-output grammar digest drift;
- missing operator acknowledgement;
- missing executable digest;
- caller-supplied executable path;
- caller-supplied argv;
- shell fragments;
- inherited environment;
- stdin;
- network access;
- output roots inside protected repository paths;
- accepted Evidence Ledger paths;
- Level2+ evidence paths;
- score-axis paths;
- benchmark-output paths;
- proof-promotion paths.

## Future Source-Scan Exception Shape

The current source scan forbids general process APIs in HSAI crates, with a
narrow historical exception for the Phase 313/319 local fixture path.

A future implementation may add one new exception only if it is restricted to a
single function in `crates/hsai-agent-admission/src/lib.rs` with this shape:

```text
function name: run_gateway_formal_real_command_lane_fixed_smt_process
allowed process API: std::process::Command::new(fixed_executable)
required command policy: direct_process_no_shell
required stdin policy: Stdio::null()
required stdout policy: Stdio::piped()
required stderr policy: Stdio::piped()
required environment policy: env_clear()
required network policy: no network handles and no network crates
required argv policy: fixed argv from validated descriptor only
required timeout policy: bounded timeout from validated descriptor only
```

The exception must not allow:

- caller-supplied executable paths;
- caller-supplied argv;
- shell execution;
- inherited environment;
- stdin;
- network APIs;
- arbitrary backend runners;
- Lean, COBALT, Aeneas, Hax, rust-lean, Coq, TLA+, CBMC, or model-checker
  execution;
- proof artifact retention;
- checker transcript promotion;
- solver certificate promotion;
- accepted evidence creation;
- Level2+ evidence creation;
- score-axis population;
- semantic-correctness claims;
- production-readiness claims;
- SOTA claims;
- breakthrough claims;
- full-security claims;
- authority grants.

## Future Preflight Output

A future preflight output may be an inert metadata object that records:

- schema version;
- run id;
- state slice;
- Phase 323 manifest digest;
- command request digest;
- command descriptor digest;
- obligation digest;
- expected-output grammar digest;
- executable policy id;
- executable digest;
- fixed executable label;
- fixed argv template digest;
- timeout;
- stdout/stderr byte bounds;
- operator acknowledgement;
- process-spawn authorization status;
- explicit nonclaims;
- claim boundary.

The preflight output must use `process_spawn_authorized = true` only for the one
fixed local SMT-LIB2 command policy. It must still set:

```text
process_spawned = false
backend_executed = false
proof_artifact_created = false
checker_transcript_created = false
solver_certificate_created = false
creates_accepted_evidence = false
creates_level2_evidence = false
populates_score_axes = false
semantic_correctness_claimed = false
production_readiness_claimed = false
sota_claimed = false
breakthrough_claimed = false
full_security_claimed = false
grants_authority = false
```

## Evidence Meaning

This phase supports only this claim:

```text
HSAI has a documented execution-preflight boundary for one future fixed local SMT-LIB2 command invocation over one tiny gateway invariant.
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

## Required Future Tests

A future implementation must include focused tests for:

- valid preflight construction from a read back Phase 323 bundle;
- missing operator acknowledgement rejection;
- missing executable digest rejection;
- caller executable path rejection;
- caller argv rejection;
- shell fragment rejection;
- inherited environment rejection;
- stdin rejection;
- network-enabled rejection;
- protected output-root rejection;
- Phase 323 manifest digest drift rejection;
- command descriptor digest drift rejection;
- obligation digest drift rejection;
- expected-output grammar digest drift rejection;
- accepted-evidence path rejection;
- Level2+ path rejection;
- score-axis path rejection;
- benchmark-output path rejection;
- proof-promotion path rejection;
- source-scan exception remains single-function and fixed-command only.

## Validation

Required validation for this docs-first boundary:

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

Phase 325 implements the inert execution-preflight metadata and the
corresponding source-scan exception. It still does not run the solver.

The first real SMT/Z3 command run must wait until a later quarantined execution
phase after preflight metadata, source-scan exception, and readback boundary are
implemented and validated.
