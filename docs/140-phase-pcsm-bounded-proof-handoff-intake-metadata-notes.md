# Phase 140 PCSM Bounded-Proof Handoff Intake Metadata Notes

Status: implemented for local, hermetic PCSM bounded-proof handoff intake
metadata validation.

## State Slice

This phase touched only:

- `crates/hsai-agent-admission/src/lib.rs`
- `docs/140-phase-pcsm-bounded-proof-handoff-intake-metadata-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No other source, fixture, artifact, package-runtime, or output-bundle surface is
part of this phase.

## Implemented Surface

The `hsai-agent-admission` crate now includes a local structured intake surface
for PCSM CL12 bounded-proof handoff metadata:

- `PcsmSourceRepoStatus`
- `PcsmVerifierOutcome`
- `PcsmVerifierStatus`
- `PcsmBoundedProofHandoffIntake`
- `PcsmHandoffIntakeError`
- `pcsm_bounded_proof_required_nonclaims`
- `validate_pcsm_bounded_proof_handoff_intake`
- `pcsm_bounded_proof_handoff_candidate`

The validator requires a clean committed source identity, the declared
`docs/pcsm-cl12-bounded-proof-handoff.md` handoff path, a nonzero SHA-256
handoff digest, required source verifier statuses, bounded-proof admission,
`threshold_admitted=false`, `replication_admission_status=blocked_preflight_only`,
`blocked_item=live_external_runtime_replication`, PCSM accepted and rejected
counts, PCSM journal evidence, digest-only source artifact references, and the
required nonclaims.

The candidate mapper produces an `AdmissionSourceKind::PcsmBoundedProofHandoff`
candidate with `LocalOnly` claim boundary and no accepted claim envelope. It is
local admission metadata only.

## Claim Boundary

This phase does not parse the current recoverable-ghost-states markdown file
directly. It does not read the filesystem, inspect git state, run
recoverable-ghost commands, import PCSM runtime code, import recoverable-ghost
artifacts, materialize admission journals, create generated output bundles,
mutate accepted Evidence Ledgers, run external replay, perform provider calls,
populate score axes, or create Level2+ evidence.

The current recoverable-ghost-states handoff observed during this phase was
still staged or dirty, so it is intentionally not treated as a stable intake
source. A future actual intake must bind a committed source revision and a
digest-stable handoff.

## Rejection Coverage

Focused tests cover:

- valid bounded handoff metadata becoming a local admission candidate without
  an accepted envelope;
- staged or dirty source status rejection;
- invalid source commit rejection;
- unsafe handoff path rejection;
- missing handoff digest rejection;
- full threshold admission rejection;
- live-external replication escalation rejection;
- provider and production authority rejection;
- raw provider payload commitment rejection;
- accepted-ledger mutation, official submission, external replay, score-axis,
  and Level2+ requests;
- missing verifier status;
- failed verifier status;
- missing required nonclaim;
- missing source artifact digest;
- missing PCSM accepted/rejected counts.

## Validation

Run from repository root:

```sh
cargo fmt --all -- --check
git diff --check
cargo test -p hsai-agent-admission
cargo test -p hsai-e2e-harness --test claim_boundary_source_scan
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --all-features
cargo clippy --workspace --all-targets --all-features -- -D warnings
RUSTDOCFLAGS='-D warnings' cargo doc --workspace --all-features --no-deps
rg --files -g 'package.json' -g 'pnpm-lock.yaml' || true
```

No `pnpm` gate exists in this repository because there is no package runtime
surface.
