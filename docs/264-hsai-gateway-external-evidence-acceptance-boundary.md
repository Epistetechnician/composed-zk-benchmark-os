# Phase 264 HSAI Gateway External Evidence Acceptance Boundary

Status: complete for docs-first accepted-evidence promotion boundary.

## Purpose

Phase 264 defines the exact path from the current gateway-to-attestation bridge
to one reviewed accepted Evidence Ledger mutation. It does not implement that
mutation. It exists to prevent claim inflation before code touches accepted
evidence.

The bounded breakthrough target is:

```text
One concrete HSAI gateway admission case can be bound to fresh external
attestation evidence, reviewed, and admitted as a local accepted evidence
record without granting model authority, retaining credentials, retaining raw
provider payloads, creating Level2+ evidence, populating score axes, or claiming
production readiness.
```

This is a single-case secure inference gateway evidence path. It is not a claim
that all inference is secure.

## Current Inputs Already Built

The implementation phase must reuse these existing surfaces:

```text
crates/hsai-agent-admission/src/lib.rs
```

- `GatewayAttestationChallengeBinding`
- `GatewayOperatorArtifactReference`
- `GatewayOperatorBridgeBundle`
- `GatewayOperatorBridgeOutputManifest`
- `GatewayReportArtifactManifest`
- `GatewayReportMaterializationRequest`
- `GatewayReportOutputManifest`
- `GatewayReportOutputValidationReport`
- `GatewayOperatorBridgePromotionPreflightRequest`
- `GatewayOperatorBridgePromotionPreflightReport`
- `GatewayOperatorBridgePromotionReviewDecision::ApprovedMetadataOnly`
- `GatewayOperatorBridgeAcceptancePreviewRequest`
- `GatewayOperatorBridgeAcceptancePreviewReport`
- `GatewayOperatorBridgeAcceptancePreviewDecision::ApproveCandidateOnly`
- `GatewayOperatorBridgeAcceptancePreviewOutputManifest`
- `materialize_gateway_report_bundle`
- `read_gateway_report_bundle`
- `build_gateway_attestation_challenge_binding`
- `validate_gateway_attestation_challenge_binding`
- `build_gateway_operator_bridge_bundle`
- `validate_gateway_operator_bridge_bundle`
- `materialize_gateway_operator_bridge_bundle`
- `read_gateway_operator_bridge_bundle`
- `build_gateway_operator_bridge_promotion_preflight_report`
- `validate_gateway_operator_bridge_promotion_preflight_request`
- `build_gateway_operator_bridge_acceptance_preview_report`
- `validate_gateway_operator_bridge_acceptance_preview_request`
- `materialize_gateway_operator_bridge_acceptance_preview_bundle`
- `read_gateway_operator_bridge_acceptance_preview_bundle`

```text
crates/zkbench-core/src/evidence/accepted_append.rs
crates/zkbench-core/src/evidence/accepted_append_output.rs
```

- `AcceptedLedgerAppendTransactionRequest`
- `AcceptedLedgerAppendTransactionReport`
- `AcceptedLedgerAppendTransactionValidation`
- `validate_accepted_ledger_append_transaction_request`
- `apply_accepted_ledger_append_transaction`
- `apply_materialized_accepted_ledger_append_transaction`
- `build_evidence_record_from_transaction`
- `MaterializedAcceptedLedgerAppendRequest`
- `EvidenceLedger`
- `EvidenceRecord`
- `EvidenceRecordCandidate`
- `EvidenceAppendPreview`
- `ReviewedPromotionPreflightRequest`
- `ReviewedPromotionPreflightReport`

The current bridge stops at candidate-only acceptance preview. The future
implementation must map the gateway bridge evidence into the existing accepted
append transaction path instead of inventing a parallel ledger.

## Required Future State Slice

A future implementation phase may add a gateway-specific accepted-evidence
adapter with a narrow touch surface:

```text
crates/hsai-agent-admission/src/lib.rs
crates/hsai-agent-admission/tests/
crates/hsai-agent-admission/examples/
docs/
README.md
AGENTS.md
```

It may call existing `zkbench-core` accepted append APIs. It must not change
`zkbench-core` accepted-ledger semantics unless a separate explicit phase opens
that surface.

## Required Accepted Evidence Request Shape

The future request must be pure data and must include:

- gateway report output manifest digest;
- gateway action proposal digest;
- gateway admission policy id;
- gateway decision recomputation status;
- `authority_granted=false`;
- `GatewayAttestationChallengeBinding`;
- operator-live artifact reference digest;
- operator artifact path outside git;
- provider or verifier family label;
- redacted artifact digest table;
- reviewed bridge promotion preflight digest;
- source acceptance-preview digest;
- target accepted Evidence Ledger id;
- expected current ledger tip;
- human review decision id;
- explicit nonclaims.

The request must not include:

- raw provider response bodies;
- raw quotes;
- raw JWKS or OpenID documents;
- raw TLS exporters;
- credentials;
- secrets;
- private keys;
- model prompts or outputs beyond already typed gateway proposal metadata;
- endpoint tokens;
- bearer tokens;
- unbounded filesystem paths;
- network instructions.

## Required Evidence Class And Claim Boundary

The future accepted record must be capped at:

```text
claim_boundary <= Level1LocalReplay
```

The future accepted record must not use evidence classes that the accepted append
transaction already treats as Level2+ or formal evidence, including:

- `ReproducibleBenchmarkArtifact`;
- `CrossBackendReplay`;
- `FormalPropertyStatement`;
- `MachineCheckedScopedProof`;
- `IndependentlyReproducedEvidence`.

If an external attestation artifact is present, the record may describe it only
as an `Attested` input to the local gateway evidence path. It must not describe
the gateway decision as proven by the attestation.

## Required Verification Order

The future implementation must fail closed in this order:

1. Validate the gateway report output manifest.
2. Recompute the selected gateway proposal digest.
3. Recompute the gateway attestation challenge binding from proposal digest,
   anchor id, public key, nonce, and validity window.
4. Validate that the bridge bundle digest matches the gateway report digest,
   challenge binding digest, and operator artifact reference digest.
5. Validate that the promotion preflight report remains non-mutating and
   `ApprovedMetadataOnly`.
6. Validate that the acceptance preview remains `candidate_only=true` and
   `ApproveCandidateOnly`.
7. Validate the redacted operator artifact reference digest table.
8. Reject raw provider payload retention.
9. Reject credential or secret retention.
10. Reject authority grants.
11. Reject Level2+ evidence requests.
12. Reject score-axis population.
13. Reject production-readiness, semantic-correctness, SOTA, breakthrough, full
    security, or global uniqueness claim text.
14. Build a normal `AcceptedLedgerAppendTransactionRequest`.
15. Validate the transaction against the target `EvidenceLedger`.
16. Apply the transaction only after all prior checks pass.
17. Validate the resulting ledger.

## Required Output Shape

If materialized, the future accepted-evidence output root must be caller
selected, ignored by git, and contain only declared files:

```text
gateway-accepted-evidence/request.json
gateway-accepted-evidence/transaction.json
gateway-accepted-evidence/transaction-report.json
gateway-accepted-evidence/accepted-ledger-after.json
gateway-accepted-evidence/artifact-digests.json
gateway-accepted-evidence/nonclaims.md
gateway-accepted-evidence/validation-report.json
gateway-accepted-evidence/digests/request.sha256
gateway-accepted-evidence/digests/transaction.sha256
gateway-accepted-evidence/digests/transaction-report.sha256
gateway-accepted-evidence/digests/accepted-ledger-after.sha256
gateway-accepted-evidence/digests/artifact-digests.sha256
gateway-accepted-evidence/digests/nonclaims.sha256
gateway-accepted-evidence/digests/validation-report.sha256
```

The future implementation must reject:

- undeclared files;
- missing declared files;
- stale digest sidecars;
- symlink roots;
- symlink declared files;
- parent-directory traversal;
- absolute paths inside portable references;
- repository-root output paths;
- output roots overlapping `crates/`, `docs/`, `.git/`, `target/`, or any
  accepted ledger input file;
- partial bundle repair unless overwrite is explicit and the existing root
  already validates against the same request.

## Required Review Decision

The future implementation must require a new review decision that is stronger
than `ApproveCandidateOnly` but still bounded:

```text
ApproveGatewayExternalEvidenceForLocalAcceptedLedger
```

The decision must require:

- reviewer id;
- reviewed gateway report digest;
- reviewed attestation challenge digest;
- reviewed operator artifact digest table;
- reviewed accepted append transaction digest;
- explicit acknowledgement that the mutation is local accepted evidence only;
- explicit acknowledgement that no Level2+ evidence is created;
- explicit acknowledgement that no score axes are populated;
- explicit acknowledgement that no production-readiness, semantic-correctness,
  SOTA, breakthrough, full-security, or global-uniqueness claim is made.

## Required Tests

The future implementation must include focused tests for:

- valid single-case accepted evidence mutation;
- stale gateway report digest rejection;
- proposal digest drift rejection;
- challenge binding drift rejection;
- operator artifact digest drift rejection;
- missing operator artifact reference rejection;
- raw provider payload retention rejection;
- credential retention rejection;
- authority grant rejection;
- Level2+ evidence request rejection;
- score-axis population rejection;
- production-readiness claim rejection;
- semantic-correctness claim rejection;
- SOTA claim rejection;
- breakthrough claim rejection;
- stale target ledger tip rejection;
- invalid existing ledger rejection;
- source acceptance-preview drift rejection;
- accepted append transaction mismatch rejection;
- output root overlap rejection;
- undeclared-file rejection;
- stale-digest rejection;
- symlink rejection.

## Required Verifier Commands

The future implementation phase must pass at least:

```sh
cargo fmt --all --check
git diff --check
cargo test -p hsai-agent-admission --lib --quiet
cargo test -p hsai-agent-admission --test gateway_external_evidence_acceptance --quiet
cargo check -p hsai-agent-admission --examples
cargo test -p zkbench-core --test repo_hygiene --quiet
cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet
cargo test --workspace --quiet
cargo test --workspace --features external-runner --quiet
```

If the future phase adds an ignored example run, the run command and ignored
output-root status must also be recorded, and generated files must remain
uncommitted.

## Buyer-Facing Wording After Future Implementation

Allowed only after the future implementation accepts one gateway-bound external
evidence record:

```text
HSAI demonstrates a local accepted-evidence path for one secure inference
gateway case: model output remains a proposal, gateway policy decides before
authority, the gateway case is bound to an external attestation artifact by
digest, and the combined record is reviewed and appended to a local accepted
Evidence Ledger.
```

Short version:

```text
HSAI has one reproducible gateway-to-attestation accepted-evidence path for a
single local case.
```

## Nonclaims

Phase 264 does not claim:

- implemented accepted bridge evidence;
- accepted Evidence Ledger mutation;
- final bridge acceptance;
- Level2+ evidence;
- live provider evidence for a gateway case;
- live attestation capture in this phase;
- benchmark evidence;
- official benchmark submission;
- score-axis population;
- live gateway execution;
- live model behavior;
- verifier-agent runtime behavior;
- production readiness;
- semantic correctness;
- SOTA status;
- breakthrough status;
- full security;
- global software-agent uniqueness;
- any claim above `Attested`.

## Next Step

The next implementation slice is a gateway-specific accepted-evidence adapter
that maps one validated gateway bridge acceptance preview into the existing
`AcceptedLedgerAppendTransactionRequest` path, with all raw provider artifacts
and generated outputs kept outside git unless a separate reviewed phase allows
specific redacted digest artifacts.
