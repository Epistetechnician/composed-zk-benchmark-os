# Phase 307 HSAI Gateway Formal Backend Hermetic Execution Result Quarantine Output-Bundle Boundary

State slice: `Phase 307 HSAI gateway formal backend hermetic execution result quarantine output-bundle boundary`.

## Status

Complete for the docs-first hermetic execution result quarantine output-bundle
boundary.

## Purpose

Phase 306 materialized and read back the Phase 304 no-spawn descriptor report.
Phase 307 defines the future declared-file output-bundle boundary for the first
local hermetic execution result shape.

This phase does not add Rust code, does not spawn a process, and does not run
SMT, Z3, COBALT, Lean, or any formal backend.

## Future Bundle Scope

A future implementation may materialize only the bounded, redacted, local
candidate result of the `local_smt_tiny_gateway_invariant` lane under:

`gateway-formal-backend-hermetic-execution-result-quarantine/*`

The future bundle may be produced only after:

- a valid Phase 304 no-spawn descriptor;
- a valid Phase 306 descriptor-report output-bundle readback result;
- an explicit caller-selected output root;
- a direct-process no-shell command contract;
- a fixed backend id of `local_smt_tiny_gateway_invariant`;
- fixed argv policy;
- empty or allowlisted environment policy;
- timeout and stdout/stderr byte limits;
- redaction policy;
- declared output inventory policy.

The bundle must remain quarantined local candidate metadata. It must not become
accepted evidence, Level2+ evidence, benchmark evidence, proof evidence,
checker transcript evidence, semantic correctness, production readiness, SOTA
status, breakthrough status, full security, or action authority.

## Future Declared Files

A future bundle should use exactly this logical namespace:

- `gateway-formal-backend-hermetic-execution-result-quarantine/manifest.json`;
- `gateway-formal-backend-hermetic-execution-result-quarantine/execution-status.json`;
- `gateway-formal-backend-hermetic-execution-result-quarantine/input-binding.json`;
- `gateway-formal-backend-hermetic-execution-result-quarantine/command-contract.json`;
- `gateway-formal-backend-hermetic-execution-result-quarantine/stdout-summary.json`;
- `gateway-formal-backend-hermetic-execution-result-quarantine/stderr-summary.json`;
- `gateway-formal-backend-hermetic-execution-result-quarantine/redaction-report.json`;
- `gateway-formal-backend-hermetic-execution-result-quarantine/output-inventory.json`;
- `gateway-formal-backend-hermetic-execution-result-quarantine/invariant-verdict.json`;
- `gateway-formal-backend-hermetic-execution-result-quarantine/nonpromotion-report.json`;
- `gateway-formal-backend-hermetic-execution-result-quarantine/validation.json`;
- `gateway-formal-backend-hermetic-execution-result-quarantine/nonclaims.md`.

Each declared file must have a sibling `.sha256` sidecar containing the SHA-256
digest of the exact materialized bytes.

The future readback implementation must reject every undeclared file and
directory, including raw stdout, raw stderr, raw solver traces, raw prover logs,
raw checker logs, proof artifacts, checker transcripts, solver certificates,
proof assistant caches, external repo source, accepted Evidence Ledger files,
Level2+ evidence files, benchmark outputs, score-axis outputs, and any earlier
formal-bundle namespace nested inside the quarantine bundle.

## Future Manifest Fields

The future manifest must bind:

- schema version;
- bundle id;
- state slice;
- created-at timestamp supplied by the caller;
- descriptor digest;
- descriptor-report output manifest digest;
- descriptor-report validation digest;
- input binding digest;
- command contract digest;
- execution status digest;
- stdout summary digest;
- stderr summary digest;
- redaction report digest;
- output inventory digest;
- invariant verdict digest;
- nonpromotion report digest;
- validation digest;
- nonclaims digest;
- backend id;
- backend kind;
- tool name;
- tool version label;
- executable path label;
- argv template digest;
- environment policy digest;
- output-root label digest;
- timeout milliseconds;
- maximum stdout bytes;
- maximum stderr bytes;
- process exit code label;
- timeout flag;
- signal flag;
- solver status label;
- invariant verdict label;
- declared files;
- declared file digest map;
- claim boundary;
- process-spawned flag;
- backend-executed flag;
- proof-artifact-created flag;
- checker-transcript-created flag;
- solver-certificate-created flag;
- accepted-evidence-created flag;
- Level2+ evidence-created flag;
- score-axis-populated flag;
- semantic-correctness-claimed flag;
- production-readiness-claimed flag;
- SOTA-claimed flag;
- breakthrough-claimed flag;
- full-security-claimed flag;
- action-authority-granted flag;
- required nonclaim labels.

`process-spawned` and `backend-executed` may become true only inside the future
explicit implementation phase that actually crosses the backend-execution
boundary. Every proof, evidence, score, readiness, SOTA, security, semantic, and
authority flag must remain false.

## Future Execution Status Meaning

The future `execution-status.json` file may report only:

- backend id and backend kind;
- tool name and local tool version label;
- start and finish timestamps;
- wall-clock timeout classification;
- process exit code label;
- timeout flag;
- signal flag;
- stdout and stderr truncation flags;
- solver status label;
- invariant verdict label;
- command descriptor digest;
- input binding digest;
- output inventory digest.

It must not report that a proof was accepted, a solver certificate was accepted,
a checker transcript was promoted, an Evidence Ledger changed, a benchmark ran,
score axes were populated, HSAI is semantically correct, HSAI is production
ready, HSAI is SOTA, HSAI is a breakthrough, HSAI is fully secure, or any action
authority exists.

## Future Readback Rules

A future readback implementation must:

- reject protected output roots;
- reject existing output roots unless explicit overwrite is set;
- use a staging directory before final rename;
- reject output-root symlinks;
- reject bundle-directory symlinks;
- reject declared-file symlinks;
- reject declared-sidecar symlinks;
- reject missing declared files;
- reject missing declared sidecars;
- reject stale sidecars;
- reject undeclared files;
- reject undeclared directories;
- reject malformed declared JSON;
- reject malformed UTF-8 Markdown;
- recompute every declared-file digest;
- recompute the manifest from read bytes;
- reject descriptor digest drift;
- reject descriptor-report manifest drift;
- reject command-contract drift;
- reject input-binding drift;
- reject execution-status drift;
- reject stdout-summary drift;
- reject stderr-summary drift;
- reject redaction-report drift;
- reject output-inventory drift;
- reject invariant-verdict drift;
- reject nonpromotion-report drift;
- reject validation drift;
- reject nonclaim Markdown drift;
- reject process-spawned drift outside the explicit future execution phase;
- reject proof-artifact flag drift;
- reject checker-transcript flag drift;
- reject solver-certificate flag drift;
- reject accepted-evidence flag drift;
- reject Level2+ flag drift;
- reject score-axis flag drift;
- reject semantic-correctness claim drift;
- reject production-readiness claim drift;
- reject SOTA claim drift;
- reject breakthrough claim drift;
- reject full-security claim drift;
- reject action-authority drift.

## Future Validation Report

The future `validation.json` file should state only that the quarantined local
execution-result bundle passed declared-file, sidecar, bounded-output,
redaction, nonpromotion, and claim-boundary checks.

It must not state that:

- Lean proof exists;
- COBALT containment proof exists;
- Rust-to-Lean extraction succeeded;
- a proof artifact is accepted evidence;
- a checker transcript is accepted evidence;
- a solver certificate is accepted evidence;
- accepted Evidence Ledger state changed;
- Level2+ evidence exists;
- score axes are populated;
- benchmark evidence exists;
- HSAI is semantically correct;
- HSAI is production ready;
- HSAI is SOTA;
- HSAI is a breakthrough;
- HSAI is fully secure;
- the gateway has authority to execute an action.

## Required Future Tests

The implementation slice should include focused tests for:

- valid declared-file materialization and readback;
- invalid descriptor-report bundle rejection before write;
- unsafe bundle id rejection;
- protected output-root rejection;
- existing output-root overwrite rejection;
- missing sidecar rejection;
- stale sidecar rejection;
- malformed execution-status JSON rejection;
- malformed invariant-verdict JSON rejection;
- manifest semantic drift rejection;
- descriptor digest drift rejection;
- descriptor-report output manifest drift rejection;
- command-contract drift rejection;
- input-binding drift rejection;
- execution-status drift rejection;
- stdout-summary drift rejection;
- stderr-summary drift rejection;
- redaction-report drift rejection;
- output-inventory drift rejection;
- invariant-verdict drift rejection;
- nonpromotion-report drift rejection;
- validation drift rejection;
- nonclaim Markdown drift rejection;
- undeclared raw stdout rejection;
- undeclared raw stderr rejection;
- undeclared solver trace rejection;
- undeclared prover log rejection;
- undeclared checker log rejection;
- undeclared proof artifact rejection;
- undeclared checker transcript rejection;
- undeclared solver certificate rejection;
- undeclared accepted Evidence Ledger file rejection;
- undeclared Level2+ evidence file rejection;
- undeclared benchmark output rejection;
- undeclared score-axis output rejection;
- nested earlier formal-bundle rejection;
- output-root symlink rejection;
- bundle-directory symlink rejection;
- declared-file symlink rejection;
- declared-sidecar symlink rejection;
- semantic-correctness claim rejection;
- production-readiness claim rejection;
- SOTA claim rejection;
- breakthrough claim rejection;
- full-security claim rejection;
- action-authority claim rejection.

## Anti-Goals

This phase does not permit:

- Rust implementation changes;
- Cargo metadata changes;
- package runtime files;
- filesystem materialization behavior;
- command execution;
- process spawning;
- backend runner implementation;
- proof assistant setup files;
- external repo clones;
- vendored source;
- Lean, Coq, TLA+, SMT, Z3, CBMC, model-checker, Aeneas, Hax, rust-lean, or
  COBALT execution;
- generated proof artifact promotion;
- generated checker transcript promotion;
- solver certificate promotion;
- raw prover log retention;
- raw checker log retention;
- raw solver trace retention;
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

Phase 308 implements this local result-quarantine output-bundle boundary with
not-run materialization, readback, sidecar checks, bounded-output validation,
nonpromotion checks, and focused negative tests. Actual backend process spawning
should remain deferred until the result-quarantine output bundle and its drift
coverage are stable.
