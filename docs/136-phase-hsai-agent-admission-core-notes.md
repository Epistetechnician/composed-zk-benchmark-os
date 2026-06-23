# Phase 136 HSAI Agent Admission Core Notes

Status: implemented for local, hermetic PCSM-governed agent admission core.

## State Slice

This phase touched only:

- `Cargo.toml`
- `crates/hsai-agent-admission/Cargo.toml`
- `crates/hsai-agent-admission/src/lib.rs`
- `docs/136-phase-hsai-agent-admission-core-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No other source, fixture, artifact, package-runtime, or output-bundle surface is
part of this phase.

## Implemented Surface

The new `hsai-agent-admission` crate implements the local admission surface
authorized by the Phase 134 boundary:

- `AgentAdmissionCandidate`
- `AgentAdmissionPolicy`
- `AgentAdmissionDecision`
- `AgentAdmissionJournalEntry`
- `AgentAdmissionJournal`
- `evaluate_admission`
- `accepted_claim_envelope`

The candidate is strict typed data derived from an `AgentCase`, a proposed
`ClaimEnvelope`, a provider response, or a benchmark-result proposal. The first
implemented handoff path accepts a bounded `ClaimEnvelope` proposal only after
policy validation and exposes it through the accepted decision. Agent-case
candidates can be admitted as local metadata, but they do not mint a claim
envelope by themselves.

The policy rejects:

- raw provider output that has not been strictly typed;
- provider direct-authority requests;
- claim-boundary elevation above the policy maximum;
- missing source artifact digests;
- missing required nonclaim labels;
- accepted-ledger mutation requests;
- score-axis population requests;
- external or formal evidence claims in the local-only admission path.

The journal is append-only in memory. It validates sequence numbers, previous
entry digests, candidate digests, decision digests, and replayed candidate
digests. Rejected and quarantined decisions can still be appended as audit
metadata without exposing an accepted claim envelope.

## Claim Boundary

This is a local admission core only. It is not the recoverable-ghost PCSM
runtime. It imports no recoverable-ghost artifact. It performs no provider call,
network access, credential access, operator-live flow, external replay,
official submission, accepted Evidence Ledger mutation, generated artifact
write, score-axis population, DCAP/PCCS/JWKS/JWT/TLS work, or benchmark
execution.

An accepted admission decision means only that a strict typed candidate passed
the local `AgentAdmissionPolicy`. It is not proof. It is not benchmark evidence.
It is not Level2+ evidence. It is not semantic correctness. It is not
production readiness. It is not global software-agent uniqueness.

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
cargo llvm-cov --workspace --all-features --summary-only
rg --files -g 'package.json' -g 'pnpm-lock.yaml' || true
```

No `pnpm` gate exists in this repository because there is no package runtime
surface.
