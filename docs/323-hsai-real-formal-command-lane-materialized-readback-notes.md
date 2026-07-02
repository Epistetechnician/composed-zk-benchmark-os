# Phase 323 HSAI Real Formal Command Lane Materialized Readback Notes

State slice: `Phase 323 HSAI real formal command lane materialized output readback`.

## Scope

Phase 323 implements local filesystem materialization and readback for the Phase
322 real formal command-lane output contract.

This phase is implemented in `crates/hsai-agent-admission/src/lib.rs`.

It does not run SMT, Z3, Lean, COBALT, Aeneas, Hax, rust-lean, Coq, TLA+,
CBMC, or any model checker. It does not add solver scripts, checker scripts,
proof assistant setup files, package runtime files, process spawning, backend
runner implementation, proof artifacts, accepted evidence, Level2+ evidence,
score axes, benchmark evidence, or proof-authority claims.

## Implemented Surface

Phase 323 adds:

- `GatewayFormalRealCommandLaneOutputRequest`;
- `GatewayFormalRealCommandLaneOutputError`;
- `GatewayFormalRealCommandLaneRedactionReport`;
- `materialize_gateway_formal_real_command_lane_output_bundle`;
- `read_gateway_formal_real_command_lane_output_bundle`;
- staged filesystem writes for `gateway-formal-real-command-lane/*`;
- SHA-256 sidecar generation for every declared file;
- output-root validation and protected-root rejection;
- output-root, bundle-directory, declared-file, and sidecar symlink rejection;
- undeclared-file rejection;
- malformed declared JSON rejection;
- sidecar digest mismatch rejection;
- manifest semantic drift rejection;
- transcript/checker-transcript drift rejection;
- stdout/stderr summary drift rejection;
- redaction-report drift rejection;
- solver-verdict drift rejection;
- nonpromotion-report drift rejection;
- nonclaims drift rejection.

## Materialized Files

The readback path accepts only:

```text
gateway-formal-real-command-lane/manifest.json
gateway-formal-real-command-lane/source-execution-manifest.json
gateway-formal-real-command-lane/command-request.json
gateway-formal-real-command-lane/command-descriptor.json
gateway-formal-real-command-lane/obligation.smt2
gateway-formal-real-command-lane/obligation-binding.json
gateway-formal-real-command-lane/execution-transcript.json
gateway-formal-real-command-lane/stdout-summary.json
gateway-formal-real-command-lane/stderr-summary.json
gateway-formal-real-command-lane/solver-verdict.json
gateway-formal-real-command-lane/checker-transcript.json
gateway-formal-real-command-lane/redaction-report.json
gateway-formal-real-command-lane/nonpromotion-report.json
gateway-formal-real-command-lane/nonclaims.md
gateway-formal-real-command-lane/validation-report.json
```

Each declared file must have a `.sha256` sidecar. Any other file or directory
is rejected.

## Readback Boundary

Readback validates local artifact consistency only. It checks that:

- the source execution manifest remains the declared Phase 319 manifest;
- the command request and descriptor remain fixed to Phase 321/322 policy;
- the static SMT-LIB2 obligation file matches the declared obligation digest;
- the execution transcript and checker transcript remain not-run metadata;
- stdout and stderr summaries retain only bounded not-run summaries;
- the redaction report shows no raw solver trace, proof artifact, checker
  transcript, solver certificate, secret, or credential retention;
- the solver verdict remains `not_run`;
- the nonpromotion report creates no accepted evidence, Level2+ evidence, score
  axes, proof artifacts, checker transcript evidence, solver certificate
  evidence, semantic-correctness claim, production-readiness claim, SOTA claim,
  breakthrough claim, full-security claim, or authority grant.

## Tests

Phase 323 extends the focused suite:

```text
cargo test -p hsai-agent-admission gateway_formal_real_command_lane --quiet
```

The tests cover:

- valid materialization and readback;
- exact declared file and sidecar grammar;
- stale sidecar rejection;
- malformed declared JSON rejection;
- undeclared proof-artifact rejection;
- manifest promotion drift rejection.

## Claim Boundary

This phase supports only this claim:

```text
HSAI has a materialized local readback bundle for one future local SMT-LIB2 command lane over one tiny gateway invariant, with fail-closed digest, grammar, and nonpromotion checks.
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

Phase 324 defines the source-scan exception and execution preflight boundary for
one fixed local SMT-LIB2 command invocation.

Phase 325 may implement the inert execution-preflight metadata and the
corresponding source-scan exception. Phase 325 still must not run the solver.
The first real run requires a later phase after command execution policy,
readback, and source-scan exception are complete and reviewed.
