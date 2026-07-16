# Statebook P6 Read-Only External Sources Boundary

Date: 16 July 2026.

Status: documentation-first boundary complete; implementation requires a
separate commit.

Evidence ceiling for this document: `DocumentationOnly` at
`Level0DesignNote`.

Named boundary state slice:
`statebook-p6-read-only-external-sources-boundary`.

Future implementation state slice:
`statebook-p6-read-only-external-sources`.

## Objective

Add a read-only external import boundary that ingests captured (and, only after
the Stage 5 gate below, live) venue terms and market observations without
trading, signing, custody, or settlement authority.

P6 addresses Integration Stage 5: external evidence with credential handling and
network import. It validates source identity, revision, schema, and provenance,
then feeds digest-bound bytes into the existing P1–P5 pipeline.

P6 does not implement P7 authority integration.

## Relationship to prior phases

- P1 remains the sole terms parser and StateKey identity source.
- P2–P4 remain payoff, completeness, and settlement-kernel identity sources.
- P5 remains the sole portable audit-bundle and proposal-handoff surface.
- P6 consumes public P1 parse/lower APIs as a library consumer. It does not
  reimplement normalization, residuals, completeness, gates, or bundles.
- Source lineage must not enter `StateKeyV1`. Distinct sources that lower to
  identical normalized semantics retain distinct lineage receipts.

## Integration Stage 5 freeze (mandatory before network)

This boundary freezes one first authorized source profile:

| Field | Frozen value |
|-------|--------------|
| Source profile id | `synthetic-clearing-terms-v1` |
| Venue / clearing namespace | `synthetic.clearing.v1` |
| Legal / operational status | synthetic hermetic double; non-authoritative |
| Operator workflow | local captured-artifact import only in the first implementation |
| Credential handling | credentials are forbidden in library and default test paths; any future live credential store is operator-owned, out of crate, and separately reviewed |
| Hermetic test double | required captured JSON artifacts under `crates/statebook-source/tests/fixtures/` |
| Fail-closed import contract | unknown schema/profile, missing provenance, digest mismatch, duplicate keys, unknown fields, oversized payloads, and superseded-active conflicts reject |

Live network clients are **not** authorized in the first implementation commit.
A later separately reviewed commit may add an opt-in live path only after the
hermetic double and fail-closed contract above remain green.

## Crate and ownership boundary

Future implementation may add at most one new workspace crate:

1. `crates/statebook-source` — source registry, provenance, closed captured
   import profiles, import receipts, and domain-separated digests.

No `statebook-sim`. No second new crate. No generic venue/source adapter trait
until two real, independently reviewed implementations exist (PRD ID-019). The
first phase uses closed named profiles and explicit functions.

Ownership rules:

- `statebook-core`, `statebook-settlement`, and `statebook-report` public APIs,
  digests, fixtures, and kernel/bundle behavior remain unchanged. P6 may depend
  on `statebook-core` as a library consumer.
- No `zkbench-core`, custody, execution, clearing, signing, pause, transfer,
  admission mutation, or Evidence Ledger append dependency.
- Network clients, credential material, and process spawn are forbidden in
  library sources and default hermetic tests.
- Filesystem reads are permitted for captured artifact import under caller-
  selected bounded paths in tests; no production venue filesystem authority.

## Source registry and provenance

The future implementation must support:

- register a source revision with venue namespace, source id, revision,
  observation/retrieval times, content digest, evidence class, supported claims,
  and limitations;
- classify sources using a closed evidence-class enum that includes at least
  `VenueDocumentation`, `DirectArtifact`, `CapturedReplay`, and
  `IllustrativeNarrative`;
- supersede or revoke a revision without deleting historical digests;
- reject missing digest/revision and reject using `IllustrativeNarrative` as
  assurance, price, solvency, finality, or settlement evidence.

Every external fact remains an observation-time fact.

## Captured import surface

Closed import functions map captured artifacts into:

1. raw terms bytes suitable for `parse_source_contract_v1`;
2. an import receipt binding profile id, source digests, provenance fields, and
   adapter nonclaims;
3. optional observation envelopes that preserve unknown facts and never invent
   market properties.

Rules:

- missing facts remain unknown;
- evidence maturity is preserved and not reinterpreted as financial expiry;
- adapters state they do not prove price, solvency, semantics, legality,
  execution, or finality;
- adapters do not perform P4 assurance resolution, quorum, tier selection, gate
  evaluation, or release decisions;
- media/narrative classes cannot enter assurance calculations.

## Canonical identity

P6 identities use domain-separated tagged length-delimited binary encodings and
SHA-256. JSON or Serde rendering hashes are forbidden for identity.

New digest families must include at least:

```text
statebook:p6-source-registration:v1\0
statebook:p6-import-receipt:v1\0
statebook:p6-captured-artifact:v1\0
statebook:p6-provenance-set:v1\0
```

An implementation-diverse second SHA-256 encoder (dev-dependency only) must
reproduce frozen golden vectors for every new public digest family.

Frozen P1–P5 identities remain byte-identical.

## Closed inputs

Allowed:

- captured artifacts for `synthetic-clearing-terms-v1`;
- public `statebook-core` parse/lower APIs;
- local temporary roots for bounded import tests.

Forbidden:

- live venue network clients in the first implementation;
- credentials, secrets, or API keys in library/default tests;
- generic unbounded source-adapter traits;
- trading, signing, custody, pause, transfer, margin, or settlement commands;
- admission mutation or Evidence Ledger append;
- `grants_authority=true`;
- empirically claimed production-calibrated caps, ratios, or delays;
- `statebook-sim` scenario/sweep APIs.

## Resource bounds

Future implementation must freeze exact ceilings for:

- artifact byte size (no larger than 1,048,576 bytes unless separately justified);
- registration count;
- provenance field length;
- observation count;
- supported-claim / limitation count.

Every exact limit must succeed and every limit-plus-one must reject.

## Frozen scenarios

The future implementation must cover at least:

1. captured terms import yields bytes accepted by `parse_source_contract_v1` with
   a matching content digest in the import receipt;
2. missing required provenance field rejects;
3. unknown schema version rejects;
4. unknown profile id rejects;
5. duplicate JSON key rejects;
6. unknown field rejects;
7. content digest mismatch rejects;
8. superseded active revision cannot silently replace historical digests;
9. `IllustrativeNarrative` cannot enter assurance/price/solvency paths;
10. unknown facts are preserved and not invented;
11. adapter nonclaims are present on every successful import;
12. resource limit-plus-one rejects;
13. independent test encoding reproduces every new P6 golden digest;
14. unchanged P1–P5 golden digests and public APIs;
15. source and serialized-output scans reject network, process, credential,
    unsafe code, floating-point financial arithmetic, `zkbench`, live venue
    authority, and authority-grant surfaces;
16. no generic public source-adapter trait is exported while only one profile
    exists.

## Authorized future implementation paths

The future implementation may change only:

- root `Cargo.toml` and resulting `Cargo.lock` solely for `statebook-source`
  membership and hermetic dependencies;
- new `crates/statebook-source/**`;
- new
  `docs/statebook-p6-read-only-external-sources-implementation-notes.md`;
- `README.md`;
- `AGENTS.md`;
- `docs/12-task-list.md`;
- `docs/90-whole-codebase-validation-report.md`.

No `statebook-core`, `statebook-settlement`, or `statebook-report` mutation is
authorized. No publication PDF rewrite is authorized.

## Acceptance gates

- no P1–P5 source, fixture, canonical bytes, digest, status, or public API
  behavior changes;
- captured import plus P1 parse both pass for golden fixtures;
- every listed rejection path fails closed;
- adapters preserve unknown and emit nonclaims;
- no aggregate completeness boolean or scalar trust score is introduced;
- an implementation-diverse encoder reproduces all new golden digests;
- focused format, tests, and warning-denied Clippy pass for `statebook-source`;
- unchanged `statebook-core`, `statebook-settlement`, and `statebook-report`
  tests and Clippy pass;
- repository documentation and hygiene tests pass;
- clean-tree workspace Clippy findings outside P6 are reported, not absorbed;
- independent scope/claim-boundary and import/digest reviews complete.

## Nonclaims

P6 creates no live order, fill, routing, optimization, custody, signing, pause
action, withdrawal, transfer, bridge, margin award, clearing recognition, legal
finality, asset control, oracle truth, venue solvency, empirical calibration,
scalar trust score, release-safety probability, admission authority, Evidence
Ledger mutation, P7 authority integration, production credential vault,
benchmark evidence, proof, semantic-correctness claim, production readiness,
SOTA, independent audit, or full-security claim. Captured synthetic import is
local hermetic regression evidence only and never moves value.
