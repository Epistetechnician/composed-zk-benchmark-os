# Statebook P7 Authority Integration Boundary

Date: 16 July 2026.

Status: documentation-first boundary complete; implementation requires a
separate commit.

Evidence ceiling for this document: `DocumentationOnly` at
`Level0DesignNote`.

Named boundary state slice:
`statebook-p7-authority-integration-boundary`.

Future implementation state slice:
`statebook-p7-authority-integration`.

## Objective

Authorize the legal/ops authority-integration phase required by PRD **P7** /
**ID-020** and whitepaper Phase 7.

P7 freezes:

1. a hermetic, synthetic, time-bound authority-statement attach surface that can
   change capital-recognition overlay only (PRD US-35);
2. an explicit legal/ops gate that must remain green before any live
   execution, custody, signing, pause, real margin recognition, or settlement
   product may be separately owned and reviewed.

P7 does not move value. P7 does not grant runtime execution authority.
`grants_execution_authority` is permanently false in this phase.

## Relationship to prior phases

- P1 remains the sole terms parser and StateKey identity source.
- P2 remains the sole residual/payoff identity source.
- P3 remains the sole completeness-report identity source, including fixture
  capital completeness.
- P4 remains the sole settlement transition kernel.
- P5 remains the sole portable audit-bundle and proposal-handoff surface.
- P6 remains the sole captured-source import and provenance registry.
- P7 consumes opaque digests (`subject_terms_digest`, optional
  `economic_residual_digest`) as library inputs. It does not reimplement
  normalization, residuals, completeness evaluation, gates, bundles, or
  source import.
- Authority lineage must not enter `StateKeyV1` or rewrite economic residual
  digests. Economic offset and recognized capital relief remain separate
  (whitepaper §10.1).

## Legal/ops gate freeze (mandatory before live authority products)

This boundary freezes the gate that blocks live authority-bearing products:

| Gate field | Frozen requirement |
|------------|--------------------|
| Threat model | Named owner and reviewed threat-model reference required |
| Legal review | Named counsel or compliance sign-off reference required |
| Operational evidence | Named runbook plus loss-limit evidence reference required |
| Loss limits | Explicit quantitative loss-budget owner and ceiling required |
| Authority owner | Named human/organization accountable for recognition scope |
| Live product ownership | Execution, custody, signing, pause, real margin recognition, and settlement each require a separately owned product phase after this gate |

Live authority products are **not** authorized in the first implementation
commit. Completing P1–P6 does not imply the gate is satisfied. Completing the
hermetic P7 statement surface does not satisfy the gate by itself.

## Hermetic authority-statement freeze

This boundary freezes one first authorized authority profile:

| Field | Frozen value |
|-------|--------------|
| Authority profile id | `synthetic-clearing-authority-v1` |
| Authority namespace | `synthetic.clearing.authority.v1` |
| Legal / operational status | synthetic hermetic double; non-authoritative |
| Operator workflow | local captured authority-statement attach only |
| Credential / key material | forbidden in library and default test paths |
| Hermetic test double | required JSON artifacts under `crates/statebook-authority/tests/fixtures/` |
| Fail-closed attach contract | unknown schema/profile, missing fields, digest mismatch, duplicate keys, unknown fields, oversized payloads, expired-at-or-before-issued, revoke/expire conflicts, and `grants_execution_authority=true` reject |

## Crate and ownership boundary

Future implementation may add at most one new workspace crate:

1. `crates/statebook-authority` — authority-statement registry, attach/revoke/
   expire evaluation, capital-recognition overlays, attach receipts, and
   domain-separated digests.

No `statebook-sim`. No second new crate. No generic authority-adapter trait
until two real, independently reviewed implementations exist.

Ownership rules:

- `statebook-core`, `statebook-settlement`, `statebook-report`, and
  `statebook-source` public APIs, digests, fixtures, kernels, bundles, and
  import behavior remain unchanged. P7 may depend on them only as optional
  library consumers of opaque digests; the conservative default is no
  production dependency on those crates.
- No `zkbench-core`, custody, execution, clearing command, signing, pause,
  transfer, admission mutation, or Evidence Ledger append dependency.
- Network clients, credential material, and process spawn are forbidden in
  library sources and default hermetic tests.
- Filesystem reads are permitted for captured statement import under caller-
  selected bounded paths in tests; no production authority filesystem control.

## Authority statement and capital overlay

The future implementation must support:

- attach a time-bound authority statement binding at least authority id,
  eligible account, model id/version/digest, margin rule id, jurisdiction,
  subject terms digest, issued/expires times, recognized quantity (exact
  rational string pair), and explicit `grants_execution_authority=false`;
- keep economic residual identity unchanged: attach receipts bind optional
  `economic_residual_digest` as an opaque input and never recompute or mutate
  payoff/residual bytes;
- revoke or expire a statement without deleting historical statement digests;
- emit a capital-recognition overlay whose status may be
  `recognized_in_fixture`, `partially_recognized_in_fixture`,
  `not_recognized_in_fixture`, or `not_evaluated`, and whose changes affect
  capital overlay only;
- reject any statement that sets `grants_execution_authority` to true;
- reject expired statements at evaluation time (`now >= expires_at`) as
  non-recognized without granting any execution path;
- reject illustrative or narrative authority classes if introduced.

Every authority fact remains an observation-time, non-authoritative fixture
fact until a separately owned live product clears the legal/ops gate.

## Canonical identity

P7 identities use domain-separated tagged length-delimited binary encodings and
SHA-256. JSON or Serde rendering hashes are forbidden for identity.

New digest families must include at least:

```text
statebook:p7-authority-statement:v1\0
statebook:p7-attach-receipt:v1\0
statebook:p7-capital-overlay:v1\0
statebook:p7-authority-registration:v1\0
```

An implementation-diverse second SHA-256 encoder (dev-dependency only) must
reproduce frozen golden vectors for every new public digest family.

Frozen P1–P6 identities remain byte-identical.

## Closed inputs

Allowed:

- captured authority statements for `synthetic-clearing-authority-v1`;
- opaque lowercase 64-hex digests supplied by the caller;
- local temporary roots for bounded attach tests.

Forbidden:

- live execution, custody, signing, pause, transfer, withdrawal, bridge, or
  settlement commands;
- real clearinghouse margin awards or legal finality claims;
- network clients or credentials in library/default tests;
- generic unbounded authority-adapter traits;
- admission mutation or Evidence Ledger append;
- `grants_execution_authority=true` / `grants_authority=true`;
- empirically claimed production-calibrated caps, ratios, or delays;
- `statebook-sim` scenario/sweep APIs;
- mutation of P1–P6 crates.

## Resource bounds

Future implementation must freeze exact ceilings for:

- statement byte size (no larger than 1,048,576 bytes unless separately
  justified);
- registration count;
- identifier / field length;
- limitation / nonclaim count.

Every exact limit must succeed and every limit-plus-one must reject.

## Frozen scenarios

The future implementation must cover at least:

1. attach of a valid synthetic statement yields an attach receipt with capital
   overlay `recognized_in_fixture` (or partial when quantity is partial) and
   `grants_execution_authority=false`;
2. economic residual digest on the receipt equals the caller-supplied opaque
   input and is unchanged by revoke/expire;
3. revoke changes capital overlay to `not_recognized_in_fixture` while
   preserving historical statement digests;
4. evaluation at or after `expires_at` yields non-recognized capital overlay;
5. `grants_execution_authority=true` rejects;
6. unknown schema version rejects;
7. unknown profile id rejects;
8. duplicate JSON key rejects;
9. unknown field rejects;
10. missing required field rejects;
11. issued_at >= expires_at rejects;
12. resource limit-plus-one rejects;
13. independent test encoding reproduces every new P7 golden digest;
14. unchanged P1–P6 golden digests and public APIs;
15. source and serialized-output scans reject network, process, credential,
    unsafe code, floating-point financial arithmetic, `zkbench`, live venue
    authority, release/transfer/trade surfaces, and authority-grant surfaces;
16. no generic public authority-adapter trait is exported while only one
    profile exists;
17. legal/ops gate checklist constants remain present and claim live products
    are deferred.

## Authorized future implementation paths

The future implementation may change only:

- root `Cargo.toml` and resulting `Cargo.lock` solely for
  `statebook-authority` membership and hermetic dependencies;
- new `crates/statebook-authority/**`;
- new
  `docs/statebook-p7-authority-integration-implementation-notes.md`;
- `README.md`;
- `AGENTS.md`;
- `docs/12-task-list.md`;
- `docs/90-whole-codebase-validation-report.md`.

No `statebook-core`, `statebook-settlement`, `statebook-report`, or
`statebook-source` mutation is authorized. No publication PDF rewrite is
authorized.

## Acceptance gates

- no P1–P6 source, fixture, canonical bytes, digest, status, or public API
  behavior changes;
- attach/revoke/expire paths fail closed as listed;
- capital overlay changes never rewrite economic residual digests;
- every successful receipt preserves `grants_execution_authority=false` and
  adapter nonclaims;
- no aggregate completeness boolean or scalar trust score is introduced;
- an implementation-diverse encoder reproduces all new golden digests;
- focused format, tests, and warning-denied Clippy pass for
  `statebook-authority`;
- unchanged `statebook-core`, `statebook-settlement`, `statebook-report`, and
  `statebook-source` tests and Clippy pass;
- repository documentation and hygiene tests pass;
- clean-tree workspace Clippy findings outside P7 are reported, not absorbed;
- independent scope/claim-boundary and authority/digest reviews complete.

## Nonclaims

P7 creates no live order, fill, routing, optimization, custody, signing, pause
action, withdrawal, transfer, bridge, real margin award, clearinghouse
recognition, legal finality, asset control, oracle truth, venue solvency,
empirical calibration, scalar trust score, release-safety probability,
admission authority, Evidence Ledger mutation, production credential vault,
benchmark evidence, proof, semantic-correctness claim, production readiness,
SOTA, independent audit, or full-security claim. Hermetic synthetic
authority-statement attach is local regression evidence only and never moves
value. Completing this phase does not satisfy the legal/ops gate for live
authority products.
