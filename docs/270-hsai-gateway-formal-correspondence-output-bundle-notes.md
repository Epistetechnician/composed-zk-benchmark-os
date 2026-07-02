# Phase 270 HSAI Gateway Formal Correspondence Output Bundle Notes

State slice: `Phase 270 HSAI gateway formal correspondence output-bundle implementation`.

## Status

Complete for local filesystem materialization and readback of the Phase 268
formal correspondence certificate bundle.

## Scope

This phase implements the Phase 269 output-bundle contract inside
`hsai-agent-admission`. It materializes a local, declared-file bundle for one
valid `GatewayFormalCorrespondenceCertificate` and validates readback without
running any formal backend.

The implemented surface is:

- `GatewayFormalCorrespondenceOutputRequest`
- `GatewayFormalCorrespondenceOutputManifest`
- `GatewayFormalCorrespondenceOutputValidationReport`
- `GatewayFormalCorrespondenceRedactionReport`
- `GatewayFormalCorrespondenceOutputError`
- `materialize_gateway_formal_correspondence_bundle`
- `read_gateway_formal_correspondence_bundle`

## Declared Files

The bundle writes only this logical file set:

```text
gateway-formal-correspondence/certificate.json
gateway-formal-correspondence/validation-report.json
gateway-formal-correspondence/source-files.json
gateway-formal-correspondence/source-anchors.json
gateway-formal-correspondence/proof-obligations.json
gateway-formal-correspondence/assumptions.md
gateway-formal-correspondence/nonclaims.md
gateway-formal-correspondence/redaction-report.json
gateway-formal-correspondence/manifest.json
```

Each declared file receives a matching `.sha256` sidecar. The manifest records
the certificate digest, component digests, declared files, claim boundary, and
nonclaim flags.

## Fail-Closed Behavior

Materialization rejects:

- invalid correspondence certificates;
- empty bundle ids;
- empty output roots;
- protected output roots;
- file output roots;
- symlink output roots;
- existing output roots without explicit overwrite;
- serialization and filesystem failures.

Readback rejects:

- missing declared files;
- symlinked declared files;
- symlinked sidecars;
- undeclared files under `gateway-formal-correspondence/`;
- stale digest sidecars;
- malformed declared JSON;
- manifest drift;
- validation-report drift;
- redaction-report drift;
- nonclaim drift;
- claim-boundary escalation.

Writes are staged before the final output root is moved into place.

## Validation

Executed:

```bash
cargo test -p hsai-agent-admission gateway_formal_correspondence_bundle
```

Result: passed.

Focused tests cover:

- materializing declared files and sidecars;
- readback of a valid local bundle;
- invalid certificate rejection before output;
- undeclared file rejection;
- nonclaim drift rejection;
- redaction-report drift rejection.

## Nonclaims

This phase does not run Lean, Coq, TLA+, SMT, Z3, CBMC, model checkers, Aeneas,
Rust-to-Lean extraction, COBALT, VeriSoftBench, Federated Formal Verification,
or certificate-explanation tooling.

It does not clone external repositories, vendor source, create proof assistant
setup files, generate proof artifacts, retain raw prover logs, retain raw solver
transcripts, mutate accepted evidence, populate score axes, submit benchmark
results, call live providers, handle credentials, prove semantic correctness,
establish production readiness, establish SOTA, establish breakthrough status,
establish full security, or grant execution authority.

Readback success means only that the local correspondence bundle is internally
consistent with the metadata certificate and declared nonclaims.

## Next Slice

Phase 271 adds audit-first negative coverage for output-root, sidecar,
manifest, validation-report, symlink, and claim-boundary drift. After that, the
next useful formal-verification slice should be docs-first: define the first
tiny backend-specific proof-adapter boundary without running the backend.
