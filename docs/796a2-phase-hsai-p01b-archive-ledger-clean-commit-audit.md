# Phase 796-A2 HSAI P01B Archive Ledger Clean-Commit Audit

## Status

Complete with a retained zero-gap decision over the clean Phase 796-A1
commit. Phase 796-A3 remains unauthorized.

State slice: `phase-796a2-hsai-p01b-archive-ledger-clean-commit-audit`.

Classification: `P01BArchiveLedgerParserCleanCommitAuditAccepted`.

Execution status: `LocalValidationOnly`.

Evidence ceiling: `Level1LocalReplayOrLower`.

## Audited Authority

The audit reviewed this exact detached commit:

```text
53442464ec851be46dd1e47b44b0918a14e9cf4a
```

The detached audit worktree was clean before and after validation. Its Phase
796-A1 implementation identities were:

| Object | SHA-256 |
|---|---|
| immutable Phase 796-A boundary document | `2b52a3b24d94b565434dc341d808fe7ee3ad44757ea5ff8365f8dc88aefe1ba0` |
| immutable Phase 796-A contract digest | `9a85d6b33f31ee3e78d6176da9208753bc5c244c4fecc44ab29efc265b4f7bd1` |
| `tools/hsai-formal-preflight/p01b_archive_ledger.py` | `ab7c3da98d995997fba1bd2d2d865257c9f99dfefb4ce82b815cceacd92df45f` |
| `tools/hsai-formal-preflight/tests/test_p01b_archive_ledger.py` | `0ae3a2b348e491af7d2b362272255b0bd278961f4a4b7ca24718a4470692f81b` |
| Phase 796-A1 implementation record | `00d7948b3376ef9c823240361e0242f1515dc85f246bd870ca7e84d8d7796ae9` |

The historical `raw_archive_validator.py` remained unchanged at
`31fa2450fe7e3ce87c13dd844ac6fde1cde0a4a81e7d351276e5dd2a4ba32692`.

## Audit Method

The main audit re-ran the implementation from the clean detached commit and
instrumented the focused suite to account for the deterministic failure
taxonomy. Two fresh reviewers then independently examined the implementation,
tests, immutable contract, host-limit probes, and clean-commit identities.

Observed results:

```text
/usr/bin/python3: 3.9.6
focused Phase 796-A1 suite: 68 passed, 0 failed
complete formal-preflight suite: 151 passed, 0 failed
deterministic failure classes observed: 56
deterministic failure classes missing from focused tests: 0
ruff check: passed
cargo fmt --all -- --check: passed
cargo check --workspace --all-targets: passed
detached git status: clean
```

The actual bounded-runner child limits observed through the focused test probe
were:

```json
{"cpu_seconds":900,"max_open_file_descriptors":32,"max_output_file_bytes":67108864}
```

The repository has no root `package.json`. `pnpm run lint` remains unavailable
because pnpm reports that the repository is configured for Yarn; no npm or Yarn
substitute was used.

## Contract Checklist

| Phase 796-A2 requirement | Decision |
|---|---|
| authorized files only | pass |
| constants and grammar enforced from source | pass |
| every deterministic failure class covered | pass |
| required boundary and adversarial tests pass | pass |
| golden candidate bytes match | pass |
| descriptor handling fails closed | pass |
| host CPU, output-size, descriptor, and parser limits are enforceable | pass |
| no convenience gzip or TAR parser | pass |
| no extraction or network path | pass |
| helper and test hashes published against a clean commit | pass |

Result: 10 of 10 requirements pass; unresolved P0, P1, and P2 findings: 0.

## Independent Review Records

Each record is canonical compact JSON with lexicographically sorted object
keys and no trailing newline. Its digest is
`SHA-256("hsai:p01b-archive-ledger-a2-review-record:v1\\0" || json_bytes)`.

Implementation-contract reviewer:

```json
{"review":{"checklist":{"all_failure_classes_tested":true,"authorized_files_only":true,"constants_and_grammar_enforced":true,"descriptor_handling_fail_closed":true,"golden_vectors_match":true,"hashes_published_and_clean_commit":true,"no_convenience_parser":true,"no_extraction_or_network":true,"required_tests_pass":true,"selected_host_limits_enforceable":true},"decision":"accept","reviewed_commit":"53442464ec851be46dd1e47b44b0918a14e9cf4a","reviewer_role":"independent-implementation-contract-reviewer","schema":"hsai-p01b-archive-ledger-a2-review-v1","unresolved_findings":[]},"reviewer_id":"codex-subagent:019f644f-c937-7a70-9bd8-c00192aac0b5","schema":"hsai-p01b-archive-ledger-a2-review-record-v1"}
```

```text
sha256 = 2afd7688a107e0d5d0318156740bc50e808bd54ae3da7a44f251a057c4967f4d
```

Test-and-host-limit reviewer:

```json
{"review":{"checklist":{"all_failure_classes_tested":true,"authorized_files_only":true,"constants_and_grammar_enforced":true,"descriptor_handling_fail_closed":true,"golden_vectors_match":true,"hashes_published_and_clean_commit":true,"no_convenience_parser":true,"no_extraction_or_network":true,"required_tests_pass":true,"selected_host_limits_enforceable":true},"decision":"accept","reviewed_commit":"53442464ec851be46dd1e47b44b0918a14e9cf4a","reviewer_role":"independent-test-host-reviewer","schema":"hsai-p01b-archive-ledger-a2-review-v1","unresolved_findings":[]},"reviewer_id":"codex-subagent:019f644f-d216-7851-ad39-c2752c5be780","schema":"hsai-p01b-archive-ledger-a2-review-record-v1"}
```

```text
sha256 = 3c5f5569b7cbe8745cf59c4a38ecc2bee4e7dac102c539cf255691cbe325e76f
```

Both independent decisions are `accept`; neither reviewer reported a finding.

## Retained Audit Decision

The retained aggregate is canonical compact JSON with lexicographically sorted
object keys and no trailing newline. Its digest is
`SHA-256("hsai:p01b-archive-ledger-a2-audit:v1\\0" || json_bytes)`.

```json
{"acquisition_authorized":false,"actual_limits":{"cpu_seconds":900,"max_open_file_descriptors":32,"max_output_file_bytes":67108864},"boundary_document_sha256":"2b52a3b24d94b565434dc341d808fe7ee3ad44757ea5ff8365f8dc88aefe1ba0","cargo_check_workspace_all_targets":"passed","contract_digest":"9a85d6b33f31ee3e78d6176da9208753bc5c244c4fecc44ab29efc265b4f7bd1","decision":"zero_gap","evidence_ceiling":"Level1LocalReplayOrLower","failure_classes_observed":56,"focused_tests_passed":68,"formal_preflight_tests_passed":151,"implementation_record_sha256":"00d7948b3376ef9c823240361e0242f1515dc85f246bd870ca7e84d8d7796ae9","parser_source_sha256":"ab7c3da98d995997fba1bd2d2d865257c9f99dfefb4ce82b815cceacd92df45f","phase_796_a3_authorized":false,"python_version":"3.9.6","review_record_sha256":["2afd7688a107e0d5d0318156740bc50e808bd54ae3da7a44f251a057c4967f4d","3c5f5569b7cbe8745cf59c4a38ecc2bee4e7dac102c539cf255691cbe325e76f"],"reviewed_commit":"53442464ec851be46dd1e47b44b0918a14e9cf4a","schema":"hsai-p01b-archive-ledger-a2-audit-v1","test_source_sha256":"0ae3a2b348e491af7d2b362272255b0bd278961f4a4b7ca24718a4470692f81b","unresolved_findings":0}
```

```text
audit_sha256 = 5301f672b057396791e85af8c16194617accaf40df087f9a967e4ef148d15dfb
decision = zero_gap
phase_796_a3_authorized = false
acquisition_authorized = false
```

## Authority Boundary

Phase 796-A2 is a local clean-commit audit, not an archive acquisition or an
external audit. It read no real archive, used no network, extracted nothing,
and retained no generated candidate ledger. It grants no materialization,
capture, backend, Lean, SMT, Z3, or COBALT execution authority.

It creates no proof artifact, accepted evidence, Level2+ evidence, score-axis
result, semantic-correctness claim, production-readiness claim, SOTA claim,
breakthrough claim, full-security claim, or action authority. It does not close
`P796-02`, Phase 780 lane `L07`, or the complete Phase 796 stop, and it does not
publish `preparation_contract_sha256`.

## Next Gate

The zero-gap A2 decision satisfies the clean-commit parser-audit prerequisite
only. A separate Phase 796-A3 authorization decision remains required before
any acquisition-only attempt. That future decision is still blocked by an
accepted supervisor enforcing `max_resident_bytes=536870912`, explicit network
and source authority, and the remaining immutable Phase 796-A conditions.
