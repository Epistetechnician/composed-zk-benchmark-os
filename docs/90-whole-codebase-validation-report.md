# Whole Codebase Validation Report

Status: local validation report only.

This report records the end-to-end local validation run after Phase S
audit-index ergonomics output plumbing, protected-path overlap hardening, the
Phase 102 opt-in Phala provider-client implementation, the Phase 105
operator-only live runner implementation, and the Phase 106 Phala Cloud API
live artifact materialization implementation, and the Phase 107 Phala DCAP/PCCS
collateral materialization implementation, and the Phase 108 Phala local
DCAP/QVL verification artifact implementation, and the Phase 109 managed JWKS
fetch artifact implementation, and the Phase 110 Phala local PCCS-compatible
service artifact implementation, and the Phase 111 Phala direct Intel PCS
artifact implementation, the docs-first Phase 112 TLS channel-binding boundary,
the Phase 113 Phala TLS channel-binding artifact implementation, and the
docs-first Phase 114 reviewed promotion preflight implementation boundary, plus the
coverage-hardening follow-up for serialization error paths, crate error
constructors, and local soak runner resume/output/error-policy paths. It
evaluates the implemented codebase as a local Level 1 Rust foundation by
running the available workspace gates and mapping those gates to the repo's
major behavioral surfaces.

It does not claim per-function formal correctness, line coverage, accepted
Evidence Ledger mutation, official benchmark evidence, ZK backend performance,
Level2+ evidence, live provider evidence, production readiness, semantic
correctness, or global software-agent uniqueness.

Phase 114 authorizes only inert Phase W preflight metadata and fail-closed
validation. It does not authorize accepted Evidence Ledger mutation, official
benchmark submission, external replay, live backend execution, generated
benchmark artifacts, score-axis population, ZK backend performance claims, or
Level2+ evidence creation.

## State Slice

This report touches only:

- `crates/hsai-attestation-phala/examples/operator_live_phala_api_artifact.rs`
- `crates/hsai-attestation-phala/tests/phala_operator_live_api_artifact_contract.rs`
- `docs/106-phala-cloud-api-live-artifact-implementation-notes.md`
- `crates/hsai-attestation-phala/examples/operator_live_dcap_pccs_artifact.rs`
- `crates/hsai-attestation-phala/tests/phala_operator_live_dcap_pccs_contract.rs`
- `docs/107-phala-dcap-pccs-collateral-implementation-notes.md`
- `crates/hsai-attestation-phala/examples/operator_live_dcap_qvl_artifact.rs`
- `crates/hsai-attestation-phala/tests/phala_operator_live_dcap_qvl_contract.rs`
- `docs/108-phala-local-dcap-qvl-verification-notes.md`
- `crates/hsai-attestation/examples/operator_live_jwks_artifact.rs`
- `crates/hsai-attestation/tests/managed_jwks_artifact_contract.rs`
- `docs/109-managed-jwks-fetch-artifact-notes.md`
- `crates/hsai-attestation-phala/examples/operator_live_local_pccs_artifact.rs`
- `crates/hsai-attestation-phala/tests/phala_operator_live_local_pccs_contract.rs`
- `docs/110-phala-local-pccs-service-artifact-notes.md`
- `crates/hsai-attestation-phala/examples/operator_live_intel_pcs_artifact.rs`
- `crates/hsai-attestation-phala/tests/phala_operator_live_intel_pcs_contract.rs`
- `docs/111-phala-intel-pcs-direct-artifact-notes.md`
- `crates/hsai-attestation-phala/examples/operator_live_tls_channel_artifact.rs`
- `crates/hsai-attestation-phala/tests/phala_operator_live_tls_channel_contract.rs`
- `crates/hsai-e2e-harness/tests/claim_boundary_source_scan.rs`
- `docs/112-phala-tls-channel-binding-artifact-boundary-spec.md`
- `docs/113-phala-tls-channel-binding-artifact-implementation-notes.md`
- `crates/hsai-attestation-phala/Cargo.toml`
- `Cargo.lock`
- `crates/zkbench-core/tests/soak_runner_smoke.rs`
- `crates/zkbench-core/tests/phase_v_coverage_hardening.rs`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `docs/research/zk_external_source_index.md`
- `README.md`
- `AGENTS.md`

It does not change fixtures, generated artifacts, accepted Evidence Ledgers,
benchmark packs, report bundles, audit-index outputs, ergonomics outputs,
package runtime files, command-line tools outside operator-only examples, or UI
artifacts.

## Validation Commands

Run from repository root during Phase 113 validation.

```sh
cargo fmt --all -- --check
git diff --check
cargo test -p hsai-attestation-phala --test phala_operator_live_tls_channel_contract
cargo test -p hsai-attestation-phala --example operator_live_tls_channel_artifact --features operator-live-tls-channel
cargo test --workspace --all-features
cargo clippy --workspace --all-targets --all-features -- -D warnings
RUSTDOCFLAGS='-D warnings' cargo doc --workspace --all-features --no-deps
cargo llvm-cov --workspace --all-features --summary-only
HSAI_PHALA_OPERATOR_ACK=I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN HSAI_PHALA_TLS_CHANNEL_INPUT_JSON=<repo-external-input> cargo run -p hsai-attestation-phala --example operator_live_tls_channel_artifact --features operator-live-tls-channel
```

All commands passed.

No `package.json` or `pnpm-lock.yaml` exists in this repository, so no `pnpm`
gate is available.

`cargo-llvm-cov 0.8.7` was available. The all-feature workspace coverage pass
reported `85.63%` region coverage, `82.52%` function execution, and `83.66%`
line coverage. Branch coverage was not reported by this run.

These coverage percentages are local test instrumentation only; they are not
100% coverage, production readiness, semantic correctness, official benchmark
evidence, accepted Evidence Ledger mutation, or Level2+ evidence.

## Efficacy Map

The suite exercises the repo as a set of bounded local systems:

- DSL parsing, lowering, oracle evaluation, and generated fixtures.
- Deterministic generation, mutation, local JSON replay, and stress paths.
- Evidence primitives, evidence ledgers, append previews, review ledgers,
  proposal ledgers, and candidate validation.
- Benchmark pack writing/reading, pack-readiness metadata, score reports, and
  local-only claim-boundary checks.
- zk-Harness dry-run planning, inert execution metadata, manual handoff mapping,
  and no-live-execution guards.
- Phase L soak configuration, sharding, resume checkpoints, telemetry, health
  reports, failure corpus, and local campaign aggregation.
- Phase M recursion-envelope metadata and manual handoff mapping.
- Phase N zkML workload manifest metadata.
- Phase O pack-readiness construction and output plumbing.
- Phase P read-only dashboard/reporting metadata.
- Phase Q report-bundle metadata and adjacent output plumbing.
- Phase R local audit-index metadata and adjacent output plumbing.
- Phase S audit-index ergonomics, materialized output plumbing, stale-digest
  rejection, symlink rejection, partial-bundle rejection, non-repair overwrite
  behavior, and protected-path overlap hardening.
- Phase T cross-bundle audit-index in-memory views and materialized output
  plumbing, duplicate/conflict signal preservation, declared-file output,
  digest sidecars, stale-digest rejection, symlink rejection, partial-bundle
  rejection, corrupted-root non-repair, and protected-path overlap hardening.
- Phase U local benchmark artifact manifest validation, deterministic Markdown
  rendering, declared-file output, digest sidecars, stale-digest rejection,
  symlink-resolved protected overlap rejection, symlink rejection,
  partial-bundle rejection, corrupted-root non-repair, accepted Evidence Ledger
  non-mutation, score-axis non-population, and protected-path overlap
  hardening.
- Phase V local artifact campaign manifest validation, Phase U output-root
  validation before campaign input construction, deterministic validation
  reports and Markdown rendering, declared-file output, digest sidecars,
  stale-digest rejection, symlink-resolved protected overlap rejection, symlink
  rejection, partial-campaign rejection, corrupted-root non-repair, accepted
  Evidence Ledger non-mutation, score-axis non-population, and protected-path
  overlap hardening.
- HSAI claim-envelope algebra, agent-case lanes, distinct-agent registry,
  managed attestation, offline managed-JWT verification, Phala fixture and
  captured-artifact validation, hermetic fake-client live-verifier surface,
  operator-live artifact plumbing, opt-in Phala provider-client plumbing,
  operator-live runner source-contract checks, Phala API artifact
  materialization source-contract checks, Phala DCAP/PCCS collateral
  materialization source-contract checks, Phala local DCAP/QVL verification
  artifact source-contract checks, managed JWKS artifact source-contract
  checks, Phase 4 anchor registry, economy, membrane, economy simulation, and
  e2e harness invariants.

The strongest local statement supported by this run is:

The implemented local Rust foundation remains internally consistent under the
available unit, integration, doc, lint, formatting, hygiene, and claim-boundary
gates.

## Function-Level Boundary

This validation is function-aware through Rust unit tests, integration tests,
doc tests, clippy, and public API documentation generation. It is not
function-exhaustive proof.

The suite checks behavior through invariants, round trips, adversarial
fixtures, source scans, failure-mode tests, and cross-crate composition tests.
It does not prove that every function is covered by a test, that every branch is
exercised, or that every valid domain input has been sampled.

## Wholeness Boundary

The repo's current wholeness is local and compositional:

- local data models are serialized, deserialized, digested, and validated;
- output plumbing rejects drift instead of repairing corrupted roots;
- source metadata mutation remains forbidden where phases require read-only
  behavior;
- claim boundaries remain capped at their documented levels;
- live provider behavior, network calls, external benchmark execution, and
  official evidence promotion remain blocked unless a later explicit phase
  authorizes them.

This is not production readiness and not benchmark evidence. It is local
regression evidence that the implemented parts still fit together without
claim-boundary escalation.

## Residual Gaps

- No live external backend beyond the operator-run Phala calls, operator-run
  local QVL verification, operator-run managed JWKS fetch, operator-run
  localhost PCCS-compatible replay service, and operator-run direct Intel PCS
  QVL verification was exercised. No live managed-JWT token acceptance or TLS
  channel binding was exercised.
  `docs/97-phala-operator-live-invocation-boundary-spec.md` now defines the
  docs-first invocation boundary, and
  `docs/100-phala-operator-live-invocation-implementation-notes.md` now records
  local invocation plumbing with a hermetic credential-provider boundary,
  injected client boundary, redacted artifact-bundle assembly, replay checks,
  and fail-closed tests. No shipped network client, live Phala call, real
  operator credential source, operator live test, DCAP/PCCS/TLS path in that
  Phala invocation slice, or generated operator artifact exists.
  `docs/101-phala-operator-live-provider-client-boundary-spec.md` now defines
  the future concrete provider-client boundary behind the Phase 100 seam.
  `docs/102-phala-operator-live-provider-client-implementation-notes.md` now
  records an opt-in feature-gated provider-client implementation with a
  transport seam, allowlisted environment credential provider, ureq-backed HTTP
  transport, raw-response digest replacement, and hermetic fake-transport
  tests. `docs/104-phala-operator-live-runner-boundary-spec.md` defines the
  operator-only runner boundary, and
  `docs/105-phala-operator-live-runner-implementation-notes.md` records the
  feature-gated `operator_live_run` example that requires explicit
  acknowledgement, non-secret invocation JSON, matching credential-source
  declaration, and an operator-owned credential environment.
  `docs/106-phala-cloud-api-live-artifact-implementation-notes.md` records the
  Phala Cloud API response materialization path. During Phase 106, an
  operator-run Phala Cloud `/attestations/verify` call accepted the submitted
  TDX quote with checksum
  `5c99c72274ed0745f7788cdf272cc359099c07629833306d1a13f1b8e34596bd`, and a
  local redacted `operator-live/*` artifact was generated outside git. No
  generated operator artifact is committed, and no local DCAP/PCCS/TLS path,
  accepted Evidence Ledger mutation, official benchmark submission, or claim
  above `Attested` exists.
  `docs/107-phala-dcap-pccs-collateral-implementation-notes.md` records the
  operator-only Phala Cloud collateral materialization path. During Phase 107,
  an operator-run Phala Cloud `/attestations/collateral/<checksum>` call
  returned the required collateral fields for checksum
  `5c99c72274ed0745f7788cdf272cc359099c07629833306d1a13f1b8e34596bd`, and a
  digest-only local `dcap-pccs/*` artifact was generated outside git. No raw
  collateral response is retained in the materialized output, no generated
  collateral artifact is committed, no local Intel QVL/DCAP quote-signature
  verification exists, and no TLS path, accepted Evidence Ledger mutation,
  official benchmark submission, or claim above `Attested` exists.
  `docs/108-phala-local-dcap-qvl-verification-notes.md` records the
  operator-only local DCAP/QVL verification artifact path. During Phase 108,
  the raw quote for checksum
  `5c99c72274ed0745f7788cdf272cc359099c07629833306d1a13f1b8e34596bd` was
  downloaded as a 5010-byte binary attachment with SHA-256
  `7c92c34ddc9634c873ea1ca4953a45883ed5692a0c3865323e2044fc58aaf26e`, and
  `dcap-qvl` 0.5.2 verified it with QVL, QE, and platform status `UpToDate`
  and empty advisory IDs. The digest-only local `dcap-qvl/*` artifact was
  generated outside git. No raw quote or QVL report is committed, no repo-native
  DCAP verifier implementation exists, and no TLS path, accepted Evidence
  Ledger mutation, official benchmark submission, or claim above `Attested`
  exists.
  `docs/109-managed-jwks-fetch-artifact-notes.md` records the operator-only
  managed JWKS fetch artifact path. During Phase 109, Intel Trust Authority
  OpenID metadata was fetched from
  `https://portal.trustauthority.intel.com/.well-known/openid-configuration`
  as a 663-byte JSON response with SHA-256
  `a330c2032a986845f959284c4202972bc5e698d7ea652423ca5cebc4ea33edea`, and
  JWKS was fetched from `https://portal.trustauthority.intel.com/certs` as an
  11562-byte JSON response with SHA-256
  `4e1d55c79b698cde4987d791594495e70432879be621a1b6e42a9daafc84bee3`.
  The digest-only local `managed-jwks/*` artifact was generated outside git. No
  raw OpenID or JWKS response is committed, no token is accepted, no live
  managed-JWT signature verification exists, and no TLS path, accepted Evidence
  Ledger mutation, official benchmark submission, or claim above `Attested`
  exists.
  `docs/110-phala-local-pccs-service-artifact-notes.md` records the
  operator-only localhost PCCS-compatible replay service artifact path. During
  Phase 110, `PCCS_URL=http://127.0.0.1:38119 dcap-qvl verify` fetched four
  localhost PCCS-shaped endpoints and returned QVL, QE, and platform status
  `UpToDate` with empty advisory IDs. The final access log SHA-256 was
  `936d86e8e080df2e7b68bfb559b6d43aca5e6df5cbb7ffb1ca2152698531fd77`, and
  the QVL report SHA-256 was
  `36edac15ac8c8c00da61953afa46b2cc428f1047ef8cc664df528938d329c0a7`.
  The digest-only local `local-pccs/*` artifact was generated outside git. No
  raw local PCCS access log or response body is committed, no production Intel
  PCS/PCCS operation exists, no fresh collateral authority is claimed, and no
  TLS path, accepted Evidence Ledger mutation, official benchmark submission,
  or claim above `Attested` exists.
  `docs/111-phala-intel-pcs-direct-artifact-notes.md` records the
  operator-only direct Intel PCS QVL artifact path. During Phase 111,
  `PCCS_URL=https://api.trustedservices.intel.com dcap-qvl verify` returned
  QVL, QE, and platform status `UpToDate` with empty advisory IDs. The QVL
  report SHA-256 was
  `36edac15ac8c8c00da61953afa46b2cc428f1047ef8cc664df528938d329c0a7`, and
  verifier stderr SHA-256 was
  `0e49aa6e694e9654fb3686b74644d340269946900cdfc67954b35254af30474c`.
  The digest-only local `intel-pcs/*` artifact was generated outside git. No
  raw QVL report or raw quote is committed, no repo-native DCAP verifier exists,
  and no TLS path, accepted Evidence Ledger mutation, official benchmark
  submission, or claim above `Attested` exists.
  `docs/113-phala-tls-channel-binding-artifact-implementation-notes.md`
  records the operator-only TLS 1.3 channel artifact path. During Phase 113,
  rustls negotiated `TLS13_AES_256_GCM_SHA384` with
  `cloud-api.phala.com`, validated a three-certificate Web PKI chain, derived a
  32-byte RFC 9266 `EXPORTER-Channel-Binding` value, and received HTTP 200 for
  accepted TDX checksum
  `5c99c72274ed0745f7788cdf272cc359099c07629833306d1a13f1b8e34596bd`
  on that same connection. The exporter SHA-256 was
  `a88d764e3daf48ec6a56cb31890304d3cbc5c4a8d6b140e07b5504d485bde9d7`.
  Exactly five digest-bound files were generated outside git. No credential,
  raw exporter, raw response, or peer certificate is committed. This is
  client-local connection evidence, not RA-TLS, an attested server
  certificate, independent evidence, accepted evidence, or proof.
- No committed generated benchmark artifact bundle, official benchmark
  submission, or accepted Evidence Ledger entry was created. Phase U now
  implements local artifact-bundle packaging APIs and hermetic temp-root tests,
  but it does not create durable submitted artifacts or promote them.
  `docs/98-phase-v-local-artifact-campaign-boundary-spec.md` defines the
  durable local artifact campaign boundary, and
  `docs/103-phase-v-local-artifact-campaign-implementation-notes.md` records
  local campaign output-plumbing APIs and hermetic tests. No committed durable
  campaign output, official submission package, accepted Evidence Ledger
  mutation, score-axis population, external replay evidence, or Level2+
  evidence exists.
  `docs/99-phase-w-reviewed-evidence-promotion-boundary-spec.md` now defines the
  future reviewed accepted-evidence and official-submission boundary. No durable
  submitted artifact, official submission package, accepted Evidence Ledger
  mutation, score-axis population, external replay evidence, or Level2+ evidence
  exists.
- No broader Phase S ergonomics surface was authorized or tested beyond the
  implemented single-index local output boundary.

Any next broadening should start with a docs-first boundary and should name the
state slice before mutation.
