# Phase 271 HSAI Gateway Formal Correspondence Output Bundle Drift Coverage Notes

State slice: `Phase 271 HSAI gateway formal correspondence output-bundle drift coverage`.

## Status

Complete for audit-first negative coverage over the Phase 270 local output
bundle.

## Scope

This phase adds focused hermetic tests for the local
`gateway-formal-correspondence/*` output-bundle materializer and readback path.
It does not change the output format or add proof authority.

The covered failure classes are:

- existing output root without overwrite;
- file output root;
- protected output root;
- symlink output root;
- symlink bundle directory;
- symlink declared file;
- symlink sidecar;
- missing declared sidecar;
- stale sidecar digest;
- malformed manifest JSON with a matching sidecar;
- validation-report semantic drift with a matching sidecar;
- manifest claim-boundary escalation with a matching sidecar.

These tests supplement the Phase 270 coverage for valid materialization,
readback, invalid certificate rejection, undeclared file rejection, nonclaim
drift, and redaction drift.

## Validation

Executed:

```bash
cargo test -p hsai-agent-admission gateway_formal_correspondence_bundle
```

Result: passed.

The focused selector now runs eight bundle tests.

## Nonclaims

This phase is test coverage only. It does not run Lean, Coq, TLA+, SMT, Z3,
CBMC, model checkers, Aeneas, Rust-to-Lean extraction, COBALT, VeriSoftBench,
Federated Formal Verification, or certificate-explanation tooling.

It does not clone external repositories, vendor source, create proof assistant
setup files, generate proof artifacts, retain raw prover logs, retain raw solver
transcripts, mutate accepted evidence, populate score axes, submit benchmark
results, call live providers, handle credentials, prove semantic correctness,
establish production readiness, establish SOTA, establish breakthrough status,
establish full security, or grant execution authority.

## Next Slice

The next useful formal-verification slice should be docs-first: define the first
backend-specific proof-adapter boundary for this gateway property, including
input extraction, source correspondence, tool lock disclosure, proof artifact
shape, benchmark hooks, and the exact evidence cap. It must not run the backend
until that boundary is accepted.
