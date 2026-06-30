# Phase 247 HSAI Gateway Local Demo Bundle Run

Status: complete for a reproducible ignored local gateway demo bundle run.

This phase records a concrete local execution of the Phase 215
`gateway_demo_report` runner. The generated bundle remains under the ignored
`.gateway-demo-runs/` root and is not committed.

## State Slice

This phase touched only:

- `docs/247-hsai-gateway-local-demo-bundle-run.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

The generated local bundle was written to:

```text
.gateway-demo-runs/phase-247-gateway-demo/gateway-report/
```

Git confirmed the generated root is ignored:

```text
!! .gateway-demo-runs/
```

## Purpose

Phase 246 refreshed the public proof packet for the current green head. Phase
247 converts the gateway proof path into a concrete local demo artifact that a
buyer, reviewer, or operator can reproduce without treating the generated
bundle as accepted evidence.

The demo uses the existing Phase 215 example and existing gateway report output
plumbing. It does not add new gateway semantics.

## Source Commit Used For The Run

The local demo bundle was generated from:

```text
99a1410a2d11b2387a365660cd10087558558022
```

That commit is the Phase 246 public proof refresh commit.

## Exact Command

Run from the repository root:

```sh
HSAI_GATEWAY_DEMO_ACK="I acknowledge this gateway demo writes local metadata only under .gateway-demo-runs." \
HSAI_GATEWAY_DEMO_OUTPUT_ROOT="$PWD/.gateway-demo-runs/phase-247-gateway-demo" \
HSAI_GATEWAY_DEMO_BUNDLE_ID="phase-247-gateway-demo" \
HSAI_GATEWAY_DEMO_CREATED_AT_UNIX="0" \
HSAI_GATEWAY_DEMO_OVERWRITE="true" \
cargo run -p hsai-agent-admission --example gateway_demo_report
```

The command exited successfully.

## Generated Files

The local run generated exactly the declared Phase 206 bundle files:

```text
.gateway-demo-runs/phase-247-gateway-demo/gateway-report/manifest.json
.gateway-demo-runs/phase-247-gateway-demo/gateway-report/manifest.json.sha256
.gateway-demo-runs/phase-247-gateway-demo/gateway-report/non-claims.md
.gateway-demo-runs/phase-247-gateway-demo/gateway-report/non-claims.md.sha256
.gateway-demo-runs/phase-247-gateway-demo/gateway-report/report.json
.gateway-demo-runs/phase-247-gateway-demo/gateway-report/report.json.sha256
.gateway-demo-runs/phase-247-gateway-demo/gateway-report/report.md
.gateway-demo-runs/phase-247-gateway-demo/gateway-report/report.md.sha256
.gateway-demo-runs/phase-247-gateway-demo/gateway-report/validation-report.json
.gateway-demo-runs/phase-247-gateway-demo/gateway-report/validation-report.json.sha256
```

## Primary File Digests

```text
281cad853916ed894552a17b58060c2fb585c8bb91b1913fd954e3d081c2bd0a  gateway-report/manifest.json
6e3cf835b0bdc6f50d559dfc067b0861000b2c6c0865d3882292b608f62e77a8  gateway-report/report.json
8e857fac477f1f2e96589bf0f933098c6144f5578e40dc4389e624515b3a8931  gateway-report/report.md
578eca16307430c2140a0c823544c25977693a53ed8f6eef2ce9aa54ad09cdb5  gateway-report/non-claims.md
9a2091b3f9460fce41d4a7223da3ec991b0099c82b4c3152ab8bf9ea7f7ec720  gateway-report/validation-report.json
```

## Demo Summary

The example emitted this non-secret summary:

```text
schema_version: hsai-gateway-demo-summary-v1
bundle_id: phase-247-gateway-demo
total_cases: 14
accepted_count: 1
rejected_count: 13
quarantined_count: 0
unsafe_action_blocked_count: 13
false_rejection_count: 0
decision_recomputation_agreement_count: 14
audit_bundle_complete: true
authority_granted: false
```

Declared files:

```text
gateway-report/manifest.json
gateway-report/report.json
gateway-report/report.md
gateway-report/non-claims.md
gateway-report/validation-report.json
```

Claim boundary:

```text
local gateway report metadata only; not benchmark evidence, proof, production readiness, semantic correctness, global uniqueness, or a fully secure system
```

## Nonclaims

This phase does not prove:

- production readiness;
- semantic correctness;
- SOTA status;
- breakthrough status;
- model execution quality;
- hosted model behavior;
- live provider evidence;
- verifier-agent runtime behavior;
- external replay;
- accepted Evidence Ledger mutation;
- score-axis population;
- official benchmark evidence;
- Level2+ evidence;
- live baseline execution;
- signer, wallet, exchange, custody, MCP, ACP, or tool authority;
- deployment safety;
- global software-agent uniqueness;
- full security;
- any claim above `Attested`.

The generated bundle is useful for demonstration and local reproducibility. It
is not accepted evidence and is not committed.

## Validation Commands

The following commands passed locally before this phase was recorded:

```sh
cargo fmt --all --check
git diff --check
cargo run -p hsai-agent-admission --example gateway_demo_report
find .gateway-demo-runs/phase-247-gateway-demo -type f | sort
git status --short --ignored .gateway-demo-runs docs README.md AGENTS.md
shasum -a 256 .gateway-demo-runs/phase-247-gateway-demo/gateway-report/manifest.json .gateway-demo-runs/phase-247-gateway-demo/gateway-report/report.json .gateway-demo-runs/phase-247-gateway-demo/gateway-report/report.md .gateway-demo-runs/phase-247-gateway-demo/gateway-report/non-claims.md .gateway-demo-runs/phase-247-gateway-demo/gateway-report/validation-report.json
```

The final validation ladder also ran:

```sh
cargo fmt --all --check
git diff --check
cargo check -p hsai-agent-admission --examples
cargo test -p hsai-agent-admission --lib
cargo test -p hsai-agent-admission --test gateway_demo_report_contract
cargo test -p zkbench-core --test repo_hygiene
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test --workspace --quiet
```

## Next Evidence Step

Phase 247 completes the local demo-bundle step in the SOTA bridge. The next
required step is Phase 248: first real external evidence lane.

Phase 248 must add actual external evidence or a tightly bounded operator path
to actual external evidence. More local coverage or local-only docs will not
cross the breakthrough threshold.
