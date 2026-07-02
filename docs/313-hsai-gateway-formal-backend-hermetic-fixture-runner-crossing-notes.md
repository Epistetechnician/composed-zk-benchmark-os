# Phase 313 HSAI Gateway Formal Backend Hermetic Fixture-Runner Crossing Notes

State slice: `Phase 313 HSAI gateway formal backend hermetic fixture-runner crossing`.

## Status

Complete for the first bounded local fixture-process crossing.

## Purpose

Phase 312 added a no-default-runner policy interface. Phase 313 crosses the
process-spawn boundary in the narrowest possible form: one fixed local fixture
process, direct execution with no shell, no inherited environment, no stdin,
bounded stdout/stderr summaries, and quarantine-only output.

This phase does not execute Lean, SMT, Z3, COBALT, Aeneas, Hax, rust-lean,
Coq, TLA+, CBMC, or a model checker. It does not create proof artifacts,
checker transcripts, solver certificates, accepted evidence, Level2+ evidence,
score axes, semantic-correctness claims, production-readiness claims, SOTA
claims, full-security claims, or authority.

## Implemented Surface

This phase adds:

- Phase 313 schema/state/claim-boundary constants;
- `GatewayFormalBackendHermeticFixtureRunnerRequest`;
- `GatewayFormalBackendHermeticFixtureRunnerReport`;
- `GatewayFormalBackendHermeticFixtureRunnerOutput`;
- `GatewayFormalBackendHermeticFixtureRunnerError`;
- a direct-process fixture runner using a policy-selected command path, no
  shell, `env_clear`, null stdin, piped stdout/stderr, and timeout handling;
- bounded stdout/stderr summary generation that retains digests and counts, not
  raw stream text;
- a Phase 313 materializer for the existing quarantine namespace;
- a Phase 313 readback validator for executed-fixture quarantine outputs;
- a narrow cross-crate source-scan exception for only the Phase 313 `Stdio`
  import and `Command::new` call in `hsai-agent-admission`;
- focused tests for successful fixture-process execution, pre-spawn rejection
  on missing operator acknowledgement, pre-spawn rejection on invalid Phase 312
  interface, and readback rejection on claim escalation.

The Phase 308 not-run result-quarantine reader remains unchanged and still
rejects Phase 313 executed-fixture bundles.

## Local Meaning

The output means only:

`A fixed local fixture process was spawned under the Phase 312 no-shell policy,
and its bounded redacted summaries were quarantined without evidence or claim
promotion.`

It does not mean:

- a formal solver ran;
- a solver certificate is valid;
- a Lean proof exists;
- a COBALT containment proof exists;
- Rust-to-Lean extraction succeeded;
- repository-scale verification succeeded;
- a checker transcript is accepted evidence;
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

Phase 314 implemented focused hardening coverage for the fixture-runner
crossing. See
`docs/314-hsai-gateway-formal-backend-hermetic-fixture-runner-hardening-coverage-notes.md`.
