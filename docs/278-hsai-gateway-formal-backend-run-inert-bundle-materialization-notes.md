# Phase 278 HSAI Gateway Formal Backend Run Inert Bundle Materialization Notes

State slice: `Phase 278 HSAI gateway formal backend-run inert bundle materialization`.

## Status

Complete for local `NotRun` backend-run bundle materialization and readback.

## Purpose

Phase 277 defined the docs-first filesystem contract for a future
`gateway-formal-backend-run/*` bundle. Phase 278 implements the inert local
writer and reader for that declared layout in `hsai-agent-admission`.

This phase materializes metadata only. It does not run a backend.

## Implemented Surface

Phase 278 adds:

- `GatewayFormalBackendRunOutputRequest`;
- `GatewayFormalBackendRunToolchainLock`;
- `GatewayFormalBackendRunRedactionReport`;
- `GatewayFormalBackendRunOutputManifest`;
- `GatewayFormalBackendRunOutputError`;
- declared `gateway-formal-backend-run/*` file and sidecar constants;
- `gateway_formal_backend_run_declared_files`;
- `materialize_gateway_formal_backend_run_bundle`;
- `read_gateway_formal_backend_run_bundle`;
- local semantic validation for the materialized bundle.

The writer emits exactly:

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

Every declared file gets a `.sha256` sidecar.

## Binding Rules

The manifest binds:

- adapter request digest;
- adapter report digest;
- run-summary digest;
- correspondence-certificate digest;
- correspondence output-manifest digest;
- source-digests file digest;
- toolchain-lock file digest;
- model-assumptions file digest;
- unsupported-Rust-features file digest;
- proof-obligations file digest;
- redaction-report digest;
- nonclaims digest;
- declared file digests;
- claim boundary;
- nonpromotion flags.

Readback validates the run summary against the adapter request and report, then
checks each materialized metadata file against that same chain.

## Fail-Closed Checks

The writer rejects:

- invalid bundle ids;
- protected output roots;
- existing output roots without overwrite;
- file output roots;
- symlink output roots;
- invalid Phase 276 run metadata;
- execution-mode escalation;
- Level2+ evidence escalation;
- accepted-evidence creation;
- score-axis population;
- authority grants;
- forbidden public claim text.

Readback rejects:

- missing declared files;
- undeclared files;
- optional proof/checker/tool-log attachments;
- symlink bundle directories;
- symlink declared files;
- symlink sidecars;
- stale sidecars;
- malformed JSON;
- digest-consistent semantic drift;
- manifest semantic drift;
- redaction-report drift;
- nonclaim drift.

## Tests

Focused tests cover:

- valid bundle materialization and readback;
- declared-file and sidecar presence;
- nonpromotion manifest flags;
- escalated run metadata rejection before write;
- optional proof artifact attachment rejection;
- digest-consistent source-digest semantic drift rejection.

## Nonclaims

Phase 278 does not:

- run Lean, SMT, COBALT, Aeneas, Hax, rust-lean, Z3, CBMC, Coq, TLA+, or any
  formal backend;
- create proof artifacts;
- create checker transcripts;
- retain raw prover logs;
- retain raw checker logs;
- retain raw solver traces;
- clone external repositories;
- vendor external source;
- mutate accepted Evidence Ledger files;
- create accepted evidence;
- create Level2+ evidence;
- populate score axes;
- create benchmark evidence;
- submit to an official benchmark;
- establish semantic correctness;
- establish production readiness;
- establish SOTA;
- establish breakthrough status;
- establish full security;
- prove HSAI;
- grant authority to execute an action.

## Next Slice

The next responsible slice was completed as Phase 279. It added audit-first
drift coverage for the Phase 278 bundle reader: protected roots, file roots,
symlink roots, stale sidecars, manifest drift, redaction drift, nonclaim drift,
malformed run-summary JSON, and symlinked declared files.

The following responsible slice should be a docs-first backend execution
preflight boundary. It still should not run a backend.
