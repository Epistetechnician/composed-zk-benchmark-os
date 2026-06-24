# Phase 149 HSAI Admission Input Semantic Integrity Implementation Notes

Status: implemented for local admission candidate and PCSM intake semantic
validation.

## State Slice

This phase touched only:

- `crates/hsai-agent-admission/src/lib.rs`
- `docs/149-phase-hsai-admission-input-semantic-integrity-implementation-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No Cargo metadata, dependency, fixture, committed generated bundle, package
runtime, source parser, command-line tool, or external runtime surface was
added.

## Source-Kind Shape Validation

`evaluate_admission` now checks source shape before policy checks.

- `AgentCase` requires one case, forbids an envelope, and requires subject
  agreement.
- `ClaimEnvelopeProposal` forbids a case and requires one envelope.
- `ProviderResponse` forbids case and envelope payload injection and cannot be
  directly accepted as a falsely strict candidate.
- `BenchmarkResultProposal` forbids case and envelope payloads.
- `PcsmBoundedProofHandoff` forbids case and envelope payloads.

Malformed strict candidates are rejected. Non-strict raw provider candidates
remain quarantined. Existing decision recomputation means journal append and
semantic readback inherit the stricter validation without a schema change.

## Artifact Digest Validation

Candidate and PCSM intake artifact digests now share one deterministic
validator.

Valid logical IDs:

- are nonempty;
- contain no leading or trailing whitespace;
- contain only ASCII alphanumeric, `-`, `_`, and `.` characters;
- contain no `..` sequence.

Zero SHA-256 values are rejected. Different hashes under one logical ID are
rejected. Existing valid logical IDs and the reserved Phase 147
`pcsm-bounded-proof-intake` binding remain unchanged.

## PCSM Count Validation

The intake validator preserves the existing nonzero count requirement and now
also requires:

```text
checked_add(pcsm_accepted, pcsm_rejected) == pcsm_inputs
pcsm_journal_entries == pcsm_inputs
```

Checked-add overflow and relational mismatch have separate error variants.
These are metadata consistency checks only; they do not inspect a source
journal.

## PCSM Verifier Validation

Verifier statuses are indexed by exact required name. The validator now
rejects:

- unknown names;
- representable duplicate names, including conflicting pass/fail statuses;
- missing required names;
- failing required outcomes.

All five required statuses must be present and pass. An exact duplicate status
object collapses under the existing typed `BTreeSet`; Phase 149 does not change
the serialized field type or add a new raw intake parser.

## Tests

The focused admission suite increased from 30 to 34 tests. Added adversarial
coverage proves:

- missing and injected source payloads fail closed;
- AgentCase subject drift fails closed;
- raw provider candidates cannot bypass typed conversion;
- benchmark and PCSM metadata candidates cannot inject envelopes;
- empty, whitespace-padded, path-like, traversal-like, and invalid-character
  artifact IDs fail closed;
- zero and conflicting artifact digests fail closed;
- PCSM count mismatch, journal-count mismatch, and overflow fail closed;
- duplicate, failing, and unknown verifier statuses fail closed;
- the valid PCSM intake, local admission, journal, and semantic readback path
  remains valid.

Focused `cargo llvm-cov` measured:

- `97.20%` region coverage;
- `95.45%` function execution;
- `97.90%` line coverage.

These are local coverage measurements, not a 100% coverage claim.

## Deferred Findings

Phase 149 does not implement:

- candidate ID or subject nonempty validation beyond AgentCase subject
  agreement;
- exact source-kind claim-boundary coupling;
- reserved PCSM artifact-ID rejection on manually constructed non-PCSM
  candidates;
- duplicate JSON object-key detection;
- raw-array duplicate detection before `BTreeSet` normalization;
- backup/restore failure-atomic overwrite;
- descriptor-relative no-follow filesystem access or randomized staging;
- committed-source handoff parsing.

## Claim Boundary

This phase establishes deterministic local typed-input consistency only. It
does not establish source authenticity, committed-source PCSM intake, source
journal validity, PCSM runtime correctness, external replication, provider or
production authority, accepted Evidence Ledger admission, benchmark evidence,
official submission, proof, semantic correctness, production readiness,
score-axis validity, Level2+ evidence, or full breakthrough-threshold
admission.

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
