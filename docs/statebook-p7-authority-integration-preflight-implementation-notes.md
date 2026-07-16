# Statebook P7 Authority Integration Preflight Implementation Notes

Date: 16 July 2026.

State slice: `statebook-p7-authority-integration-preflight`.

## Outcome

A new isolated `statebook-authority` crate hosts a fail-closed Stage 6
authority-package preflight:

- closed profile `hermetic-authority-preflight-v1`;
- required owner, maximum loss, rollback/pause semantics, audit retention,
  legal domain, and production gate;
- P5 handoff binding with mandatory `grants_authority=false`;
- rejection of `production_gate=authorized` in this slice;
- preflight outcomes limited to `Incomplete` and `Denied`;
- domain-separated P7 digests with an independent `ring` golden encoder.

No execution, custody, signing, pause, margin, or settlement controller is
invoked. No value moves.

## Implemented boundary

| Constant | Value |
|----------|-------|
| Profile | `hermetic-authority-preflight-v1` |
| Package schema | `statebook-p7-authority-package:v1` |
| Receipt schema | `statebook-p7-preflight-receipt:v1` |
| `MAX_PACKAGE_BYTES_V1` | 65,536 |
| `MAX_CONTROLLER_NAMES_V1` | 8 |
| `MAX_NONCLAIMS_V1` | 32 |

Canonical domains:

- `statebook:p7-authority-package:v1\0`
- `statebook:p7-preflight-receipt:v1\0`
- `statebook:p7-loss-bound:v1\0`
- `statebook:p7-nonclaim-set:v1\0`

## Local validation evidence

```text
cargo fmt -p statebook-authority -- --check
cargo test -p statebook-authority --tests
cargo clippy -p statebook-authority --all-targets -- -D warnings
cargo test -p statebook-core -p statebook-settlement -p statebook-report -p statebook-source --tests
```

Sixteen focused integration tests pass: eleven preflight paths, four
claim-boundary scans, and one independent `ring` digest golden.

## Remaining gaps

A future separately reviewed phase with threat model, legal review, operational
evidence, named owner, and loss limits would be required before any
`Authorized` vocabulary or controller client could exist. That work is outside
this slice.

## Claim ceiling

This is local hermetic authority-preflight regression evidence only. It is not
controller connection, production authorization, custody, signing, pause,
settlement, admission authority, Evidence Ledger mutation, production readiness,
SOTA, independent audit, or full security. No value moves.
