# Statebook P7 Authority Integration Preflight Boundary

Date: 16 July 2026.

Status: documentation-first boundary complete; implementation requires a
separate commit.

Evidence ceiling for this document: `DocumentationOnly` at
`Level0DesignNote`.

Named boundary state slice:
`statebook-p7-authority-integration-preflight-boundary`.

Future implementation state slice:
`statebook-p7-authority-integration-preflight`.

## Objective

Add a fail-closed authority-integration **preflight** surface that consumes P5
proposal handoffs and validates whether a separately owned controller package
names the Stage 6 required fields: authority owner, maximum loss, rollback and
pause semantics, audit retention, legal domain, and production gate.

P7 addresses Integration Stage 6 without connecting any execution, custody,
clearing, pause, signing, margin, or settlement controller. Completing P1–P6
does not imply authority.

## Relationship to prior phases

- P1–P4 remain semantic, residual, completeness, and settlement-kernel sources.
- P5 remains the sole producer of proposal handoffs with
  `grants_authority=false`.
- P6 remains the sole captured-source import boundary.
- P7 consumes public P5 handoff digests/outcomes as opaque inputs. It does not
  reimplement kernels, bundles, or source import.
- No controller client, signer, custodian, venue executor, or pause actuator is
  authorized in this slice.

## Integration Stage 6 freeze

This boundary freezes one hermetic authority-package profile:

| Field | Frozen value |
|-------|--------------|
| Profile id | `hermetic-authority-preflight-v1` |
| Legal / operational status | synthetic hermetic preflight; non-authoritative |
| Authority owner | must be a nonempty bounded ASCII identifier |
| Maximum loss | exact rational string pair; must be finite and non-negative |
| Rollback semantics | closed enum: `reject_and_journal`, `hold_and_escalate` |
| Pause semantics | closed enum: `scoped_halt`, `global_halt_required` |
| Audit retention | closed enum: `days_30`, `days_90`, `days_365` |
| Legal domain | nonempty bounded ASCII identifier |
| Production gate | closed enum in this slice: `incomplete`, `denied` only |

The production-gate value `authorized` is **rejected** in this slice. A future
separately reviewed phase with threat model, legal review, operational evidence,
and named owner may authorize a different gate vocabulary. This slice never
emits `grants_authority=true` and never invokes a controller.

## Crate and ownership boundary

Future implementation may add at most one new workspace crate:

1. `crates/statebook-authority` — authority-package parsing, preflight
   evaluation, receipts, nonclaims, and domain-separated digests.

No `statebook-sim`. No generic controller trait. No live network or credential
clients in library or default tests.

Ownership rules:

- `statebook-core`, `statebook-settlement`, `statebook-report`, and
  `statebook-source` public APIs, digests, fixtures, and behavior remain
  unchanged. P7 may depend on `statebook-report` as a library consumer for
  handoff types or may accept digest-bound handoff fields as opaque JSON.
- No `zkbench-core`, venue executor, custody, signing, pause, transfer, margin,
  or settlement controller dependency.
- Filesystem writes are forbidden except temporary test roots if needed for
  fixture loading.

## Preflight surface

The future implementation must:

- parse a closed authority-package schema with unknown-field and duplicate-key
  rejection;
- bind a P5 handoff (`decision_record_digest`, `intent_digest`,
  `decision_context_digest`, `outcome`, `grants_authority=false`);
- reject packages that set `grants_authority=true` or omit required Stage 6
  fields;
- reject `production_gate=authorized` in this slice;
- emit a preflight receipt with outcome `Incomplete` or `Denied`, never
  `Authorized`;
- emit adapter nonclaims stating no controller was invoked and no value moved.

## Canonical identity

P7 identities use domain-separated tagged length-delimited binary encodings and
SHA-256. JSON or Serde rendering hashes are forbidden for identity.

New digest families must include at least:

```text
statebook:p7-authority-package:v1\0
statebook:p7-preflight-receipt:v1\0
statebook:p7-loss-bound:v1\0
statebook:p7-nonclaim-set:v1\0
```

An implementation-diverse second SHA-256 encoder (dev-dependency only) must
reproduce frozen golden vectors for every new public digest family.

Frozen P1–P6 identities remain byte-identical.

## Closed inputs

Allowed:

- hermetic authority-package fixtures for `hermetic-authority-preflight-v1`;
- opaque P5 handoff digests/outcomes with `grants_authority=false`;
- local temporary roots for bounded tests.

Forbidden:

- execution, custody, clearing, pause, signing, margin, or settlement clients;
- network, credentials, process spawn in library/default tests;
- `grants_authority=true`;
- `production_gate=authorized` acceptance;
- admission mutation or Evidence Ledger append;
- scalar trust scores or release-safety probabilities;
- `statebook-sim`.

## Resource bounds

Future implementation must freeze exact ceilings for:

- package byte size (no larger than 65,536 bytes unless separately justified);
- identifier length;
- nonclaim count;
- controller-name count (metadata only; no invocation).

Every exact limit must succeed and every limit-plus-one must reject.

## Frozen scenarios

1. complete hermetic package with `production_gate=denied` yields `Denied`
   receipt and `grants_authority=false`;
2. missing authority owner rejects;
3. missing maximum loss rejects;
4. malformed exact rational loss rejects;
5. unknown rollback/pause/retention/gate enum rejects;
6. `production_gate=authorized` rejects;
7. handoff with `grants_authority=true` rejects;
8. handoff digest mismatch / noncanonical digest rejects;
9. unknown field / duplicate key / unknown schema rejects;
10. resource limit-plus-one rejects;
11. receipt nonclaims assert no controller invocation and no value movement;
12. independent encoder reproduces every new P7 golden digest;
13. unchanged P1–P6 golden digests and public APIs;
14. source scans reject network, process, credential, unsafe code, floating-point
    financial arithmetic, `zkbench`, and controller-invocation surfaces;
15. no public controller client trait or `connect_`/`execute_`/`sign_` API is
    exported.

## Authorized future implementation paths

The future implementation may change only:

- root `Cargo.toml` and resulting `Cargo.lock` solely for `statebook-authority`
  membership and hermetic dependencies;
- new `crates/statebook-authority/**`;
- new
  `docs/statebook-p7-authority-integration-preflight-implementation-notes.md`;
- `README.md`;
- `AGENTS.md`;
- `docs/12-task-list.md`;
- `docs/90-whole-codebase-validation-report.md`.

No mutation of `statebook-core`, `statebook-settlement`, `statebook-report`, or
`statebook-source` is authorized.

## Acceptance gates

- no P1–P6 source, fixture, digest, status, or public API behavior changes;
- every listed rejection path fails closed;
- every successful preflight keeps `grants_authority=false` and never emits
  `Authorized`;
- focused format, tests, and warning-denied Clippy pass for
  `statebook-authority`;
- unchanged prior Statebook crate tests pass;
- repository documentation and hygiene tests pass;
- independent scope/claim-boundary and digest reviews complete.

## Nonclaims

P7 preflight creates no live order, fill, routing, custody, signing, pause
action, withdrawal, transfer, bridge, margin award, clearing recognition, legal
finality, asset control, oracle truth, venue solvency, empirical calibration,
scalar trust score, release-safety probability, admission authority, Evidence
Ledger mutation, controller connection, production authorization, benchmark
evidence, proof, semantic-correctness claim, production readiness, SOTA,
independent audit, or full-security claim. A `Denied` or `Incomplete` preflight
receipt is local hermetic regression evidence only and never moves value.
