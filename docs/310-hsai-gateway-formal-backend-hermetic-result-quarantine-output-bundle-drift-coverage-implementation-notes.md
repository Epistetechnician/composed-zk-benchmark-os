# Phase 310 HSAI Gateway Formal Backend Hermetic Result Quarantine Output-Bundle Drift Coverage Implementation Notes

State slice: `Phase 310 HSAI gateway formal backend hermetic result quarantine output-bundle drift coverage implementation`.

## Status

Complete for the focused local drift-coverage test slice.

## Purpose

Phase 309 defined the negative-test coverage required for the Phase 308
not-run result-quarantine output-bundle. Phase 310 implements that coverage as
focused Rust tests.

This phase does not add backend execution, does not spawn a process, and does
not change result-quarantine materialization behavior.

## Implemented Coverage

This phase adds focused tests for:

- protected output-root rejection;
- existing output-root overwrite rejection;
- missing declared sidecar rejection;
- malformed declared JSON rejection;
- nested descriptor-report bundle rejection;
- input-binding claim-boundary drift rejection;
- command-contract network drift rejection;
- execution-status process-spawned drift rejection;
- redaction-report credential-looking drift rejection;
- nonpromotion-report Level2 evidence drift rejection;
- validation-report accepted-evidence drift rejection.

This extends the Phase 308 coverage for valid materialization/readback, invalid
descriptor rejection before write, unsafe bundle id rejection, descriptor-report
manifest drift rejection, stale sidecar rejection, bounded-summary drift,
output-inventory drift, invariant-verdict drift, manifest escalation,
undeclared proof artifact rejection, and Unix symlink rejection.

## Local Meaning

The tests show only that the Phase 308 local reader fails closed for the covered
drift classes. They do not show that a backend can run, a solver certificate is
valid, a proof exists, or any evidence can be accepted.

## Validation

Required validation for this slice:

```text
cargo fmt --all -- --check
cargo test -p hsai-agent-admission gateway_formal_backend_hermetic_execution_result_quarantine_output_bundle
cargo test -p hsai-agent-admission gateway_formal_backend_hermetic_descriptor_report_output_bundle
cargo test -p hsai-agent-admission gateway_formal_backend_hermetic_execution_descriptor
cargo test -p zkbench-core --test repo_claim_boundary_docs --test repo_hygiene
git diff --check
find README.md AGENTS.md docs crates -type f -empty
pnpm run lint, if package.json exists
cargo test --workspace
```

## Next Slice

Phase 311 defines the docs-first process-spawn crossing contract for the tiny
local `local_smt_tiny_gateway_invariant` lane. It defines the exact executable
policy, no-shell argv, empty environment, timeout, output quarantine,
redaction, and nonpromotion requirements before any Rust runner implementation
is allowed.
