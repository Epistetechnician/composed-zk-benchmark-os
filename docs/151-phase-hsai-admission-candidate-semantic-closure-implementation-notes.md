# Phase 151 HSAI Admission Candidate Semantic Closure Implementation Notes

Status: implemented for local candidate identity, exact source boundary,
authenticated envelope export, and reserved PCSM digest placement.

## State Slice

This phase touched only:

- `crates/hsai-agent-admission/src/lib.rs`
- `crates/hsai-e2e-harness/src/lib.rs`
- `docs/150-phase-hsai-admission-candidate-semantic-closure-boundary-spec.md`
- `docs/151-phase-hsai-admission-candidate-semantic-closure-implementation-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No Cargo metadata, dependency, fixture, committed generated bundle, package
runtime, source parser, command-line tool, or external runtime surface was
added.

## Candidate Identity

Admission now rejects candidate IDs that are empty, padded, path-like,
traversal-like, or contain characters outside ASCII alphanumeric, `-`, `_`,
and `.`.

Subjects must be nonempty and equal their trimmed value. Subject alphabet
semantics remain owned by `hsai-claim-envelope`.

## Exact Source Boundaries

Admission now requires:

| Source kind | Exact boundary |
| --- | --- |
| `AgentCase` | `LocalOnly` |
| `ClaimEnvelopeProposal` | `Level1Local` |
| `ProviderResponse` | `LocalOnly` |
| `BenchmarkResultProposal` | `LocalOnly` |
| `PcsmBoundedProofHandoff` | `LocalOnly` |

`BenchmarkResultProposal` remains conservative `LocalOnly` metadata because the
shipped model has no typed benchmark-result payload or envelope constructor.
`ProviderResponse` remains rejected or quarantined before typed conversion.

Exact source-boundary validation is independent of the policy maximum, so both
lower and higher semantic drift fail closed.

## Authenticated Envelope Export

`evaluate_admission` now creates `accepted_envelope` only for an accepted
`ClaimEnvelopeProposal`.

The public `accepted_claim_envelope` helper now requires candidate, policy, and
decision inputs. It returns an envelope only when the decision exactly equals
fresh deterministic evaluation of that candidate and policy. The former
decision-only accessor was removed because public decision fields can be
manually constructed.

HSAI e2e callers now provide candidate and policy explicitly.

## Reserved PCSM Digest Placement

Generic candidate evaluation now requires `pcsm-bounded-proof-intake` on every
`PcsmBoundedProofHandoff` candidate and forbids that reserved ID on every other
source kind.

The Phase 147 mapper still supplies the exact
`PcsmBoundedProofHandoffIntake::digest()`. Generic candidate validation checks
placement only; it does not authenticate an arbitrary manually constructed
digest.

## Boundary Corrections

The Phase 150 spec now states accurately that:

- replay is keyed by candidate digest, not candidate ID;
- exact provider boundary removes only the boundary-mismatch reason and does
  not make raw provider input admissible;
- fully rehashed candidate drift with a newly recomputed rejected decision is
  valid rejected-audit history;
- deterministic reason order is identity, payload shape, source boundary,
  reserved PCSM placement, artifacts, strict typing, then policy and authority.

## Tests

The focused admission suite increased from 34 to 36 tests. Added coverage
proves:

- invalid candidate IDs and subjects fail closed;
- every source kind is checked against all four claim boundaries;
- provider exact-boundary input remains non-admissible;
- reserved PCSM digest omission and non-PCSM placement fail closed;
- valid mapped PCSM intake retains the exact digest;
- forged accepted decisions cannot export through the authenticated helper;
- accepted case and PCSM metadata candidates export no envelope;
- valid envelope proposals and existing HSAI e2e flows remain accepted.

Focused `cargo llvm-cov` measured:

- `97.49%` region coverage;
- `95.62%` function execution;
- `98.09%` line coverage.

These are local coverage measurements, not a 100% coverage claim.

## Deferred Findings

Phase 151 does not implement:

- cryptographic validation of an arbitrary manually constructed PCSM reserved
  digest;
- duplicate JSON object-key detection;
- raw-array duplicate detection before `BTreeSet` normalization;
- backup/restore failure-atomic overwrite;
- descriptor-relative no-follow filesystem access or randomized staging;
- committed-source handoff parsing.

## Claim Boundary

This phase establishes deterministic local candidate semantic consistency only.
It does not establish source authenticity, committed-source PCSM intake, source
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
