# Phase 215 HSAI Gateway Local Demo Runbook

Status: complete for a local, ignored gateway demo bundle runner.

## State Slice

This phase touched only:

- `.gitignore`
- `crates/hsai-agent-admission/examples/gateway_demo_report.rs`
- `crates/hsai-agent-admission/tests/gateway_demo_report_contract.rs`
- `docs/215-hsai-gateway-local-demo-runbook.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No generated gateway report bundle is committed.

## Purpose

Phase 215 turns the existing local gateway report plumbing into a reproducible
operator-facing demo run. The demo writes the declared Phase 206
`gateway-report/*` bundle under `.gateway-demo-runs/`, which is now ignored by
git.

The demo is intentionally small. It uses a fixed local adversarial corpus and
the existing `materialize_gateway_adversarial_corpus_output_run` library path.
It does not add new gateway semantics.

## Ignored Output Root

The default local demo root is:

```text
.gateway-demo-runs/
```

The example requires `HSAI_GATEWAY_DEMO_OUTPUT_ROOT` to be an absolute path
under that ignored root. This permits local reproduction while preventing
generated bundles from becoming committed evidence by accident.

## Runbook

Run from the repository root:

```sh
export HSAI_GATEWAY_DEMO_ACK="I acknowledge this gateway demo writes local metadata only under .gateway-demo-runs."
export HSAI_GATEWAY_DEMO_OUTPUT_ROOT="$PWD/.gateway-demo-runs/phase-214-gateway-demo"
export HSAI_GATEWAY_DEMO_BUNDLE_ID="phase-214-gateway-demo"
export HSAI_GATEWAY_DEMO_CREATED_AT_UNIX="0"
export HSAI_GATEWAY_DEMO_OVERWRITE="true"
cargo run -p hsai-agent-admission --example gateway_demo_report
```

Expected generated files:

```text
.gateway-demo-runs/phase-214-gateway-demo/gateway-report/manifest.json
.gateway-demo-runs/phase-214-gateway-demo/gateway-report/manifest.json.sha256
.gateway-demo-runs/phase-214-gateway-demo/gateway-report/report.json
.gateway-demo-runs/phase-214-gateway-demo/gateway-report/report.json.sha256
.gateway-demo-runs/phase-214-gateway-demo/gateway-report/report.md
.gateway-demo-runs/phase-214-gateway-demo/gateway-report/report.md.sha256
.gateway-demo-runs/phase-214-gateway-demo/gateway-report/non-claims.md
.gateway-demo-runs/phase-214-gateway-demo/gateway-report/non-claims.md.sha256
.gateway-demo-runs/phase-214-gateway-demo/gateway-report/validation-report.json
.gateway-demo-runs/phase-214-gateway-demo/gateway-report/validation-report.json.sha256
```

The example also prints a non-secret JSON summary to stdout with:

- bundle id;
- output root;
- total, accepted, rejected, and quarantined counts;
- unsafe action blocked count;
- false rejection count;
- decision recomputation agreement count;
- audit-bundle completeness;
- declared files;
- local claim boundary;
- `authority_granted = false`;
- required nonclaims.

## Environment Contract

Required:

- `HSAI_GATEWAY_DEMO_ACK`
- `HSAI_GATEWAY_DEMO_OUTPUT_ROOT`

Optional:

- `HSAI_GATEWAY_DEMO_BUNDLE_ID`
- `HSAI_GATEWAY_DEMO_CREATED_AT_UNIX`
- `HSAI_GATEWAY_DEMO_OVERWRITE`

The acknowledgement must exactly equal:

```text
I acknowledge this gateway demo writes local metadata only under .gateway-demo-runs.
```

The output root must be absolute and nested under the repository's ignored
`.gateway-demo-runs/` directory.

## Implemented

Phase 215 adds:

- ignored default root `/.gateway-demo-runs/`;
- `gateway_demo_report` Cargo example for `hsai-agent-admission`;
- fixed non-secret local model-lane provenance;
- fixed adversarial corpus covering the required gateway threat labels;
- existing gateway corpus validation before output creation;
- existing Phase 206 bundle materialization and readback validation;
- summary JSON emission to stdout;
- source-contract tests for the example environment contract, ignored-root
  constraint, nonclaim text, and absence of provider/process runtime surfaces.

## Claim Boundary

The Phase 215 demo bundle is local gateway metadata only. It is not production
readiness, not semantic correctness, not model execution evidence, not live
provider evidence, not external replay, not accepted Evidence Ledger mutation,
not score-axis population, not benchmark evidence, not Level2+ evidence, not
signer/wallet/exchange/custody/MCP/ACP/tool authority, not global
software-agent uniqueness, not fully secure, and not a claim above `Attested`.

The generated `gateway-report/*` bundle is useful for product demonstration and
local reproduction. It is not accepted evidence.

## Validation

Run from repository root:

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
