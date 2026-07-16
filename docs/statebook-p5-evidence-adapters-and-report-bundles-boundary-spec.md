# Statebook P5 Evidence Adapters And Report Bundles Boundary

Date: 16 July 2026.

Status: documentation-first boundary complete; implementation requires a
separate commit.

Evidence ceiling for this document: `DocumentationOnly` at
`Level0DesignNote`.

Named boundary state slice:
`statebook-p5-evidence-adapters-and-report-bundles-boundary`.

Future implementation state slice:
`statebook-p5-evidence-adapters-and-report-bundles`.

## Objective

Add narrow HSAI and hermetic fixture adapters, portable digest-bound audit
bundles, independent digest checks, and fail-closed readback validation.

P5 addresses the export and verification surface that P3 and P4 explicitly
deferred. It materializes and re-validates digest-bound decision provenance. It
does not move value, ingest live or captured venue sources, or grant authority.

P5 does not implement P6 read-only external sources or credentialed network
import (Integration Stage 5). P5 does not implement P7 authority integration.

## Relationship to prior phases

- P1–P3 remain the semantic, payoff, and completeness identity sources.
- P4 remains the sole settlement transition kernel and
  `DecisionRecordV1` producer.
- P5 consumes public P1–P4 outputs. It does not reimplement gates, tiers,
  valuation, budgets, queue transitions, or completeness evaluation.
- Integration Stage 5 (external evidence boundary with credentials and network
  import) maps to PRD **P6**, not this slice.

## Crate and ownership boundary

Future implementation may add at most two new workspace crates:

1. `crates/statebook-report` — portable audit bundles, manifests, materialization,
   readback validation, nonclaims, and hermetic fixture adapters.
2. `crates/statebook-hsai` — narrow ClaimEnvelope ↔ Statebook observation and
   decision-handoff adapters only.

Conservative default if one crate is preferred at implementation time: place
both adapter surfaces inside `statebook-report` and omit `statebook-hsai`. The
boundary authorizes either layout but forbids a third new crate and forbids
`statebook-sim`.

Ownership rules:

- `statebook-core` remains unchanged.
- `statebook-settlement` P3/P4 public APIs, digests, fixtures, and kernel
  behavior remain unchanged. P5 may depend on them as a library consumer.
- No `zkbench-core`, venue, custody, execution, clearing, signing, pause,
  transfer, network, credential, or process dependency is permitted in core
  library paths.
- HSAI dependencies, if used, are a closed allowlist of existing `hsai-*`
  crates for **read-only mapping** of committed hermetic types or fixture
  doubles. Admission mutation, Evidence Ledger append, and
  `grants_authority=true` are forbidden.
- Filesystem writes are permitted only inside bounded report
  materialization/readback tests.

## Evidence adapters

### Hermetic fixture adapters

Fixture adapters accept only closed, named fixture profiles. They map synthetic
documents into the Statebook normalized observation and bundle-input model with
strict unknown-field rejection, duplicate JSON key rejection, exact rational
strings, lowercase 64-hex digests, and nonempty bounded ASCII identifiers.

No generic venue or source adapter trait is authorized until two real,
independently reviewed implementations exist (PRD ID-019). That gate is outside
this slice.

### HSAI ClaimEnvelope → observation

A narrow inbound adapter may map relevant ClaimEnvelope facts into the
Statebook observation model (issuer, subject, property, scope, nonce,
issue/expiry, trust roots, policy version, source refs, dependency roots).

Rules:

- missing facts remain unknown; never invent market properties;
- evidence maturity is preserved and not reinterpreted as financial expiry;
- the adapter states that it does not prove price, solvency, semantics,
  legality, execution, or finality;
- the adapter does not perform P4 assurance resolution, quorum, tier selection,
  gate evaluation, or release decisions.

### Statebook decision → HSAI proposal handoff

A narrow outbound adapter may consume a completed P4 `DecisionRecordV1` and its
bound digests and emit a proposal-only handoff envelope.

Rules:

- every emitted handoff preserves `grants_authority=false`;
- financial semantics must not be forced into a lossy generic action string;
- no admission-state mutation, Evidence Ledger append, signing, pause, custody,
  or settlement command is permitted;
- if the live admission seam remains an unstable dirty surface, hermetic doubles
  are required and sufficient for this slice.

## Portable audit bundle

### Required trace members

One portable bundle must carry a single digest-bound trace containing records
for:

- contract / terms identity;
- `StateKeyV1`;
- residual / payoff report;
- seven-dimension completeness composition;
- evidence snapshot;
- policy;
- valuation;
- linked-plan or obligation when present;
- queue and transfer status;
- budget ledger tips before/after;
- decision record;
- nonclaim records.

Every record binds its input digests and schema version. No record may claim
live execution, clearing recognition, legal finality, or value movement without
external evidence, and this slice supplies none.

### Manifest and file set

The future implementation must freeze:

- a closed manifest schema version string;
- a closed required file set and filenames;
- a domain-separated manifest digest over exact member file bytes;
- rejection of undeclared files, missing required files, path traversal, and
  symlinks.

Exact filenames and schema identifiers are implementation-frozen in the
implementation notes and golden fixtures. Until frozen, no implementation is
complete.

### Materialization

Materialization writes the closed file set under a caller-selected bounded
output root. In-memory construction alone is not acceptance evidence. A
successful write that fails readback is a failed materialization.

## Readback validation

Readback must independently parse and validate a materialized bundle. Rejection
is mandatory for:

- missing required files;
- undeclared extra files;
- path traversal;
- symlink substitution;
- stale digests;
- malformed JSON, unknown versions, unknown enums, duplicate keys;
- noncanonical digests or identifiers;
- malformed exact rationals or overflowed amounts;
- semantically inconsistent sections (for example, composition digest mismatch
  against embedded seven-report digests, or decision-context mismatch against
  intent, evidence, policy, and valuation digests);
- secret or raw response-body retention;
- tampered or missing nonclaims;
- mismatched report sections.

Reports are not trusted because generation returned success.

## Canonical identity and independent digest verification

P5 identities use domain-separated tagged length-delimited binary encodings and
SHA-256. JSON or Serde rendering hashes are forbidden for identity.

New digest families must include at least:

```text
statebook:p5-bundle-manifest:v1\0
statebook:p5-bundle-member:v1\0
statebook:p5-audit-trace:v1\0
statebook:p5-nonclaim-set:v1\0
```

An implementation-diverse second SHA-256 encoder (dev-dependency only) must
reproduce frozen golden vectors for every new public digest family. That second
encoder is local regression evidence, not independent audit.

Frozen P1–P4 identities remain byte-identical, including:

- P1 701-byte preimage and StateKey
  `f1662f3fb5a10c074680c0baf76ba488b7230337456358be92f3127d8a632c08`;
- P1 validated-contract digest
  `7634410968adb9b56c62f213de7956796f9f3f62b102d4f6efe7f45d86858788`;
- P2 domain digest
  `67cb8e1807cd3e619f73d569f70de494ef60610f4d44acea236b0ee006e45e6a`;
- all P3 subject, fixture, report, capital-context, recovery-profile, and
  composition digests;
- all P4 intent, decision-context, release-attempt, ledger-tip, and decision-
  record digests used by exported golden bundles.

## Closed inputs

Allowed:

- hermetic fixture profiles and P1–P4 public opaque reports / decision records;
- closed HSAI ClaimEnvelope fixture doubles or read-only allowlisted `hsai-*`
  types for mapping tests;
- injected clocks already present in P4 decision records;
- local temporary output roots for bounded report tests.

Forbidden:

- live or captured venue terms, books, oracles, or observations (P6);
- network clients, credentials, process spawn;
- media, tweets, or memes as assurance evidence;
- generic unbounded source-adapter traits;
- admission mutation or Evidence Ledger append;
- empirically claimed production-calibrated caps, ratios, or delays;
- `statebook-sim` scenario/sweep APIs.

## Resource bounds

Future implementation must freeze exact ceilings for:

- gross bundle byte size (no larger than 1,048,576 bytes unless a separately
  justified bound is frozen);
- member file count;
- path length;
- observation count;
- nonclaim count;
- trace record count.

Every exact limit must succeed and every limit-plus-one must reject.

## Frozen scenarios

The future implementation must cover at least:

1. one fully populated hermetic bundle round-trip with independent readback
   success and matching golden digests;
2. missing required file rejects;
3. undeclared extra file rejects;
4. path traversal rejects;
5. symlink substitution rejects;
6. stale member digest rejects;
7. malformed JSON / duplicate key / unknown field rejects;
8. tampered nonclaim rejects;
9. composition digest mismatch rejects;
10. decision-context digest mismatch rejects;
11. secret or response-body retention rejects;
12. fixture adapter maps a closed profile without inventing unknowns;
13. HSAI inbound adapter preserves unknown and maturity, emitting adapter
    nonclaims;
14. HSAI outbound handoff preserves `grants_authority=false`;
15. exporting a P4 `Immediate` or `Queued` decision never introduces transfer,
    signing, or authority fields;
16. unchanged P1–P4 golden digests and public report/decision bytes;
17. independent test encoding reproduces every new P5 golden digest;
18. source and serialized-output scans reject network, process, credential,
    unsafe code, floating-point financial arithmetic, `zkbench`, live venue,
    and authority-grant surfaces.

## Authorized future implementation paths

The future implementation may change only:

- root `Cargo.toml` and resulting `Cargo.lock` solely for the authorized new
  crate membership and hermetic dependencies;
- new `crates/statebook-report/**` and, if used, new `crates/statebook-hsai/**`;
- new
  `docs/statebook-p5-evidence-adapters-and-report-bundles-implementation-notes.md`;
- `README.md`;
- `AGENTS.md`;
- `docs/12-task-list.md`;
- `docs/90-whole-codebase-validation-report.md`.

No `statebook-core` mutation, no `statebook-settlement` kernel/completeness
mutation, no `statebook-sim`, no publication PDF rewrite, and no external
adapter path outside the closed HSAI allowlist is authorized.

## Acceptance gates

- no P1–P4 source, fixture, canonical bytes, digest, status, or public API
  behavior changes;
- bundle materialization plus independent readback both pass for golden
  fixtures;
- every listed readback rejection path fails closed;
- adapters preserve unknown, maturity, and `grants_authority=false`;
- no aggregate completeness boolean or scalar trust score is introduced;
- an implementation-diverse encoder reproduces all new golden digests;
- focused format, tests, and warning-denied Clippy pass for new crates;
- unchanged `statebook-core` and `statebook-settlement` tests and Clippy pass;
- repository documentation and hygiene tests pass;
- clean-tree workspace tests run;
- clean-tree workspace Clippy findings outside P5 are reported, not absorbed;
- independent scope/claim-boundary and bundle/digest reviews complete.

## Nonclaims

P5 creates no live order, fill, routing, optimization, custody, signing, pause
action, withdrawal, transfer, bridge, margin award, clearing recognition, legal
finality, asset control, oracle truth, venue solvency, empirical calibration,
scalar trust score, release-safety probability, admission authority, Evidence
Ledger mutation, P6 external source ingestion, P7 authority integration,
network access, credential handling, process execution, benchmark evidence,
proof, semantic-correctness claim, production readiness, SOTA, independent
audit, or full-security claim. A portable bundle that embeds a simulated
decision record is local hermetic regression and readback evidence only and
never moves value.
