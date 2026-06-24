# Phase 148 HSAI Admission Input Semantic Integrity Boundary Spec

Status: docs-first boundary for future fail-closed admission candidate and PCSM
intake semantic validation.

## State Slice

This documentation-only phase may touch only:

- `docs/148-phase-hsai-admission-input-semantic-integrity-boundary-spec.md`
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

Phase 147 closed admission decision provenance and protected-root overlap, but
three local semantic input gaps remain.

### Source-Kind Shape Ambiguity

`AgentAdmissionCandidate` exposes a source-kind discriminator plus optional
`case` and `proposed_envelope` payloads. Admission currently does not verify
that those fields agree. A candidate can therefore claim an `AgentCase` or
`ClaimEnvelopeProposal` source while omitting its required payload, retaining
the wrong payload, or mismatching the candidate subject and case subject.

Raw `ProviderResponse` values also need an explicit non-admissible shape. A raw
provider response must be converted into a typed candidate before admission;
setting `strict_typed=true` must not permit direct acceptance.

### Artifact Digest Ambiguity

Admission currently requires only a nonempty artifact set when policy demands
artifacts. Empty or unsafe logical IDs, zero SHA-256 values, and multiple
different digests under the same logical ID can satisfy that check.

Artifact identity must be deterministic and portable before a candidate can be
accepted.

### PCSM Count And Verifier Ambiguity

The PCSM intake validator currently checks only that all four count fields are
nonzero. It does not enforce:

```text
pcsm_accepted + pcsm_rejected == pcsm_inputs
pcsm_journal_entries == pcsm_inputs
```

The verifier collection is ordered by full status value, so the same verifier
name can appear once with `Pass` and once with `Fail`. Unknown verifier names
are also not rejected. The future validator must require exactly the declared
required verifier-name set, with one status per name and every outcome equal to
`Pass`.

## Required Candidate Shape Contract

A future implementation must evaluate source shape before claim-boundary and
authority policy checks and emit deterministic reasons in source-field order.

Required shapes:

| Source kind | `case` | `proposed_envelope` | Additional rule |
| --- | --- | --- | --- |
| `AgentCase` | exactly one | none | `candidate.subject == case.subject` |
| `ClaimEnvelopeProposal` | none | exactly one | no raw case payload |
| `ProviderResponse` | none | none | never directly admissible; typed conversion required |
| `BenchmarkResultProposal` | none | none | metadata-only candidate |
| `PcsmBoundedProofHandoff` | none | none | metadata-only candidate |

The future implementation must not infer a source kind from whichever optional
field happens to be populated. The declared discriminator controls validation.

Invalid source shape must produce a rejection reason. A non-strict raw provider
candidate remains quarantined; a falsely strict provider candidate is rejected.

## Required Artifact Digest Contract

Every candidate artifact digest must satisfy:

- the logical ID is nonempty;
- the logical ID has no leading or trailing whitespace;
- the logical ID is one portable segment;
- only ASCII alphanumeric, `-`, `_`, and `.` characters are allowed;
- `/`, `\`, and `..` are forbidden;
- the SHA-256 value is not all zeroes;
- one logical ID maps to exactly one SHA-256 value.

Exact duplicate `(id, sha256)` values may collapse under `BTreeSet` semantics.
Different SHA-256 values under one logical ID must fail closed.

The reserved `pcsm-bounded-proof-intake` ID remains governed by Phase 147.
General artifact validation must not weaken or bypass that reserved binding.

## Required PCSM Count Contract

A future implementation must:

- preserve the existing nonzero count requirement;
- compute `pcsm_accepted + pcsm_rejected` with checked arithmetic;
- reject overflow;
- reject any total unequal to `pcsm_inputs`;
- reject `pcsm_journal_entries != pcsm_inputs`.

These checks validate internal metadata consistency only. They do not validate
the source journal or establish PCSM runtime correctness.

## Required PCSM Verifier Contract

The required verifier names remain:

- `verify_cl12_local_mlx_pcsm_surrogate`;
- `verify_cl12_external_benchmark_replication`;
- `verify_breakthrough_threshold_audit`;
- `verify_native_pcsm`;
- `source_lint_gate`.

A future implementation must:

- reject an empty verifier name;
- reject duplicate verifier names regardless of outcome;
- reject unknown verifier names;
- reject missing required verifier names;
- reject every required verifier whose outcome is not `Pass`;
- use deterministic error ordering.

The validator must not accept a passing status when a second failing status
exists under the same name.

## Required Future Tests

A later implementation phase must prove:

- every valid source kind accepts only its exact field shape;
- missing and extra case/envelope payloads are rejected;
- an `AgentCase` subject mismatch is rejected;
- raw provider responses cannot be directly accepted;
- empty, whitespace-padded, path-like, and invalid-character artifact IDs are
  rejected;
- zero artifact digests are rejected;
- conflicting digests under one artifact ID are rejected;
- valid portable artifact IDs remain accepted;
- PCSM count overflow and inconsistent totals are rejected;
- PCSM journal count mismatch is rejected;
- duplicate verifier names are rejected even when one status passes;
- unknown verifier names are rejected;
- missing and failing required verifier statuses remain rejected;
- a valid Phase 140/147 PCSM intake still maps, admits locally, journals,
  materializes, and reads back;
- normal tests remain process-free, network-free, and source-repo independent.

## Deterministic Compatibility Rules

The future implementation may add new `AdmissionReason` values and
`PcsmHandoffIntakeError` variants. Existing valid constructors and the valid
PCSM fixture must remain accepted.

Tests that assert exact reason vectors must be updated only when the candidate
is intentionally malformed under this contract. Reason ordering must remain
stable so journal decision digests are deterministic.

No serialized schema change is required for this phase. Existing Phase 147
candidate and policy snapshots are sufficient to recompute the stricter
decision.

## Deferred Findings

This phase does not authorize:

- duplicate JSON object-key detection;
- failure-atomic overwrite backup and restore;
- descriptor-relative no-follow filesystem access;
- randomized staging paths;
- committed-source handoff parsing.

Those surfaces require separate named boundaries.

## Claim Boundary

These checks establish local typed-input consistency only. They do not
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
- evaluate semantic errors deterministically;
- preserve Phase 147 decision recomputation and reserved intake binding;
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
