# Phase 269 HSAI Gateway Formal Correspondence Output Bundle Boundary

State slice: `Phase 269 HSAI gateway formal correspondence-certificate output bundle boundary`.

## Status

Complete for the docs-first output-bundle boundary.

## Purpose

Phase 268 added a local pure-data correspondence certificate for the Phase 267
source mapping. Phase 269 defines the future output bundle contract for
materializing that certificate as declared files with digest sidecars and
readback validation.

This phase does not implement output materialization. It defines the bundle
shape and claim boundary before code mutation.

## Future Output Root

A future implementation may write only under a caller-selected output root. The
output root must be outside protected repository roots unless a test tempdir is
used.

The implementation must reject:

- empty output roots;
- repository roots;
- file roots;
- symlink roots;
- existing roots unless explicit overwrite is set;
- path traversal;
- absolute declared paths;
- undeclared files;
- missing declared files;
- stale sidecars;
- malformed declared JSON;
- claim-boundary drift.

## Declared Files

The future bundle should use this logical layout:

```text
gateway-formal-correspondence/
  certificate.json
  validation-report.json
  source-files.json
  source-anchors.json
  proof-obligations.json
  assumptions.md
  nonclaims.md
  redaction-report.json
  manifest.json
```

Each declared file except sidecars must have a matching `.sha256` sidecar:

```text
gateway-formal-correspondence/certificate.json.sha256
gateway-formal-correspondence/validation-report.json.sha256
gateway-formal-correspondence/source-files.json.sha256
gateway-formal-correspondence/source-anchors.json.sha256
gateway-formal-correspondence/proof-obligations.json.sha256
gateway-formal-correspondence/assumptions.md.sha256
gateway-formal-correspondence/nonclaims.md.sha256
gateway-formal-correspondence/redaction-report.json.sha256
gateway-formal-correspondence/manifest.json.sha256
```

No raw prover logs, raw solver transcripts, raw external repository copies, raw
provider responses, credentials, API tokens, live provider payloads, or proof
assistant cache files may be written by this bundle.

## Manifest Contract

The future `manifest.json` must include:

- schema version;
- bundle id;
- created-at timestamp;
- certificate digest;
- validation-report digest;
- source-file digest set;
- source-anchor digest set;
- proof-obligation digest set;
- assumptions digest;
- nonclaims digest;
- redaction-report digest;
- declared file list;
- declared file digest map;
- claim boundary;
- `creates_formal_proof = false`;
- `mutates_accepted_evidence_ledger = false`;
- `creates_level2_evidence = false`;
- `populates_score_axes = false`;
- `grants_authority = false`.

## Validation Report Contract

The future `validation-report.json` must include:

- schema version;
- bundle id;
- certificate digest;
- `valid`;
- issue count;
- checked file list;
- claim boundary;
- `creates_formal_proof = false`;
- `mutates_accepted_evidence_ledger = false`;
- `creates_level2_evidence = false`;
- `populates_score_axes = false`;
- `grants_authority = false`.

The validation report must be derived from
`validate_gateway_formal_correspondence_certificate`.

## Redaction Report Contract

The future `redaction-report.json` must state:

- no credentials retained;
- no raw prover logs retained;
- no raw solver transcripts retained;
- no raw external repo source retained;
- no proof assistant cache retained;
- no live provider responses retained;
- no accepted Evidence Ledger JSON retained;
- no benchmark outputs retained;
- no secrets retained.

## Readback Semantics

Readback must:

- read only declared files;
- reject missing declared files;
- reject undeclared files;
- reject symlinked bundle files or sidecars;
- verify every `.sha256` sidecar;
- recompute the manifest;
- recompute the validation report;
- re-run certificate validation;
- reject drift between certificate, manifest, sidecars, and validation report;
- reject malformed JSON or non-UTF-8 Markdown.

Readback success proves only that the local bundle is internally consistent. It
does not prove a formal obligation.

## Required Tests For Future Implementation

A future implementation phase must add focused tests for:

- materializing all declared files and sidecars;
- readback of a valid local bundle;
- protected root rejection;
- symlink root rejection;
- symlink declared-file rejection;
- undeclared file rejection;
- missing declared file rejection;
- stale sidecar rejection;
- malformed certificate rejection;
- malformed manifest rejection;
- validation-report drift rejection;
- nonclaim drift rejection;
- redaction-report drift rejection;
- claim-boundary escalation rejection;
- proof artifact retention rejection;
- accepted Evidence Ledger mutation flag rejection.

## Anti-Goals

This phase does not permit:

- Rust implementation changes;
- Cargo metadata changes;
- package runtime files;
- filesystem output implementation;
- generated output bundles;
- proof assistant setup files;
- external repo clones;
- vendored source;
- Lean, Coq, TLA+, SMT, Z3, CBMC, or model-checker execution;
- generated proof artifacts;
- proof artifact submission;
- raw prover or solver logs;
- accepted Evidence Ledger mutation;
- Level2+ evidence;
- score-axis population;
- benchmark evidence;
- official benchmark submission;
- live provider calls;
- credential handling;
- semantic-correctness claims;
- production-readiness claims;
- SOTA claims;
- breakthrough claims;
- full-security claims;
- global software-agent uniqueness claims;
- authority to execute an action.

## Next Slice

Phase 270 implements this local output-bundle materialization and readback
contract inside `hsai-agent-admission`. It remains local filesystem metadata
only and does not run a prover or promote the bundle into accepted evidence.
