# Phase 153 HSAI Admission Journal Duplicate JSON Implementation Notes

Status: implemented for recursive duplicate object-key rejection before typed
canonical admission-journal readback.

## State Slice

This phase touched only:

- `crates/hsai-agent-admission/src/lib.rs`
- `docs/153-phase-hsai-admission-journal-duplicate-json-implementation-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No Cargo metadata, dependencies, fixtures, committed generated bundles, package
runtime, source-repo parser, command-line tool, or external runtime surface was
added.

## Implemented Parser

`parse_json_value_rejecting_duplicate_keys` is a dependency-free recursive JSON
parser used inside `parse_strict_json_bytes` before typed deserialization.

The pipeline is now:

```text
raw bytes
-> recursive duplicate-key rejection
-> serde_json::Value
-> typed deserialize
-> typed serialize
-> exact canonical value comparison
-> cross-file semantic validation
```

Duplicate object keys map to the existing
`AdmissionJournalMaterializationError::MalformedDeclaredFile(logical_path)` error
surface.

## Coverage

The focused test suite now proves:

- duplicate top-level and nested manifest fields, including digest-map keys;
- duplicate journal top-level and nested candidate, policy, decision, and
  artifact-digest fields;
- duplicate decision JSONL row fields;
- duplicate source-digest-index and nested artifact-digest fields;
- duplicate redaction-report and validation-report fields;
- equal-value and conflicting duplicate keys;
- duplicate keys nested inside arrays;
- trailing non-whitespace after an otherwise valid JSON value;
- identical key names in separate object scopes remain valid;
- valid raw UTF-8 strings and escaped surrogate-pair strings remain valid JSON
  string content;
- escaped key spelling that decodes to an existing key is rejected as a
  duplicate;
- digest-consistent duplicate-key tampering still fails before semantic checks.

## Claim Boundary

Duplicate JSON rejection establishes unambiguous local JSON object
interpretation only. It does not establish source authenticity, committed-source
PCSM intake, provider authority, accepted Evidence Ledger admission, benchmark
evidence, official submission, proof, semantic correctness, production readiness,
score-axis validity, Level2+ evidence, or full breakthrough-threshold
admission.

## Validation

```sh
cargo test -p hsai-agent-admission duplicate_json
cargo test -p hsai-agent-admission
```
