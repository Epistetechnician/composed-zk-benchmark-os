# Agent Rules

## Scope

This repository has been explicitly promoted from the documentation-only Level 0 scaffold to a Level 1 local Rust foundation. Future agents must treat every mutation as a named state slice. Do not infer mutation scope from imports, file names, or convenience.

Allowed in the current Level 1 state:

- Markdown documentation.
- Architecture, schemas, pseudo-types, and pseudo-traits.
- Source inventories and adapter plans.
- Validation checks over the documentation tree.
- Cargo workspace metadata.
- Rust source under `crates/zkbench-core/src/`.
- Rust integration tests and small YAML fixtures under `crates/zkbench-core/tests/`.
- Local JSON replay manifests, local replay results, local evidence ledgers, and benchmark pack skeleton code under `crates/zkbench-core`.
- zk-Harness dry-run adapter preparation types, tests, and docs under `crates/zkbench-core` and `docs/`.
- External-runner boundary, manual handoff bundle, artifact capture contract, provenance contract, result import validation schema, and quarantine types under `crates/zkbench-core` and `docs/`.
- Synthetic result import, normalization, quarantine flow, evidence append proposal, review-state, proposal ledger, and small JSON fixtures under `crates/zkbench-core` and `docs/`.
- Reviewed proposal acceptance policy, manual review decisions, evidence-record candidates, append previews, Level2 eligibility reports, review ledgers, and small JSON fixtures under `crates/zkbench-core` and `docs/`.
- Local soak run configuration, deterministic shard planning, resumable shard checkpoints, local soak runner APIs, internal benchmark OS telemetry, local health reports, failure corpus extraction, report bundle schemas, tests, and docs under `crates/zkbench-core` and `docs/`.

Explicit HSAI claim-envelope phase now allowed: standalone Rust source, tests, and crate metadata under `crates/hsai-claim-envelope`, workspace membership for that crate, and phase notes under `docs/`. This phase is limited to the Level 1 local claim-envelope data model, deterministic provenance hashing, `top()`, `conjoin()`, and acceptance-policy algebra from `docs/23-claim-envelope-implementation-spec.md`; it does not permit identity, economy, evidence lanes, external rails, backend execution, benchmark outputs, or conflating HSAI code with `zkbench-core`.

Explicit HSAI agent-case phase now allowed: standalone Rust source, tests, and crate metadata under `crates/hsai-agent-case`, workspace membership for that crate, and phase notes under `docs/`. This phase is limited to local `AgentCase` data, the `CaseSource` and `EvidenceLane` interfaces, and the honest `DeclaredLane` and `LocalMemoryLane` reference lanes from `docs/26-agent-case-evidence-lane-spec.md`; it does not permit distinct-agent identity, economy, real ZK or TEE lanes, network access, external rails, backend execution, benchmark outputs, or changes to `zkbench-core` or `hsai-claim-envelope`.

Explicit HSAI distinct-agent phase now allowed: standalone Rust source, tests, and crate metadata under `crates/hsai-distinct-agent`, workspace membership for that crate, and phase notes under `docs/`. This phase is limited to anchor data, conditional `DistinctAgentLane` envelope emission, and the minimal deterministic `IdentityRegistry` from `docs/29-distinct-agent-lane-spec.md`; it does not verify attestations, stakes, or credentials, does not permit economy, harness, interop, network access, real ZK or TEE verification lanes, backend execution, benchmark outputs, or changes to existing crates.

Explicit HSAI economy phase now allowed: standalone Rust source, tests, and crate metadata under `crates/hsai-economy`, workspace membership for that crate, and phase notes under `docs/`. This phase is limited to signed in-memory credits, admitted-work reward records, the floor-plus-demand peg stub, demurrage and mutual-credit pool policies, and a deterministic `Economy` ledger gated on the L2 `IdentityRegistry` from `docs/32-economy-stub-spec.md`; it does not permit regenerative-economy claims, external rails, membrane conversion, real settlement, real demand verification, full corrigibility, backend execution, benchmark outputs, or changes to existing crates.

Explicit HSAI membrane phase now allowed: standalone Rust source, tests, and crate metadata under `crates/hsai-membrane`, workspace membership for that crate, phase notes under `docs/`, and exactly two authorized `hsai-economy` methods, `Economy::debit_external` and `Economy::credit_external`, with focused tests. This phase is limited to bounded in-memory conversion between internal `Credits` and opaque `ExternalAmount` units with L2 registration gating, freeze gating, and per-window autonomy-scaled caps from `docs/35-membrane-spec.md`; it does not permit real rails, settlement, fees, external resource control, full corrigibility, backend execution, benchmark outputs, or other changes to existing crates.

Explicit HSAI economy-simulation phase now allowed: standalone Rust source, tests, and crate metadata under `crates/hsai-economy-sim`, workspace membership for that crate, phase notes under `docs/`, and a measured A5 update under `docs/research/assumption-ledger.md`. This phase is limited to a deterministic integer simulation harness over the shipped HSAI economy from `docs/38-economy-simulation-spec.md`; it does not permit new protocol primitives, empirical economic claims, pool-demurrage economy changes, external rails, backend execution, benchmark outputs, or changes to existing crates.

Explicit HSAI funding-rule sweep phase now allowed: backward-compatible Rust source and tests under `crates/hsai-economy-sim`, phase notes under `docs/`, and an append-only A5 refinement under `docs/research/assumption-ledger.md`. This phase is limited to adding `FundingRule`, `run_with_funding`, `SweepCell`, and `sweep` from `docs/41-funding-rule-sweep-spec.md`; it does not permit changes to any other crate, empirical economic claims, new funding mechanisms beyond the three probes, pool-demurrage economy changes, external rails, backend execution, or benchmark outputs.

Explicit HSAI attestation-verification phase now allowed: standalone Rust source, tests, and crate metadata under `crates/hsai-attestation`, workspace membership for that crate, and phase notes under `docs/`. This phase is limited to the interface-level attestation lane from `docs/44-attestation-verification-lane-spec.md`: the `Token`/`VerifiedAttestation`/`VerifyError` types, the `AttestationVerifier` trait, the reference `ManagedTokenVerifier` (which checks anchor id, nonce, report data, measurements, and freshness but does NOT verify the managed service signature), and `AttestationLane` emitting an `Attested` (never `Proven`) anchor-validity `ClaimEnvelope` that discharges the distinct-agent open assumption. It does not permit real managed-service signature verification, JWKS/JWT or vendor-quote validation, network access, real ZK or TEE verification, GPU attestation formats, onchain verification, backend execution, benchmark outputs, or changes to existing crates. A verified attestation is not a proof: it establishes hardware-bounded distinctness only, under the assumption that the managed service signed the token honestly — the signature check is the deferred real step where the stack leaves pure-data.

Explicit managed-attestation Phase 1 integration now allowed: backward-compatible Rust source, tests, and crate metadata under `crates/hsai-attestation`, plus phase notes under `docs/`. This phase is limited to the local report-data binding profile, `ManagedTokenVerifier` field checks over anchor id, nonce, report data, measurements, and freshness, and pure-Rust integration tests composing `AgentCase -> DistinctAgentLane -> AttestationLane<ManagedTokenVerifier> -> IdentityRegistry -> Economy -> Membrane` from `docs/47-managed-attestation-proof-of-agent-prd.md` and `docs/48-managed-attestation-feasibility.md`. It does not permit real managed-service signature verification, JWKS/JWT or vendor-quote validation, Phala API calls, network access, a new backend crate, external rails, backend execution, benchmark outputs, or claims above `Attested`.

Explicit managed-attestation Phase 2 pure-data adversarial harness now allowed: standalone Rust source, tests, and crate metadata under `crates/hsai-e2e-harness`, workspace membership for that crate, and phase notes under `docs/`. This phase is limited to the pure Rust harness in `docs/49-pure-data-adversarial-harness-spec.md`, using the shipped HSAI crates and `AttestationLane<ManagedTokenVerifier>` to test local claim-boundary and admission invariants. It does not permit Phala/Azure/Intel/Apple/Darkbloom integration, managed-service signature verification, JWKS/JWT or vendor-quote validation, network access, external rails, new protocol primitives, backend execution, benchmark outputs, or claims above local regression evidence.

Explicit managed-attestation Phase 3 Phala fixture-backend preparation now allowed: standalone Rust source, tests, and crate metadata under `crates/hsai-attestation-phala`, workspace membership for that crate, and phase notes under `docs/`. This phase is limited to the deterministic fixture-oriented Phala/dstack evidence boundary in `docs/50-phala-attestation-backend-spec.md`: `PhalaEvidence`, `PhalaTrustPolicy`, `PhalaVerifyMode`, `PhalaAttestationVerifier`, parser/policy helpers, and `AttestationVerifier` mapping that accepts only local fixture evidence. It does not permit live Phala API calls, network access, real TDX quote verification, real managed-service signature verification, JWKS/JWT validation, external rails, backend execution, benchmark outputs, or claims above `Attested`. A fixture-accepted Phala evidence record is preparatory local regression evidence, not external attestation evidence and not proof that hardware was actually verified.

Explicit managed-attestation Phase 3 captured-artifact validation add-on now allowed: additive Rust source, tests, and small public fixture data under `crates/hsai-attestation-phala`, plus phase notes under `docs/`. This add-on is limited to parsing and locally validating a captured non-secret Phala/dstack Trust Center artifact in managed-verifier mode: report-data equality, quote-contained report data, compose SHA-256, RTMR event-log replay, app/instance/os event payloads, Docker image digest presence, freshness, and explicit managed trust roots. It does not permit live Phala API calls, network access, local Intel DCAP verification, real managed-service signature/JWKS/JWT validation, external rails, backend execution, benchmark outputs, claims above `Attested`, or Phase 4 anchor-registry claims. Captured artifact validation is managed-verifier evidence, not proof, not local quote verification, and not evidence that the artifact was generated by an HSAI-owned fresh challenge unless the fixture explicitly carries that binding.

Explicit managed-attestation Phase 57 real-artifact promotion planning now allowed: Markdown spec and navigation updates under `docs/`, `README.md`, and `AGENTS.md`. This phase is limited to defining the HSAI-owned fresh challenge protocol, the non-secret artifact bundle shape, verification order, trust-root disclosure, and Phase 4 recheck rule from `docs/57-managed-attestation-real-artifact-promotion-spec.md`. It does not permit Phase 4 `crates/hsai-agent-anchor-registry`, live Phala API calls, network access, local Intel DCAP implementation, managed-service signature/JWKS/JWT implementation, secrets, external rails, backend execution, benchmark outputs, fabricated artifacts, or claims above `Attested`.

Explicit managed-attestation challenge-capture tooling now allowed: additive Rust source and tests under `crates/hsai-attestation-phala`, an operator-facing example binary under `crates/hsai-attestation-phala/examples/`, plus docs/navigation updates under `docs/`, `README.md`, and `AGENTS.md`. This phase is limited to deterministic HSAI-owned challenge packet construction, local challenge validation, in-memory replay guarding, non-secret capture workflow manifests, and an operator-facing capture preflight example that emits those documents from fixed sample inputs, from `docs/58-managed-attestation-challenge-capture-tooling-notes.md` and `docs/59-operator-capture-runbook.md`. It does not permit live Phala API calls, network access, real quote generation, local Intel DCAP implementation, managed-service signature/JWKS/JWT implementation, secrets, external rails, backend execution, benchmark outputs, fabricated artifacts, claims above `Attested`, or Phase 4 `crates/hsai-agent-anchor-registry`.

Explicit managed-attestation Phase 57 real-artifact acceptance now allowed: additive Rust source, tests, a non-secret captured fixture, and docs updates under `crates/hsai-attestation-phala`, `docs/`, `README.md`, and `AGENTS.md`. This phase is limited to extending the `PhalaArtifactBundle` validator to accept the Phase 57 SHA-256 `report_data_binding` format (64 hex chars) alongside the existing Phase 3 captured-artifact format (128 hex chars), committing one real HSAI-owned non-secret artifact fixture generated by an operator capture, an integration test validating that fixture, and the acceptance record under `docs/57-managed-attestation-real-artifact-promotion-spec.md`. It does not permit managed-service signature/JWKS/JWT verification, local Intel DCAP implementation, network access, secrets, external rails, backend execution, benchmark outputs, claims above `Attested`, or Phase 4 `crates/hsai-agent-anchor-registry`.

Explicit managed-attestation Phase 4 proof-of-agent anchor registry now allowed: standalone Rust source, tests, and crate metadata under `crates/hsai-agent-anchor-registry`, workspace membership for that crate, and phase notes under `docs/`, `README.md`, and `AGENTS.md`. This phase is authorized only because the first real HSAI-owned Phala/dstack artifact was accepted under `docs/57-managed-attestation-real-artifact-promotion-spec.md`. It is limited to the local `AgentAnchorSet`, sponsor/bond/reputation anchor data model, deterministic anchor-set hashing, active anchor reuse prevention, sponsor policy enforcement, revocation downgrade/revocation behavior, and claim-envelope export from `docs/51-proof-of-agent-anchor-registry-spec.md`. It does not permit real Proof of Humanity integration, zkTLS proving, legal-entity registry integration, staking/slashing implementation, governance UI, external rails, backend execution, benchmark outputs, local Intel DCAP implementation, managed-service signature/JWKS/JWT verification, network access, global software-agent uniqueness claims, or any claim above the minimum maturity of admitted input envelopes.

Explicit Phase M recursion-envelope stress docs-first opening now allowed and completed: Markdown spec and navigation updates under `docs/`, `README.md`, and `AGENTS.md`. This completed docs-first slice is limited to the boundary contract in `docs/63-phase-m-recursion-envelope-stress-spec.md`: recursion-envelope input contracts, candidate metric labels, validation rules, negative tests, and claim-boundary restrictions. It did not permit Rust implementation code, live gnark execution, Go code, external repo clones, vendored source, external result import, benchmark outputs, official benchmark evidence, ZK backend performance claims, Level2+ evidence creation, dashboards, or claiming that recursion proof is semantic proof.

Explicit Phase M inert contract implementation now allowed and implemented: additive Rust source and tests under `crates/zkbench-core`, plus docs/navigation updates under `docs/`, `README.md`, and `AGENTS.md`. This phase is limited to local inert recursion-envelope candidate data, input refs, metric labels, validation results, serialization helpers, and claim-boundary non-escalation tests from `docs/63-phase-m-recursion-envelope-stress-spec.md`. It does not permit live gnark execution, Go code, external repo clones, vendored source, external result import, benchmark outputs, official benchmark evidence, ZK backend performance claims, Level2+ evidence creation, dashboards, accepted Evidence Ledger mutation, or claiming that recursion proof is semantic proof.

Explicit Phase M adapter-preparation metadata now allowed and implemented: additive Rust source and tests under `crates/zkbench-core`, plus docs/navigation updates under `docs/`, `README.md`, and `AGENTS.md`. This phase is limited to inert `RecursionAdapterPreparationPlan` metadata, expected local artifact declarations, portable artifact-reference validation, JSON serialization helpers, and claim-boundary/source-scan tests from `docs/63-phase-m-recursion-envelope-stress-spec.md`. It does not permit live gnark execution, Go code, external repo clones, vendored source, external result import, executable adapter authorization, executable step lists, benchmark outputs, official benchmark evidence, ZK backend performance claims, Level2+ evidence creation, dashboards, accepted Evidence Ledger mutation, or claiming that recursion proof is semantic proof.

Explicit Phase M manual handoff mapping now allowed and implemented: additive Rust source and tests under `crates/zkbench-core`, plus docs/navigation updates under `docs/`, `README.md`, and `AGENTS.md`. This phase is limited to building and validating a manual-only `RecursionAdapterManualHandoffBundle` from valid `RecursionAdapterPreparationPlan` metadata, reusing the existing external-runner `ManualHandoffBundle` contract, preserving `ManualHandoffOnly` policy, preserving `Level0DesignNote` mapping/export boundaries, and proving that no recursion-adapter result is emitted. It does not permit live gnark execution, Go code, external repo clones, vendored source, external result import, executable adapter authorization, benchmark outputs, official benchmark evidence, ZK backend performance claims, Level2+ evidence creation, dashboards, accepted Evidence Ledger mutation, or claiming that recursion proof is semantic proof.

Explicit Phase N narrow zkML adapter docs-first opening now allowed and completed: Markdown spec and navigation updates under `docs/`, `README.md`, and `AGENTS.md`. This completed docs-first slice is limited to the boundary contract in `docs/64-phase-n-narrow-zkml-adapter-spec.md`: narrow zkML/control-flow purpose, local input contract, candidate metric labels, validation rules, negative tests, non-goals, and claim-boundary restrictions. It does not permit Rust implementation code, live zkML execution, zkonduit or legacy zkML repository checkout, external repo clones, vendored source, external result import, benchmark outputs, official benchmark evidence, ZK backend performance claims, Level2+ evidence creation, dashboards, broad zkML benchmark scope, or treating model accuracy as proof-system correctness.

Explicit Phase N inert manifest implementation now allowed and implemented: additive Rust source and tests under `crates/zkbench-core`, plus docs/navigation updates under `docs/`, `README.md`, and `AGENTS.md`. This phase is limited to inert `ZkMlWorkloadManifest` metadata, local input refs, local model artifact refs, candidate metric labels, workload digest-root validation, JSON serialization helpers, and claim-boundary/source-scan tests from `docs/64-phase-n-narrow-zkml-adapter-spec.md`. It does not permit live zkML execution, zkonduit or legacy zkML repository checkout, external repo clones, vendored source, external result import, executable adapter authorization, executable step lists, benchmark outputs, official benchmark evidence, ZK backend performance claims, Level2+ evidence creation, dashboards, broad zkML benchmark scope, accepted Evidence Ledger mutation, or treating model accuracy as proof-system correctness.

Explicit Phase O-A local reproducible-pack readiness docs-first opening now allowed and completed: Markdown spec and navigation updates under `docs/`, `README.md`, and `AGENTS.md`. This completed docs-first slice is limited to the boundary contract in `docs/65-phase-o-local-reproducible-pack-readiness-spec.md`: local pack-readiness target, local readiness contract, inert replay-command metadata rules, future Level2 promotion preconditions, required negative tests, non-goals, and claim-boundary restrictions. It does not permit Rust implementation code, pack-output generation, external replay, live backend execution, external repo clones, vendored source, external result import, official benchmark evidence, ZK backend performance claims, Level2+ evidence creation, dashboards, broad leaderboard claims, or accepted Evidence Ledger mutation from readiness metadata.

Forbidden in the current Level 1 state:

- `package.json`, `pnpm-lock.yaml`, `yarn.lock`, `package-lock.json`, `node_modules`, JavaScript or TypeScript runtime files, `Makefile`, CI files, generated benchmark artifacts, or benchmark outputs.
- External repo clones or vendored source.
- Fabricated benchmark results.
- Claims that any backend is formally verified unless a future evidence ledger proves the scoped claim.

## Claim Boundaries

Use these statements as hard boundaries:

- A benchmark pass is not a proof.
- A local replay is not official benchmark evidence.
- A formal proof about one layer is not a formal proof about the full system.
- A recursion proof is not semantic proof.
- A backend rejection is not automatically semantic correctness.
- A timeout is not automatically a soundness failure.
- A successful proof is not automatically evidence that the source spec was meaningful.
- A single aggregate score must not hide weak soundness evidence.
- Local replay artifacts are not official benchmark evidence.
- Evidence ledgers are local integrity records, not tamper-proof proof systems.
- Phase F benchmark packs are local packs only.
- Future agents must not reinterpret local oracle results as ZK backend results.
- zk-Harness dry-run plans are inert design artifacts.
- zk-Harness dry-run plans are not benchmark results.
- External execution is disabled by default.
- Future agents must not enable external execution without an explicit new phase.
- Future agents must not reinterpret dry-run plans as benchmark results.
- Future agents must not import external zk-Harness data without provenance and validation.
- Future agents must not elevate claim boundaries from local packs.
- External execution is disabled unless a future explicit phase enables it.
- Manual handoff bundles are not benchmark results.
- Result import candidates are quarantined or pending review until validated.
- Future agents must not convert imported data into Level2 evidence without artifact and provenance validation.
- Future agents must not reinterpret handoff bundles as zk-Harness execution.
- Synthetic result candidates are not benchmark results.
- Evidence append proposals are not accepted evidence.
- Evidence-record candidates are not accepted evidence.
- Append previews are not accepted evidence and must not mutate the accepted Evidence Ledger.
- Level2 eligibility reports are not Level2 evidence.
- Review ledgers are review artifacts only and must not mutate the accepted Evidence Ledger.
- Proposal ledgers are review ledgers only and must not mutate the accepted Evidence Ledger.
- Future agents must not treat synthetic metric candidates as performance evidence.
- Local soak telemetry is not official benchmark evidence.
- Internal timing telemetry is not ZK backend performance.
- Failure corpus entries are reproduction aids, not accepted evidence.
- Future agents must not use soak timing as prover/verifier timing.
- Future agents must not commit large soak outputs unless explicitly requested.
- Future agents must run long soak jobs only with explicit user approval and outside normal tests.
- Future agents must preserve shard resumability and claim-boundary checks.
- Managed-attestation Phase 1 integration tests are local regression evidence only, not external attestation evidence, backend verification, benchmark evidence, or proof.
- Managed-attestation Phase 2 harness results are local regression evidence only, not external attestation evidence, backend verification, benchmark evidence, or proof.
- Managed-attestation Phase 3 fixture backend results are local regression evidence only unless backed by real validated Phala/dstack artifacts in a future explicit phase.
- Managed-attestation Phase 3 captured-artifact validation is managed-verifier artifact evidence only, not local DCAP quote verification, not managed-service signature verification, not benchmark evidence, and not proof.
- Managed-attestation Phase 57 was a promotion spec until the first real HSAI-owned fresh-challenge artifact was accepted under the spec.
- Managed-attestation challenge packets and capture manifests are capture inputs only, not attestation evidence, not proof, not benchmark evidence, and not independent Phase 4 authorization.
- Managed-attestation operator preflight examples and capture runbooks are capture input documentation only, not attestation evidence, not proof, not benchmark evidence, and not independent Phase 4 authorization.
- Managed-attestation Phase 57 real-artifact acceptance is managed-verifier local regression evidence only, not local DCAP quote verification, not managed-service signature verification, not benchmark evidence, not global software-agent uniqueness, and authorizes only the bounded Phase 4 anchor-registry crate.
- Managed-attestation Phase 4 anchor-registry output means one active HSAI identity per accepted, non-reused registered anchor set. It is not global software-agent uniqueness, proof, benchmark evidence, backend execution evidence, local DCAP verification, or managed-service signature verification.

The architecture docs remain Level 0 design notes. The Rust core crate is Level 1 local implementation foundation only.

## Validation Instructions

For the current Level 1 Rust foundation, validate:

```sh
ROOT="/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os"
find "$ROOT" -type f | sort
find "$ROOT" -type f | sort | sed "s#^$ROOT/##"
find "$ROOT" -type f \( -name "package.json" -o -name "pnpm-lock.yaml" -o -name "yarn.lock" -o -name "package-lock.json" -o -path "*/node_modules/*" \)
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo test --workspace --features external-runner
cargo doc --workspace --no-deps
find "$ROOT" -type f -empty
grep -R "benchmark pass is not proof" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "recursion proof is not semantic proof" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "local replay is not official benchmark evidence" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "Manual handoff bundles are not benchmark results" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "Synthetic result candidates are not benchmark results" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "Evidence append proposals are not accepted evidence" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "Evidence-record candidates are not accepted evidence" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "Level2 eligibility reports are not Level2 evidence" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "Local soak telemetry is not official benchmark evidence" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "Internal timing telemetry is not ZK backend performance" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "Failure corpus entries are reproduction aids" "$ROOT/docs" "$ROOT/README.md" "$ROOT/AGENTS.md" || true
grep -R "std::process::Command" "$ROOT/crates/zkbench-core/src" || true
grep -R "Command::new" "$ROOT/crates/zkbench-core/src" || true
grep -R "prover_time\|verifier_time\|proof_size\|zk_harness_time\|memory_usage\|constraint_count" "$ROOT/crates/zkbench-core/tests/fixtures" || true
```

If package scripts are introduced in a later phase, preserve `pnpm run lint` as the heavy gate and split fast gates into `lint:fast`, `test:focused`, `verify:contracts`, and `verify:full`.

## Updating Docs

Every doc edit must preserve terminology:

- Surface DSL
- Parsed AST
- Semantic IR
- Benchmark Family
- Benchmark Instance
- Mutation Variant
- Oracle
- Expected Verdict
- Backend Outcome
- Evidence Record
- Claim Boundary
- Score Report

When changing behavior, document public utilities under `docs/` before claiming completion.

## Future Rust Work

The Rust foundation now includes the DSL/core schema, deterministic local generation, the first mutation engine classes, local JSON replay, evidence ledger persistence, deterministic artifact digests, benchmark pack skeletons, zk-Harness dry-run adapter preparation, the reviewed external-runner boundary schema, a local/synthetic result import prototype, reviewed proposal acceptance primitives, a deterministic local soak runner, internal benchmark OS telemetry, local health reports, failure corpus extraction, bounded Phase L local soak acceptance, Phase M inert recursion-envelope contract types, Phase M inert adapter-preparation metadata, Phase M manual handoff mapping, Phase N narrow zkML docs-first boundary metadata, Phase N inert zkML workload manifest metadata, and Phase O-A local reproducible-pack readiness boundary metadata. Do not run external benchmarks, claim official evidence, add dashboards, broaden recursion/zkML/pack-readiness support beyond the authorized inert Phase M, inert Phase N, and docs-first Phase O-A boundaries, or create Level2+ evidence without a future reviewed phase.

## External Repos

Default to wrap or reference, not fork. Fork only for upstream contribution or when an adapter cannot be implemented without changing upstream. Curated lists are discovery-only. Existing benchmark/formal/zkML/recursion repos are evidence sources and adapter targets, not feature sets to copy.

## Evidence Classification

Classify evidence before using it:

- Level 0: design note only.
- Level 1: local replay evidence.
- Level 2: reproducible benchmark artifact.
- Level 3: cross-backend replay evidence.
- Level 4: formal property statement.
- Level 5: machine-checked proof for a scoped property.
- Level 6: independently reproduced evidence.

Do not claim Level 2+ without artifacts. Do not claim Level 5 without a scoped machine-checked proof.

## Preserving The SOTA Wedge

The novelty is semantic benchmark generation with formal hooks and adversarial mutation scoring. Avoid adapter sprawl, dashboard-first work, and broad cloning. The core must stay centered on Semantic IR, Oracle, Expected Verdict, Backend Outcome, Evidence Record, Claim Boundary, and Score Report.
