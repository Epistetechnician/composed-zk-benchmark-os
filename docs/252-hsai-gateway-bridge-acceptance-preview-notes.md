# Phase 252 HSAI Gateway Bridge Acceptance Preview Notes

Status: complete for local candidate-only acceptance preview metadata.

This phase adds a fail-closed preview over the Phase 251 gateway bridge
promotion preflight report. The preview can say that the local bridge preflight
is ready for a later reviewed acceptance path, but it remains candidate-only and
does not append to any accepted Evidence Ledger.

## State Slice

This phase touches:

- `crates/hsai-agent-admission/src/lib.rs`
- `docs/252-hsai-gateway-bridge-acceptance-preview-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No generated output was committed.

## Implemented Surface

`hsai-agent-admission` now includes:

- `GatewayOperatorBridgeAcceptancePreviewDecision`;
- `GatewayOperatorBridgeAcceptancePreviewRequest`;
- `GatewayOperatorBridgeAcceptancePreviewIssue`;
- `GatewayOperatorBridgeAcceptancePreviewValidation`;
- `GatewayOperatorBridgeAcceptancePreviewReport`;
- `gateway_operator_bridge_acceptance_preview_required_nonclaims`;
- `gateway_operator_bridge_acceptance_preview_request_schema_version`;
- `gateway_operator_bridge_acceptance_preview_claim_boundary`;
- `build_gateway_operator_bridge_acceptance_preview_report`;
- `validate_gateway_operator_bridge_acceptance_preview_request`.

The preview is valid only when:

- the request uses the Phase 252 schema version;
- the preview id is portable and non-empty;
- a reviewer id is present;
- the review decision is `ApproveCandidateOnly`;
- the source Phase 251 preflight report is valid and non-escalating;
- the expected preflight digest matches the source preflight report digest;
- the request stays `candidate_only=true`;
- no accepted Evidence Ledger mutation is requested;
- no Level2+ evidence is requested;
- no score-axis population is requested;
- no production-readiness, semantic-correctness, or live-provider-evidence
  claim is requested;
- no raw provider artifact retention, credential retention, or authority grant
  is requested;
- required nonclaims are present.

## Claim Boundary

The report claim boundary is:

```text
candidate-only gateway/operator bridge acceptance preview metadata; not
accepted evidence, final acceptance, ledger append, Level2+ evidence, live
provider evidence, production readiness, semantic correctness, SOTA,
breakthrough, full security, score-axis population, or authority to execute an
action
```

## Nonclaims

This phase does not prove:

- accepted bridge evidence;
- final acceptance;
- ledger append;
- accepted Evidence Ledger mutation;
- Level2+ evidence;
- score-axis population;
- raw provider artifact validation;
- credential handling;
- live provider evidence;
- benchmark evidence;
- production readiness;
- semantic correctness;
- SOTA status;
- breakthrough status;
- full security;
- signer, wallet, exchange, custody, ACP, MCP, or tool authority;
- any claim above `Attested`.

## Validation Commands

The following focused commands passed during implementation:

```sh
cargo fmt --all
cargo fmt --all --check
git diff --check
cargo test -p hsai-agent-admission --lib gateway_operator_bridge_acceptance_preview
cargo test -p hsai-agent-admission --lib gateway_operator_bridge_promotion_preflight --quiet
```

The final validation ladder also passed:

```sh
cargo test -p hsai-agent-admission --lib --quiet
cargo test -p zkbench-core --test repo_hygiene --quiet
cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet
cargo check -p hsai-agent-admission --examples
cargo test --workspace --features external-runner --quiet
cargo test --workspace --quiet
```

## Next Evidence Step

The next bridge candidate is an ignored local preview bundle/run artifact for
the Phase 252 report. It should remain local, reproducible, and ignored, and it
must still not mutate accepted evidence.
