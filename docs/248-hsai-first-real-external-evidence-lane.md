# Phase 248 HSAI First Real External Evidence Lane

Status: complete for a bounded public evidence-lane map.

This phase connects the Phase 247 local HSAI Gateway demo path to the existing
real/operator external-evidence surfaces without promoting either side into a
stronger claim. It is a public bridge artifact, not a new verifier, not a live
operator run, not accepted evidence, and not a SOTA or breakthrough proof.

## State Slice

This phase touches only:

- `docs/248-hsai-first-real-external-evidence-lane.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No Rust source, tests, Cargo metadata, generated artifacts, credentials,
fixtures, accepted Evidence Ledgers, official submission artifacts, package
runtime files, model prompts, model outputs, provider responses, raw quotes,
raw JWKS documents, raw TLS exporters, signer/tool integrations, or deployment
files are changed by this phase.

## Purpose

Phase 247 proves the gateway can produce an ignored local admission/report
bundle with strict nonclaims. The repository also contains a separate
managed-attestation path with real/operator evidence. Phase 248 states exactly
what those external-evidence surfaces can contribute to the gateway bridge and
what is still missing before the gateway can claim accepted external evidence.

The bridge claim is:

```text
HSAI has a local gateway admission/report stack and a separate real/operator
attestation evidence lane. The current public bridge is an evidence map between
those surfaces, not an accepted evidence mutation and not a proof that a
gateway decision was produced inside an attested live runtime.
```

## Source Commit

The public state mapped by this packet starts from:

```text
e75cb6203cd946b707af3cb048b7d254ab931529
```

That commit is the Phase 247 gateway local demo bundle run.

## Gateway Surface Being Connected

The gateway side is the local Phase 204-215 and Phase 247 stack:

- local typed action admission before authority;
- local gateway report bundle generation;
- local report output validation and digest sidecars;
- local adversarial corpus validation and output-run plumbing;
- local baseline comparison and effectiveness metrics;
- local cost routing with `authority_granted=false`;
- ignored demo bundle run under `.gateway-demo-runs/`.

The Phase 247 demo run produced:

```text
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

This is local gateway metadata only. It is not live provider evidence and is
not accepted evidence.

## External Evidence Surfaces Already Present

### Real HSAI-Owned Phala/dstack Artifact

`docs/57-managed-attestation-real-artifact-promotion-spec.md` records the first
real HSAI-owned Phala/dstack artifact capture accepted on 2026-06-16.

Relevant committed surface:

```text
crates/hsai-attestation-phala/tests/fixtures/phala_hsai_owned_real_2026_06_16.json
crates/hsai-attestation-phala/tests/phala_hsai_owned_real.rs
```

What it supports:

- HSAI-owned fresh challenge binding via `report_data_binding`;
- report-data equality against the captured artifact;
- compose-hash equality;
- RTMR3 event-log replay;
- explicit managed-verifier trust roots;
- `Attested`-capped local regression evidence for the binding path.

What it does not support:

- local Intel DCAP quote verification;
- managed-service signature/JWKS/JWT verification;
- live gateway execution;
- gateway admission decision binding;
- benchmark evidence;
- global software-agent uniqueness;
- accepted Evidence Ledger mutation;
- proof.

### Phala Cloud API Live Artifact Materialization

`docs/106-phala-cloud-api-live-artifact-implementation-notes.md` records an
operator-only path from a saved Phala Cloud `/attestations/verify` response into
the local redacted `operator-live/*` artifact shape.

What it supports:

- operator-run live Phala verification response ingestion from repo-external
  saved input;
- `success=true`, `quote.verified=true`, and `TEE_TDX` checks;
- report-data prefix binding to the captured artifact bundle;
- raw provider response hashing without retaining the raw body;
- redacted digest-bound output outside git.

What it does not support:

- normal-test network access;
- committed provider response bodies;
- local DCAP verification;
- managed-service signature verification;
- accepted evidence;
- benchmark evidence;
- proof.

### Local DCAP/QVL Artifact Materialization

`docs/108-phala-local-dcap-qvl-verification-notes.md` records an operator-only
local QVL path for the existing Phala-verified TDX quote.

What it supports:

- operator-run `dcap-qvl verify` over a repo-external raw quote;
- digest-only materialization of raw quote, decoded quote, PCK info, and QVL
  report;
- `UpToDate` QVL, QE, and platform status in the recorded run;
- measurement consistency checks between Phala parsed measurements and QVL
  outputs.

What it does not support:

- a repo-native DCAP verifier implementation;
- normal-test PCCS collateral fetching;
- committed raw quote or QVL report;
- managed-service signature verification;
- accepted evidence;
- benchmark evidence;
- proof.

### Managed JWKS Fetch Artifact

`docs/109-managed-jwks-fetch-artifact-notes.md` records an operator-only public
OpenID/JWKS fetch artifact for Intel Trust Authority.

What it supports:

- operator-fetched OpenID metadata and JWKS from public endpoints;
- local structural consistency checks over saved JSON;
- digest-only materialization outside git.

What it does not support:

- accepting or verifying a live managed JWT;
- Phala managed-signature verification;
- token acceptance;
- committed raw JWKS/OpenID responses;
- accepted evidence;
- proof.

### TLS Channel-Binding Artifact

`docs/113-phala-tls-channel-binding-artifact-implementation-notes.md` records a
feature-gated operator-only TLS 1.3 artifact path for Phala Cloud.

What it supports:

- one operator-observed Phala verification response and RFC 9266 exporter on
  the same TLS 1.3 connection;
- request, response, exporter, and peer-chain digests;
- digest-only output outside git.

What it does not support:

- RA-TLS;
- proof that the TLS private key resides in the attested CVM;
- independently verifiable server-attestation evidence;
- local DCAP verification;
- accepted evidence;
- benchmark evidence;
- proof.

## Tangible Gateway Reliance

The gateway can tangibly rely on the external lane for this bounded role:

```text
external attestation lane = runtime/anchor evidence input
gateway admission lane = typed proposal and authority-denial policy
```

That means the marketable bridge is not "models are trusted." It is:

```text
model outputs stay proposals; typed gateway policy decides before authority;
runtime/anchor evidence can be attached as a separate Attested input; and all
claim boundaries remain explicit in public artifacts.
```

This is useful for buyer-facing demos because it separates three risks:

- model quality risk;
- action-authority risk;
- runtime/identity evidence risk.

The current repo has local controls and public evidence artifacts for those
risks, but it does not yet bind all three into one accepted gateway evidence
record.

## Explicit Missing Bridge

The current public state still lacks:

- a gateway admission case whose subject, case hash, nonce, and policy id are
  bound into a fresh external attestation challenge;
- a gateway report bundle that references an accepted external attestation
  artifact by digest;
- an accepted Evidence Ledger mutation that admits the gateway plus external
  evidence bundle;
- independent reproduction of the gateway plus external lane;
- official benchmark evidence;
- live model execution evidence;
- semantic-correctness evidence;
- production-readiness evidence;
- Level2+ evidence;
- SOTA or breakthrough evidence.

## Honest Buyer-Facing Phrasing

Use:

```text
HSAI can demonstrate a local secure-admission gateway and a separate
operator-backed attestation evidence lane. The public packet shows how those
surfaces connect and what remains before we can claim accepted external
gateway evidence.
```

Do not use:

```text
fully secure
production ready
SOTA proven
breakthrough proven
formally verified gateway
live attested gateway execution
accepted external evidence
official benchmark result
```

## Reproduction Checklist

From the repository root:

```sh
cargo fmt --all --check
git diff --check
cargo test -p hsai-attestation-phala --test phala_hsai_owned_real
cargo test -p hsai-attestation-phala --test phala_operator_live_api_artifact_contract
cargo test -p hsai-attestation-phala --test phala_operator_live_dcap_qvl_contract
cargo test -p hsai-attestation --test managed_jwks_artifact_contract
cargo test -p hsai-attestation-phala --test phala_operator_live_tls_channel_contract
cargo test -p hsai-agent-admission --test gateway_demo_report_contract
cargo test -p zkbench-core --test repo_hygiene
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test --workspace --quiet
```

These commands reproduce the local contract checks and public claim-boundary
guards. They do not perform live Phala calls, fetch JWKS, fetch PCCS
collateral, run `dcap-qvl`, execute models, submit benchmarks, or mutate
accepted evidence.

## Nonclaims

This phase does not prove:

- production readiness;
- semantic correctness;
- SOTA status;
- breakthrough status;
- live gateway execution;
- live model behavior;
- verifier-agent runtime behavior;
- accepted Evidence Ledger mutation;
- score-axis population;
- official benchmark evidence;
- Level2+ evidence;
- live baseline execution;
- deployment safety;
- signer, wallet, exchange, custody, MCP, ACP, or tool authority;
- global software-agent uniqueness;
- full security;
- any claim above `Attested`.

## Next Evidence Step

The next highest-leverage phase is a gateway-to-attestation binding spec or
implementation that takes one gateway admission case and derives the attested
challenge from its subject, policy id, case hash, and nonce. That phase should
still write no secrets, should keep live artifacts outside git, and should not
mutate the accepted Evidence Ledger until a separate reviewed promotion phase.
