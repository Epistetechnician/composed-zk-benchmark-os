# Phase 326 HSAI Real Formal Command Lane Quarantined Fixed SMT Execution Notes

State slice: `Phase 326 HSAI real formal command lane quarantined fixed SMT-LIB2 execution`.

## Scope

Phase 326 implements the first bounded process-spawn crossing for the Phase
321-325 real formal command lane. The crossing is limited to one fixed local
executable path supplied to `run_gateway_formal_real_command_lane_fixed_smt_process`
after Phase 325 preflight authorization and executable digest verification.

This phase does not implement a generic backend runner, caller-controlled
executable paths, caller-controlled argv, shell execution, inherited
environment, stdin, network access, solver scripts, checker scripts, proof
assistant setup files, generated proof artifacts, generated checker
transcripts, generated solver certificates, accepted evidence, Level2+
evidence, score axes, benchmark evidence, official benchmark submission,
semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, full-security claims, or authority to execute an action.

## Implemented Surface

Phase 326 adds local Rust execution metadata under
`crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalRealCommandLaneFixedSmtStreamSummary`;
- `GatewayFormalRealCommandLaneFixedSmtProcessOutput`;
- `GatewayFormalRealCommandLaneFixedSmtProcessError`;
- `run_gateway_formal_real_command_lane_fixed_smt_process`;
- `gateway_formal_real_command_lane_fixed_smt_process_plan`.

The execution function:

- requires `process_spawn_authorized = true` from the Phase 325 preflight;
- reads the fixed executable and checks its SHA-256 digest against the preflight;
- uses direct `std::process::Command::new(fixed_executable)`;
- applies the fixed argv template from the validated command descriptor;
- clears the environment;
- sets stdin to null;
- pipes stdout and stderr;
- enforces the descriptor timeout;
- records bounded redacted stream summaries;
- classifies solver-like stdout labels `unsat`, `sat`, and `unknown`;
- sets all proof, evidence, score, semantic-correctness, production-readiness,
  SOTA, full-security, and authority flags to false.

The focused test uses the current test binary as a hermetic fixed executable
that prints `unsat`. That test proves the process-crossing and quarantine path
without requiring a system Z3 installation and without claiming the fixture is
formal proof.

## Source-Scan Boundary

The HSAI source scan continues to allow only the historical fixture-runner
process lines and the single Phase 326 line inside
`run_gateway_formal_real_command_lane_fixed_smt_process`:

```text
let mut command = std::process::Command::new(fixed_executable);
```

Any arbitrary backend runner, caller-provided argv, shell command, inherited
environment, stdin, network API, or unrelated process API remains forbidden.

## Validation

Phase 326 adds focused tests for:

- fixed executable digest verification;
- direct process spawn over the authorized preflight;
- bounded stdout/stderr quarantine;
- solver-like `unsat` classification without certificate or proof authority;
- explicit nonpromotion flags after execution;
- digest mismatch rejection before spawn;
- source-scan confinement of the process API exception.

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
HSAI has a local quarantined fixed-process SMT-LIB2 execution lane that can run one preflight-authorized local executable and classify bounded solver-like output without evidence promotion.
```

It does not support SOTA, full security, semantic correctness, production
readiness, accepted formal evidence, Level2+ formal evidence, backend score
axes, a system Z3 proof, a Lean proof, a COBALT containment proof,
Rust-to-Lean extraction, proof artifacts as accepted evidence, checker
transcripts as accepted evidence, solver certificates as accepted evidence,
source correspondence proof, accepted Evidence Ledger mutation, or authority to
execute an action.

## Next Slice

Phase 327 materializes and reads back the Phase 326 quarantined fixed-SMT
execution output bundle with digest sidecars and promotion rejection. Phase 328
may define a docs-first formal-evidence promotion boundary for that quarantined
output, but must not create accepted evidence, Level2+ evidence, score axes,
semantic correctness claims, production-readiness claims, SOTA claims,
full-security claims, or action authority.
