# Phase 250 HSAI Gateway Operator Bridge Bundle Notes

Status: complete for local ignored gateway/operator bridge bundle output.

This phase implements and records the first reproducible local bridge bundle
that places a gateway report digest, a gateway attestation challenge binding,
and a repo-external operator-live artifact reference in one declared output
shape.

The generated demo output remains under `.gateway-demo-runs/` and is ignored.
It is not committed.

## State Slice

This phase touches:

- `crates/hsai-agent-admission/src/lib.rs`
- `crates/hsai-agent-admission/examples/gateway_operator_bridge_bundle.rs`
- `crates/hsai-agent-admission/tests/gateway_operator_bridge_bundle_contract.rs`
- `docs/250-hsai-gateway-operator-bridge-bundle-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

The generated local bundle was written to:

```text
.gateway-demo-runs/phase-250-gateway-bridge/
```

Git confirmed the generated root is ignored:

```text
!! .gateway-demo-runs/
```

## Implemented Surface

`hsai-agent-admission` now includes:

- `GatewayOperatorArtifactReference`;
- `GatewayOperatorBridgeBundle`;
- `GatewayOperatorBridgeMaterializationRequest`;
- `GatewayOperatorBridgeOutputManifest`;
- `GatewayOperatorBridgeValidationReport`;
- `GatewayOperatorBridgeIssue`;
- `GatewayOperatorBridgeMaterializationError`;
- `gateway_operator_bridge_required_nonclaims`;
- `gateway_operator_bridge_claim_boundary`;
- `build_gateway_operator_bridge_bundle`;
- `validate_gateway_operator_bridge_bundle`;
- `materialize_gateway_operator_bridge_bundle`;
- `read_gateway_operator_bridge_bundle`.

The declared bundle files are:

```text
gateway-bridge/manifest.json
gateway-bridge/bridge-bundle.json
gateway-bridge/attestation-binding.json
gateway-bridge/operator-artifact-reference.json
gateway-bridge/non-claims.md
gateway-bridge/validation-report.json
```

Each declared file has a `.sha256` sidecar. Readback rejects undeclared files,
missing files, symlinks, stale sidecars, malformed declared JSON, manifest
semantic drift, binding drift, nonclaim drift, validation-report drift, raw
provider body retention, authority grants, and accepted-evidence mutation.

## Exact Demo Command

Run from the repository root:

```sh
HSAI_GATEWAY_BRIDGE_ACK="I acknowledge this bridge demo writes local metadata only under .gateway-demo-runs." \
HSAI_GATEWAY_BRIDGE_OUTPUT_ROOT="$PWD/.gateway-demo-runs/phase-250-gateway-bridge" \
HSAI_GATEWAY_BRIDGE_BUNDLE_ID="phase-250-gateway-bridge" \
HSAI_GATEWAY_BRIDGE_CREATED_AT_UNIX="0" \
HSAI_GATEWAY_BRIDGE_OVERWRITE="true" \
cargo run -p hsai-agent-admission --example gateway_operator_bridge_bundle
```

The command exited successfully.

## Generated Files

```text
.gateway-demo-runs/phase-250-gateway-bridge/gateway-bridge-output/gateway-bridge/attestation-binding.json
.gateway-demo-runs/phase-250-gateway-bridge/gateway-bridge-output/gateway-bridge/attestation-binding.json.sha256
.gateway-demo-runs/phase-250-gateway-bridge/gateway-bridge-output/gateway-bridge/bridge-bundle.json
.gateway-demo-runs/phase-250-gateway-bridge/gateway-bridge-output/gateway-bridge/bridge-bundle.json.sha256
.gateway-demo-runs/phase-250-gateway-bridge/gateway-bridge-output/gateway-bridge/manifest.json
.gateway-demo-runs/phase-250-gateway-bridge/gateway-bridge-output/gateway-bridge/manifest.json.sha256
.gateway-demo-runs/phase-250-gateway-bridge/gateway-bridge-output/gateway-bridge/non-claims.md
.gateway-demo-runs/phase-250-gateway-bridge/gateway-bridge-output/gateway-bridge/non-claims.md.sha256
.gateway-demo-runs/phase-250-gateway-bridge/gateway-bridge-output/gateway-bridge/operator-artifact-reference.json
.gateway-demo-runs/phase-250-gateway-bridge/gateway-bridge-output/gateway-bridge/operator-artifact-reference.json.sha256
.gateway-demo-runs/phase-250-gateway-bridge/gateway-bridge-output/gateway-bridge/validation-report.json
.gateway-demo-runs/phase-250-gateway-bridge/gateway-bridge-output/gateway-bridge/validation-report.json.sha256
.gateway-demo-runs/phase-250-gateway-bridge/gateway-report-output/gateway-report/manifest.json
.gateway-demo-runs/phase-250-gateway-bridge/gateway-report-output/gateway-report/manifest.json.sha256
.gateway-demo-runs/phase-250-gateway-bridge/gateway-report-output/gateway-report/non-claims.md
.gateway-demo-runs/phase-250-gateway-bridge/gateway-report-output/gateway-report/non-claims.md.sha256
.gateway-demo-runs/phase-250-gateway-bridge/gateway-report-output/gateway-report/report.json
.gateway-demo-runs/phase-250-gateway-bridge/gateway-report-output/gateway-report/report.json.sha256
.gateway-demo-runs/phase-250-gateway-bridge/gateway-report-output/gateway-report/report.md
.gateway-demo-runs/phase-250-gateway-bridge/gateway-report-output/gateway-report/report.md.sha256
.gateway-demo-runs/phase-250-gateway-bridge/gateway-report-output/gateway-report/validation-report.json
.gateway-demo-runs/phase-250-gateway-bridge/gateway-report-output/gateway-report/validation-report.json.sha256
```

## Primary Digests

```text
6eb2bbe2bb77ae6a6417eea7a74cd13850982c35dbde7d93db644ed44deb7048  gateway-bridge/manifest.json
03064e7fc9782a0a8eac4befa3d2498883ee976b0b3a9234d32be3537a587d2b  gateway-bridge/bridge-bundle.json
829271e355f6cb3ffa39d9e63aea322bf2c503dcb28afd16c980d6789b390a72  gateway-bridge/attestation-binding.json
6004a1fccb0f53bb13e983dba92d8119a2b5d7d12fa1c2b7dd30feffca0fa933  gateway-bridge/operator-artifact-reference.json
8725c788e45c5daa64a799da62999ca496ed053f33f574c9ef53ee46142cc1e6  gateway-bridge/non-claims.md
5818e470d5ae36897adcfc454469e000618a89365879954296ad60d9fa6bbf8b  gateway-bridge/validation-report.json
1cafec844fb23cb8ec9ef526465ab40d2b53058fa6bba5e0731a77cd1ca6f268  gateway-report/manifest.json
```

## Demo Summary

```text
schema_version: hsai-gateway-bridge-demo-summary-v1
bundle_id: phase-250-gateway-bridge
gateway_report_digest: c5aac255c9cba5c7236e84973ae211eb2ef02fa71867be3fdd3ab41f854c9a47
gateway_report_manifest_digest: e81cbfdac06ed3406a3525c43fdb27d80335b40ddfbda0ef4549f32afb69a50b
attestation_binding_digest: 00de124ef70c654fde405844970358dc4168ab1748d0a567b7185e6c8e6038ad
operator_artifact_reference_digest: 0e80dbdde93257be1a76cb7b297471958240cc513de504db1c5513a1e4ee9958
authority_granted: false
accepted_evidence_mutation: false
```

## Claim Boundary

The bridge bundle is local metadata only. It says:

```text
local gateway/operator bridge metadata only; not attestation evidence, proof,
live provider evidence, accepted evidence, benchmark evidence, production
readiness, semantic correctness, SOTA, breakthrough, full security, or
authority to execute an action
```

## Nonclaims

This phase does not prove:

- attestation evidence;
- live provider evidence;
- live gateway execution;
- live model behavior;
- verifier-agent runtime behavior;
- accepted Evidence Ledger mutation;
- score-axis population;
- official benchmark evidence;
- Level2+ evidence;
- production readiness;
- semantic correctness;
- SOTA status;
- breakthrough status;
- full security;
- signer, wallet, exchange, custody, MCP, ACP, or tool authority;
- global software-agent uniqueness;
- any claim above `Attested`.

The operator artifact is a repo-external digest reference only. The bridge
bundle does not retain raw provider responses, raw quotes, raw JWKS/OpenID
documents, TLS exporters, credentials, or secrets.

## Validation Commands

The following commands passed for this phase:

```sh
cargo fmt --all --check
git diff --check
cargo check -p hsai-agent-admission --examples
cargo test -p hsai-agent-admission --lib gateway_operator_bridge
cargo test -p hsai-agent-admission --test gateway_operator_bridge_bundle_contract
cargo run -p hsai-agent-admission --example gateway_operator_bridge_bundle
find .gateway-demo-runs/phase-250-gateway-bridge -type f | sort
shasum -a 256 .gateway-demo-runs/phase-250-gateway-bridge/gateway-bridge-output/gateway-bridge/manifest.json .gateway-demo-runs/phase-250-gateway-bridge/gateway-bridge-output/gateway-bridge/bridge-bundle.json .gateway-demo-runs/phase-250-gateway-bridge/gateway-bridge-output/gateway-bridge/attestation-binding.json .gateway-demo-runs/phase-250-gateway-bridge/gateway-bridge-output/gateway-bridge/operator-artifact-reference.json .gateway-demo-runs/phase-250-gateway-bridge/gateway-bridge-output/gateway-bridge/non-claims.md .gateway-demo-runs/phase-250-gateway-bridge/gateway-bridge-output/gateway-bridge/validation-report.json .gateway-demo-runs/phase-250-gateway-bridge/gateway-report-output/gateway-report/manifest.json
git status --short --ignored .gateway-demo-runs crates/hsai-agent-admission docs README.md AGENTS.md Cargo.lock
```

The final validation ladder also ran:

```sh
cargo fmt --all --check
git diff --check
cargo check -p hsai-agent-admission --examples
cargo test -p hsai-agent-admission --lib gateway_operator_bridge
cargo test -p hsai-agent-admission --test gateway_operator_bridge_bundle_contract
cargo test -p hsai-agent-admission --lib
cargo test -p zkbench-core --test repo_hygiene
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test --workspace --quiet
```

## Next Evidence Step

The next phase should define a reviewed promotion preflight for the bridge
bundle. That preflight should accept only local metadata and repo-external
operator artifact digests, should reject raw provider bodies and credentials,
and should still avoid accepted Evidence Ledger mutation until a later reviewed
acceptance phase.
