# Phase 142 HSAI Admission Journal Semantic Readback Boundary Spec

Status: docs-first boundary for future semantic readback hardening of local
admission-journal bundles.

## State Slice

This documentation-only phase may touch only:

- `docs/142-phase-hsai-admission-journal-semantic-readback-boundary-spec.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

It does not authorize Rust source changes, tests, Cargo metadata changes,
`Cargo.lock` changes, recoverable-ghost file parsing or git inspection, source
repo command execution, PCSM runtime import or vendoring, recoverable-ghost
artifact import, generated output files, committed admission-journal bundles,
package runtime files, command-line tools, network access, provider calls,
credentials, accepted Evidence Ledger mutation, official benchmark submission,
external replay execution, score-axis population, or Level2+ evidence.

## Problem

Phase 141 verifies that every declared file matches its adjacent SHA-256
sidecar and then deserializes `manifest.json`. That detects ordinary corruption,
but digest-consistent tampering remains possible when a caller changes a file
and recomputes its sidecar.

The current reader does not independently prove that:

- `journal.json` has a valid digest chain;
- manifest entry and verdict counts match the serialized journal;
- manifest journal tips match the serialized journal;
- `decisions.jsonl` exactly represents the journal decisions;
- `source-digests.json` exactly represents journal source digests;
- `non-claims.md` matches the manifest nonclaims;
- `redaction-report.json` preserves every required false retention flag;
- `validation-report.json` matches the bundle and checked files;
- the manifest declared-file list and digest map are canonical;
- sidecar files themselves are regular non-symlink files.

Sidecars are integrity metadata, not authenticity or semantic validation.

## Goal

Define the smallest future implementation that upgrades readback from
byte-integrity validation to complete local bundle-semantic validation:

```text
declared admission-journal files
-> reject symlinks and undeclared files
-> verify sidecar digests
-> parse every declared file
-> validate journal chain
-> recompute all derived views
-> compare manifest, decisions, source digests, nonclaims, redaction, report
-> return validated manifest
```

This hardening must preserve Phase 141 output format and claim boundaries.

## Required Semantic Checks

### Manifest

The future reader must reject:

- schema-version drift;
- empty or path-shaped bundle ids;
- noncanonical declared-file order or contents;
- missing or extra declared digest entries;
- content digest mismatches against manifest entries;
- wrong claim-boundary label;
- missing required admission-journal nonclaims.

### Journal

The future reader must:

- deserialize `journal.json` as `AgentAdmissionJournal`;
- run `AgentAdmissionJournal::validate`;
- recompute entry count and verdict counts;
- recompute journal tip after;
- verify the declared journal tip before is compatible with the bundle
  contract;
- reject replay, sequence, previous-digest, candidate, or decision drift.

### Decision Review Index

The future reader must:

- parse every nonempty `decisions.jsonl` line as
  `AdmissionDecisionReviewRow`;
- reject malformed, blank-interleaved, missing, extra, duplicated, or
  reordered rows;
- recompute the expected rows from `journal.json`;
- require exact row equality.

### Source Digests

The future reader must:

- parse `source-digests.json`;
- recompute the union of journal source artifact digests;
- require exact equality;
- reject duplicate digest ids with conflicting hashes.

### Nonclaims

The future reader must:

- parse the rendered nonclaim lines;
- require exact agreement with manifest nonclaims;
- require every Phase 141 nonclaim;
- reject missing, duplicated, malformed, or undeclared nonclaims.

### Redaction Report

The future reader must require every retention flag to remain `false`. A
digest-consistent report that permits credentials, raw provider responses,
raw request bodies, raw transcripts, raw attestation material, raw JWKS or
OpenID documents, raw TLS exporters, benchmark result bodies, or accepted
Evidence Ledger JSON must be rejected.

### Validation Report

The future reader must require:

- the expected schema version;
- matching bundle id;
- `valid=true`;
- `journal_error_count=0`;
- the local-only claim-boundary label;
- the canonical checked-file list.

The validation report is a derived review record. It cannot override an
independently detected error.

### Filesystem Safety

The future reader must reject:

- symlink primary files;
- symlink digest sidecars;
- missing primary files or sidecars;
- directories where declared regular files are expected;
- undeclared files or nested directories;
- partial bundles.

## Required Future Errors

A later implementation should use explicit errors for at least:

- malformed declared file;
- manifest semantic mismatch;
- invalid serialized journal;
- decision-index mismatch;
- source-digest-index mismatch;
- nonclaim mismatch;
- unsafe redaction report;
- validation-report mismatch;
- sidecar symlink;
- declared file type mismatch.

Errors must identify the logical file or semantic surface that failed without
including secret or raw retained content.

## Required Future Tests

A later implementation phase must add hermetic mutation tests proving:

- valid Phase 141 bundles still round-trip;
- digest-consistent manifest count drift is rejected;
- digest-consistent journal-chain drift is rejected;
- digest-consistent decision-row drift is rejected;
- digest-consistent source-digest drift is rejected;
- digest-consistent nonclaim drift is rejected;
- digest-consistent redaction-policy drift is rejected;
- digest-consistent validation-report drift is rejected;
- sidecar symlinks are rejected;
- missing and undeclared files remain rejected;
- one complete local path succeeds:
  `valid PCSM intake -> candidate -> decision -> journal -> materialize ->
  semantic readback`;
- normal tests perform no process, network, credential, or source-repo access.

## Claim Boundary

Semantic readback proves only that a local bundle is internally consistent with
its declared format and journal data. It does not prove:

- source authenticity;
- external runtime replication;
- PCSM runtime correctness;
- provider authority;
- production or serving authority;
- accepted Evidence Ledger admission;
- official benchmark evidence or submission;
- semantic correctness;
- production readiness;
- Level2+ evidence;
- score-axis validity;
- full breakthrough-threshold admission.

## Source Checkout Recheck

On 2026-06-23, the recoverable-ghost-states PCSM handoff remained staged in a
dirty checkout rather than committed as a clean, digest-stable source revision.
Committed-source parsing and actual cross-repo intake therefore remain blocked.
Normal composed-zk-benchmark-os gates must remain independent of that checkout.

## Future Implementation Exit Criteria

A later implementation phase must:

- touch only `crates/hsai-agent-admission/src/lib.rs`, focused tests within that
  crate, phase notes, and navigation/status docs unless a separate phase
  broadens the slice;
- preserve the Phase 141 bundle format;
- parse and cross-validate every declared file;
- reject digest-consistent semantic tampering;
- keep tests hermetic;
- create no committed generated bundle;
- import no PCSM runtime or recoverable-ghost artifact;
- create no accepted evidence or stronger claim.

## Non-Goals

This boundary does not permit recoverable-ghost handoff parsing, source git
inspection, source verifier execution, workflow orchestration, PCSM runtime
import, provider calls, network access, credentials, external replay, official
submission, accepted Evidence Ledger mutation, score-axis population, local
Intel DCAP implementation, PCCS operation, JWKS fetching, JWT verification
changes, TLS or attested-TLS changes, formal evidence, Level2+ evidence,
full breakthrough-threshold admission, production-readiness claims,
semantic-correctness claims, proof claims, benchmark-evidence claims, or global
software-agent uniqueness claims.
