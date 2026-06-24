# Phase 147 HSAI Admission Provenance And Transaction Integrity Implementation Notes

Status: implemented for deterministic admission provenance and symmetric
protected-root safety.

## State Slice

This phase touched only:

- `crates/hsai-agent-admission/src/lib.rs`
- `crates/hsai-e2e-harness/src/lib.rs`
- `docs/147-phase-hsai-admission-provenance-transaction-integrity-implementation-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No Cargo metadata, dependency, fixture, committed generated bundle, package
runtime, source parser, command-line tool, or external runtime surface was
added.

## Deterministic Decision Provenance

`AgentAdmissionJournalEntry` now retains:

- the complete typed `AgentAdmissionCandidate`;
- the complete `AgentAdmissionPolicy`;
- the existing candidate, policy, source-digest, decision, and chain metadata.

`AgentAdmissionJournal::append_decision` now requires an explicit policy and
rejects any caller-supplied decision that differs from
`evaluate_admission(candidate, policy)`.

Journal validation independently verifies:

- candidate snapshot id and digest agreement;
- policy id and decision policy agreement;
- source artifact snapshot agreement;
- exact deterministic decision recomputation;
- decision digest, verdict-envelope, replay, sequence, and chain invariants.

The serialized journal schema changed intentionally. Strict semantic readback
rejects legacy or malformed entries that lack the required snapshots.

## PCSM Intake Digest Binding

Every valid Phase 140 PCSM bounded-proof candidate now receives:

```text
id = pcsm-bounded-proof-intake
sha256 = PcsmBoundedProofHandoffIntake::digest()
```

The mapper rejects a caller-supplied digest using that reserved id. Changes to
source commit, handoff digest, verifier statuses, counts, blocked state, or
authority fields therefore change the candidate digest and journal entry.

This is local provenance binding only. It is not source authentication or
actual committed-source intake.

## Protected-Root Overlap

Output-root validation now rejects protected path overlap in both directions:

- output equals protected;
- output is below protected;
- output is above protected.

The rejection occurs before output deletion. Overwrite cannot recursively
remove a protected descendant. Sibling paths remain allowed.

## Tests

The focused admission suite increased from 27 to 30 tests. Added coverage
proves:

- forged accepted and rejected decisions are rejected;
- candidate, policy, policy-id, and source snapshot drift are rejected;
- fully rehashed snapshot tampering fails semantic readback;
- valid accepted, rejected, and quarantined decisions still append;
- PCSM intake changes alter the candidate digest;
- reserved PCSM digest collision is rejected;
- overwrite of an ancestor containing a protected descendant is rejected;
- sibling output remains valid.

All HSAI e2e append callers now provide the policy explicitly.

Focused `cargo llvm-cov` measured:

- `97.19%` region coverage;
- `95.97%` function execution;
- `97.75%` line coverage.

These are local coverage measurements, not a 100% coverage claim.

## Deferred Findings

Phase 147 does not implement:

- source-kind structural shape validation;
- general artifact-id and zero-digest validation;
- PCSM count equality and exact verifier-name-set validation;
- duplicate JSON object-key rejection;
- backup/restore failure-atomic overwrite;
- descriptor-relative no-follow filesystem access or randomized staging;
- committed-source handoff parsing.

## Claim Boundary

This phase establishes deterministic local provenance and protected-root safety
only. It does not establish source authenticity, committed-source PCSM intake,
PCSM runtime correctness, external replication, provider or production
authority, accepted Evidence Ledger admission, benchmark evidence, official
submission, proof, semantic correctness, production readiness, score-axis
validity, Level2+ evidence, or full breakthrough-threshold admission.

The recoverable-ghost-states handoff remained staged and absent from `HEAD` on
2026-06-24. No source commit or handoff digest is admitted by this phase.

## Validation

Run from repository root:

```sh
cargo fmt --all -- --check
git diff --check
cargo test -p hsai-agent-admission
cargo test -p hsai-e2e-harness
cargo test -p hsai-e2e-harness --test claim_boundary_source_scan
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --all-features
cargo clippy --workspace --all-targets --all-features -- -D warnings
RUSTDOCFLAGS='-D warnings' cargo doc --workspace --all-features --no-deps
cargo llvm-cov -p hsai-agent-admission --all-features --summary-only
rg --files -g 'package.json' -g 'pnpm-lock.yaml' || true
```

No `pnpm` gate exists because this repository still has no package runtime
surface.
