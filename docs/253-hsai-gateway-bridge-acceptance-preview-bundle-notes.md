# Phase 253 HSAI Gateway Bridge Acceptance Preview Bundle Notes

Status: complete for local ignored acceptance-preview bundle output.

This phase materializes a reproducible local output bundle for the Phase 252
candidate-only acceptance preview. The generated output remains under
`.gateway-demo-runs/` and is ignored. It is not committed.

## State Slice

This phase touches:

- `crates/hsai-agent-admission/src/lib.rs`
- `crates/hsai-agent-admission/examples/gateway_acceptance_preview_bundle.rs`
- `crates/hsai-agent-admission/tests/gateway_acceptance_preview_bundle_contract.rs`
- `docs/253-hsai-gateway-bridge-acceptance-preview-bundle-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

The generated local bundle was written to:

```text
.gateway-demo-runs/phase-253-gateway-acceptance-preview/
```

Git confirmed the generated root is ignored:

```text
!! .gateway-demo-runs/
```

## Implemented Surface

`hsai-agent-admission` now includes:

- `GatewayOperatorBridgeAcceptancePreviewMaterializationRequest`;
- `GatewayOperatorBridgeAcceptancePreviewOutputManifest`;
- `GatewayOperatorBridgeAcceptancePreviewOutputValidationReport`;
- `GatewayOperatorBridgeAcceptancePreviewMaterializationError`;
- `materialize_gateway_operator_bridge_acceptance_preview_bundle`;
- `read_gateway_operator_bridge_acceptance_preview_bundle`.

The declared preview bundle files are:

```text
gateway-acceptance-preview/manifest.json
gateway-acceptance-preview/acceptance-preview-request.json
gateway-acceptance-preview/acceptance-preview-report.json
gateway-acceptance-preview/source-preflight-report.json
gateway-acceptance-preview/non-claims.md
gateway-acceptance-preview/validation-report.json
```

Each declared file has a `.sha256` sidecar. Readback rejects undeclared files,
missing files, symlinks, stale sidecars, malformed declared JSON, manifest
semantic drift, report drift, nonclaim drift, validation-report drift, raw
provider body retention, accepted-evidence mutation, Level2+ creation,
score-axis population, authority grants, and credential retention.

## Exact Demo Command

Run from the repository root:

```sh
HSAI_GATEWAY_ACCEPTANCE_PREVIEW_ACK="I acknowledge this preview demo writes local metadata only under .gateway-demo-runs." \
HSAI_GATEWAY_ACCEPTANCE_PREVIEW_OUTPUT_ROOT="$PWD/.gateway-demo-runs/phase-253-gateway-acceptance-preview" \
HSAI_GATEWAY_ACCEPTANCE_PREVIEW_BUNDLE_ID="phase-253-gateway-acceptance-preview" \
HSAI_GATEWAY_ACCEPTANCE_PREVIEW_CREATED_AT_UNIX="0" \
HSAI_GATEWAY_ACCEPTANCE_PREVIEW_OVERWRITE="true" \
cargo run -p hsai-agent-admission --example gateway_acceptance_preview_bundle
```

The command exited successfully.

## Generated Files

```text
.gateway-demo-runs/phase-253-gateway-acceptance-preview/gateway-acceptance-preview-output/gateway-acceptance-preview/acceptance-preview-report.json
.gateway-demo-runs/phase-253-gateway-acceptance-preview/gateway-acceptance-preview-output/gateway-acceptance-preview/acceptance-preview-report.json.sha256
.gateway-demo-runs/phase-253-gateway-acceptance-preview/gateway-acceptance-preview-output/gateway-acceptance-preview/acceptance-preview-request.json
.gateway-demo-runs/phase-253-gateway-acceptance-preview/gateway-acceptance-preview-output/gateway-acceptance-preview/acceptance-preview-request.json.sha256
.gateway-demo-runs/phase-253-gateway-acceptance-preview/gateway-acceptance-preview-output/gateway-acceptance-preview/manifest.json
.gateway-demo-runs/phase-253-gateway-acceptance-preview/gateway-acceptance-preview-output/gateway-acceptance-preview/manifest.json.sha256
.gateway-demo-runs/phase-253-gateway-acceptance-preview/gateway-acceptance-preview-output/gateway-acceptance-preview/non-claims.md
.gateway-demo-runs/phase-253-gateway-acceptance-preview/gateway-acceptance-preview-output/gateway-acceptance-preview/non-claims.md.sha256
.gateway-demo-runs/phase-253-gateway-acceptance-preview/gateway-acceptance-preview-output/gateway-acceptance-preview/source-preflight-report.json
.gateway-demo-runs/phase-253-gateway-acceptance-preview/gateway-acceptance-preview-output/gateway-acceptance-preview/source-preflight-report.json.sha256
.gateway-demo-runs/phase-253-gateway-acceptance-preview/gateway-acceptance-preview-output/gateway-acceptance-preview/validation-report.json
.gateway-demo-runs/phase-253-gateway-acceptance-preview/gateway-acceptance-preview-output/gateway-acceptance-preview/validation-report.json.sha256
```

The same ignored run also regenerated local gateway-report and gateway-bridge
output sub-bundles under the phase root.

## Primary Digests

```text
c05f28e653c9199ed436e46fb385b4b8f07204ce3fefa9606adfdec35d26f5a3  gateway-acceptance-preview/manifest.json
4c8032342ae1a44cb9870216641a2c874cdb0658b319caeaac1a53b2c68c0cfc  gateway-acceptance-preview/acceptance-preview-request.json
c440a3cb639160233e090babcac6de56ea8323b62ee14103551318280e60d280  gateway-acceptance-preview/acceptance-preview-report.json
dc85772636da9175e11f964dfedbc16ab1647d27a18865207729bff9029982e8  gateway-acceptance-preview/source-preflight-report.json
84e763ef04ee91437b752355cd490c38b78036b5d623092a94a35405ffa1c25e  gateway-acceptance-preview/non-claims.md
441cf37805812afd1561c7c5570d09fa401fb674c4a0002c8c0a02a4509664b9  gateway-acceptance-preview/validation-report.json
```

## Demo Summary

```text
schema_version: hsai-gateway-acceptance-preview-demo-summary-v1
bundle_id: phase-253-gateway-acceptance-preview
source_preflight_report_digest: 748554169ea39ded3da75752efedc62cd123ac40b92ad9a7837f409029c5f0bb
acceptance_preview_report_digest: a5ce513d74642e023410d6d659304af4bd881c985e8cc96a3f7c6ed7a33358b8
preview_output_manifest_digest: 13b60f5a45ed2050dfb557d393422187b87055cdf3f7730e7575d910ed1a4d82
candidate_only: true
mutates_accepted_evidence_ledger: false
creates_level2_evidence: false
populates_score_axes: false
grants_authority: false
retains_raw_provider_artifacts: false
retains_credentials_or_secrets: false
```

## Claim Boundary

The preview bundle is local metadata only. It says:

```text
candidate-only gateway/operator bridge acceptance preview metadata; not
accepted evidence, final acceptance, ledger append, Level2+ evidence, live
provider evidence, production readiness, semantic correctness, SOTA,
breakthrough, full security, score-axis population, or authority to execute an
action
```

## Nonclaims

This phase does not prove:

- final acceptance;
- accepted evidence;
- accepted Evidence Ledger mutation;
- ledger append;
- Level2+ evidence;
- score-axis population;
- live provider evidence;
- benchmark evidence;
- production readiness;
- semantic correctness;
- SOTA status;
- breakthrough status;
- full security;
- raw provider artifact validation;
- credential handling;
- signer, wallet, exchange, custody, ACP, MCP, or tool authority;
- any claim above `Attested`.

## Validation Commands

The following focused commands passed during implementation:

```sh
cargo fmt --all --check
git diff --check
cargo test -p hsai-agent-admission --lib gateway_acceptance_preview_bundle
cargo test -p hsai-agent-admission --test gateway_acceptance_preview_bundle_contract
cargo check -p hsai-agent-admission --examples
cargo run -p hsai-agent-admission --example gateway_acceptance_preview_bundle
find .gateway-demo-runs/phase-253-gateway-acceptance-preview -type f | sort
shasum -a 256 .gateway-demo-runs/phase-253-gateway-acceptance-preview/gateway-acceptance-preview-output/gateway-acceptance-preview/manifest.json .gateway-demo-runs/phase-253-gateway-acceptance-preview/gateway-acceptance-preview-output/gateway-acceptance-preview/acceptance-preview-request.json .gateway-demo-runs/phase-253-gateway-acceptance-preview/gateway-acceptance-preview-output/gateway-acceptance-preview/acceptance-preview-report.json .gateway-demo-runs/phase-253-gateway-acceptance-preview/gateway-acceptance-preview-output/gateway-acceptance-preview/source-preflight-report.json .gateway-demo-runs/phase-253-gateway-acceptance-preview/gateway-acceptance-preview-output/gateway-acceptance-preview/non-claims.md .gateway-demo-runs/phase-253-gateway-acceptance-preview/gateway-acceptance-preview-output/gateway-acceptance-preview/validation-report.json
git status --short --ignored .gateway-demo-runs crates/hsai-agent-admission docs README.md AGENTS.md Cargo.lock
```

The final validation ladder also passed:

```sh
cargo test -p hsai-agent-admission --lib --quiet
cargo test -p zkbench-core --test repo_hygiene --quiet
cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet
cargo test --workspace --quiet
cargo test --workspace --features external-runner --quiet
```

## Next Evidence Step

The next bridge candidate is a local claim packet that summarizes Phases 249
through 253 as a bounded gateway-to-attestation-to-preview bridge. It should be
public-facing but must keep the same nonclaims: no accepted evidence, no final
acceptance, no Level2+ evidence, no live provider evidence, no production
readiness, no semantic correctness, no SOTA, and no breakthrough claim.
