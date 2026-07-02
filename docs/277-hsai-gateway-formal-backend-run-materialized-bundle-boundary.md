# Phase 277 HSAI Gateway Formal Backend Run Materialized Bundle Boundary

State slice: `Phase 277 HSAI gateway formal backend-run materialized bundle boundary`.

## Status

Complete for the docs-first materialized backend-run bundle boundary.

## Purpose

Phase 276 added local `NotRun` backend-run artifact metadata in
`hsai-agent-admission`. Phase 277 defines the filesystem boundary for a future
materialized `gateway-formal-backend-run/*` bundle before any implementation is
allowed to write or read those files.

This phase does not implement file materialization and does not run a backend.

## Output Root Contract

A future implementation may write only to a caller-selected output root.

The output root must be rejected when it is:

- empty;
- the repository root;
- inside a protected repository root, unless the caller uses a test tempdir;
- a file;
- a symlink;
- an existing directory without explicit overwrite;
- an existing directory containing undeclared files;
- a path with traversal components;
- a path that resolves through a symlink parent.

Overwrite mode may be allowed only when every existing file belongs to the
declared bundle layout and every stale sidecar is replaced atomically.

## Declared Layout

A future implementation may materialize exactly this logical tree:

```text
gateway-formal-backend-run/
  adapter-request.json
  adapter-report.json
  run-summary.json
  correspondence-certificate-digest.json
  correspondence-output-manifest-digest.json
  source-digests.json
  toolchain-lock.json
  model-assumptions.json
  unsupported-rust-features.json
  proof-obligations.json
  redaction-report.json
  nonclaims.md
  manifest.json
```

Every declared file must have a same-directory `.sha256` sidecar. The future
manifest must list every declared file and every sidecar by logical path and
digest.

No other files are declared in this phase.

## Optional Attachments

Phase 277 does not authorize materializing optional proof, checker, or tool-log
attachments.

The following names remain reserved for a later explicit phase:

- `candidate-proof-artifact.ref.json`;
- `candidate-checker-transcript.ref.json`;
- `candidate-tool-log-summary.md`.

If these files appear in a Phase 277 bundle, readback must reject the bundle.

## File Semantics

The future files must carry only bounded metadata:

- `adapter-request.json`: serialized Phase 273 adapter request metadata;
- `adapter-report.json`: serialized Phase 273 adapter report metadata;
- `run-summary.json`: serialized Phase 276 backend-run artifact metadata;
- `correspondence-certificate-digest.json`: digest only, not the full
  certificate;
- `correspondence-output-manifest-digest.json`: digest only, not the full
  correspondence output bundle;
- `source-digests.json`: source paths and SHA-256 digests only;
- `toolchain-lock.json`: tool name, tool version, backend kind, and lock digest
  only;
- `model-assumptions.json`: explicit modeled assumptions only;
- `unsupported-rust-features.json`: unsupported feature labels only;
- `proof-obligations.json`: requested proof-obligation ids only;
- `redaction-report.json`: booleans proving raw or secret material was not
  retained;
- `nonclaims.md`: required nonclaims;
- `manifest.json`: declared logical paths, file digests, run-summary digest,
  claim boundary, and nonpromotion flags.

## Redaction Report Contract

The future redaction report must fail closed if any field indicates retention
of:

- credentials;
- secrets;
- raw proof assistant cache;
- raw prover logs;
- raw checker transcripts;
- raw SMT solver traces;
- raw external repository source;
- accepted Evidence Ledger files;
- benchmark result files;
- live-provider responses;
- generated proof artifacts;
- generated checker artifacts.

The report must also declare that no proof/checker optional attachment was
materialized in this phase.

## Readback Contract

A future readback implementation must reject:

- missing declared files;
- extra files;
- symlink directories;
- symlink files;
- symlink sidecars;
- stale sidecars;
- malformed JSON;
- invalid UTF-8 in Markdown files;
- mismatched manifest digests;
- mismatched run-summary digest;
- adapter-request digest drift;
- adapter-report digest drift;
- correspondence-certificate digest drift;
- output-manifest digest drift;
- backend-kind drift;
- tool metadata drift;
- proof-obligation drift;
- modeled-assumption digest drift;
- unsupported-feature digest drift;
- redaction-report drift;
- nonclaim drift;
- any materialized optional attachment;
- accepted Evidence Ledger retention;
- Level2+ evidence flags;
- score-axis population;
- authority grants;
- forbidden public claim text.

Readback must return local validation metadata only. It must not append to any
ledger and must not change evidence maturity.

## Manifest Contract

The future manifest must include:

- schema version;
- bundle id;
- state slice;
- created-at timestamp supplied by the caller;
- adapter request digest;
- adapter report digest;
- run-summary digest;
- correspondence certificate digest;
- correspondence output-manifest digest;
- declared file digests;
- redaction-report digest;
- nonclaims digest;
- claim boundary;
- `creates_accepted_evidence = false`;
- `creates_level2_evidence = false`;
- `populates_score_axes = false`;
- `grants_authority = false`.

The manifest must not include proof status above candidate metadata.

## Required Future Tests

A future implementation phase must add tests for:

- valid bundle materialization and readback;
- protected-root rejection;
- repository-root rejection;
- file-root rejection;
- symlink output-root rejection;
- symlink parent rejection;
- symlink declared-file rejection;
- symlink sidecar rejection;
- existing-root rejection without overwrite;
- stale-sidecar rejection;
- missing declared-file rejection;
- undeclared-file rejection;
- malformed JSON rejection;
- invalid nonclaims Markdown rejection;
- run-summary digest drift rejection;
- adapter-request/report digest drift rejection;
- certificate/output-manifest digest drift rejection;
- redaction-report drift rejection;
- nonclaim drift rejection;
- optional attachment rejection;
- accepted Evidence Ledger retention rejection;
- Level2+ evidence escalation rejection;
- score-axis population rejection;
- authority grant rejection;
- forbidden public claim text rejection.

## Anti-Goals

This phase does not permit:

- Rust implementation changes;
- Cargo metadata changes;
- package runtime files;
- filesystem bundle materialization code;
- proof assistant setup files;
- external repo clones;
- vendored source;
- Lean, Coq, TLA+, SMT, Z3, CBMC, model-checker, Aeneas, Hax, rust-lean, or
  COBALT execution;
- generated proof artifacts;
- generated checker transcripts;
- raw prover logs;
- raw checker logs;
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

The next implementation slice was completed as Phase 278. It added inert bundle
materialization and readback code for the declared Phase 277 layout in
`hsai-agent-admission`. It writes only `NotRun` metadata bundles, rejects
optional proof/checker attachments, and preserves all Phase 276 nonpromotion
rules.

The next responsible slice should add audit-first drift coverage for the Phase
278 bundle reader. It still should not run a backend.
