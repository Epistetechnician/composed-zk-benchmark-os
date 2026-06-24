# Phase 146 HSAI Admission Provenance And Transaction Integrity Boundary Spec

Status: docs-first boundary for future fail-closed admission provenance and
output-root transaction hardening.

## State Slice

This documentation-only phase may touch only:

- `docs/146-phase-hsai-admission-provenance-transaction-integrity-boundary-spec.md`
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

Post-Phase-145 adversarial review identified three high-severity local
integrity gaps.

### Caller-Forgeable Decisions

`AgentAdmissionJournal::append_decision` accepts a caller-supplied decision and
checks only candidate identity and digest. A caller can construct an
`Accepted` decision for a candidate that the declared policy would reject.

The journal stores neither the candidate snapshot nor policy snapshot, so
readback cannot recompute the decision independently.

Required invariant:

```text
stored decision == evaluate_admission(stored candidate, stored policy)
```

### Unbound PCSM Intake Metadata

The Phase 140 mapper validates `PcsmBoundedProofHandoffIntake`, but the
resulting candidate does not bind the full intake digest. Source commit,
handoff digest, verifier statuses, counts, blocked status, and authority flags
can differ while producing the same candidate when the artifact set and
nonclaims are unchanged.

Every PCSM handoff candidate must carry a reserved source metadata digest equal
to `PcsmBoundedProofHandoffIntake::digest()`.

### Protected Descendant Deletion

Output-root validation rejects an output equal to or below a protected root,
but can allow an output root that is an ancestor of a protected path. With
overwrite enabled, recursive deletion of that ancestor can delete the protected
descendant.

Protected-root overlap must be symmetric:

```text
output == protected
output starts with protected
protected starts with output
```

Any matching condition must reject the output root before mutation.

## Required Future Journal Contract

A future implementation must persist enough information in every
`AgentAdmissionJournalEntry` to independently verify:

- the complete typed candidate snapshot;
- the complete admission policy snapshot;
- candidate id and digest agreement;
- policy id agreement;
- source artifact digest agreement;
- exact deterministic decision recomputation;
- decision digest agreement;
- verdict-envelope consistency;
- sequence, previous digest, and replay rules.

The public append path must require an explicit policy and must reject any
caller-supplied decision that differs from deterministic evaluation.

Existing journal bundle schema compatibility is not required if preserving it
would keep forged decisions unverifiable. Any schema change must remain local,
versioned, deterministic, and covered by malformed or legacy-shape rejection
tests.

## Required PCSM Binding

The future PCSM candidate mapper must add exactly one reserved artifact digest:

```text
id = pcsm-bounded-proof-intake
sha256 = PcsmBoundedProofHandoffIntake::digest()
```

The implementation must reject:

- a caller-supplied source artifact using that reserved id;
- missing reserved intake digest;
- reserved digest mismatch;
- duplicate reserved ids;
- a journal snapshot whose PCSM candidate lacks the binding.

The binding is local metadata provenance only. It does not authenticate the
source repository or admit a staged handoff.

## Required Protected-Root Behavior

The output validator must reject all equal, descendant, and ancestor overlaps
after normalization. Rejection must occur before staging cleanup, output
deletion, rename, or any other target-root mutation.

Focused tests must cover:

- output equal to protected root;
- output below protected root;
- output above protected root;
- overwrite-enabled ancestor overlap;
- sibling path acceptance;
- nonexistent normalized paths.

## Required Future Tests

A later implementation phase must prove:

- a forged accepted decision for a rejected candidate is rejected;
- a forged rejected decision for an accepted candidate is rejected;
- candidate snapshot drift is rejected;
- policy snapshot drift is rejected;
- policy id drift is rejected;
- source digest snapshot drift is rejected;
- fully rehashed bundle tampering still fails deterministic recomputation;
- valid accepted, rejected, and quarantined decisions still append;
- every valid PCSM candidate carries the exact reserved intake digest;
- reserved-id collision and binding drift are rejected;
- symmetric protected-root overlap rejects ancestor deletion;
- normal tests remain process-free, network-free, and source-repo independent.

## Deferred Medium Findings

This phase does not authorize:

- structural source-kind shape validation;
- general artifact-id and zero-digest validation;
- PCSM count equality or exact verifier-name-set hardening;
- duplicate JSON object-key detection;
- failure-atomic overwrite backup/restore;
- descriptor-relative no-follow filesystem operations or randomized staging.

Each requires a separate named boundary or a later explicitly compatible
hardening phase.

## Claim Boundary

These fixes establish deterministic local provenance and mutation safety only.
They do not establish source authenticity, committed-source PCSM intake, PCSM
runtime correctness, external replication, provider or production authority,
accepted Evidence Ledger admission, benchmark evidence, official submission,
proof, semantic correctness, production readiness, score-axis validity,
Level2+ evidence, or full breakthrough-threshold admission.

## Source Checkout Recheck

On 2026-06-24, `recoverable-ghost-states` remained dirty and 32 commits ahead
of `origin/main`; the handoff remained staged and absent from `HEAD`. Actual
committed-source parsing remains blocked and is not part of this phase.

## Future Implementation Exit Criteria

A later implementation phase must:

- touch only `crates/hsai-agent-admission/src/lib.rs`,
  `crates/hsai-e2e-harness/src/lib.rs`, phase notes, and navigation/status docs
  unless a separate phase broadens the slice;
- add no dependency or Cargo metadata change;
- update all append callers to provide the policy explicitly;
- preserve deterministic hashing and strict readback;
- reject invalid state before filesystem mutation;
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
