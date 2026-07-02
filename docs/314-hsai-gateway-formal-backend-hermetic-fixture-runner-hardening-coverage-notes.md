# Phase 314 HSAI Gateway Formal Backend Hermetic Fixture-Runner Hardening Coverage Notes

State slice: `Phase 314 HSAI gateway formal backend hermetic fixture-runner hardening coverage`.

## Status

Complete for focused local negative coverage over the Phase 313 fixture-runner
crossing.

## Purpose

Phase 313 crossed the process boundary with one fixed local fixture process.
Phase 314 hardens that boundary by testing failure modes and readback rejection
paths around the executed-fixture quarantine bundle.

This phase still does not run Lean, SMT, Z3, COBALT, Aeneas, Hax, rust-lean,
Coq, TLA+, CBMC, or a model checker as proof authority. It does not create proof
artifacts, checker transcripts, solver certificates, accepted evidence, Level2+
evidence, score axes, semantic-correctness claims, production-readiness claims,
SOTA claims, breakthrough claims, full-security claims, or action authority.

## Implemented Surface

This phase adds focused coverage for:

- nonzero fixture-process exit classification;
- timeout fixture-process classification;
- bounded stdout truncation without raw stream retention;
- stale sidecar rejection;
- declared summary drift rejection through manifest digest bindings;
- redaction-report drift rejection through manifest digest bindings;
- undeclared proof-artifact rejection;
- bundle-directory symlink rejection.

The only source hardening change is a readback guard that rejects a symlinked or
non-directory `gateway-formal-backend-hermetic-execution-result-quarantine`
bundle directory before declared-file validation.

## Local Meaning

The output means only:

`The Phase 313 local fixture-runner quarantine reader rejects additional malformed
or claim-escalating local bundles, and the fixture runner classifies bounded
fixture-process failures without promoting evidence.`

It does not mean:

- a formal solver ran;
- a solver certificate is valid;
- a Lean proof exists;
- a COBALT containment proof exists;
- Rust-to-Lean extraction succeeded;
- repository-scale verification succeeded;
- accepted Evidence Ledger state changed;
- Level2+ evidence exists;
- score axes are populated;
- semantic correctness is proved;
- HSAI is production ready;
- HSAI is SOTA;
- HSAI is a breakthrough;
- HSAI is fully secure;
- gateway action authority exists.

## Validation

Required validation for this slice:

```text
cargo fmt --all -- --check
cargo test -p hsai-agent-admission gateway_formal_backend_hermetic_fixture_runner
cargo test -p hsai-agent-admission gateway_formal_backend_hermetic_process_spawn_interface
cargo test -p hsai-agent-admission gateway_formal_backend_hermetic_execution_result_quarantine_output_bundle
cargo test -p hsai-agent-admission gateway_formal_backend_hermetic_descriptor_report_output_bundle
cargo test -p hsai-agent-admission gateway_formal_backend_hermetic_execution_descriptor
cargo test -p hsai-e2e-harness --test claim_boundary_source_scan
cargo test -p zkbench-core --test repo_claim_boundary_docs --test repo_hygiene
git diff --check
find README.md AGENTS.md docs crates -type f -empty
pnpm run lint, if package.json exists
cargo test --workspace
```

## Next Slice

Phase 315 implemented Mesh repo-patch admission backend compatibility. See
`docs/315-hsai-mesh-repo-patch-admission-backend-compatibility-notes.md`.

Phase 316 then returned to the formal-backend lane with a docs-first tiny
hermetic adapter contract boundary. See
`docs/316-hsai-tiny-hermetic-formal-backend-adapter-contract-boundary.md`.
