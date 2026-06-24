# Phase 150 HSAI Admission Candidate Semantic Closure Boundary Spec

Status: docs-first boundary for future fail-closed candidate identity, claim
boundary, envelope export, and reserved PCSM digest placement validation.

## State Slice

This documentation-only phase may touch only:

- `docs/150-phase-hsai-admission-candidate-semantic-closure-boundary-spec.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

It does not authorize Rust source changes, tests, Cargo metadata changes,
`Cargo.lock` changes, generated output, committed bundles, source-repo parsing,
PCSM runtime import, provider calls, network access, credentials, accepted
Evidence Ledger mutation, official submission, external replay, score-axis
population, or Level2+ evidence.

## Problem

Phase 149 validates source payload shape, artifact identity, PCSM counts, and
verifier names. Four candidate-level semantic gaps remain.

### Candidate Identity

`AdmissionCandidateId` and `SubjectId` are public string wrappers. Admission
currently permits empty, whitespace-only, or whitespace-padded identities.
Candidate IDs are journal and replay identities, so ambiguous values must fail
before acceptance.

### Source-Kind Claim Boundary

The current evaluator checks only whether the requested claim boundary exceeds
the policy maximum. A malformed candidate can declare a boundary that does not
match its source kind while still staying below the policy ceiling.

### Accepted Envelope Export

The evaluator copies any candidate envelope into an accepted decision. Phase
149 rejects currently known payload-shape violations, but the export rule
should be explicit: only an accepted `ClaimEnvelopeProposal` may export an
envelope.

### Reserved PCSM Digest Placement

Phase 147 makes `pcsm-bounded-proof-intake` a reserved digest ID in the PCSM
mapper, but a manually constructed candidate can omit it from a PCSM source or
place it on a non-PCSM source.

## Required Candidate Identity Contract

A future implementation must reject:

- an empty candidate ID;
- a whitespace-only candidate ID;
- leading or trailing candidate-ID whitespace;
- candidate IDs containing `/`, `\`, or `..`;
- candidate IDs containing characters outside ASCII alphanumeric, `-`, `_`,
  and `.`;
- an empty, whitespace-only, or whitespace-padded subject ID.

Subject IDs are not restricted to the candidate-ID portable-segment alphabet
in this phase. Existing HSAI subject semantics remain owned by
`hsai-claim-envelope`; this phase requires only nonempty trimmed identity.

## Required Source-Kind Boundary Contract

The requested claim boundary must equal:

| Source kind | Exact boundary |
| --- | --- |
| `AgentCase` | `LocalOnly` |
| `ClaimEnvelopeProposal` | `Level1Local` |
| `ProviderResponse` | `LocalOnly` |
| `BenchmarkResultProposal` | `LocalOnly` |
| `PcsmBoundedProofHandoff` | `LocalOnly` |

This exact source-shape check is separate from the policy ceiling. A candidate
must satisfy both.

`ProviderResponse` remains non-admissible before typed conversion under Phase
149. The boundary rule does not grant raw provider authority.

## Required Envelope Export Contract

An accepted decision may retain an envelope only when:

```text
candidate.source_kind == ClaimEnvelopeProposal
candidate.proposed_envelope is present
decision.verdict == Accepted
```

Every other source kind must produce `accepted_envelope=None`, even if a future
bug or malformed state bypasses an earlier shape check.

Existing journal validation must continue to reject retained envelopes on
rejected or quarantined decisions.

## Required Reserved PCSM Digest Contract

The logical artifact ID `pcsm-bounded-proof-intake` must:

- be present on every `PcsmBoundedProofHandoff` candidate;
- be absent from every non-PCSM candidate;
- remain nonzero and conflict-free under Phase 149 artifact validation.

Generic candidate validation cannot prove that the reserved digest equals a
particular intake because the candidate does not retain the intake object.
The Phase 147 mapper remains responsible for binding
`PcsmBoundedProofHandoffIntake::digest()`.

This phase must not add a second PCSM digest field or change serialized
candidate shape.

## Deterministic Reason Ordering

Future identity reasons must precede source-kind reasons. Source-kind boundary
and reserved-ID reasons must follow source payload-shape reasons and precede
general artifact and policy reasons. Stable ordering is required because
decision digests are journaled.

## Required Future Tests

A later implementation phase must prove:

- empty, whitespace-only, padded, path-like, traversal-like, and
  invalid-character candidate IDs fail closed;
- empty, whitespace-only, and padded subjects fail closed;
- each source kind accepts only its exact claim boundary;
- lower as well as higher source-boundary drift fails closed;
- only an accepted `ClaimEnvelopeProposal` exports an envelope;
- non-envelope source kinds cannot export an accepted envelope;
- the reserved PCSM digest is required on PCSM candidates;
- the reserved PCSM digest is forbidden on non-PCSM candidates;
- the existing PCSM mapper still installs the exact intake digest;
- valid case, envelope, and PCSM candidates remain accepted under their
  existing policies;
- journal recomputation and semantic readback reject fully rehashed candidate
  semantic drift;
- normal tests remain process-free, network-free, and source-repo independent.

## Compatibility Rules

No public struct field, constructor signature, serialized schema, or hash tag
changes are required.

Previously accepted malformed identities, boundary drift, or reserved-ID
misplacement will intentionally become rejected. Existing valid constructor
outputs remain unchanged.

New deterministic `AdmissionReason` values may be added. Existing exact reason
assertions must change only where the candidate is intentionally malformed
under this contract.

## Deferred Findings

This phase does not authorize:

- duplicate JSON object-key detection;
- raw-array duplicate detection before `BTreeSet` normalization;
- failure-atomic overwrite backup and restore;
- descriptor-relative no-follow filesystem access;
- randomized staging paths;
- committed-source handoff parsing.

Those surfaces require separate named boundaries.

## Claim Boundary

These checks establish local candidate semantic consistency only. They do not
establish source authenticity, committed-source PCSM intake, source journal
validity, PCSM runtime correctness, external replication, provider or
production authority, accepted Evidence Ledger admission, benchmark evidence,
official submission, proof, semantic correctness, production readiness,
score-axis validity, Level2+ evidence, or full breakthrough-threshold
admission.

## Future Implementation Exit Criteria

A later implementation phase must:

- touch only `crates/hsai-agent-admission/src/lib.rs`,
  `crates/hsai-e2e-harness/src/lib.rs`, phase notes, and navigation/status docs
  unless a separate phase broadens the slice;
- add no dependency or Cargo metadata change;
- preserve existing valid constructors and valid PCSM flow;
- preserve deterministic hashing and reason ordering;
- preserve Phase 147 decision recomputation and Phase 149 semantic validation;
- keep all tests hermetic;
- create no committed generated bundle;
- parse no recoverable-ghost file;
- create no accepted evidence or stronger claim.

## Non-Goals

This boundary does not permit source parsing, source git inspection, source
verifier execution, PCSM runtime import, recoverable-ghost artifact import,
provider calls, network access, credentials, external replay, official
submission, accepted Evidence Ledger mutation, score-axis population,
DCAP/PCCS/JWKS/JWT/TLS changes, formal evidence, Level2+ evidence, production
readiness, semantic correctness, proof, benchmark evidence, global
software-agent uniqueness, or 100% coverage claims.
