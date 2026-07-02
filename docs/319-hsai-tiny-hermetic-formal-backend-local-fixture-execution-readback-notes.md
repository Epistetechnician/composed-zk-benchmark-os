# Phase 319 HSAI Tiny Hermetic Formal-Backend Local Fixture Execution Readback Notes

State slice: `Phase 319 HSAI tiny hermetic formal-backend local fixture execution readback contract`.

## Scope

Phase 319 implements the narrow Phase 318 crossing for the Phase 317 tiny
hermetic formal-backend adapter bundle. It adds one local fixture-process
execution readback contract in `hsai-agent-admission`.

The target remains exactly one property:

```text
attestation_challenge_binding_deterministic_input_sensitive
```

The backend lane label remains:

```text
local_smt_tiny_gateway_invariant
```

This phase executes only a fixed local fixture command through the existing
test-binary fixture path. It does not execute Lean, SMT/Z3, COBALT, Aeneas,
Hax, rust-lean, Coq, TLA+, CBMC, or a model checker as proof authority.

## Implemented Surface

Phase 319 adds:

- `GatewayFormalBackendTinyHermeticExecutionOutputRequest`.
- `GatewayFormalBackendTinyHermeticExecutionTranscript`.
- `GatewayFormalBackendTinyHermeticExecutionNonpromotionReport`.
- `GatewayFormalBackendTinyHermeticExecutionValidationReport`.
- `GatewayFormalBackendTinyHermeticExecutionOutputManifest`.
- `GatewayFormalBackendTinyHermeticExecutionOutputError`.
- Declared `gateway-formal-backend-tiny-hermetic-execution/*` output files and
  SHA-256 sidecars.
- Staged materialization under a caller-selected output root.
- Protected-root, symlink, file, overwrite, and undeclared-file rejection.
- Source Phase 317 adapter-manifest revalidation before process spawn.
- Fixed direct-process execution using the Phase 317 command descriptor argv.
- Cleared environment, no stdin, no shell, piped stdout/stderr, and bounded
  stdout/stderr summaries.
- Redaction-report validation.
- Nonpromotion-report validation.
- Execution transcript semantic readback.
- Manifest digest and semantic readback.
- Nonclaim Markdown readback.

The focused tests cover:

- Successful materialization and readback for the local fixture process.
- Missing operator acknowledgement rejection before process spawn.
- Phase 317 source-adapter manifest promotion drift rejection before process
  spawn.
- Manifest escalation drift rejection after materialization.
- Stale sidecar rejection after materialization.
- Undeclared proof-artifact rejection after materialization.

## Declared Output Files

The output bundle declares exactly:

```text
gateway-formal-backend-tiny-hermetic-execution/manifest.json
gateway-formal-backend-tiny-hermetic-execution/source-adapter-manifest.json
gateway-formal-backend-tiny-hermetic-execution/adapter-request.json
gateway-formal-backend-tiny-hermetic-execution/fixture-input.json
gateway-formal-backend-tiny-hermetic-execution/command-descriptor.json
gateway-formal-backend-tiny-hermetic-execution/execution-transcript.json
gateway-formal-backend-tiny-hermetic-execution/stdout-summary.json
gateway-formal-backend-tiny-hermetic-execution/stderr-summary.json
gateway-formal-backend-tiny-hermetic-execution/redaction-report.json
gateway-formal-backend-tiny-hermetic-execution/nonpromotion-report.json
gateway-formal-backend-tiny-hermetic-execution/nonclaims.md
gateway-formal-backend-tiny-hermetic-execution/validation-report.json
```

Every declared file has a `.sha256` sidecar. Any undeclared child under the
bundle directory is rejected.

## Evidence Meaning

This phase can support only this claim:

```text
HSAI has a tiny hermetic local formal-backend fixture execution readback lane for one gateway invariant, with explicit nonpromotion and quarantine-only output.
```

This is local regression evidence for the execution wrapper and readback
contract. It is not proof authority.

## Nonclaims

Phase 319 does not support:

- `HSAI is SOTA.`
- `HSAI is fully secure.`
- `HSAI proves semantic correctness.`
- `HSAI is production ready.`
- `HSAI has accepted formal evidence.`
- `HSAI has Level2+ formal evidence.`
- `HSAI has backend score axes.`
- `HSAI has Lean proof artifacts.`
- `HSAI has SMT/Z3 proof artifacts.`
- `HSAI has COBALT proof artifacts.`
- `HSAI has checker transcripts.`
- `HSAI has solver certificates.`
- `HSAI has authority to execute downstream actions.`

## Anti-Goals

This phase does not permit:

- Generic backend runners.
- Caller-supplied executable paths.
- Caller-supplied argv.
- Shell execution.
- Inherited environment.
- Stdin.
- Network access.
- Package runtime files.
- External repo clones.
- Vendored source.
- Lean execution.
- SMT/Z3 execution.
- COBALT execution.
- Aeneas/Hax/rust-lean execution.
- Coq/TLA+/CBMC/model-checker execution.
- Solver scripts.
- Checker scripts.
- Proof artifact creation.
- Checker transcript creation.
- Solver-certificate creation.
- Accepted Evidence Ledger mutation.
- Level2+ evidence.
- Score-axis population.
- Benchmark evidence.
- Official benchmark submission.
- Live provider calls.
- Credential handling.
- Semantic-correctness claims.
- Production-readiness claims.
- SOTA claims.
- Breakthrough claims.
- Full-security claims.
- Authority to execute an action.

## Validation

Targeted validation:

```text
cargo test -p hsai-agent-admission gateway_formal_backend_tiny_hermetic_execution -- --nocapture
```

Full validation remains:

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

Phase 320 completed the hardening pass for the Phase 319 local fixture
execution readback lane with negative tests for malformed declared JSON,
symlink shapes, output-root overwrite rejection, and summary/redaction/
nonpromotion drift.

The next responsible slice is Phase 321: a docs-first boundary for a real
Lean/SMT/COBALT command lane. It must define the exact property, backend mode,
artifact grammar, checker transcript grammar, quarantine readback contract, and
nonpromotion rules before any real proof assistant, solver, or COBALT command
is allowed to run.
