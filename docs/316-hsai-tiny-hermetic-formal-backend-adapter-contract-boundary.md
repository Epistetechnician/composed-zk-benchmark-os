# Phase 316 HSAI Tiny Hermetic Formal-Backend Adapter Contract Boundary

State slice: `Phase 316 HSAI tiny hermetic formal-backend adapter contract boundary`.

## Status

Complete for a docs-first contract boundary before any new real backend runner.

## Purpose

Phase 316 defines the narrow contract that must exist before HSAI can
responsibly move from the Phase 313 fixture-process crossing toward a real
Lean/SMT/Z3/COBALT backend run.

This phase does not add Rust implementation code. It does not run Lean, SMT,
Z3, COBALT, Aeneas, Hax, rust-lean, Coq, TLA+, CBMC, or a model checker. It
does not create proof artifacts, checker transcripts, solver certificates,
accepted evidence, Level2+ evidence, score axes, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, or authority.

## Phase Chain

The contract is wired to the existing formal-backend sequence:

- Phase 265: ranked formal-verification evidence architecture boundary;
- Phase 266: local gateway formal-evidence metadata adapter;
- Phase 267: source-correspondence boundary for the attestation challenge
  binding property;
- Phase 268: correspondence-certificate metadata;
- Phase 272-279: inert backend-adapter and backend-run metadata surfaces;
- Phase 280-302: preflight, transcript, authorization, quarantine, and
  validation-summary metadata surfaces;
- Phase 303-314: hermetic execution descriptor, no-default-runner interface,
  fixture-process crossing, and fixture-runner hardening;
- Phase 315: Mesh repo-patch admission compatibility.

Phase 316 does not supersede those phases. It binds the next implementation
slice to them.

## Target Invariant

The first executable formal-backend contract is limited to one non-secret
gateway invariant:

`gateway attestation challenge binding is deterministic for identical inputs and changes when the nonce or gateway action proposal changes`

The only source anchors in scope are:

- `GatewayAttestationChallengeBinding`;
- `GatewayAttestationChallengeBinding::digest`;
- `gateway_attestation_binding_from_proposal`;
- `validate_gateway_attestation_challenge_binding`;
- `GatewayFormalEvidencePropertyKind::AttestationChallengeBindingDeterministicInputSensitive`;
- `GatewayFormalBackendHermeticInvariantProperty::AttestationChallengeBindingDeterminism`;
- imported `report_data_binding`.

The `report_data_binding` dependency must remain explicit. A backend adapter may
either model it with the existing length-prefixed SHA-256 transcript assumption
or mark it as an open imported assumption. It may not silently treat imported
hashing behavior as proved HSAI semantics.

## Adapter Contract

A future implementation phase may introduce a tiny adapter request only if it is
bound to the existing Phase 312 no-default-runner interface and the Phase 313
fixture-runner quarantine rules.

The request must declare:

- adapter id: `tiny_hermetic_formal_backend_adapter`;
- backend id: `local_smt_tiny_gateway_invariant`;
- property id:
  `attestation_challenge_binding_deterministic_input_sensitive`;
- source correspondence certificate digest from Phase 268 or later;
- descriptor-report manifest digest from Phase 306 or later;
- process-spawn interface digest from Phase 312 or later;
- fixed input fixture digest;
- fixed command descriptor digest;
- expected transcript schema digest;
- explicit operator acknowledgement;
- required nonclaims.

The command descriptor must remain:

- direct process only;
- no shell;
- null stdin;
- cleared or explicit allowlisted environment;
- fixed executable label;
- fixed argv template;
- fixed timeout;
- bounded stdout and stderr;
- no network;
- no caller-supplied executable path;
- no output-root authority except the ignored quarantine root.

## Fixture Inputs

The first executable fixture must be a non-secret JSON fixture with:

- one baseline gateway action proposal digest;
- one changed gateway action proposal digest;
- one baseline nonce;
- one changed nonce;
- one anchor id;
- one public agent key digest or fixture byte string;
- expected deterministic binding equality for identical inputs;
- expected binding inequality for changed proposal digest;
- expected binding inequality for changed nonce;
- explicit imported `report_data_binding` assumption text.

No live attestation token, credential, operator secret, provider response, raw
quote, raw solver log, or external artifact may be used.

## Transcript Contract

A future checker transcript must be quarantined and must contain only bounded
metadata:

- transcript schema version;
- backend id;
- property id;
- command descriptor digest;
- input fixture digest;
- source correspondence certificate digest;
- process exit label;
- timeout flag;
- solver/checker status;
- invariant verdict;
- stdout summary digest;
- stderr summary digest;
- redaction report digest;
- imported-assumption list;
- nonpromotion report digest;
- required nonclaims.

The transcript may not contain raw solver traces, raw prover logs, raw checker
logs, proof artifacts, solver certificates, accepted evidence entries,
score-axis values, secrets, credentials, or provider responses.

## Quarantine And Nonpromotion

All future executable outputs must land in the existing quarantine model before
any evidence decision.

The quarantine reader must reject:

- missing or stale SHA-256 sidecars;
- undeclared files;
- symlinked roots, bundle directories, files, or sidecars;
- raw stdout or stderr retention;
- raw solver trace retention;
- proof artifact retention;
- checker transcript promotion;
- solver-certificate promotion;
- accepted Evidence Ledger mutation;
- Level2+ evidence creation;
- score-axis population;
- semantic-correctness claims;
- production-readiness claims;
- SOTA or breakthrough claims;
- full-security claims;
- authority grants.

The accepted evidence boundary remains blocked by
`crates/zkbench-core/src/evidence/accepted_append.rs`. No Phase 316 artifact is
eligible to bypass the existing `Level1LocalReplay` ceiling or to become
accepted formal evidence.

## Implementation Exit Criteria

A later implementation phase may cross from this boundary into Rust only when it
can add all of the following in one narrow slice:

- typed tiny-adapter request and validation types;
- typed non-secret fixture input;
- typed transcript summary;
- typed nonpromotion report;
- materialization and readback of a declared-file quarantine bundle;
- focused tests for valid fixture execution through the already bounded
  process path;
- negative tests for shell, environment, stdin, network, executable-path,
  output-root, raw-log, proof-artifact, checker-transcript, solver-certificate,
  accepted-evidence, Level2+, score-axis, semantic-correctness,
  production-readiness, SOTA, and full-security escalation;
- source-scan preservation showing no widened process/network exception beyond
  the named implementation lines.

That future phase still must not claim proof authority unless a later checker
phase validates the transcript and the imported assumptions are explicit.

## Validation

Required validation for this docs-first slice:

```text
cargo fmt --all -- --check
cargo test -p hsai-e2e-harness --test claim_boundary_source_scan
cargo test -p zkbench-core --test repo_claim_boundary_docs --test repo_hygiene
git diff --check
find README.md AGENTS.md docs crates -type f -empty
pnpm run lint, if package.json exists
cargo test --workspace
```

## Next Slice

Phase 317 may implement the tiny hermetic adapter data model and quarantine
bundle if it stays within the Phase 316 contract. It should still use a fixed
local fixture and must not run Lean/SMT/Z3/COBALT as proof authority, create
accepted evidence, create Level2+ evidence, populate score axes, or claim
semantic correctness, production readiness, SOTA, breakthrough status, full
security, or authority.
