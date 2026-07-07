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
handoff digest, a matching `source-handoff` artifact digest entry, required
source verifier statuses, bounded-proof admission, `threshold_admitted=false`,
`replication_admission_status=blocked_preflight_only`,
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

The recoverable-ghost-states handoff originally observed during this phase was
still staged or dirty, so the initial Phase 140 intake did not treat it as a
stable source. That external blocker was later resolved by committing the
bounded proof handoff in recoverable-ghost-states at:

```text
commit=8b342fe159324395174a149052b9ea1d937a50ce
path=docs/pcsm-cl12-bounded-proof-handoff.md
sha256=93e07a250c9a6a5f530d02f07095074e7df8a5b5ce7e8e2dfa6e5feb376ea149
state_slice=pcsm-cl12-bounded-proof-package
schema=pcsm-cl12-bounded-proof-handoff-v1
```

That commit resolves the dirty-source intake blocker. It does not change the
Phase 140 claim boundary: the HSAI intake remains local metadata validation
only and does not import PCSM runtime code, create accepted evidence, or raise
the claim boundary above `LocalOnly`.

## Rejection Coverage

Focused tests cover:

- valid bounded handoff metadata becoming a local admission candidate without
  an accepted envelope;
- staged or dirty source status rejection;
- invalid source commit rejection;
- unsafe handoff path rejection;
- missing handoff digest rejection;
- missing or mismatched `source-handoff` artifact digest rejection;
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
