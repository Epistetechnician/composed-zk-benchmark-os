# Phase 144 HSAI Admission Journal Adversarial Invariant Boundary Spec

Status: docs-first boundary for future fail-closed hardening of admission
decisions and admission-journal readback.

## State Slice

This documentation-only phase may touch only:

- `docs/144-phase-hsai-admission-journal-adversarial-invariant-boundary-spec.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

It does not authorize Rust source changes, tests, Cargo metadata changes,
`Cargo.lock` changes, generated output files, package runtime additions,
source-repo parsing, PCSM runtime import, provider calls, network access,
credentials, accepted Evidence Ledger mutation, official submission, external
replay, score-axis population, or Level2+ evidence.

## Problem

Phase 143 closed digest-consistent cross-file drift, but adversarial review
identified three remaining fail-closed gaps.

### Verdict-Envelope Consistency

`AgentAdmissionDecision::accepted_envelope` can expose an envelope without
checking the decision verdict. A malicious, fully rehashed journal entry could
also carry an envelope under a `Rejected` or `Quarantined` verdict because
journal validation does not enforce the invariant.

Required invariant:

```text
verdict == Accepted      -> accepted_envelope may be present
verdict == Rejected      -> accepted_envelope must be absent
verdict == Quarantined   -> accepted_envelope must be absent
```

Rejected and quarantined decisions are audit records only. They must never
export or retain accepted state.

### Strict Declared-File Schemas

Normal Serde deserialization ignores unknown JSON fields unless the target type
rejects them. A digest-consistent file could therefore add undeclared retained
material such as `raw_provider_response` while the semantic reader silently
discards that field.

Every serialized admission-journal file type must reject unknown fields.
Strictness applies recursively to nested journal, decision, artifact, manifest,
source-index, redaction, and validation-report structures used by readback.

### Root And Bundle-Directory Symlinks

Phase 143 rejects symlink primary files and sidecars, but readback does not
explicitly reject a symlink `output_root` or symlink `admission-journal`
directory. Readback must validate the entire path boundary before reading leaf
files.

## Required Future Implementation

A later implementation phase must:

- make decision envelope access verdict-aware;
- add an explicit journal validation error for a non-accepted verdict carrying
  an envelope;
- reject append into an invalid existing journal containing that state;
- reject materialization of such a journal before output mutation;
- reject digest-consistent readback tampering that carries the state;
- reject unknown JSON fields in all admission-journal serialized structures;
- reject unknown nested fields, not only top-level fields;
- reject symlink output roots during readback;
- reject symlink `admission-journal` directories during readback;
- preserve Phase 141 file names and Phase 143 semantic checks.

## Required Future Tests

Focused tests must prove:

- rejected decision helper access returns no envelope;
- quarantined decision helper access returns no envelope;
- journal validation rejects rejected-envelope state;
- journal validation rejects quarantined-envelope state;
- append rejects an existing journal containing either invalid state;
- materialization rejects the invalid state and creates no output root;
- fully rehashed semantic readback tampering remains rejected;
- unknown fields in manifest, journal entry, nested decision, decision row,
  source digest, redaction report, and validation report are rejected;
- output-root symlinks are rejected during readback;
- bundle-directory symlinks are rejected during readback;
- valid Phase 143 bundles still round-trip.

Test-only coverage may also close remaining missing-file, malformed-file,
directory-substitution, output-root, manifest-drift, decision-index, and PCSM
metadata rejection branches while production behavior stays within this
boundary.

## Claim Boundary

These fixes establish stricter local decision and bundle-format invariants
only. They do not establish:

- source authenticity;
- actual committed-source PCSM intake;
- PCSM runtime correctness;
- external runtime replication;
- provider, production, or serving authority;
- accepted Evidence Ledger admission;
- official benchmark evidence or submission;
- proof or semantic correctness;
- production readiness;
- score-axis validity;
- Level2+ evidence;
- full breakthrough-threshold admission.

## Source Checkout Recheck

On 2026-06-23, `recoverable-ghost-states` remained dirty, its handoff remained
staged rather than present in `HEAD`, and local `main` remained ahead of
`origin/main`. Actual committed-source parsing therefore remains blocked and is
not part of this phase.

## Future Implementation Exit Criteria

A later implementation phase must:

- touch only `crates/hsai-agent-admission/src/lib.rs`, phase notes, and
  navigation/status docs unless a separate phase broadens the slice;
- add no dependency or Cargo metadata change;
- keep all tests hermetic;
- reject invalid state before filesystem mutation;
- preserve valid Phase 143 bundle compatibility;
- create no committed generated bundle;
- parse no recoverable-ghost file;
- create no accepted evidence or stronger claim.

## Non-Goals

This boundary does not permit committed-source parsing, source git inspection,
source verifier execution, PCSM runtime import, recoverable-ghost artifact
import, provider calls, network access, credentials, external replay, official
submission, accepted Evidence Ledger mutation, score-axis population,
DCAP/PCCS/JWKS/JWT/TLS changes, formal evidence, Level2+ evidence, production
readiness, semantic correctness, proof, benchmark evidence, global
software-agent uniqueness, or 100% coverage claims.
