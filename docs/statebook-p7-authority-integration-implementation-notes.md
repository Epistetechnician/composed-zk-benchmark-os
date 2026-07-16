# Statebook P7 Authority Integration Implementation Notes

Date: 16 July 2026.

State slice: `statebook-p7-authority-integration`.

## Outcome

A new isolated `statebook-authority` crate hosts:

- a hermetic attach path for the frozen profile
  `synthetic-clearing-authority-v1`;
- an authority-statement registry with revoke and historical digest retention;
- capital-recognition overlay evaluation that never rewrites economic residual
  digests;
- permanent `grants_execution_authority=false` with fail-closed rejection of
  true grants;
- legal/ops gate deferred checklist constants on every successful receipt;
- domain-separated P7 SHA-256 identities with an implementation-diverse `ring`
  golden encoder in tests.

P7 does not mutate P1–P6 crates. Live execution, custody, signing, pause, real
margin recognition, and settlement remain deferred behind the legal/ops gate.
No value moves.

## Implemented boundary

| Constant | Value |
|----------|-------|
| Profile | `synthetic-clearing-authority-v1` |
| Authority namespace | `synthetic.clearing.authority.v1` |
| Statement schema | `statebook-p7-authority-statement:v1` |
| Registration schema | `statebook-p7-authority-registration:v1` |
| Attach receipt schema | `statebook-p7-attach-receipt:v1` |
| Capital overlay schema | `statebook-p7-capital-overlay:v1` |

Resource ceilings:

| Constant | Value |
|----------|------:|
| `MAX_STATEMENT_BYTES_V1` | 1,048,576 |
| `MAX_REGISTRATIONS_V1` | 256 |
| `MAX_FIELD_BYTES_V1` | 512 |
| `MAX_LIMITATION_OR_NONCLAIM_COUNT_V1` | 32 |
| `MAX_IDENTIFIER_BYTES_V1` | 128 |

Canonical domains:

- `statebook:p7-authority-statement:v1\0`
- `statebook:p7-attach-receipt:v1\0`
- `statebook:p7-capital-overlay:v1\0`
- `statebook:p7-authority-registration:v1\0`

## Local validation evidence

```text
cargo fmt -p statebook-authority -- --check
cargo test -p statebook-authority --tests
cargo clippy -p statebook-authority --all-targets -- -D warnings
cargo test -p statebook-core -p statebook-settlement -p statebook-report -p statebook-source --tests
```

Seventeen focused integration tests pass: eleven attach/registry paths, five
claim-boundary scans, and one independent `ring` digest golden.

## Remaining gaps vs boundary frozen scenarios

Minimum acceptance scenarios are covered. Optional follow-ons:

- dedicated duplicate-key named fixture beyond the strict UniqueValue parser;
- live authority products only after legal/ops gate evidence is separately
  owned and reviewed;
- optional consumption of capital overlays by a future P3 report adapter
  without mutating economic residuals.

## Claim ceiling

This is local hermetic synthetic authority-statement / capital-overlay
regression evidence only. It is not live clearing recognition, legal finality,
custody, signing, pause, transfer, admission authority, Evidence Ledger
mutation, production readiness, SOTA, independent audit, or full security.
Completing P7 does not satisfy the legal/ops gate for live authority products.
No value moves.
