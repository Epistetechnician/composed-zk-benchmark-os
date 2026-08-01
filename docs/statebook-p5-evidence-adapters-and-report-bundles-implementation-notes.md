# Statebook P5 Evidence Adapters And Report Bundles Implementation Notes

Date: 16 July 2026.

State slice: `statebook-p5-evidence-adapters-and-report-bundles`.

## Outcome

A new isolated `statebook-report` crate hosts:

- closed hermetic fixture and HSAI fixture-envelope adapters that preserve unknown
  facts and evidence maturity without inventing market properties;
- a proposal-only decision handoff that always emits `grants_authority=false`;
- portable digest-bound audit-bundle materialization under a caller-selected
  temporary root;
- independent readback validation that re-parses and re-digests the closed file
  set before acceptance;
- domain-separated P5 SHA-256 identities with an implementation-diverse `ring`
  golden encoder in tests.

P5 consumes public P1–P4 digests and P4 decision-record fields as opaque inputs.
It does not reimplement gates, tiers, valuation, budgets, queues, or completeness
evaluation. No value moves.

## Implemented boundary

Conservative single-crate layout: adapters and bundles live in
`crates/statebook-report`. No `statebook-hsai` crate and no `statebook-sim`.

Frozen schema and path identifiers:

| Constant | Value |
|----------|-------|
| `BUNDLE_SCHEMA_VERSION_V1` | `statebook-p5-audit-bundle:v1` |
| `TRACE_SCHEMA_VERSION_V1` | `statebook-p5-audit-trace:v1` |
| `NONCLAIMS_SCHEMA_VERSION_V1` | `statebook-p5-nonclaims:v1` |
| `FIXTURE_ADAPTER_SCHEMA_VERSION_V1` | `statebook-p5-fixture-adapter:v1` |
| `HSAI_FIXTURE_SCHEMA_VERSION_V1` | `statebook-p5-hsai-fixture-envelope:v1` |
| `HANDOFF_SCHEMA_VERSION_V1` | `statebook-p5-decision-handoff:v1` |

Required member paths:

- `records/decision.json`
- `records/completeness.json`
- `records/evidence.json`
- `records/policy.json`
- `records/valuation.json`
- `records/budget.json`
- `records/queue.json`
- `records/nonclaims.json`
- `records/trace.json`

Plus `manifest.json` and `digests/manifest.sha256`.

Resource ceilings:

| Constant | Value |
|----------|------:|
| `MAX_BUNDLE_BYTES_V1` | 1,048,576 |
| `MAX_BUNDLE_MEMBER_COUNT_V1` | 9 |
| `MAX_BUNDLE_PATH_LENGTH_V1` | 256 |
| `MAX_OBSERVATIONS_V1` | 128 |
| `MAX_NONCLAIMS_V1` | 64 |
| `MAX_TRACE_RECORDS_V1` | 16 |
| `MAX_IDENTIFIER_BYTES_V1` | 128 |
| `MAX_FIXTURE_BYTES_V1` | 65,536 |

Canonical identity uses tagged length-delimited binary encodings and SHA-256 with
domain tags:

- `statebook:p5-bundle-manifest:v1\0`
- `statebook:p5-bundle-member:v1\0`
- `statebook:p5-audit-trace:v1\0`
- `statebook:p5-nonclaim-set:v1\0`

The audit-trace digest binds content members only (`TRACE_BOUND_MEMBER_PATHS`) to
avoid a self-digest cycle on `records/trace.json`. The manifest digest binds all
nine required member file digests after the trace embeds that identity.

Frozen P1–P4 golden digests remain byte-identical in golden bundle construction,
including the P1 StateKey, validated-contract, and P2 domain digests cited by the
boundary.

## Local validation evidence

Focused gates on this worktree:

```text
cargo fmt -p statebook-report -- --check
cargo test -p statebook-report --tests
cargo clippy -p statebook-report --all-targets -- -D warnings
cargo test -p statebook-core -p statebook-settlement --tests
```

The package reports nineteen passing integration tests: ten bundle
materialization/readback and fail-closed paths, four adapter/handoff tests, four
claim-boundary scans, and one independent `ring` digest golden.

## Remaining gaps vs boundary frozen scenarios

Minimum acceptance scenarios and resource-bound rejection paths are covered.
Optional follow-ons not required for this slice:

- exhaustive malformed-JSON / duplicate-key / unknown-field matrix as named
  fixtures beyond the strict parser already used on every readback path;
- secret-retention rejection as a dedicated named fixture (token scan is live on
  every written and read member);
- exporting a second P4 `Queued` golden bundle beyond the Immediate fixture used
  for round-trip coverage (handoff already covers both Immediate and Queued
  outcomes without transfer/signing/authority fields).

## Claim ceiling

This is local hermetic digest-bound audit-bundle and adapter regression evidence
only. It is not live venue ingestion, clearing recognition, legal finality,
custody, signing, pause, transfer, admission authority, Evidence Ledger mutation,
P6 external-source import, P7 authority integration, scalar trust scoring,
empirical calibration, production readiness, SOTA, independent audit, or full
security. A portable bundle that embeds a simulated decision record never moves
value.
