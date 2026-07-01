# Phase 254 HSAI Gateway Bridge Public Claim Packet

Status: complete for bounded public claim packaging.

This packet summarizes what the local gateway-to-attestation-to-preview bridge
proves across Phases 249 through 253, how to reproduce it, and what it does not
prove. It is designed for public sharing without inflating local metadata into
accepted evidence, live provider evidence, production readiness, SOTA status, or
breakthrough status.

## Commit

The packet is based on:

```text
edbae44ea2f47f067683e28d2c6d5cb8af4362e8
```

Top commit:

```text
edbae44 Materialize gateway acceptance preview bundle
```

## Validated Surfaces

This packet covers:

- Phase 249: gateway action proposal to attestation challenge binding.
- Phase 250: ignored local gateway/operator bridge bundle.
- Phase 251: reviewed local promotion preflight metadata.
- Phase 252: candidate-only acceptance preview metadata.
- Phase 253: ignored local acceptance-preview output bundle.

The covered bridge path is:

```text
gateway action proposal
-> deterministic gateway case hash
-> attestation report-data binding input
-> gateway/operator bridge bundle
-> reviewed local promotion preflight
-> candidate-only acceptance preview
-> ignored local preview output bundle
```

## Public Claim

HSAI has a local hermetic gateway bridge stack that can:

- bind a concrete gateway action proposal into attestation challenge input
  metadata;
- place a gateway report digest, attestation challenge binding, and
  repo-external operator-live artifact reference digest into a declared local
  bridge bundle;
- validate a reviewed metadata-only promotion preflight over that bridge bundle;
- validate a candidate-only acceptance preview over that preflight report;
- materialize an ignored local `gateway-acceptance-preview/*` output bundle with
  deterministic JSON files, Markdown nonclaims, validation report, manifest, and
  SHA-256 sidecars;
- reject raw provider bodies, credentials, authority grants, Level2+ escalation,
  score-axis population, accepted Evidence Ledger mutation, and stronger claim
  text in the local validation path.

This is a local metadata and artifact-shape claim only.

## Structured Claim-Packet Manifest

This manifest is parsed by the local reproduction checker. It is not accepted
evidence and does not strengthen the public claim.

The `manifest_digest_sha256` value is computed over the sorted `key=value`
manifest lines, excluding the `manifest_digest_sha256` line itself, with one
newline after each included line.

```claim-packet-manifest-v1
packet_id=phase-254-hsai-gateway-bridge-public-claim-packet
packet_path=docs/254-hsai-gateway-bridge-public-claim-packet.md
base_commit=edbae44ea2f47f067683e28d2c6d5cb8af4362e8
top_commit=edbae44 Materialize gateway acceptance preview bundle
validated_phase=249
validated_phase=250
validated_phase=251
validated_phase=252
validated_phase=253
claim_level=local_metadata_and_artifact_shape_only
max_claim_maturity=Attested
ignored_demo_root=.gateway-demo-runs/phase-253-gateway-acceptance-preview/
ignored_status=!! .gateway-demo-runs/
manifest_digest_sha256=9cec879e89def697a5fdbb07a5ea1885ea2e4ce330cc6e8c0ed91e69de793fa9
declared_file=gateway-acceptance-preview/manifest.json
declared_file=gateway-acceptance-preview/acceptance-preview-request.json
declared_file=gateway-acceptance-preview/acceptance-preview-report.json
declared_file=gateway-acceptance-preview/source-preflight-report.json
declared_file=gateway-acceptance-preview/non-claims.md
declared_file=gateway-acceptance-preview/validation-report.json
summary_flag=candidate_only:true
summary_flag=mutates_accepted_evidence_ledger:false
summary_flag=creates_level2_evidence:false
summary_flag=populates_score_axes:false
summary_flag=grants_authority:false
summary_flag=retains_raw_provider_artifacts:false
summary_flag=retains_credentials_or_secrets:false
phase253_command=cargo fmt --all --check
phase253_command=git diff --check
phase253_command=cargo test -p hsai-agent-admission --lib gateway_acceptance_preview_bundle
phase253_command=cargo test -p hsai-agent-admission --test gateway_acceptance_preview_bundle_contract
phase253_command=cargo check -p hsai-agent-admission --examples
phase253_command=cargo run -p hsai-agent-admission --example gateway_acceptance_preview_bundle
phase253_command=cargo test -p hsai-agent-admission --lib --quiet
phase253_command=cargo test -p zkbench-core --test repo_hygiene --quiet
phase253_command=cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet
phase253_command=cargo test --workspace --quiet
phase253_command=cargo test --workspace --features external-runner --quiet
packet_validation_command=cargo fmt --all --check
packet_validation_command=git diff --check
packet_validation_command=cargo test -p zkbench-core --test gateway_claim_packet_reproduction --quiet
packet_validation_command=cargo test -p zkbench-core --test repo_hygiene --quiet
packet_validation_command=cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet
packet_validation_command=cargo test --workspace --quiet
packet_validation_command=cargo test --workspace --features external-runner --quiet
nonclaim=accepted evidence
nonclaim=final acceptance
nonclaim=accepted Evidence Ledger mutation
nonclaim=Level2+ evidence
nonclaim=live provider evidence
nonclaim=live attestation capture
nonclaim=benchmark evidence
nonclaim=score-axis population
nonclaim=production readiness
nonclaim=semantic correctness
nonclaim=SOTA status
nonclaim=breakthrough status
nonclaim=full security
nonclaim=global software-agent uniqueness
nonclaim=any claim above Attested
do_not_use=HSAI has proven production-ready secure agent execution.
do_not_use=HSAI has accepted live attestation evidence.
do_not_use=HSAI is SOTA.
do_not_use=HSAI has proven a breakthrough.
do_not_use=HSAI has Level2+ evidence.
do_not_use=HSAI is fully secure.
```

## Exact Passed Commands

The Phase 253 final gate on `edbae44ea2f47f067683e28d2c6d5cb8af4362e8`
passed:

```sh
cargo fmt --all --check
git diff --check
cargo test -p hsai-agent-admission --lib gateway_acceptance_preview_bundle
cargo test -p hsai-agent-admission --test gateway_acceptance_preview_bundle_contract
cargo check -p hsai-agent-admission --examples
cargo run -p hsai-agent-admission --example gateway_acceptance_preview_bundle
cargo test -p hsai-agent-admission --lib --quiet
cargo test -p zkbench-core --test repo_hygiene --quiet
cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet
cargo test --workspace --quiet
cargo test --workspace --features external-runner --quiet
```

## Packet Validation Commands

The Phase 254 docs-only packet validation passed:

```sh
cargo fmt --all --check
git diff --check
cargo test -p zkbench-core --test gateway_claim_packet_reproduction --quiet
cargo test -p zkbench-core --test repo_hygiene --quiet
cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet
cargo test --workspace --quiet
cargo test --workspace --features external-runner --quiet
```

The ignored demo run command was:

```sh
HSAI_GATEWAY_ACCEPTANCE_PREVIEW_ACK="I acknowledge this preview demo writes local metadata only under .gateway-demo-runs." \
HSAI_GATEWAY_ACCEPTANCE_PREVIEW_OUTPUT_ROOT="$PWD/.gateway-demo-runs/phase-253-gateway-acceptance-preview" \
HSAI_GATEWAY_ACCEPTANCE_PREVIEW_BUNDLE_ID="phase-253-gateway-acceptance-preview" \
HSAI_GATEWAY_ACCEPTANCE_PREVIEW_CREATED_AT_UNIX="0" \
HSAI_GATEWAY_ACCEPTANCE_PREVIEW_OVERWRITE="true" \
cargo run -p hsai-agent-admission --example gateway_acceptance_preview_bundle
```

## Phase 253 Run Evidence

The ignored run wrote:

```text
.gateway-demo-runs/phase-253-gateway-acceptance-preview/
```

Git confirmed the generated root is ignored:

```text
!! .gateway-demo-runs/
```

The declared acceptance-preview files were:

```text
gateway-acceptance-preview/manifest.json
gateway-acceptance-preview/acceptance-preview-request.json
gateway-acceptance-preview/acceptance-preview-report.json
gateway-acceptance-preview/source-preflight-report.json
gateway-acceptance-preview/non-claims.md
gateway-acceptance-preview/validation-report.json
```

Primary file digests:

```text
c05f28e653c9199ed436e46fb385b4b8f07204ce3fefa9606adfdec35d26f5a3  gateway-acceptance-preview/manifest.json
4c8032342ae1a44cb9870216641a2c874cdb0658b319caeaac1a53b2c68c0cfc  gateway-acceptance-preview/acceptance-preview-request.json
c440a3cb639160233e090babcac6de56ea8323b62ee14103551318280e60d280  gateway-acceptance-preview/acceptance-preview-report.json
dc85772636da9175e11f964dfedbc16ab1647d27a18865207729bff9029982e8  gateway-acceptance-preview/source-preflight-report.json
84e763ef04ee91437b752355cd490c38b78036b5d623092a94a35405ffa1c25e  gateway-acceptance-preview/non-claims.md
441cf37805812afd1561c7c5570d09fa401fb674c4a0002c8c0a02a4509664b9  gateway-acceptance-preview/validation-report.json
```

Key run summary:

```text
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

## Reproduction Checklist

1. Start from commit
   `edbae44ea2f47f067683e28d2c6d5cb8af4362e8`.
2. Confirm the worktree is clean:

```sh
git status --short --branch
```

3. Run the ignored Phase 253 demo command from the repository root.
4. Confirm generated files are ignored:

```sh
git status --short --ignored .gateway-demo-runs
```

5. Confirm focused validation:

```sh
cargo test -p hsai-agent-admission --lib gateway_acceptance_preview_bundle
cargo test -p hsai-agent-admission --test gateway_acceptance_preview_bundle_contract
cargo check -p hsai-agent-admission --examples
```

6. Confirm repo claim-boundary validation:

```sh
cargo test -p zkbench-core --test repo_hygiene --quiet
cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet
```

7. Confirm the full workspace gates:

```sh
cargo test --workspace --quiet
cargo test --workspace --features external-runner --quiet
```

## Explicit Nonclaims

This packet does not claim:

- accepted evidence;
- final acceptance;
- accepted Evidence Ledger mutation;
- ledger append;
- Level2+ evidence;
- live provider evidence;
- live attestation capture;
- local Intel DCAP verification;
- managed-service signature/JWKS/JWT verification in this bridge packet;
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
- raw provider artifact validation;
- credential handling;
- signer, wallet, exchange, custody, ACP, MCP, or tool authority;
- global software-agent uniqueness;
- any claim above `Attested`.

## Buyer-Facing Wording

Use:

```text
HSAI has a local, reproducible gateway bridge that connects an action proposal
to attestation challenge input, bridge-bundle metadata, reviewed preflight
metadata, candidate-only acceptance-preview metadata, and an ignored local
preview output bundle. The current proof is hermetic and metadata-only: it
shows the bridge shape, digest bindings, nonclaim enforcement, and fail-closed
local validation. It is not live provider evidence or accepted production
evidence.
```

Short version:

```text
HSAI can locally prove the gateway-to-attestation-to-preview bridge shape with
deterministic digests and explicit nonclaims, without granting authority or
mutating accepted evidence.
```

Do not use:

```text
HSAI has proven production-ready secure agent execution.
HSAI has accepted live attestation evidence.
HSAI is SOTA.
HSAI has proven a breakthrough.
HSAI has Level2+ evidence.
HSAI is fully secure.
```

## Next Evidence Step

The next defensible step is not to strengthen the public claim. The next step
is to add a local public-packet index that lists the latest shareable packet,
digest, checker command, and nonclaims without creating generated artifacts or
strengthening the claim.
