# Phase 273 HSAI Gateway Formal Backend Adapter Inert Metadata Notes

State slice: `Phase 273 HSAI gateway formal backend-adapter inert metadata`.

## Status

Complete for local inert backend-adapter request/report metadata.

## Scope

This phase implements the first code surface from the Phase 272 backend-adapter
boundary. It does not run Lean, SMT, COBALT, or any external tool.

The implemented `hsai-agent-admission` surface is:

- `GatewayFormalBackendAdapterRequest`
- `GatewayFormalBackendAdapterReport`
- `GatewayFormalBackendAdapterValidation`
- `GatewayFormalBackendAdapterIssue`
- `GatewayFormalBackendAdapterStatus`
- `GatewayFormalBackendAdapterMaturity`
- `gateway_formal_backend_adapter_required_nonclaims`
- `gateway_formal_backend_adapter_claim_boundary`
- `validate_gateway_formal_backend_adapter_request`
- `build_gateway_formal_backend_adapter_report`

## Valid Request Contract

A valid request must bind:

- Phase 273 schema version;
- Phase 273 state slice;
- gateway binding property kind;
- `RustToLean` backend kind;
- valid Phase 268 correspondence-certificate digest;
- valid Phase 270 output-manifest digest;
- matching output-manifest certificate digest;
- matching source commit;
- matching source-file digest set;
- matching source anchors;
- matching proof obligations;
- nonempty future tool metadata;
- nonzero toolchain lock digest;
- `NotRun` tool execution status;
- required model assumptions;
- required modeled replacements;
- explicit unsupported Rust features;
- matching input/output schema digest;
- expected future proof artifact format;
- expected future checker transcript format;
- `NotRun` maturity;
- explicit nonclaims;
- Phase 273 claim boundary.

## Fail-Closed Checks

Validation rejects:

- schema drift;
- unsafe adapter ids;
- state-slice drift;
- unsupported property kind;
- backend kind other than `RustToLean`;
- invalid correspondence certificates;
- certificate digest mismatch;
- output-manifest digest mismatch;
- output-manifest certificate digest mismatch;
- output-manifest claim-boundary drift;
- output-manifest escalation flags;
- source commit drift;
- source-file drift;
- source-anchor drift;
- proof-obligation drift;
- tool backend mismatch;
- empty tool name or version;
- missing toolchain lock digest;
- executed backend status;
- missing model assumptions;
- missing modeled replacements;
- unsupported Rust feature silence;
- missing or mismatched input/output schema digest;
- missing expected proof artifact format;
- missing expected checker transcript format;
- proof artifact digest submission;
- checker transcript digest submission;
- maturity above `NotRun`;
- requested claim-boundary drift;
- formal backend execution request;
- accepted Evidence Ledger mutation request;
- Level2+ evidence request;
- score-axis population request;
- production-readiness claim;
- semantic-correctness claim;
- SOTA claim;
- full-security claim;
- authority-grant request;
- forbidden public claim text;
- missing required nonclaims.

## Validation

Executed:

```bash
cargo test -p hsai-agent-admission gateway_formal_backend_adapter
```

Result: passed.

Focused tests cover:

- valid inert metadata report construction;
- certificate/output manifest digest binding;
- source, anchor, proof-obligation, backend, tool, assumption, replacement, and
  schema drift rejection;
- backend execution, proof artifact, checker transcript, maturity, accepted
  evidence, Level2+, score-axis, production-readiness, semantic-correctness,
  SOTA, full-security, authority, forbidden text, and nonclaim escalation
  rejection.

## Nonclaims

This phase does not run Lean, Coq, TLA+, SMT, Z3, CBMC, model checkers, Aeneas,
Hax, rust-lean, COBALT, VeriSoftBench, Federated Formal Verification, or
certificate-explanation tooling.

It does not clone external repositories, vendor source, create proof assistant
setup files, generate proof artifacts, generate checker transcripts, mutate
accepted evidence, populate score axes, submit benchmark results, call live
providers, handle credentials, prove semantic correctness, establish production
readiness, establish SOTA, establish breakthrough status, establish full
security, or grant execution authority.

The report is candidate metadata only.

## Next Slice

Phase 274 adds audit-first negative coverage for the Phase 273 adapter
metadata, focused on output-manifest drift, invalid certificate nesting,
request identity drift, and claim-boundary drift. Do not run a backend until a
future docs-first backend-run artifact boundary is accepted.
