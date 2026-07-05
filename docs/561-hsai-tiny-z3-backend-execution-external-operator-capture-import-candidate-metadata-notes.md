# Phase 561 HSAI Tiny Z3 Backend Execution External Operator Capture Import Candidate Metadata Notes

State slice: `Phase 561 HSAI tiny Z3 backend execution external operator capture import candidate metadata`.

Phase 561 implements the local import-candidate metadata lane authorized by
Phase 560. It derives one quarantined in-memory `zkbench_core::ExternalResultCandidate`
from one exact Phase 559 external operator capture manifest, then records only
candidate, validation, validation-issue, and quarantine-record digests.

## Implemented Surface

- `GatewayFormalTinyZ3ExternalOperatorCaptureImportCandidateInput`;
- `GatewayFormalTinyZ3ExternalOperatorCaptureImportCandidate`;
- bounded classification, label, issue, and validation enums;
- Phase 561 schema, state-slice, and claim-boundary constants;
- nonclaim, blocker, rule, forbidden-API, and inherited-digest requirement helpers;
- Phase 559 manifest to `zkbench_core::ExternalResultCandidate` construction;
- `zkbench_core::validate_external_result_candidate` digest binding;
- `zkbench_core::external_result_quarantine_record` digest binding;
- fail-closed Phase 559 capture-state checks;
- fail-closed promotion-flag checks;
- focused tests for successful quarantined metadata, invalid Phase 559 state,
  and digest-drift plus promotion rejection.

## Required Bindings

The Phase 561 record binds:

- Phase 559 capture manifest digest;
- Phase 559 readback validation digest;
- Phase 559 nonpromotion report digest;
- Phase 557 handoff packet manifest/readback/nonpromotion digests;
- Phase 557 to Phase 555 handoff digest;
- Phase 555 manual handoff bundle and validation digests;
- Phase 553 import-review digest;
- inherited Phase 551, 549, 547, 545, 543, 541, 535, 533, 531, 529, and 527 digests;
- operator provenance, execution observation, captured-artifact index, and redaction report digests;
- quarantined external-result candidate digest;
- validation and validation-issue digests;
- quarantine-record digest;
- requested `ClaimBoundary::Level0DesignNote`.

## Validation

Focused tests:

```text
cargo test -p hsai-agent-admission --quiet phase561_tiny_z3_external_operator_capture_import_candidate
```

The tests verify that Phase 561 accepts a valid Phase 559 manifest, rejects a
Phase 559 manifest that claims external result import, and rejects candidate
digest drift plus attempted promotion.

## Claim Boundary

Phase 561 does not run an external replay, run a backend, run Lean, run
another SMT/Z3 execution, run COBALT, run Rust-to-Lean extraction, create
proof artifacts, create checker transcripts, create solver certificates,
write filesystem artifact bundles, import external results, mutate the
accepted Evidence Ledger, accept independent external reproduction, create
accepted formal evidence, create Level2+ evidence, populate score axes, create
benchmark evidence, establish external audit status, establish SOTA, prove
semantic correctness, establish production readiness, establish full security,
or grant authority to execute an action.

Evidence meaning is limited to:

```text
HSAI can derive a quarantined local external-result import candidate from a
locally validated operator capture packet.
```
