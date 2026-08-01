# Statebook P6 Read-Only External Sources Implementation Notes

Date: 16 July 2026.

State slice: `statebook-p6-read-only-external-sources`.

## Outcome

A new isolated `statebook-source` crate hosts:

- a captured-first import path for the frozen Stage 5 profile
  `synthetic-clearing-terms-v1`;
- a provenance-aware source registry with active/superseded statuses;
- fail-closed envelope parsing (schema, profile, digest, unknown fields,
  illustrative-narrative rejection, resource ceilings);
- domain-separated P6 SHA-256 identities with an implementation-diverse `ring`
  golden encoder in tests;
- adapter nonclaims on every successful import.

P6 feeds exact terms bytes into unchanged `parse_source_contract_v1`. It does
not reimplement normalization, residuals, completeness, settlement, or bundles.
No live network client is present. No value moves.

## Implemented boundary

| Constant | Value |
|----------|-------|
| Profile | `synthetic-clearing-terms-v1` |
| Venue namespace | `synthetic.clearing.v1` |
| Artifact schema | `statebook-p6-captured-artifact:v1` |
| Registration schema | `statebook-p6-source-registration:v1` |
| Import receipt schema | `statebook-p6-import-receipt:v1` |

Resource ceilings:

| Constant | Value |
|----------|------:|
| `MAX_ARTIFACT_BYTES_V1` | 1,048,576 |
| `MAX_REGISTRATIONS_V1` | 256 |
| `MAX_PROVENANCE_FIELD_BYTES_V1` | 512 |
| `MAX_OBSERVATIONS_V1` | 128 |
| `MAX_CLAIM_OR_LIMITATION_COUNT_V1` | 32 |
| `MAX_IDENTIFIER_BYTES_V1` | 128 |

Canonical domains:

- `statebook:p6-source-registration:v1\0`
- `statebook:p6-import-receipt:v1\0`
- `statebook:p6-captured-artifact:v1\0`
- `statebook:p6-provenance-set:v1\0`

## Local validation evidence

```text
cargo fmt -p statebook-source -- --check
cargo test -p statebook-source --tests
cargo clippy -p statebook-source --all-targets -- -D warnings
cargo test -p statebook-core -p statebook-settlement -p statebook-report --tests
```

Fourteen focused integration tests pass: nine import/registry paths, four
claim-boundary scans, and one independent `ring` digest golden.

## Remaining gaps vs boundary frozen scenarios

Minimum acceptance scenarios are covered. Optional follow-ons:

- dedicated duplicate-key named fixture beyond the strict UniqueValue parser;
- optional operator-gated live network path after a second reviewed venue
  profile exists (ID-019);
- broader captured observation envelopes for books/valuation beyond terms.

## Claim ceiling

This is local hermetic captured-source import regression evidence only. It is
not live venue truth, clearing recognition, legal finality, custody, signing,
pause, transfer, admission authority, Evidence Ledger mutation, P7 authority
integration, production readiness, SOTA, independent audit, or full security.
No value moves.
