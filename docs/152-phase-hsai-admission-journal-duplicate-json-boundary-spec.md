# Phase 152 HSAI Admission Journal Duplicate JSON Boundary Spec

Status: boundary complete; implementation landed in
`docs/153-phase-hsai-admission-journal-duplicate-json-implementation-notes.md`.

## State Slice

This documentation-only phase may touch only:

- `docs/152-phase-hsai-admission-journal-duplicate-json-boundary-spec.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

It does not authorize Rust source changes, tests, Cargo metadata changes,
`Cargo.lock` changes, generated output, committed bundles, filesystem
transaction changes, source-repo parsing, PCSM runtime import, provider calls,
network access, credentials, accepted Evidence Ledger mutation, official
submission, external replay, score-axis population, or Level2+ evidence.

## Problem

Phase 145 added typed canonical JSON round-trip validation. The parser first
deserializes bytes into `serde_json::Value`, but JSON objects with duplicate
keys are normalized before that value is returned. The later typed comparison
therefore cannot distinguish:

```json
{"valid": true, "valid": false}
```

from the final normalized value.

Digest sidecars do not solve this ambiguity. They bind the ambiguous bytes, not
a unique object interpretation.

## Required Future Parser Contract

A future implementation must add a dependency-free recursive JSON visitor
before the existing typed canonical round-trip.

The visitor must:

- parse one complete JSON value from the supplied bytes;
- reject a repeated key within the same object;
- apply the same rule recursively to objects nested inside arrays or objects;
- allow the same key name in different object scopes;
- preserve JSON null, boolean, string, number, array, and object values;
- reject malformed JSON;
- reject non-whitespace trailing data;
- return a normal `serde_json::Value` only after duplicate-key validation.

The implementation should use the existing `serde` and `serde_json`
dependencies. No parser dependency or Cargo metadata change is authorized.

## Integration Surface

The duplicate-aware parser must replace only the initial
`serde_json::from_slice::<serde_json::Value>` step inside
`parse_strict_json_bytes`.

The existing pipeline remains:

```text
raw bytes
-> recursive duplicate-key rejection
-> serde_json::Value
-> typed deserialization
-> typed serialization
-> exact canonical value comparison
-> cross-file semantic validation
```

This automatically covers:

- `admission-journal/manifest.json`;
- `admission-journal/journal.json`;
- every object in `admission-journal/decisions.jsonl`;
- `admission-journal/source-digests.json`;
- `admission-journal/redaction-report.json`;
- `admission-journal/validation-report.json`.

Digest sidecars are plain text and are outside this parser.

## Error Contract

Duplicate object keys must fail closed as the existing:

```text
AdmissionJournalMaterializationError::MalformedDeclaredFile(logical_path)
```

No public error enum or serialized schema change is required.

The failure must occur before typed deserialization and before semantic
cross-file comparison.

## Required Future Tests

A later implementation phase must prove rejection of:

- a duplicate top-level manifest field;
- a duplicate nested manifest digest-map key;
- a duplicate journal top-level field;
- a duplicate nested candidate field;
- a duplicate nested policy field;
- a duplicate nested decision field;
- a duplicate nested artifact-digest field;
- a duplicate decision JSONL row field;
- a duplicate source-digest-index field;
- a duplicate redaction-report field;
- a duplicate validation-report field;
- duplicate keys whose first and last values are equal;
- duplicate keys whose values conflict;
- duplicate keys nested inside an array;
- trailing non-whitespace after an otherwise valid JSON value.

Tests must also prove:

- identical key names in separate object scopes remain valid;
- all current generated bundle JSON reads successfully;
- malformed and recursively unknown fields remain rejected;
- digest-consistent duplicate-key tampering still fails;
- normal tests remain process-free, network-free, and source-repo independent.

## Deferred Findings

This phase does not authorize:

- repeated array-element rejection;
- raw PCSM verifier-array duplicate detection before `BTreeSet` normalization;
- backup/restore failure-atomic overwrite;
- descriptor-relative no-follow filesystem access;
- randomized staging paths;
- committed-source handoff parsing.

Repeated array values are not duplicate JSON object keys. A future raw PCSM
intake parser may define array-level uniqueness before typed set normalization.

## Claim Boundary

This parser hardening establishes unambiguous local JSON object interpretation
only. It does not establish source authenticity, committed-source PCSM intake,
source journal validity, PCSM runtime correctness, external replication,
provider or production authority, accepted Evidence Ledger admission,
benchmark evidence, official submission, proof, semantic correctness,
production readiness, score-axis validity, Level2+ evidence, or full
breakthrough-threshold admission.

## Future Implementation Exit Criteria

A later implementation phase must:

- touch only `crates/hsai-agent-admission/src/lib.rs`, phase notes, and
  navigation/status docs unless a separate phase broadens the slice;
- add no dependency or Cargo metadata change;
- preserve existing valid serialized schemas and generated output;
- preserve typed canonical round-trip and cross-file semantic checks;
- map duplicate keys to the existing malformed-file error;
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
