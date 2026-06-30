# Phase 251 HSAI Gateway Bridge Promotion Preflight Notes

Status: complete for local reviewed promotion preflight metadata.

This phase adds a fail-closed preflight report for the Phase 250
gateway/operator bridge bundle. The preflight validates local bridge metadata,
the bridge manifest digest surface, and the repo-external operator artifact
reference digest. It does not promote the bridge bundle into accepted evidence.

## State Slice

This phase touches:

- `crates/hsai-agent-admission/src/lib.rs`
- `docs/251-hsai-gateway-bridge-promotion-preflight-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No generated output was committed.

## Implemented Surface

`hsai-agent-admission` now includes:

- `GatewayOperatorBridgePromotionReviewDecision`;
- `GatewayOperatorBridgePromotionPreflightRequest`;
- `GatewayOperatorBridgePromotionPreflightIssue`;
- `GatewayOperatorBridgePromotionPreflightValidation`;
- `GatewayOperatorBridgePromotionPreflightReport`;
- `gateway_operator_bridge_promotion_preflight_required_nonclaims`;
- `gateway_operator_bridge_promotion_preflight_request_schema_version`;
- `gateway_operator_bridge_promotion_preflight_claim_boundary`;
- `build_gateway_operator_bridge_promotion_preflight_report`;
- `validate_gateway_operator_bridge_promotion_preflight_request`.

The preflight is valid only when:

- the request uses the Phase 251 schema version;
- the preflight id is portable and non-empty;
- a reviewer id is present;
- the review decision is `ApprovedMetadataOnly`;
- the bridge bundle passes Phase 250 validation;
- the bridge manifest matches the bridge bundle digests and declared file map;
- the operator artifact reference remains repo-external;
- no raw provider artifacts or credentials are retained;
- no accepted Evidence Ledger mutation is requested;
- no Level2+ evidence is requested;
- no score-axis population is requested;
- no production-readiness, semantic-correctness, or live-provider-evidence
  claim is requested;
- required nonclaims are present.

## Claim Boundary

The report claim boundary is:

```text
reviewed local gateway/operator bridge preflight metadata only; not promotion,
accepted evidence, Level2+ evidence, live provider evidence, production
readiness, semantic correctness, SOTA, breakthrough, full security,
score-axis population, or authority to execute an action
```

## Nonclaims

This phase does not prove:

- bridge promotion;
- reviewed evidence acceptance;
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

The operator-live artifact remains a repo-external digest reference only.

## Validation Commands

The following focused commands passed during implementation:

```sh
cargo fmt --all --check
git diff --check
cargo test -p hsai-agent-admission --lib gateway_operator_bridge_promotion_preflight
cargo test -p hsai-agent-admission --lib gateway_operator_bridge --quiet
```

The final validation ladder also passed:

```sh
cargo test -p hsai-agent-admission --lib --quiet
cargo test -p zkbench-core --test repo_hygiene --quiet
cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet
cargo test --workspace --quiet
cargo test --workspace --features external-runner --quiet
cargo check -p hsai-agent-admission --examples
```

## Next Evidence Step

The next bridge candidate is a local reviewed acceptance preview for this
preflight report. It should still be candidate-only and should not mutate an
accepted Evidence Ledger until a separate explicit acceptance phase exists.
