# Composed ZK Benchmark OS

A benchmark operating system for generating ZK workloads from control-flow semantics, mutating them adversarially, replaying them across benchmark/formal/proof backends, and scoring performance separately from soundness evidence.

## Thesis

ZK benchmark cases should be generated from semantic machine specifications - states, transitions, guards, loops, invariants, traces, witnesses, and expected accept/reject outcomes - rather than only selected from hand-authored circuits or workload examples.

## Why This Is Novel

Most benchmark systems compare known workloads or circuits. This project starts from explicit semantics, generates families of state machines and loops, creates valid and adversarial mutation variants, then asks each backend what evidence it can produce. The SOTA wedge is the architecture and benchmark-generation thesis, not measured benchmark results yet.

Core novelty:

- Semantic benchmark generation from FSMs, loops, recursion envelopes, and control-flow families.
- Adversarial mutations with expected semantic verdicts.
- Oracle contracts for accepted traces, rejected traces, expected results, witness policies, and public/private boundaries.
- Multi-backend adapters that normalize evidence instead of forcing universal feature parity.
- Separate scoring for performance, correctness, soundness-failure detection, recursion stress, formal evidence, reproducibility, portability, and risk.
- Claim-boundary discipline: benchmark pass is not proof; recursion proof is not semantic proof; local replay is not official benchmark evidence.

## What This Repo Is

This is now a Level 1 local Rust foundation plus the original Level 0 architecture scaffold. It defines the architecture, vocabulary, repo integration decisions, DSL schema, Rust core crate, deterministic generator, v0 mutation engine, local JSON replay adapter, evidence ledger, benchmark pack skeleton, zk-Harness dry-run adapter preparation, external-runner boundary contracts, manual handoff bundle schema, synthetic result import prototype, evidence append proposal workflow, reviewed proposal acceptance policy, evidence-record candidate metadata, append previews, Level2 eligibility checks, review ledger primitives, proposal ledger primitives, scoring primitives, inert recursion-envelope metadata, inert zkML workload manifest metadata, inert pack-readiness metadata, validation gates, and adapter roadmap.

## What This Repo Is Not

This repo is not a benchmark-results claim, formal-verification claim, live external backend integration, fork of existing ZK tooling, or dashboard. No document or test claims Level 2+ evidence. No benchmark results have been generated here.

## Architecture

```text
Specification DSL
  -> State/Loop Generator
  -> Mutation Engine
  -> Multi-Backend Adapter Layer
  -> Scoring And Evidence Ledger
```

The Semantic IR is the center of the system. Backends are evidence lanes around it.

```text
             +------------------+
             |  Surface DSL     |
             +--------+---------+
                      |
                      v
             +------------------+
             |  Semantic IR     |
             +----+--------+----+
                  |        |
        +---------+        +----------------+
        v                                   v
+------------------+              +------------------+
| Generator        |              | Oracle Model     |
+--------+---------+              +--------+---------+
         |                                 |
         v                                 v
+------------------+              +------------------+
| Mutation Engine  |------------->| Expected Verdict |
+--------+---------+              +------------------+
         |
         v
+------------------+      +----------------+      +----------------+
| Backend Adapters |----->| Evidence Record|----->| Score Report   |
+------------------+      +----------------+      +----------------+
```

## Canonical Pipeline

```text
Surface DSL
  -> parsed AST
  -> canonical semantic IR
  -> generated benchmark family
  -> concrete benchmark instance
  -> mutation variant
  -> backend artifact
  -> replay result
  -> evidence record
  -> scored report
```

## Documentation Navigation

| File | Purpose |
|---|---|
| [AGENTS.md](AGENTS.md) | Strict working rules for future agents and maintainers. |
| [docs/00-project-brief.md](docs/00-project-brief.md) | Mission, thesis, success criteria, risks, vocabulary. |
| [docs/01-source-inventory.md](docs/01-source-inventory.md) | External and local source inventory. |
| [docs/02-repo-integration-map.md](docs/02-repo-integration-map.md) | Fork, wrap, ignore, reference, discovery, local pattern, and pending-verification decisions. |
| [docs/03-sota-architecture.md](docs/03-sota-architecture.md) | Serious system architecture and SOTA wedge. |
| [docs/04-fork-wrap-ignore-decisions.md](docs/04-fork-wrap-ignore-decisions.md) | Decision policy for reuse and adapter boundaries. |
| [docs/05-adapter-roadmap.md](docs/05-adapter-roadmap.md) | Adapter phases, manifests, capability flags, anti-goals. |
| [docs/06-dsl-schema.md](docs/06-dsl-schema.md) | v0 DSL pseudo-schema and examples. |
| [docs/07-rust-module-layout.md](docs/07-rust-module-layout.md) | Planned Rust core layout, types, traits, errors, implementation order. |
| [docs/08-benchmark-taxonomy.md](docs/08-benchmark-taxonomy.md) | Benchmark family taxonomy and evidence expectations. |
| [docs/09-mutation-engine.md](docs/09-mutation-engine.md) | Mutation taxonomy, verdicts, triage, provenance. |
| [docs/10-scoring-rubric.md](docs/10-scoring-rubric.md) | Separate performance and soundness scoring with claim-boundary warnings. |
| [docs/11-validation-gates.md](docs/11-validation-gates.md) | Docs-only validation and future gate ladder. |
| [docs/12-task-list.md](docs/12-task-list.md) | Phased execution plan from docs to benchmark packs. |
| [docs/13-semantics-oracles-and-claim-boundaries.md](docs/13-semantics-oracles-and-claim-boundaries.md) | Semantic spine, oracle model, result matrix, claim boundary levels. |
| [docs/14-phase-b-implementation-notes.md](docs/14-phase-b-implementation-notes.md) | Phase B/C local Rust foundation notes and limitations. |
| [docs/15-phase-d-e-generator-mutation-notes.md](docs/15-phase-d-e-generator-mutation-notes.md) | Phase D/E deterministic generator and mutation engine notes. |
| [docs/16-phase-f-local-replay-evidence-ledger-notes.md](docs/16-phase-f-local-replay-evidence-ledger-notes.md) | Phase F local JSON replay, evidence ledger, artifact digest, and benchmark pack notes. |
| [docs/17-phase-g-zk-harness-dry-run-adapter-notes.md](docs/17-phase-g-zk-harness-dry-run-adapter-notes.md) | Phase G zk-Harness dry-run adapter preparation notes. |
| [docs/18-phase-h-external-runner-boundary-notes.md](docs/18-phase-h-external-runner-boundary-notes.md) | Phase H external-runner boundary and manual handoff notes. |
| [docs/19-phase-i-synthetic-result-import-notes.md](docs/19-phase-i-synthetic-result-import-notes.md) | Phase I synthetic result import, normalization, quarantine, proposal, and proposal ledger notes. |
| [docs/20-phase-j-reviewed-proposal-acceptance-notes.md](docs/20-phase-j-reviewed-proposal-acceptance-notes.md) | Phase J reviewed proposal acceptance policy, candidates, previews, eligibility, and review ledger notes. |
| [docs/21-phase-k-local-soak-runner-telemetry-notes.md](docs/21-phase-k-local-soak-runner-telemetry-notes.md) | Phase K local soak runner, internal benchmark OS telemetry, health reports, and failure corpus notes. |
| [docs/22-hyper-sacred-ai-architecture.md](docs/22-hyper-sacred-ai-architecture.md) | Hyper Sacred AI architecture and claim-boundary framing. |
| [docs/23-claim-envelope-implementation-spec.md](docs/23-claim-envelope-implementation-spec.md) | HSAI claim-envelope implementation spec. |
| [docs/24-hsai-implementation-handoff.md](docs/24-hsai-implementation-handoff.md) | HSAI claim-envelope implementation handoff. |
| [docs/25-hsai-claim-envelope-phase-notes.md](docs/25-hsai-claim-envelope-phase-notes.md) | HSAI claim-envelope phase notes. |
| [docs/26-agent-case-evidence-lane-spec.md](docs/26-agent-case-evidence-lane-spec.md) | Agent-case and evidence-lane spec. |
| [docs/27-agent-case-implementation-handoff.md](docs/27-agent-case-implementation-handoff.md) | Agent-case implementation handoff. |
| [docs/28-hsai-agent-case-phase-notes.md](docs/28-hsai-agent-case-phase-notes.md) | HSAI agent-case phase notes. |
| [docs/29-distinct-agent-lane-spec.md](docs/29-distinct-agent-lane-spec.md) | Distinct-agent lane spec. |
| [docs/30-distinct-agent-implementation-handoff.md](docs/30-distinct-agent-implementation-handoff.md) | Distinct-agent implementation handoff. |
| [docs/31-hsai-distinct-agent-phase-notes.md](docs/31-hsai-distinct-agent-phase-notes.md) | HSAI distinct-agent phase notes. |
| [docs/32-economy-stub-spec.md](docs/32-economy-stub-spec.md) | HSAI economy stub spec. |
| [docs/33-economy-implementation-handoff.md](docs/33-economy-implementation-handoff.md) | Economy implementation handoff. |
| [docs/34-hsai-economy-phase-notes.md](docs/34-hsai-economy-phase-notes.md) | HSAI economy phase notes. |
| [docs/35-membrane-spec.md](docs/35-membrane-spec.md) | HSAI membrane spec. |
| [docs/36-membrane-implementation-handoff.md](docs/36-membrane-implementation-handoff.md) | Membrane implementation handoff. |
| [docs/37-hsai-membrane-phase-notes.md](docs/37-hsai-membrane-phase-notes.md) | HSAI membrane phase notes. |
| [docs/38-economy-simulation-spec.md](docs/38-economy-simulation-spec.md) | Economy simulation spec. |
| [docs/39-economy-simulation-handoff.md](docs/39-economy-simulation-handoff.md) | Economy simulation handoff. |
| [docs/40-hsai-economy-sim-phase-notes.md](docs/40-hsai-economy-sim-phase-notes.md) | HSAI economy simulation phase notes. |
| [docs/41-funding-rule-sweep-spec.md](docs/41-funding-rule-sweep-spec.md) | Funding-rule sweep spec. |
| [docs/42-funding-rule-sweep-handoff.md](docs/42-funding-rule-sweep-handoff.md) | Funding-rule sweep handoff. |
| [docs/43-hsai-funding-rule-sweep-phase-notes.md](docs/43-hsai-funding-rule-sweep-phase-notes.md) | HSAI funding-rule sweep phase notes. |
| [docs/44-attestation-verification-lane-spec.md](docs/44-attestation-verification-lane-spec.md) | Attestation-verification lane spec. |
| [docs/45-attestation-verification-handoff.md](docs/45-attestation-verification-handoff.md) | Attestation-verification handoff. |
| [docs/46-attestation-verification-phase-notes.md](docs/46-attestation-verification-phase-notes.md) | Attestation-verification phase notes. |
| [docs/47-managed-attestation-proof-of-agent-prd.md](docs/47-managed-attestation-proof-of-agent-prd.md) | Managed-attestation proof-of-agent PRD. |
| [docs/48-managed-attestation-feasibility.md](docs/48-managed-attestation-feasibility.md) | Managed-attestation feasibility analysis. |
| [docs/49-pure-data-adversarial-harness-spec.md](docs/49-pure-data-adversarial-harness-spec.md) | Pure-data adversarial harness spec. |
| [docs/50-phala-attestation-backend-spec.md](docs/50-phala-attestation-backend-spec.md) | Phala attestation backend spec. |
| [docs/51-managed-attestation-phase1-integration-notes.md](docs/51-managed-attestation-phase1-integration-notes.md) | Managed-attestation Phase 1 integration notes. |
| [docs/51-proof-of-agent-anchor-registry-spec.md](docs/51-proof-of-agent-anchor-registry-spec.md) | Phase 4 proof-of-agent anchor registry spec. |
| [docs/52-managed-attestation-phase2-harness-notes.md](docs/52-managed-attestation-phase2-harness-notes.md) | Managed-attestation Phase 2 harness notes. |
| [docs/53-managed-attestation-phase3-phala-fixture-notes.md](docs/53-managed-attestation-phase3-phala-fixture-notes.md) | Managed-attestation Phase 3 Phala fixture notes. |
| [docs/54-proof-of-agent-anchor-phase4-boundary-note.md](docs/54-proof-of-agent-anchor-phase4-boundary-note.md) | Boundary note recording Phase 4 authorization after real artifact acceptance. |
| [docs/55-real-phala-artifact-handoff.md](docs/55-real-phala-artifact-handoff.md) | Real Phala artifact handoff requirements. |
| [docs/56-managed-attestation-phase3-captured-artifact-notes.md](docs/56-managed-attestation-phase3-captured-artifact-notes.md) | Managed-attestation captured artifact validation notes. |
| [docs/57-managed-attestation-real-artifact-promotion-spec.md](docs/57-managed-attestation-real-artifact-promotion-spec.md) | HSAI-owned real artifact promotion spec for Phase 3. |
| [docs/58-managed-attestation-challenge-capture-tooling-notes.md](docs/58-managed-attestation-challenge-capture-tooling-notes.md) | Managed-attestation challenge packet and capture workflow tooling notes. |
| [docs/59-operator-capture-runbook.md](docs/59-operator-capture-runbook.md) | Operator capture runbook for repo-external Phala/dstack artifact capture. |
| [docs/60-proof-of-agent-anchor-registry-phase-notes.md](docs/60-proof-of-agent-anchor-registry-phase-notes.md) | Phase 4 proof-of-agent anchor registry implementation notes. |
| [docs/61-phase-l-qwable-autoresearch-contract.md](docs/61-phase-l-qwable-autoresearch-contract.md) | Phase L local autoresearch soak contract and guardrails. |
| [docs/62-phase-l-local-soak-acceptance-notes.md](docs/62-phase-l-local-soak-acceptance-notes.md) | Phase L bounded local soak acceptance notes. |
| [docs/63-phase-m-recursion-envelope-stress-spec.md](docs/63-phase-m-recursion-envelope-stress-spec.md) | Phase M recursion-envelope stress spec and claim-boundary contract. |
| [docs/64-phase-n-narrow-zkml-adapter-spec.md](docs/64-phase-n-narrow-zkml-adapter-spec.md) | Phase N narrow zkML adapter docs-first boundary contract. |
| [docs/65-phase-o-local-reproducible-pack-readiness-spec.md](docs/65-phase-o-local-reproducible-pack-readiness-spec.md) | Phase O local reproducible-pack readiness boundary contract. |
| [docs/66-managed-signature-verification-boundary-spec.md](docs/66-managed-signature-verification-boundary-spec.md) | Managed-signature verification docs-first boundary and source attribution. |
| [docs/67-phase-p-read-only-reporting-boundary-notes.md](docs/67-phase-p-read-only-reporting-boundary-notes.md) | Phase P read-only reporting boundary over score and pack-readiness metadata. |
| [docs/68-phase-q-report-bundle-boundary-spec.md](docs/68-phase-q-report-bundle-boundary-spec.md) | Phase Q report-bundle docs-first boundary over read-only reporting metadata. |
| [docs/69-phase-q-report-bundle-implementation-notes.md](docs/69-phase-q-report-bundle-implementation-notes.md) | Phase Q inert in-memory report-bundle metadata implementation notes. |
| [docs/70-phase-q-report-bundle-output-plumbing-spec.md](docs/70-phase-q-report-bundle-output-plumbing-spec.md) | Phase Q report-bundle adjacent local output-plumbing boundary. |
| [docs/71-phase-q-report-bundle-output-implementation-notes.md](docs/71-phase-q-report-bundle-output-implementation-notes.md) | Phase Q report-bundle adjacent local output implementation notes. |
| [docs/72-phase-q-report-bundle-ergonomics-hardening-notes.md](docs/72-phase-q-report-bundle-ergonomics-hardening-notes.md) | Phase Q report-bundle local ergonomics hardening notes. |
| [docs/73-phase-r-local-audit-index-boundary-spec.md](docs/73-phase-r-local-audit-index-boundary-spec.md) | Phase R local audit-index docs-first boundary over existing local metadata outputs. |
| [docs/74-phase-r-local-audit-index-implementation-notes.md](docs/74-phase-r-local-audit-index-implementation-notes.md) | Phase R inert in-memory local audit-index metadata implementation notes. |
| [docs/75-phase-r-audit-index-output-plumbing-spec.md](docs/75-phase-r-audit-index-output-plumbing-spec.md) | Phase R audit-index adjacent local output-plumbing boundary. |
| [docs/76-phase-r-audit-index-output-implementation-notes.md](docs/76-phase-r-audit-index-output-implementation-notes.md) | Phase R audit-index adjacent local output implementation notes. |
| [docs/86-phase-s-audit-index-ergonomics-boundary-spec.md](docs/86-phase-s-audit-index-ergonomics-boundary-spec.md) | Phase S audit-index ergonomics docs-first boundary. |
| [docs/87-phase-s-audit-index-ergonomics-implementation-notes.md](docs/87-phase-s-audit-index-ergonomics-implementation-notes.md) | Phase S in-memory audit-index ergonomics implementation notes. |
| [docs/88-phase-s-audit-index-ergonomics-output-plumbing-spec.md](docs/88-phase-s-audit-index-ergonomics-output-plumbing-spec.md) | Phase S audit-index ergonomics output-plumbing docs-first boundary. |
| [docs/89-phase-s-audit-index-ergonomics-output-plumbing-implementation-notes.md](docs/89-phase-s-audit-index-ergonomics-output-plumbing-implementation-notes.md) | Phase S audit-index ergonomics output-plumbing implementation notes. |
| [docs/90-whole-codebase-validation-report.md](docs/90-whole-codebase-validation-report.md) | Whole-codebase local validation report and claim-boundary summary. |
| [docs/91-phase-t-cross-bundle-audit-index-boundary-spec.md](docs/91-phase-t-cross-bundle-audit-index-boundary-spec.md) | Phase T cross-bundle audit-index docs-first boundary. |
| [docs/92-phase-t-cross-bundle-audit-index-implementation-notes.md](docs/92-phase-t-cross-bundle-audit-index-implementation-notes.md) | Phase T in-memory cross-bundle audit-index implementation notes. |
| [docs/93-phase-t-cross-bundle-audit-index-output-plumbing-spec.md](docs/93-phase-t-cross-bundle-audit-index-output-plumbing-spec.md) | Phase T cross-bundle audit-index output-plumbing docs-first boundary. |
| [docs/94-phase-t-cross-bundle-audit-index-output-implementation-notes.md](docs/94-phase-t-cross-bundle-audit-index-output-implementation-notes.md) | Phase T cross-bundle audit-index output implementation notes. |
| [docs/95-phase-u-local-benchmark-artifact-boundary-spec.md](docs/95-phase-u-local-benchmark-artifact-boundary-spec.md) | Phase U local benchmark artifact docs-first boundary. |
| [docs/96-phase-u-local-benchmark-artifact-implementation-notes.md](docs/96-phase-u-local-benchmark-artifact-implementation-notes.md) | Phase U local benchmark artifact implementation notes. |
| [docs/97-phala-operator-live-invocation-boundary-spec.md](docs/97-phala-operator-live-invocation-boundary-spec.md) | Phala/dstack operator-live invocation docs-first boundary. |
| [docs/98-phase-v-local-artifact-campaign-boundary-spec.md](docs/98-phase-v-local-artifact-campaign-boundary-spec.md) | Phase V durable local artifact campaign docs-first boundary. |
| [docs/99-phase-w-reviewed-evidence-promotion-boundary-spec.md](docs/99-phase-w-reviewed-evidence-promotion-boundary-spec.md) | Phase W reviewed evidence-promotion and official-submission docs-first boundary. |
| [docs/100-phala-operator-live-invocation-implementation-notes.md](docs/100-phala-operator-live-invocation-implementation-notes.md) | Phala/dstack operator-live invocation local plumbing implementation notes. |
| [docs/101-phala-operator-live-provider-client-boundary-spec.md](docs/101-phala-operator-live-provider-client-boundary-spec.md) | Phala/dstack operator-live provider-client docs-first boundary. |
| [docs/102-phala-operator-live-provider-client-implementation-notes.md](docs/102-phala-operator-live-provider-client-implementation-notes.md) | Phala/dstack operator-live provider-client opt-in implementation notes. |
| [docs/103-phase-v-local-artifact-campaign-implementation-notes.md](docs/103-phase-v-local-artifact-campaign-implementation-notes.md) | Phase V local artifact campaign output-plumbing implementation notes. |
| [docs/104-phala-operator-live-runner-boundary-spec.md](docs/104-phala-operator-live-runner-boundary-spec.md) | Phala/dstack operator-live runner docs-first boundary. |
| [docs/105-phala-operator-live-runner-implementation-notes.md](docs/105-phala-operator-live-runner-implementation-notes.md) | Phala/dstack operator-live runner implementation notes. |
| [docs/106-phala-cloud-api-live-artifact-implementation-notes.md](docs/106-phala-cloud-api-live-artifact-implementation-notes.md) | Phala Cloud API live verification response to local operator artifact materialization notes. |
| [docs/107-phala-dcap-pccs-collateral-implementation-notes.md](docs/107-phala-dcap-pccs-collateral-implementation-notes.md) | Phala DCAP/PCCS collateral fetch and digest-only materialization notes. |
| [docs/108-phala-local-dcap-qvl-verification-notes.md](docs/108-phala-local-dcap-qvl-verification-notes.md) | Phala raw quote local DCAP/QVL verification artifact notes. |
| [docs/109-managed-jwks-fetch-artifact-notes.md](docs/109-managed-jwks-fetch-artifact-notes.md) | Managed OpenID/JWKS live fetch digest-only artifact notes. |
| [docs/110-phala-local-pccs-service-artifact-notes.md](docs/110-phala-local-pccs-service-artifact-notes.md) | Phala localhost PCCS-compatible replay service artifact notes. |
| [docs/111-phala-intel-pcs-direct-artifact-notes.md](docs/111-phala-intel-pcs-direct-artifact-notes.md) | Phala raw quote direct Intel PCS QVL artifact notes. |
| [docs/112-phala-tls-channel-binding-artifact-boundary-spec.md](docs/112-phala-tls-channel-binding-artifact-boundary-spec.md) | Phala operator-only TLS 1.3 channel-binding artifact docs-first boundary. |
| [docs/113-phala-tls-channel-binding-artifact-implementation-notes.md](docs/113-phala-tls-channel-binding-artifact-implementation-notes.md) | Phala operator-only TLS 1.3 channel-binding artifact implementation notes. |
| [docs/114-phase-w-promotion-preflight-boundary-spec.md](docs/114-phase-w-promotion-preflight-boundary-spec.md) | Phase W inert reviewed promotion preflight implementation boundary. |
| [docs/115-phase-w-promotion-preflight-implementation-notes.md](docs/115-phase-w-promotion-preflight-implementation-notes.md) | Phase W inert reviewed promotion preflight implementation notes. |
| [docs/116-phase-w-accepted-ledger-append-boundary-spec.md](docs/116-phase-w-accepted-ledger-append-boundary-spec.md) | Phase W accepted Evidence Ledger append transaction docs-first boundary. |
| [docs/117-phase-w-accepted-ledger-append-implementation-notes.md](docs/117-phase-w-accepted-ledger-append-implementation-notes.md) | Phase W accepted Evidence Ledger append transaction implementation notes. |
| [docs/118-phase-w-accepted-ledger-materialization-boundary-spec.md](docs/118-phase-w-accepted-ledger-materialization-boundary-spec.md) | Phase W accepted Evidence Ledger materialization docs-first boundary. |
| [docs/119-phase-w-accepted-ledger-materialization-implementation-notes.md](docs/119-phase-w-accepted-ledger-materialization-implementation-notes.md) | Phase W accepted Evidence Ledger materialization implementation notes. |
| [docs/120-phase-w-official-submission-package-materialization-boundary-spec.md](docs/120-phase-w-official-submission-package-materialization-boundary-spec.md) | Phase W official-submission package materialization docs-first boundary. |
| [docs/121-phase-w-official-submission-package-materialization-implementation-notes.md](docs/121-phase-w-official-submission-package-materialization-implementation-notes.md) | Phase W official-submission package materialization implementation notes. |
| [docs/122-phase-w-external-replay-official-submission-boundary-spec.md](docs/122-phase-w-external-replay-official-submission-boundary-spec.md) | Phase W external replay and official-submission promotion docs-first boundary. |
| [docs/123-phase-w-external-replay-submission-preflight-implementation-notes.md](docs/123-phase-w-external-replay-submission-preflight-implementation-notes.md) | Phase W external replay and official-submission preflight implementation notes. |
| [docs/124-phase-w-external-replay-preflight-output-boundary-spec.md](docs/124-phase-w-external-replay-preflight-output-boundary-spec.md) | Phase W external replay preflight output docs-first boundary. |
| [docs/125-phase-w-external-replay-preflight-output-implementation-notes.md](docs/125-phase-w-external-replay-preflight-output-implementation-notes.md) | Phase W external replay preflight output implementation notes. |
| [docs/126-phase-w-coverage-hardening-notes.md](docs/126-phase-w-coverage-hardening-notes.md) | Phase W external replay preflight output coverage hardening notes. |
| [docs/127-phase-dsl-coverage-campaign-notes.md](docs/127-phase-dsl-coverage-campaign-notes.md) | Local DSL/oracle coverage campaign notes. |
| [docs/128-phase-soak-serialization-coverage-notes.md](docs/128-phase-soak-serialization-coverage-notes.md) | Local soak serialization coverage campaign notes. |
| [docs/129-phase-proposal-validation-coverage-notes.md](docs/129-phase-proposal-validation-coverage-notes.md) | Local evidence append proposal validation coverage campaign notes. |
| [docs/130-phase-phala-provider-coverage-notes.md](docs/130-phase-phala-provider-coverage-notes.md) | Local Phala operator-live provider-client coverage campaign notes. |
| [docs/131-phase-phala-artifact-coverage-notes.md](docs/131-phase-phala-artifact-coverage-notes.md) | Local Phala captured-artifact validation coverage campaign notes. |
| [docs/132-phase-local-json-adapter-coverage-notes.md](docs/132-phase-local-json-adapter-coverage-notes.md) | Local JSON adapter coverage campaign notes. |
| [docs/133-phase-zk-harness-export-coverage-notes.md](docs/133-phase-zk-harness-export-coverage-notes.md) | Local zk-Harness export helper coverage campaign notes. |
| [docs/134-pcsm-governed-agent-admission-boundary-spec.md](docs/134-pcsm-governed-agent-admission-boundary-spec.md) | PCSM-governed agent-output admission docs-first boundary. |
| [docs/135-phase-zk-harness-validation-coverage-notes.md](docs/135-phase-zk-harness-validation-coverage-notes.md) | Local zk-Harness validation coverage campaign notes. |
| [docs/136-phase-hsai-agent-admission-core-notes.md](docs/136-phase-hsai-agent-admission-core-notes.md) | HSAI local agent admission core implementation notes. |
| [docs/137-phase-hsai-admission-e2e-harness-notes.md](docs/137-phase-hsai-admission-e2e-harness-notes.md) | HSAI admission-gated e2e harness implementation notes. |
| [docs/138-phase-hsai-admission-journal-materialization-boundary-spec.md](docs/138-phase-hsai-admission-journal-materialization-boundary-spec.md) | HSAI admission journal materialization docs-first boundary. |
| [docs/139-phase-pcsm-bounded-proof-handoff-intake-boundary-spec.md](docs/139-phase-pcsm-bounded-proof-handoff-intake-boundary-spec.md) | PCSM CL12 bounded-proof handoff intake docs-first boundary. |
| [docs/140-phase-pcsm-bounded-proof-handoff-intake-metadata-notes.md](docs/140-phase-pcsm-bounded-proof-handoff-intake-metadata-notes.md) | PCSM CL12 bounded-proof handoff intake metadata implementation notes. |
| [docs/141-phase-hsai-admission-journal-materialization-implementation-notes.md](docs/141-phase-hsai-admission-journal-materialization-implementation-notes.md) | HSAI admission journal materialization implementation notes. |
| [docs/142-phase-hsai-admission-journal-semantic-readback-boundary-spec.md](docs/142-phase-hsai-admission-journal-semantic-readback-boundary-spec.md) | HSAI admission journal semantic readback docs-first boundary. |
| [docs/143-phase-hsai-admission-journal-semantic-readback-implementation-notes.md](docs/143-phase-hsai-admission-journal-semantic-readback-implementation-notes.md) | HSAI admission journal semantic readback implementation notes. |
| [docs/144-phase-hsai-admission-journal-adversarial-invariant-boundary-spec.md](docs/144-phase-hsai-admission-journal-adversarial-invariant-boundary-spec.md) | HSAI admission journal adversarial invariant docs-first boundary. |
| [docs/145-phase-hsai-admission-journal-adversarial-invariant-implementation-notes.md](docs/145-phase-hsai-admission-journal-adversarial-invariant-implementation-notes.md) | HSAI admission journal adversarial invariant implementation notes. |
| [docs/146-phase-hsai-admission-provenance-transaction-integrity-boundary-spec.md](docs/146-phase-hsai-admission-provenance-transaction-integrity-boundary-spec.md) | HSAI admission provenance and transaction integrity docs-first boundary. |
| [docs/147-phase-hsai-admission-provenance-transaction-integrity-implementation-notes.md](docs/147-phase-hsai-admission-provenance-transaction-integrity-implementation-notes.md) | HSAI admission provenance and transaction integrity implementation notes. |
| [docs/148-phase-hsai-admission-input-semantic-integrity-boundary-spec.md](docs/148-phase-hsai-admission-input-semantic-integrity-boundary-spec.md) | HSAI admission input semantic integrity docs-first boundary. |
| [docs/149-phase-hsai-admission-input-semantic-integrity-implementation-notes.md](docs/149-phase-hsai-admission-input-semantic-integrity-implementation-notes.md) | HSAI admission input semantic integrity implementation notes. |
| [docs/150-phase-hsai-admission-candidate-semantic-closure-boundary-spec.md](docs/150-phase-hsai-admission-candidate-semantic-closure-boundary-spec.md) | HSAI admission candidate semantic closure docs-first boundary. |
| [docs/151-phase-hsai-admission-candidate-semantic-closure-implementation-notes.md](docs/151-phase-hsai-admission-candidate-semantic-closure-implementation-notes.md) | HSAI admission candidate semantic closure implementation notes. |
| [docs/152-phase-hsai-admission-journal-duplicate-json-boundary-spec.md](docs/152-phase-hsai-admission-journal-duplicate-json-boundary-spec.md) | HSAI admission journal duplicate JSON key docs-first boundary. |
| [docs/153-phase-hsai-admission-journal-duplicate-json-implementation-notes.md](docs/153-phase-hsai-admission-journal-duplicate-json-implementation-notes.md) | HSAI admission journal duplicate JSON key implementation notes. |
| [docs/154-phase-new-benchmark-families-boundary-spec.md](docs/154-phase-new-benchmark-families-boundary-spec.md) | Phase 154 new benchmark families docs-first boundary (`NestedLoop`, `GuardHeavyMachine`). |
| [docs/154-phase-new-benchmark-families-implementation-notes.md](docs/154-phase-new-benchmark-families-implementation-notes.md) | Phase 154 new benchmark families implementation notes. |
| [docs/155-phase-operator-soak-campaign-runner-boundary-spec.md](docs/155-phase-operator-soak-campaign-runner-boundary-spec.md) | Phase 155 operator soak campaign runner docs-first boundary. |
| [docs/155-phase-operator-soak-campaign-runner-implementation-notes.md](docs/155-phase-operator-soak-campaign-runner-implementation-notes.md) | Phase 155 operator soak campaign runner implementation notes. |
| [docs/156-phase-mutation-engine-depth-boundary-spec.md](docs/156-phase-mutation-engine-depth-boundary-spec.md) | Phase 156 mutation engine depth docs-first boundary (five new `MutationPass` impls). |
| [docs/156-phase-mutation-engine-depth-implementation-notes.md](docs/156-phase-mutation-engine-depth-implementation-notes.md) | Phase 156 mutation engine depth implementation notes. |
| [docs/157-phase-mutation-distinguishability-scoring-boundary-spec.md](docs/157-phase-mutation-distinguishability-scoring-boundary-spec.md) | Phase 157 mutation distinguishability scoring docs-first boundary. |
| [docs/157-phase-mutation-distinguishability-scoring-implementation-notes.md](docs/157-phase-mutation-distinguishability-scoring-implementation-notes.md) | Phase 157 mutation distinguishability scoring implementation notes. |
| [docs/158-phase-oracle-completeness-audit-boundary-spec.md](docs/158-phase-oracle-completeness-audit-boundary-spec.md) | Phase 158 oracle completeness audit docs-first boundary. |
| [docs/158-phase-oracle-completeness-audit-implementation-notes.md](docs/158-phase-oracle-completeness-audit-implementation-notes.md) | Phase 158 oracle completeness audit implementation notes. |
| [docs/159-phase-formal-lane-interface-stub-boundary-spec.md](docs/159-phase-formal-lane-interface-stub-boundary-spec.md) | Phase 159 formal lane interface stub docs-first boundary. |
| [docs/159-phase-formal-lane-interface-stub-implementation-notes.md](docs/159-phase-formal-lane-interface-stub-implementation-notes.md) | Phase 159 formal lane interface stub implementation notes. |
| [docs/160-phase-mutation-formal-cross-product-boundary-spec.md](docs/160-phase-mutation-formal-cross-product-boundary-spec.md) | Phase 160 mutation × formal cross-product mapping docs-first boundary. |
| [docs/160-phase-mutation-formal-cross-product-implementation-notes.md](docs/160-phase-mutation-formal-cross-product-implementation-notes.md) | Phase 160 mutation × formal cross-product mapping implementation notes. |
| [docs/161-phase-mutation-engine-completion-implementation-notes.md](docs/161-phase-mutation-engine-completion-implementation-notes.md) | Phase 161 mutation engine completion implementation notes. |
| [docs/162-phase-distinguishability-soak-telemetry-implementation-notes.md](docs/162-phase-distinguishability-soak-telemetry-implementation-notes.md) | Phase 162 distinguishability soak telemetry implementation notes. |
| [docs/163-phase-formal-lane-pipeline-implementation-notes.md](docs/163-phase-formal-lane-pipeline-implementation-notes.md) | Phase 163 formal lane pipeline implementation notes. |
| [docs/164-phase-remaining-benchmark-families-implementation-notes.md](docs/164-phase-remaining-benchmark-families-implementation-notes.md) | Phase 164 remaining benchmark families implementation notes. |
| [docs/165-phase-formal-pipeline-observability-hardening-notes.md](docs/165-phase-formal-pipeline-observability-hardening-notes.md) | Phase 165 formal pipeline observability hardening notes. |
| [docs/166-phase-mutation-coverage-first-tranche-notes.md](docs/166-phase-mutation-coverage-first-tranche-notes.md) | Phase 166 mutation coverage first tranche notes. |
| [docs/167-phase-mutation-coverage-second-tranche-notes.md](docs/167-phase-mutation-coverage-second-tranche-notes.md) | Phase 167 mutation coverage second tranche notes. |
| [docs/168-phase-mutation-coverage-third-tranche-notes.md](docs/168-phase-mutation-coverage-third-tranche-notes.md) | Phase 168 mutation coverage third tranche notes. |
| [docs/169-phase-mutation-coverage-fourth-tranche-notes.md](docs/169-phase-mutation-coverage-fourth-tranche-notes.md) | Phase 169 mutation coverage fourth tranche notes. |
| [docs/170-phase-mutation-coverage-fifth-tranche-notes.md](docs/170-phase-mutation-coverage-fifth-tranche-notes.md) | Phase 170 mutation coverage fifth tranche notes. |
| [docs/171-phase-mutation-coverage-sixth-tranche-notes.md](docs/171-phase-mutation-coverage-sixth-tranche-notes.md) | Phase 171 mutation coverage sixth tranche notes. |
| [docs/172-phase-external-handoff-coverage-seventh-tranche-notes.md](docs/172-phase-external-handoff-coverage-seventh-tranche-notes.md) | Phase 172 external handoff coverage seventh tranche notes. |
| [docs/173-phase-external-quarantine-coverage-eighth-tranche-notes.md](docs/173-phase-external-quarantine-coverage-eighth-tranche-notes.md) | Phase 173 external quarantine coverage eighth tranche notes. |
| [docs/174-phase-external-synthetic-coverage-ninth-tranche-notes.md](docs/174-phase-external-synthetic-coverage-ninth-tranche-notes.md) | Phase 174 external synthetic coverage ninth tranche notes. |
| [docs/175-phase-acceptance-policy-coverage-tenth-tranche-notes.md](docs/175-phase-acceptance-policy-coverage-tenth-tranche-notes.md) | Phase 175 acceptance policy coverage tenth tranche notes. |
| [docs/176-phase-evidence-candidate-coverage-eleventh-tranche-notes.md](docs/176-phase-evidence-candidate-coverage-eleventh-tranche-notes.md) | Phase 176 evidence candidate coverage eleventh tranche notes. |
| [docs/177-phase-promotion-preflight-coverage-twelfth-tranche-notes.md](docs/177-phase-promotion-preflight-coverage-twelfth-tranche-notes.md) | Phase 177 promotion preflight coverage twelfth tranche notes. |
| [docs/178-phase-proposal-ledger-coverage-thirteenth-tranche-notes.md](docs/178-phase-proposal-ledger-coverage-thirteenth-tranche-notes.md) | Phase 178 proposal ledger coverage thirteenth tranche notes. |
| [docs/179-phase-zkml-coverage-fourteenth-tranche-notes.md](docs/179-phase-zkml-coverage-fourteenth-tranche-notes.md) | Phase 179 zkML coverage fourteenth tranche notes. |
| [docs/180-phase-external-submission-preflight-coverage-fifteenth-tranche-notes.md](docs/180-phase-external-submission-preflight-coverage-fifteenth-tranche-notes.md) | Phase 180 external submission preflight coverage fifteenth tranche notes. |
| [docs/181-phase-soak-shard-coverage-sixteenth-tranche-notes.md](docs/181-phase-soak-shard-coverage-sixteenth-tranche-notes.md) | Phase 181 soak shard coverage sixteenth tranche notes. |
| [docs/182-phase-evidence-eligibility-coverage-seventeenth-tranche-notes.md](docs/182-phase-evidence-eligibility-coverage-seventeenth-tranche-notes.md) | Phase 182 evidence eligibility coverage seventeenth tranche notes. |
| [docs/183-phase-local-benchmark-artifact-coverage-eighteenth-tranche-notes.md](docs/183-phase-local-benchmark-artifact-coverage-eighteenth-tranche-notes.md) | Phase 183 local benchmark artifact coverage eighteenth tranche notes. |
| [docs/184-phase-accepted-append-output-coverage-nineteenth-tranche-notes.md](docs/184-phase-accepted-append-output-coverage-nineteenth-tranche-notes.md) | Phase 184 accepted append output coverage nineteenth tranche notes. |
| [docs/185-phase-mutation-apply-coverage-twentieth-tranche-notes.md](docs/185-phase-mutation-apply-coverage-twentieth-tranche-notes.md) | Phase 185 mutation apply coverage twentieth tranche notes. |
| [docs/186-phase-official-submission-output-coverage-twenty-first-tranche-notes.md](docs/186-phase-official-submission-output-coverage-twenty-first-tranche-notes.md) | Phase 186 official submission output coverage twenty-first tranche notes. |
| [docs/187-phase-scoring-coverage-twenty-second-tranche-notes.md](docs/187-phase-scoring-coverage-twenty-second-tranche-notes.md) | Phase 187 scoring coverage twenty-second tranche notes. |
| [docs/188-phase-soak-reproduction-coverage-twenty-third-tranche-notes.md](docs/188-phase-soak-reproduction-coverage-twenty-third-tranche-notes.md) | Phase 188 soak reproduction coverage twenty-third tranche notes. |
| [docs/189-phase-external-runner-importer-coverage-twenty-fourth-tranche-notes.md](docs/189-phase-external-runner-importer-coverage-twenty-fourth-tranche-notes.md) | Phase 189 external runner importer coverage twenty-fourth tranche notes. |
| [docs/190-phase-generator-instance-coverage-twenty-fifth-tranche-notes.md](docs/190-phase-generator-instance-coverage-twenty-fifth-tranche-notes.md) | Phase 190 generator instance coverage twenty-fifth tranche notes. |
| [docs/191-phase-recursion-coverage-twenty-sixth-tranche-notes.md](docs/191-phase-recursion-coverage-twenty-sixth-tranche-notes.md) | Phase 191 recursion coverage twenty-sixth tranche notes. |
| [docs/192-phase-evidence-review-coverage-twenty-seventh-tranche-notes.md](docs/192-phase-evidence-review-coverage-twenty-seventh-tranche-notes.md) | Phase 192 evidence review coverage twenty-seventh tranche notes. |
| [docs/193-phase-pack-reader-coverage-twenty-eighth-tranche-notes.md](docs/193-phase-pack-reader-coverage-twenty-eighth-tranche-notes.md) | Phase 193 pack reader coverage twenty-eighth tranche notes. |
| [docs/194-phase-local-artifact-campaign-coverage-twenty-ninth-tranche-notes.md](docs/194-phase-local-artifact-campaign-coverage-twenty-ninth-tranche-notes.md) | Phase 194 local artifact campaign coverage twenty-ninth tranche notes. |
| [docs/77-managed-jwt-signature-verification-notes.md](docs/77-managed-jwt-signature-verification-notes.md) | Managed-JWT offline ES256 signature-verification implementation notes. |
| [docs/78-phala-live-managed-verifier-boundary-spec.md](docs/78-phala-live-managed-verifier-boundary-spec.md) | Phala/dstack live managed-verifier docs-first boundary. |
| [docs/79-phala-hermetic-live-verifier-implementation-spec.md](docs/79-phala-hermetic-live-verifier-implementation-spec.md) | Phala/dstack hermetic live-verifier implementation authorization spec. |
| [docs/80-phala-hermetic-live-verifier-implementation-notes.md](docs/80-phala-hermetic-live-verifier-implementation-notes.md) | Phala/dstack hermetic live-verifier implementation notes. |
| [docs/81-phala-operator-live-path-boundary-spec.md](docs/81-phala-operator-live-path-boundary-spec.md) | Phala/dstack operator-only live path docs-first boundary. |
| [docs/82-phala-operator-live-artifact-plumbing-spec.md](docs/82-phala-operator-live-artifact-plumbing-spec.md) | Phala/dstack operator-live artifact plumbing docs-first boundary. |
| [docs/83-phala-operator-live-artifact-plumbing-implementation-notes.md](docs/83-phala-operator-live-artifact-plumbing-implementation-notes.md) | Phala/dstack operator-live artifact plumbing implementation notes. |
| [docs/84-phala-operator-live-artifact-output-plumbing-boundary-spec.md](docs/84-phala-operator-live-artifact-output-plumbing-boundary-spec.md) | Phala/dstack operator-live artifact output plumbing docs-first boundary. |
| [docs/85-phala-operator-live-artifact-output-plumbing-implementation-notes.md](docs/85-phala-operator-live-artifact-output-plumbing-implementation-notes.md) | Phala/dstack operator-live artifact output plumbing implementation notes. |
| [docs/integrations/zk_harness_adapter.md](docs/integrations/zk_harness_adapter.md) | Future zk-Harness adapter plan. |
| [docs/integrations/formal_semantics_lanes.md](docs/integrations/formal_semantics_lanes.md) | Future clean, zkLean, and Garden formal lanes. |
| [docs/integrations/gnark_recursion_adapter.md](docs/integrations/gnark_recursion_adapter.md) | Future gnark recursion-envelope adapter. |
| [docs/integrations/zkml_benchmark_manifest.md](docs/integrations/zkml_benchmark_manifest.md) | Future narrow zkML workload adapter. |
| [docs/research/zk_external_source_index.md](docs/research/zk_external_source_index.md) | External source index and verification notes. |

## Current Implementation Status

- `zkbench-core` exists as a Rust core crate.
- v0 DSL structs exist for Surface DSL, Parsed AST, Semantic IR, Oracle, Expected Verdict, Backend Outcome, Evidence Record, Claim Boundary, Benchmark Family, Benchmark Instance, Mutation Variant metadata, Replay Manifest metadata, and Score Report primitives.
- YAML fixtures parse.
- Semantic IR lowering exists.
- The local oracle evaluates executable traces for a small v0 subset.
- Deterministic generation exists for BaselineFsm, BranchingFsm, BoundedCounterLoop, NestedLoop, GuardHeavyMachine, RecursiveEnvelope, MemoryHeavyStateMachine, PublicPrivateBoundaryStress, and ZkMlControlFlowMixed.
- Concrete generated Benchmark Instances carry config, provenance, Surface DSL, Semantic IR, traces, expected verdicts, and Level1LocalReplay claim boundaries.
- Mutation engine v0 exists for all 14 declared `MutationClass` variants.
- Mutation distinguishability scoring composes each mutation's `ExpectedVerdict` with each `BackendOutcome` via the existing `classify_result` into a deterministic matrix (`Level1LocalReplay`).
- Oracle completeness audit reports which generated constructs the shipped v0 oracle can evaluate locally (`Level0DesignNote`).
- Formal lane interface stub provides the `FormalVerifier`/`NoopFormalVerifier`/`FormalLane` seam for the "formal hooks" half of the SOTA wedge; the shipped verifier is declared-only and capped at `Level0DesignNote`.
- Mutation × formal cross-product mapping maps each of the 14 declared `MutationClass` variants to the `FormalPropertyScope` it most directly stress-tests (`Level0DesignNote`).
- Mutation provenance records affected machine, transitions, guards/actions, fields when available, expected verdict, safety class, claim boundary, and notes.
- Local JSON adapter exists for local oracle replay only.
- Replay manifest serialization exists.
- Local replay result serialization exists.
- Evidence ledger persistence exists with a deterministic local digest chain.
- Deterministic artifact digesting exists for local JSON and pack files.
- Benchmark pack skeleton exists for local generated instances, mutation variants, replay manifests, replay results, ledgers, and conservative score reports.
- zk-Harness dry-run adapter preparation exists.
- zk-Harness adapter manifest serialization exists.
- zk-Harness dry-run plan serialization exists.
- Local benchmark packs can map into inert zk-Harness dry-run plans.
- External-runner boundary exists.
- Manual handoff bundle schema exists.
- Artifact capture contract exists.
- Provenance contract exists.
- Result import validation schema exists.
- Quarantine schema exists for future external result candidates.
- zk-Harness dry-run plans can map into inert manual handoff bundles.
- Synthetic result candidate JSON import exists for local fixtures only.
- Artifact digest validation checks synthetic candidate references against caller-provided local bytes.
- Provenance validation checks synthetic candidates against the local provenance contract.
- Metric candidate validation rejects unsupported units, missing source refs, negative numeric values, and overclaiming notes.
- Invalid synthetic result candidates are quarantined.
- Valid synthetic result candidates normalize into pending-review drafts only.
- Evidence append proposal primitives exist.
- Manual review decision primitives exist.
- Evidence acceptance policy primitives exist.
- Evidence-record candidate primitives exist.
- Evidence append preview primitives exist and do not mutate `EvidenceLedger`.
- Level2 eligibility checker primitives exist for future-review readiness only.
- Evidence review ledger persistence exists and remains separate from the accepted `EvidenceLedger`.
- Proposal ledger persistence exists and is separate from the accepted `EvidenceLedger`.
- Local soak runner exists for deterministic, sharded, resumable local-only stress studies.
- Local soak run configuration, deterministic shard planning, shard manifests, checkpointing, report bundles, and artifact layout types exist.
- An operator-facing `operator_soak_campaign` example exists under `crates/zkbench-core/examples/` for running an approved, repo-external local soak campaign through the shipped library surface without writing Rust. It reads a fixed authorized set of environment variables, requires an explicit acknowledgement, and emits a non-secret `Level0DesignNote` summary JSON.
- Internal benchmark OS telemetry exists for generation, mutation, local oracle, local replay, pack read/write, proposal-preview counters, and local runner duration.
- Local health report models exist and warn that local soak telemetry is not official benchmark evidence.
- Failure corpus extraction exists with reproduction manifests and minimization metadata only.
- Inert local audit-index metadata exists for summarizing existing local
  report-bundle metadata without writing files, executing replay commands,
  mutating source packs/reports/bundles, or creating accepted evidence.
- Adjacent local audit-index output plumbing exists for exactly
  `audit-index/audit-index-manifest.json` and
  `audit-index/digests/audit-index-manifest.sha256`. The output remains a
  `Level0DesignNote` local integrity summary and is not accepted evidence,
  official benchmark evidence, ZK backend performance, or Level2+ evidence.
- Phase S in-memory audit-index ergonomics now exists for one valid
  `LocalAuditIndexManifest`: exact filters over manifest fields, deterministic
  grouping and sorting, selected input ids, warning summaries, required
  limitation labels, and deterministic Markdown rendering. It writes no files,
  adds no CLI/UI/package runtime, constructs no cross-bundle index, performs no
  external replay, populates no score axes, and creates no accepted, official,
  backend-performance, or Level2+ evidence.
- `docs/88-phase-s-audit-index-ergonomics-output-plumbing-spec.md` records the
  docs-first boundary for future materialized ergonomics output: one selected
  view JSON, one rendered Markdown file, two digest sidecars, output-root safety,
  overwrite-drift rejection, source immutability, and required limitation-label
  preservation. It authorizes no Rust implementation, generated ergonomics files,
  CLI, UI, package runtime files, external replay, score-axis population, or
  Level2+ evidence.
- Phase S audit-index ergonomics output plumbing now materializes exactly
  `audit-index-ergonomics/ergonomics-view.json`,
  `audit-index-ergonomics/rendered/ergonomics-view.md`, and two digest sidecars
  under a caller-owned local root. It rederives the view from the supplied
  manifest/request, rejects protected path overlap, stale digests, symlinks,
  unexpected files, partial bundles, and drift, and remains `Level0DesignNote`
  local presentation metadata only.
- `docs/90-whole-codebase-validation-report.md` records the full local
  validation suite run after Phase S hardening, maps the suite to implemented
  subsystems, and states the remaining coverage and live-execution gaps. It does
  not claim per-function proof, line coverage, production readiness, official
  benchmark evidence, ZK backend performance, Level2+ evidence, or accepted
  Evidence Ledger mutation.
- `docs/91-phase-t-cross-bundle-audit-index-boundary-spec.md` records the
  docs-first boundary for future cross-bundle audit-index planning over
  multiple existing local audit-index manifests. It authorizes no Rust
  implementation, generated cross-bundle files, CLI, UI, package runtime files,
  external replay, score-axis population, accepted Evidence Ledger mutation, or
  Level2+ evidence.
- Phase T in-memory cross-bundle audit-index planning now exists for two or
  more valid `LocalAuditIndexManifest` values. It computes deterministic source
  summaries, groups, duplicate/conflict signals, warning summaries, required
  limitation labels, and Markdown while writing no files, adding no CLI/UI, and
  creating no accepted, official, backend-performance, or Level2+ evidence.
- `docs/93-phase-t-cross-bundle-audit-index-output-plumbing-spec.md` records
  the docs-first boundary for future materialized Phase T output-root plumbing.
  It centers protected-path overlap rejection and corrupted-output-root
  non-repair before any writer/reader API, generated cross-bundle file,
  command-line surface, UI dashboard, package runtime, external replay, official
  benchmark evidence, ZK backend performance claim, score-axis population, or
  Level2+ evidence promotion.
- Phase T cross-bundle audit-index output plumbing now materializes exactly
  `cross-bundle-audit-index/cross-bundle-view.json`,
  `cross-bundle-audit-index/rendered/cross-bundle-view.md`, and two digest
  sidecars under a caller-owned local root. It rederives the view from the
  supplied request, rejects protected path overlap, stale digests, symlinks,
  unexpected files, partial bundles, and drift, and remains `Level0DesignNote`
  local presentation metadata only.
- `docs/95-phase-u-local-benchmark-artifact-boundary-spec.md` records the
  docs-first boundary for future generated local benchmark artifact bundles.
  It permits no Rust implementation, generated artifact files, external replay,
  official benchmark submission, accepted Evidence Ledger mutation, package
  runtime, CLI/UI, ZK backend performance claim, score-axis population, or
  Level2+ promotion in this slice.
- Phase U local benchmark artifact packaging now exists as a Rust API. It
  validates local artifact manifests, renders deterministic Markdown, writes
  exactly one manifest JSON file, one rendered Markdown file, and two digest
  sidecars under a caller-owned output root, rejects protected-path overlap,
  symlink-resolved protected overlap, stale digests, symlinks, unexpected
  files, partial bundles, and repair overwrites, and remains local
  reproducibility packaging only.
- `docs/98-phase-v-local-artifact-campaign-boundary-spec.md` records the
  docs-first boundary for a future user-approved durable local artifact
  campaign under an ignored output root. It authorizes no Rust implementation,
  generated campaign files, external replay, official submission, accepted
  Evidence Ledger mutation, score-axis population, ZK backend performance
  claim, or Level2+ promotion in this slice.
- Phase V local artifact campaign output plumbing now exists as a Rust API. It
  validates campaign manifests, validates Phase U output roots before building
  campaign inputs, renders deterministic Markdown, writes one manifest JSON
  file, one validation JSON file, one rendered Markdown file, and three digest
  sidecars under a caller-owned output root, rejects protected-path overlap,
  stale digests, symlinks, unexpected files, partial campaigns, and repair
  overwrites, and remains local durability metadata only. `.local-artifact-campaigns/`
  is ignored for operator-owned durable local outputs.
- `docs/99-phase-w-reviewed-evidence-promotion-boundary-spec.md` records the
  docs-first boundary for future reviewed accepted-evidence mutation and
  official benchmark submission. It authorizes no accepted Evidence Ledger
  mutation, official submission package, external replay, live backend
  execution, score-axis population, or Level2+ evidence creation in this slice.
- Phase L bounded local soak acceptance exists for
  `phase_l_qwable_local_soak_2026_06_17_extended_256`: 768 completed local
  cases, zero failures, zero failure-corpus entries, a valid report bundle, no
  ZK backend performance claims, and `Level0DesignNote` claim boundary.
- Phase M inert local recursion-envelope contract implementation exists.
  It defines local input contracts, metric labels, validation rules, negative
  tests, serialization helpers, and claim-boundary non-escalation checks, while
  live gnark execution and Level2+ evidence remain blocked.
- Result classification exists.
- Evidence and scoring primitives exist.
- HSAI Level 1 local crates exist for claim envelopes, agent cases,
  PCSM-governed local admission, distinct-agent registration, economy,
  membrane conversion, economy simulation, managed-attestation verification,
  pure-data e2e harnessing, and Phala/dstack fixture/captured-artifact
  validation.
- Managed-attestation Phase 57 defines the real-artifact promotion
  requirements for an HSAI-owned fresh challenge. A first real HSAI-owned
  Phala/dstack artifact has been captured and accepted under this spec
  (2026-06-16); see
  [docs/57-managed-attestation-real-artifact-promotion-spec.md](docs/57-managed-attestation-real-artifact-promotion-spec.md).
  The acceptance is managed-verifier local regression evidence only. It
  authorizes only the bounded Phase 4 anchor-registry crate and no stronger
  attestation or uniqueness claim.
- `hsai-agent-anchor-registry` implements the Phase 4 local Proof of Agent
  anchor registry. It records one active HSAI identity per accepted,
  non-reused registered anchor set; it does not prove global software-agent
  uniqueness.
- `hsai-e2e-harness` now composes the Phase 4 anchor registry over the pure-data
  managed-attestation harness path. This is local regression evidence only, not
  backend verification, external attestation evidence, proof, or benchmark
  output.
- `docs/66-managed-signature-verification-boundary-spec.md` records the
  managed-attestation boundary as source attribution for managed-service
  signature/JWKS/JWT or quote verification.
- `docs/77-managed-jwt-signature-verification-notes.md` records the first
  bounded implementation of that boundary: an offline ES256 managed-JWT verifier
  over local in-memory public keys. It performs no JWKS fetch, no live service
  call, no DCAP quote verification, no network access, and no claim above
  `Attested`.
- `docs/78-phala-live-managed-verifier-boundary-spec.md` opens the next
  docs-first managed-attestation boundary: Phala/dstack live managed-verifier
  planning only. It permits no Rust implementation, network access, live Phala
  calls, secrets, local DCAP, backend execution, benchmark output, Phase 4
  semantic changes, or claims above `Attested`.
- `docs/79-phala-hermetic-live-verifier-implementation-spec.md` records the
  code-phase authorization spec for a future hermetic Phala/dstack verifier
  surface: provider trait, offline test double, response normalization, failure
  taxonomy, trust-root mapping, replay/freshness checks, and `Attested`-only
  output. This spec itself adds no Rust code and still forbids live calls in
  normal tests.
- `docs/80-phala-hermetic-live-verifier-implementation-notes.md` records the
  implementation of that hermetic surface in `hsai-attestation-phala`: injected
  provider-client trait, deterministic in-memory fake client, normalized
  response validation, replay/freshness guard, trust-root mapping, and
  `Attested`-only output. It still performs no live calls, network access,
  local DCAP, credential handling, or benchmark work.
- `docs/81-phala-operator-live-path-boundary-spec.md` records the docs-first
  operator-only live-path boundary: secret handling outside git, explicit
  operator acknowledgement, timeout and retry limits, redaction, audit output,
  ignored/feature-gated live behavior, and `Attested`-only claim limits. It
  authorizes no Rust implementation, examples, credentials, generated
  artifacts, or live Phala calls in this slice.
- `docs/82-phala-operator-live-artifact-plumbing-spec.md` records the
  docs-first operator-live artifact plumbing boundary: local output-bundle file
  roles, digest and schema rules, redaction-report validation, deterministic
  validation requirements, future code touch surface, hermetic test
  requirements, and `Attested`-only claim limits. It authorizes no Rust
  implementation, examples, scripts, credentials, generated artifacts, operator
  live tests, network access, or live Phala calls in this slice.
- `docs/83-phala-operator-live-artifact-plumbing-implementation-notes.md`
  records the local in-memory implementation of that artifact-plumbing surface
  in `hsai-attestation-phala`: declared logical file parsing, portable path
  checks, schema and SHA-256 digest validation, redaction-report validation,
  provider/trust-root consistency checks, existing hermetic response validation,
  and `Attested`-only output metadata. It performs no filesystem writes, network
  access, credential loading, live Phala calls, operator live tests, local DCAP,
  or benchmark work.
- `docs/84-phala-operator-live-artifact-output-plumbing-boundary-spec.md`
  records the docs-first boundary for future materialized output plumbing:
  caller-selected output-root rules, write/read policy, overwrite policy,
  symlink and path-traversal rejection, raw-response retention limits, future
  tests, and `Attested`-only claim limits. It authorizes no Rust
  implementation, filesystem writes, examples, scripts, credentials, generated
  operator artifacts, operator live tests, network access, or live Phala calls
  in this slice.
- `docs/85-phala-operator-live-artifact-output-plumbing-implementation-notes.md`
  records the local output-root implementation of that materialized artifact
  surface in `hsai-attestation-phala`: explicit output-root validation,
  symlink rejection, explicit overwrite mode, staged writes, declared-file-only
  reads, stale digest rejection, raw-response body retention rejection, and
  Phase 83 in-memory validation reuse. It performs no network access, credential
  loading, live Phala calls, operator live tests, local DCAP, managed-service
  signature verification, generated operator artifact acceptance, or benchmark
  work.
- `docs/97-phala-operator-live-invocation-boundary-spec.md` records the
  docs-first boundary for a future operator-owned live Phala/dstack invocation
  path. It authorizes no Rust implementation, examples, scripts, credentials,
  generated operator artifacts, operator live tests, network access, live Phala
  calls, local DCAP, PCCS, JWKS fetching, TLS channel binding, accepted Evidence
  Ledger mutation, benchmark output, or claims above `Attested` in this slice.
- `docs/100-phala-operator-live-invocation-implementation-notes.md` records the
  local operator-live invocation plumbing implementation. The
  `hsai-attestation-phala` crate now has an explicit invocation input, opaque
  credential-provider boundary, credential-aware injected client boundary,
  bounded retry handling, replay rejection, redacted artifact-bundle assembly,
  and Phase 85 output-root reuse. It still ships no HTTP client, performs no
  live Phala call, loads no process environment credentials, runs no operator
  live tests, implements no local DCAP/PCCS/JWKS/TLS path, creates no benchmark
  output, mutates no accepted Evidence Ledger, and claims nothing above
  `Attested`.
- `docs/101-phala-operator-live-provider-client-boundary-spec.md` records the
  docs-first boundary for a future concrete Phala/dstack provider client behind
  the existing Phase 100 injected-client seam. It authorizes no Rust
  implementation, Cargo metadata, examples, scripts, package runtime files,
  network access, live Phala calls, operator live tests, real credentials,
  generated operator artifacts, local DCAP, PCCS, JWKS fetching, TLS channel
  binding, benchmark output, accepted Evidence Ledger mutation, or claims above
  `Attested` in this slice.
- `docs/102-phala-operator-live-provider-client-implementation-notes.md`
  records the opt-in Phala/dstack provider-client implementation behind the
  existing Phase 100 seam. The `operator-live-provider` feature adds explicit
  configuration, an allowlisted environment credential provider, a transport
  seam, a ureq-backed HTTP transport, normalized response parsing, and
  raw-response digest replacement. It is disabled by default, has hermetic fake
  transport tests, commits no credentials or generated operator artifacts, runs
  no operator live test, performs no live Phala call in normal gates, implements
  no DCAP/PCCS/TLS or token-verification path, creates no benchmark output,
  mutates no accepted Evidence Ledger, and claims nothing above `Attested`.
- `docs/104-phala-operator-live-runner-boundary-spec.md` records the
  docs-first boundary for a future operator-only live runner over the existing
  provider-client and invocation plumbing. It keeps live calls explicit,
  feature-gated, credential-free in git, excluded from normal tests, and capped
  at `Attested`.
- `docs/105-phala-operator-live-runner-implementation-notes.md` records the
  operator-only `operator_live_run` example. It requires explicit
  acknowledgement, a non-secret invocation JSON path, a matching credential
  source declaration, and `--features operator-live-provider`; it writes only
  the existing redacted `operator-live/*` bundle. No operator live artifact is
  generated unless a real operator supplies endpoint, credential, and input JSON
  outside git.
- `docs/106-phala-cloud-api-live-artifact-implementation-notes.md` records the
  operator-only Phala Cloud `/attestations/verify` response materialization
  path. The live API call is performed outside normal tests by the authorized
  operator CLI, and the example maps the saved raw response into the existing
  redacted `operator-live/*` bundle without retaining the raw response body or
  committing generated artifacts.
- `docs/107-phala-dcap-pccs-collateral-implementation-notes.md` records the
  operator-only Phala Cloud collateral materialization path. The live
  `/attestations/collateral/<checksum>` call is performed outside normal tests,
  and the example writes digest-only `dcap-pccs/*` metadata outside git. It does
  not implement local Intel QVL/DCAP quote-signature verification or operate a
  local PCCS.
- `docs/108-phala-local-dcap-qvl-verification-notes.md` records the
  operator-only local DCAP/QVL verification artifact path. The raw quote is
  downloaded outside normal tests, verified by the operator-installed
  `dcap-qvl` CLI, and the example writes digest-only `dcap-qvl/*` metadata
  outside git. It does not add a repo-native DCAP verifier or operate a local
  PCCS service.
- `docs/109-managed-jwks-fetch-artifact-notes.md` records the operator-only
  managed JWKS fetch artifact path. Intel Trust Authority OpenID metadata and
  JWKS are fetched outside normal tests, and the example writes digest-only
  `managed-jwks/*` metadata outside git. It does not accept tokens, verify a
  live managed JWT, or add network access to normal tests.
- `docs/110-phala-local-pccs-service-artifact-notes.md` records the
  operator-only localhost PCCS-compatible replay service artifact path. The
  raw quote and Phala collateral are fetched outside normal tests, `dcap-qvl`
  is run with `PCCS_URL` pointed at `127.0.0.1`, and the example writes
  digest-only `local-pccs/*` metadata outside git. It does not operate Intel
  PCS or a production PCCS.
- `docs/111-phala-intel-pcs-direct-artifact-notes.md` records the
  operator-only direct Intel PCS QVL artifact path. The raw quote is verified
  by `dcap-qvl` with `PCCS_URL=https://api.trustedservices.intel.com`, and the
  example writes digest-only `intel-pcs/*` metadata outside git. It does not
  add a repo-native DCAP verifier.
- Managed-attestation challenge packet tooling exists for local, non-secret
  capture preflight. It creates capture inputs only, not real attestation
  evidence. The operator-facing preflight example
  (`crates/hsai-attestation-phala/examples/operator_capture_preflight.rs`)
  emits a JSON challenge packet and capture manifest from fixed sample inputs,
  and `docs/59-operator-capture-runbook.md` documents the repo-external
  capture steps an operator must run to produce a real artifact.
- No external adapters exist.
- No live zk-Harness execution exists.
- No live external execution exists beyond the operator-only Phala and managed
  JWKS artifact paths recorded above.
- No real external result import exists.
- No local soak telemetry is used as ZK backend performance.
- No failure corpus entry is accepted evidence.
- No evidence append proposal is accepted evidence.
- No evidence-record candidate is accepted evidence.
- No append preview is accepted evidence.
- No Level2 eligibility report is Level2 evidence.
- No review ledger entry is accepted evidence.
- No external adapter evidence exists.
- No official benchmark evidence exists.
- No formal evidence exists.

## Next Implementation Slice

For the benchmark OS track,
[docs/98-phase-v-local-artifact-campaign-boundary-spec.md](docs/98-phase-v-local-artifact-campaign-boundary-spec.md)
now records the docs-first boundary for a future durable local artifact campaign,
and
[docs/103-phase-v-local-artifact-campaign-implementation-notes.md](docs/103-phase-v-local-artifact-campaign-implementation-notes.md)
records the local output-plumbing implementation for that campaign boundary.
It still does not create official benchmark evidence, accepted Evidence Ledger
entries, external replay evidence, score-axis population, ZK backend performance
claims, or Level2+ evidence.
[docs/99-phase-w-reviewed-evidence-promotion-boundary-spec.md](docs/99-phase-w-reviewed-evidence-promotion-boundary-spec.md)
records the docs-first boundary for future accepted-evidence promotion and
official submission. The next implementation slice must stay inside one of
those contracts and still cannot create official benchmark evidence, accepted
Evidence Ledger entries, external replay evidence, score-axis population, ZK
backend performance claims, or Level2+ evidence without the separately
authorized implementation phase.
[docs/114-phase-w-promotion-preflight-boundary-spec.md](docs/114-phase-w-promotion-preflight-boundary-spec.md)
authorizes the next narrow inert implementation surface: reviewed promotion
preflight metadata, fail-closed validation, deterministic digesting, and
official-submission package metadata that remains blocked until accepted
evidence ids exist. It still does not authorize accepted Evidence Ledger
mutation, official submission, external replay, live backend execution,
score-axis population, or Level2+ evidence.
[docs/134-pcsm-governed-agent-admission-boundary-spec.md](docs/134-pcsm-governed-agent-admission-boundary-spec.md)
records a separate docs-first HSAI admission-governance boundary. A future code
phase may use the PCSM pattern only as a local hermetic design template between
raw agent/provider output and governed state mutation. That future phase would
still need separate authorization and must not bypass Phase W review,
accepted-ledger append validation, official-submission packaging, external
replay preflight, or managed-attestation claim boundaries.
[docs/115-phase-w-promotion-preflight-implementation-notes.md](docs/115-phase-w-promotion-preflight-implementation-notes.md)
records the implementation of that inert preflight surface in `zkbench-core`.
It validates promotion prerequisites and official-submission package metadata,
but still creates no accepted Evidence Ledger entry and performs no official
submission.
[docs/116-phase-w-accepted-ledger-append-boundary-spec.md](docs/116-phase-w-accepted-ledger-append-boundary-spec.md)
opens the next docs-first boundary for a future local accepted-ledger append
transaction over explicit inputs. This boundary still does not authorize Rust
implementation, accepted Evidence Ledger mutation, official submission,
external replay, live backend execution, score-axis population, or Level2+
evidence.
[docs/117-phase-w-accepted-ledger-append-implementation-notes.md](docs/117-phase-w-accepted-ledger-append-implementation-notes.md)
records the guarded local implementation of that append transaction in
`zkbench-core`. It can append only Level1-or-below reviewed evidence into a
caller-supplied local `EvidenceLedger` after preflight, candidate, review,
preview, digest, and ledger-tip validation. It still creates no official
benchmark submission, external replay evidence, score-axis population, or
Level2+ evidence.
[docs/118-phase-w-accepted-ledger-materialization-boundary-spec.md](docs/118-phase-w-accepted-ledger-materialization-boundary-spec.md)
and
[docs/119-phase-w-accepted-ledger-materialization-implementation-notes.md](docs/119-phase-w-accepted-ledger-materialization-implementation-notes.md)
record the local JSON materialization path for that guarded append. It can load
or create one explicit local ledger file and write the appended local ledger
through a same-directory temporary file. It still creates no official benchmark
submission, external replay evidence, score-axis population, or Level2+
evidence.
[docs/120-phase-w-official-submission-package-materialization-boundary-spec.md](docs/120-phase-w-official-submission-package-materialization-boundary-spec.md)
and
[docs/121-phase-w-official-submission-package-materialization-implementation-notes.md](docs/121-phase-w-official-submission-package-materialization-implementation-notes.md)
record the local official-submission package output-root path. It materializes
digest-bound local review files from valid package metadata plus an accepted
ledger JSON file, rejects package drift, stale digests, unexpected files,
unsafe paths, endpoint submission, and score-axis population. It still creates
no committed generated package artifact, official endpoint call, official
benchmark submission, external replay evidence, or Level2+ evidence.
[docs/122-phase-w-external-replay-official-submission-boundary-spec.md](docs/122-phase-w-external-replay-official-submission-boundary-spec.md)
opens the next docs-first boundary for a future external replay and official
submission promotion path. It defines required inputs, validation order,
future generated-output shape, redaction rules, operator acknowledgement, and
claim separation. It authorizes no Rust implementation, external replay,
network access, credentials, official endpoint call, generated artifact,
accepted Evidence Ledger mutation, score-axis population, or Level2+ evidence.
[docs/123-phase-w-external-replay-submission-preflight-implementation-notes.md](docs/123-phase-w-external-replay-submission-preflight-implementation-notes.md)
records the local preflight implementation for that boundary. It validates an
accepted ledger JSON path, Phase 121 package output, expected package digests,
non-secret benchmark target metadata, external replay provenance, source
artifact digests, operator acknowledgement, future output-root safety,
redaction policy, and claim-class separation. It still runs no external replay,
calls no endpoint, uses no credentials, writes no generated artifacts, mutates
no accepted Evidence Ledger, populates no score axes, and creates no Level2+
evidence.
[docs/124-phase-w-external-replay-preflight-output-boundary-spec.md](docs/124-phase-w-external-replay-preflight-output-boundary-spec.md)
opens the next docs-first boundary for a future local output-root materializer
for Phase 123 preflight reports. It defines declared local files, digest
sidecars, redaction requirements, protected-root rules, and future hermetic
tests. It authorizes no Rust implementation, generated output, committed
artifact, external replay, endpoint call, credential access, accepted Evidence
Ledger mutation, score-axis population, or Level2+ evidence.
[docs/125-phase-w-external-replay-preflight-output-implementation-notes.md](docs/125-phase-w-external-replay-preflight-output-implementation-notes.md)
records the local output materializer for that boundary. It writes and reads
declared digest-bound `external-replay-submission/*` review files from a valid
Phase 123 request/report pair, rejects drift and raw-material retention, and
still runs no external replay, calls no endpoint, reads no credentials, mutates
no accepted Evidence Ledger, populates no score axes, and creates no Level2+
evidence.
[docs/126-phase-w-coverage-hardening-notes.md](docs/126-phase-w-coverage-hardening-notes.md)
records local Phase W coverage hardening for the Phase 125 output materializer.
It adds focused regression coverage for unsafe output roots, symlinks,
digest-consistent malformed files, and digest-consistent readback drift. It
does not add live provider execution, external replay, official submission,
accepted Evidence Ledger mutation, score-axis population, Level2+ evidence, or
100% coverage.
[docs/127-phase-dsl-coverage-campaign-notes.md](docs/127-phase-dsl-coverage-campaign-notes.md)
records a bounded local DSL/oracle coverage campaign. It adds hermetic
regression tests for guard/action evaluation, expression helpers, validation
rejections, and claim-boundary parsing behavior. It changes no production API
and does not add live execution, external replay, official submission, accepted
Evidence Ledger mutation, score-axis population, Level2+ evidence, or 100%
coverage.
[docs/128-phase-soak-serialization-coverage-notes.md](docs/128-phase-soak-serialization-coverage-notes.md)
records a bounded local soak serialization coverage campaign. It adds hermetic
round-trip and malformed-JSON error-context tests for local soak artifact JSON
helpers. It changes no production API and does not add live execution, external
replay, official submission, accepted Evidence Ledger mutation, score-axis
population, Level2+ evidence, or 100% coverage.
[docs/129-phase-proposal-validation-coverage-notes.md](docs/129-phase-proposal-validation-coverage-notes.md)
records a bounded local evidence append proposal validation coverage campaign.
It adds hermetic rejection-path tests for local proposal metadata, blocking
import issues, claim-boundary escalation, accepted-evidence assertions, and
forbidden proof/official-evidence wording. It changes no production API and
does not add live execution, external replay, official submission, accepted
Evidence Ledger mutation, score-axis population, Level2+ evidence, or 100%
coverage.
[docs/130-phase-phala-provider-coverage-notes.md](docs/130-phase-phala-provider-coverage-notes.md)
records a bounded local Phala operator-live provider-client coverage campaign.
It adds hermetic fail-closed tests for zero-timeout config rejection,
unapproved credential-source rejection before transport, HTTP `403` auth
mapping, and non-UTF-8 bearer-token rejection before network construction. It
changes no production API and does not add live Phala calls, operator live
tests, credentials, generated operator artifacts, accepted Evidence Ledger
mutation, score-axis population, Level2+ evidence, or 100% coverage.
[docs/131-phase-phala-artifact-coverage-notes.md](docs/131-phase-phala-artifact-coverage-notes.md)
records a bounded local Phala captured-artifact validation coverage campaign.
It adds hermetic fail-closed tests for invalid JSON and hex inputs, freshness
rejection, managed-verifier trust rejection, event-log payload drift, Docker
digest shape, and RTMR event index drift. It changes no production API and
does not add live Phala calls, operator live tests, credentials, generated
operator artifacts, accepted Evidence Ledger mutation, score-axis population,
Level2+ evidence, or 100% coverage.
[docs/132-phase-local-json-adapter-coverage-notes.md](docs/132-phase-local-json-adapter-coverage-notes.md)
records a bounded local JSON adapter coverage campaign. It adds hermetic
fail-closed tests for claim-boundary and adapter drift, missing subject
payloads, selected-trace drift, mock replay command/status handling, legacy
manifest preparation, and empty-evidence normalization. It changes no
production API and does not add live external execution, external replay,
official submission, accepted Evidence Ledger mutation, score-axis population,
Level2+ evidence, or 100% coverage.
[docs/133-phase-zk-harness-export-coverage-notes.md](docs/133-phase-zk-harness-export-coverage-notes.md)
records a bounded local zk-Harness export helper coverage campaign. It adds
hermetic tests for direct pack export, dry-run plan JSON round-trip, adapter
manifest JSON round-trip, and malformed JSON rejection. It changes no
production API and does not add zk-Harness execution, live external execution,
external replay, official submission, accepted Evidence Ledger mutation,
score-axis population, Level2+ evidence, or 100% coverage.
[docs/134-pcsm-governed-agent-admission-boundary-spec.md](docs/134-pcsm-governed-agent-admission-boundary-spec.md)
records a docs-first PCSM-governed agent-output admission boundary from the
recoverable-ghost-states handoff. It treats PCSM as an admission-governance
template for strict typed candidates, deterministic accept/reject decisions,
append-only journals, source digest binding, and explicit nonclaims. It imports
no recoverable-ghost artifacts, changes no Rust code, creates no accepted
Evidence Ledger entry, and does not claim PCSM evidence, benchmark evidence,
Level2+ evidence, production readiness, semantic correctness, or global
software-agent uniqueness in this repository.
[docs/135-phase-zk-harness-validation-coverage-notes.md](docs/135-phase-zk-harness-validation-coverage-notes.md)
records a bounded local zk-Harness validation coverage campaign. It adds
hermetic fail-closed tests for dry-run validation issue paths across identifier
drift, unsupported-feature warning behavior, metric drift, inert command drift,
relative-path rejection, artifact/family/trace mapping drift, and forbidden
benchmark-evidence language. It changes no production API and does not add
zk-Harness execution, live external execution, external replay, official
submission, accepted Evidence Ledger mutation, score-axis population, Level2+
evidence, or 100% coverage.
[docs/136-phase-hsai-agent-admission-core-notes.md](docs/136-phase-hsai-agent-admission-core-notes.md)
records the local HSAI agent admission core. The `hsai-agent-admission` crate
implements strict typed `AgentAdmissionCandidate` inputs,
`AgentAdmissionPolicy`, `AgentAdmissionDecision`, append-only in-memory
`AgentAdmissionJournal` validation, and accepted-envelope handoff from admitted
claim-envelope proposals. It imports no recoverable-ghost runtime or artifact,
performs no provider call, mutates no accepted Evidence Ledger, populates no
score axes, creates no Level2+ evidence, and does not claim semantic
correctness, production readiness, proof, benchmark evidence, or global
software-agent uniqueness.
[docs/137-phase-hsai-admission-e2e-harness-notes.md](docs/137-phase-hsai-admission-e2e-harness-notes.md)
records the admission-gated HSAI e2e harness integration. The
`hsai-e2e-harness` crate now depends on `hsai-agent-admission` and covers
accepted, rejected, and quarantined admission decisions before downstream
registry, economy, or membrane use. It performs no provider call, mutates no
accepted Evidence Ledger, creates no live/external evidence, populates no score
axes, and does not claim proof, benchmark evidence, semantic correctness,
production readiness, or global software-agent uniqueness.
[docs/138-phase-hsai-admission-journal-materialization-boundary-spec.md](docs/138-phase-hsai-admission-journal-materialization-boundary-spec.md)
defines the docs-first boundary for a future local admission-journal output
bundle. It specifies declared `admission-journal/*` files, digest sidecars,
manifest fields, stale-tip and replay checks, rejected/quarantined audit
retention, source-digest disclosure, redaction requirements, and explicit
non-claims. It authorizes no Rust implementation, no generated output, no
accepted Evidence Ledger mutation, no official submission, no provider call,
no score-axis population, and no Level2+ evidence.
[docs/139-phase-pcsm-bounded-proof-handoff-intake-boundary-spec.md](docs/139-phase-pcsm-bounded-proof-handoff-intake-boundary-spec.md)
defines the docs-first boundary for future intake of a committed
recoverable-ghost-states PCSM CL12 bounded-proof handoff. It requires source
repo commit identity, source handoff path, SHA-256 digest binding, verifier
status fields, blocked-preflight and `threshold_admitted=false` preservation,
and explicit nonclaims before any typed local parser can exist. It imports no
PCSM code or artifacts, accepts no dirty or staged-only source snapshot, mutates
no accepted Evidence Ledger, performs no external replay or official
submission, and creates no proof, benchmark evidence, score axes, or Level2+
evidence.
[docs/140-phase-pcsm-bounded-proof-handoff-intake-metadata-notes.md](docs/140-phase-pcsm-bounded-proof-handoff-intake-metadata-notes.md)
implements the local structured metadata validator for that boundary inside
`hsai-agent-admission`. It validates clean committed source identity, bounded
proof fields, verifier statuses, blocked-preflight status,
`threshold_admitted=false`, digest-only source artifacts, and required
nonclaims before mapping to an `AdmissionSourceKind::PcsmBoundedProofHandoff`
candidate. It reads no recoverable-ghost files, imports no PCSM code or
artifacts, accepts no staged or dirty source snapshot, and exports no accepted
claim envelope by itself.
[docs/141-phase-hsai-admission-journal-materialization-implementation-notes.md](docs/141-phase-hsai-admission-journal-materialization-implementation-notes.md)
implements local admission-journal bundle materialization in
`hsai-agent-admission`. It writes only declared `admission-journal/*` files
with SHA-256 sidecars under a caller-selected output root, validates readback,
preserves accepted/rejected/quarantined decisions as local review metadata, and
rejects protected roots, stale tips, undeclared files, stale digests, missing
nonclaims, symlink roots, and invalid journals. It creates no committed bundle,
accepted Evidence Ledger mutation, proof, benchmark evidence, score axes, or
Level2+ evidence.
[docs/142-phase-hsai-admission-journal-semantic-readback-boundary-spec.md](docs/142-phase-hsai-admission-journal-semantic-readback-boundary-spec.md)
defines the next docs-first boundary for independently cross-validating every
Phase 141 bundle file during readback. It targets digest-consistent semantic
tampering across the journal, manifest, decisions, source digests, nonclaims,
redaction report, validation report, and sidecars. It authorizes no Rust
implementation, source-repo parsing or commands, PCSM import, generated bundle,
accepted Evidence Ledger mutation, benchmark evidence, score axes, or Level2+
evidence. Actual source intake remains blocked while the
recoverable-ghost-states handoff is staged in a dirty checkout.
[docs/143-phase-hsai-admission-journal-semantic-readback-implementation-notes.md](docs/143-phase-hsai-admission-journal-semantic-readback-implementation-notes.md)
implements that hardening in `hsai-agent-admission`. Readback now parses and
cross-validates every declared file, recomputes journal-derived views and
manifest metadata, rejects digest-consistent semantic drift, and rejects
sidecar symlinks. A hermetic PCSM bounded-proof metadata path now reaches
admission, journaling, materialization, and semantic readback without exporting
an accepted claim envelope or reading the recoverable-ghost-states checkout.
[docs/144-phase-hsai-admission-journal-adversarial-invariant-boundary-spec.md](docs/144-phase-hsai-admission-journal-adversarial-invariant-boundary-spec.md)
defines the next docs-first hardening boundary. It requires verdict-aware
envelope access, rejection of envelopes on rejected or quarantined decisions,
strict unknown-field rejection across serialized journal structures, and
readback rejection for symlink output roots and bundle directories. It
authorizes no Rust implementation, accepted evidence, PCSM source parsing, or
stronger claim.
[docs/145-phase-hsai-admission-journal-adversarial-invariant-implementation-notes.md](docs/145-phase-hsai-admission-journal-adversarial-invariant-implementation-notes.md)
implements the boundary. Rejected and quarantined decisions cannot expose or
validate retained envelopes, declared JSON rejects recursively unknown fields,
and readback rejects symlink roots and bundle directories. Focused fail-closed
coverage now exercises malformed, partial, substituted, drifted, and unsafe
bundle states without changing the claim boundary.
[docs/146-phase-hsai-admission-provenance-transaction-integrity-boundary-spec.md](docs/146-phase-hsai-admission-provenance-transaction-integrity-boundary-spec.md)
defines the next docs-first hardening boundary. It requires deterministic
decision recomputation from stored candidate and policy snapshots, mandatory
binding of the full PCSM intake digest, and symmetric protected-root overlap
rejection so overwrite cannot delete a protected descendant. It authorizes no
Rust implementation, source parsing, accepted evidence, or stronger claim.
[docs/147-phase-hsai-admission-provenance-transaction-integrity-implementation-notes.md](docs/147-phase-hsai-admission-provenance-transaction-integrity-implementation-notes.md)
implements the boundary. Journal entries now retain candidate and policy
snapshots and re-evaluate every decision, PCSM candidates bind the complete
validated intake digest under a reserved id, and protected-root overlap is
rejected in both directions before overwrite mutation.
[docs/148-phase-hsai-admission-input-semantic-integrity-boundary-spec.md](docs/148-phase-hsai-admission-input-semantic-integrity-boundary-spec.md)
defines the next docs-first hardening boundary. It requires exact source-kind
payload shapes, portable nonzero artifact digests with one digest per logical
id, checked PCSM count conservation, and an exact duplicate-free passing
verifier set. It authorizes no Rust implementation or stronger claim.
[docs/149-phase-hsai-admission-input-semantic-integrity-implementation-notes.md](docs/149-phase-hsai-admission-input-semantic-integrity-implementation-notes.md)
implements the boundary. Admission now rejects source-kind payload drift and
invalid artifact identities, while PCSM intake requires count conservation,
journal-count agreement, and an exact passing required verifier set.
[docs/150-phase-hsai-admission-candidate-semantic-closure-boundary-spec.md](docs/150-phase-hsai-admission-candidate-semantic-closure-boundary-spec.md)
defines the next docs-first hardening boundary. It requires unambiguous
candidate identity, exact source-kind claim boundaries, envelope export only
for accepted envelope proposals, and correct placement of the reserved PCSM
intake digest. It authorizes no Rust implementation or stronger claim.
[docs/151-phase-hsai-admission-candidate-semantic-closure-implementation-notes.md](docs/151-phase-hsai-admission-candidate-semantic-closure-implementation-notes.md)
implements the boundary. Candidate identities and exact source boundaries now
fail closed, reserved PCSM digest placement is enforced, and envelope export
requires exact candidate-policy decision recomputation.
[docs/152-phase-hsai-admission-journal-duplicate-json-boundary-spec.md](docs/152-phase-hsai-admission-journal-duplicate-json-boundary-spec.md)
defines the parser hardening boundary for recursive duplicate object-key
rejection before typed canonical JSON validation across every declared
admission-journal JSON document and decision JSONL row.
[docs/153-phase-hsai-admission-journal-duplicate-json-implementation-notes.md](docs/153-phase-hsai-admission-journal-duplicate-json-implementation-notes.md)
implements that boundary with a dependency-free duplicate-aware parser ahead of
the existing typed canonical round-trip.

For the managed-attestation track, the first real HSAI-owned Phala/dstack
artifact has been captured and accepted (2026-06-16) using the Phase 57
challenge packet tooling. The fixture
(`crates/hsai-attestation-phala/tests/fixtures/phala_hsai_owned_real_2026_06_16.json`)
and integration test
(`crates/hsai-attestation-phala/tests/phala_hsai_owned_real.rs`) are local
regression evidence only. Phase 4 `crates/hsai-agent-anchor-registry` is now
authorized and implemented under the Phase 4 Recheck Rule in
[docs/57-managed-attestation-real-artifact-promotion-spec.md](docs/57-managed-attestation-real-artifact-promotion-spec.md).
The managed-signature boundary:
[docs/66-managed-signature-verification-boundary-spec.md](docs/66-managed-signature-verification-boundary-spec.md)
defined the source-cited boundary for managed-service signature/JWKS/JWT or
quote-verification implementation. The first bounded code slice is now
implemented in
[docs/77-managed-jwt-signature-verification-notes.md](docs/77-managed-jwt-signature-verification-notes.md):
offline ES256 managed-JWT signature verification against caller-provided local
public keys. Future live-service token verification, DCAP, PCCS, TLS, or
transport-bound attestation work still requires a separate explicit phase.
The managed JWKS fetch artifact path is
[docs/109-managed-jwks-fetch-artifact-notes.md](docs/109-managed-jwks-fetch-artifact-notes.md):
operator-only live OpenID/JWKS fetching mapped to digest-only local metadata,
not token acceptance or managed-JWT signature verification.
The Phala local PCCS-compatible service artifact path is
[docs/110-phala-local-pccs-service-artifact-notes.md](docs/110-phala-local-pccs-service-artifact-notes.md):
operator-only localhost collateral replay consumed by `dcap-qvl`, not
production Intel PCS/PCCS operation or fresh collateral authority.
The Phala direct Intel PCS artifact path is
[docs/111-phala-intel-pcs-direct-artifact-notes.md](docs/111-phala-intel-pcs-direct-artifact-notes.md):
operator-only direct Intel PCS-backed `dcap-qvl` verification, not a repo-native
DCAP verifier or proof.
The next managed-attestation slice is a docs-first Phala/dstack live
managed-verifier boundary in
[docs/78-phala-live-managed-verifier-boundary-spec.md](docs/78-phala-live-managed-verifier-boundary-spec.md).
It names Phala/dstack live managed verification as the only future provider mode
under discussion, while continuing to forbid implementation and runtime effects.
The follow-on authorization spec is
[docs/79-phala-hermetic-live-verifier-implementation-spec.md](docs/79-phala-hermetic-live-verifier-implementation-spec.md).
It defines the smallest future hermetic code surface and keeps live Phala calls
operator-only and unauthorized for normal tests.
That hermetic surface is implemented in
[docs/80-phala-hermetic-live-verifier-implementation-notes.md](docs/80-phala-hermetic-live-verifier-implementation-notes.md)
using deterministic fake-client tests only.
The operator-live boundary is
[docs/81-phala-operator-live-path-boundary-spec.md](docs/81-phala-operator-live-path-boundary-spec.md).
It defines the future operator-only live path contract while still forbidding
Rust implementation, credentials, generated artifacts, and live Phala calls in
this slice.
The follow-on artifact-plumbing boundary is
[docs/82-phala-operator-live-artifact-plumbing-spec.md](docs/82-phala-operator-live-artifact-plumbing-spec.md).
It narrows the future local output-bundle contract and first code-phase touch
surface while still forbidding Rust implementation, examples, scripts,
credentials, generated artifacts, operator live tests, network access, and live
Phala calls in this slice.
That local artifact-plumbing surface is implemented in
[docs/83-phala-operator-live-artifact-plumbing-implementation-notes.md](docs/83-phala-operator-live-artifact-plumbing-implementation-notes.md)
using in-memory logical files and hermetic tests only. It still forbids
filesystem writes, examples, scripts, credentials, generated operator
artifacts, operator live tests, network access, and live Phala calls.
That local output-root plumbing surface is implemented in
[docs/85-phala-operator-live-artifact-output-plumbing-implementation-notes.md](docs/85-phala-operator-live-artifact-output-plumbing-implementation-notes.md)
using hermetic filesystem tests only. It still forbids examples, scripts,
credentials, generated operator artifacts, operator live tests, network access,
live Phala calls, local DCAP, managed-service signature verification, benchmark
evidence, and claims above `Attested`.
The follow-on docs-first boundary is
[docs/97-phala-operator-live-invocation-boundary-spec.md](docs/97-phala-operator-live-invocation-boundary-spec.md).
It defines the future operator-owned live invocation contract while still
forbidding Rust implementation, credentials, generated artifacts, operator live
tests, network access, live Phala calls, local DCAP, PCCS, JWKS fetching, TLS
channel binding, benchmark output, accepted Evidence Ledger mutation, and claims
above `Attested`.
The local invocation plumbing is implemented in
[docs/100-phala-operator-live-invocation-implementation-notes.md](docs/100-phala-operator-live-invocation-implementation-notes.md).
It exercises the operator acknowledgement, credential-provider boundary,
bounded retry, replay, response validation, redaction, and output-bundle flow
with hermetic tests only. A real operator-owned Phala run, real credential
source, network client, DCAP/PCCS/JWKS/TLS verification, benchmark output, and
accepted Evidence Ledger mutation remain separate future slices.
The next managed-attestation boundary is
[docs/101-phala-operator-live-provider-client-boundary-spec.md](docs/101-phala-operator-live-provider-client-boundary-spec.md).
It defines the future concrete provider-client contract behind the existing
injected-client seam while still forbidding implementation, network access,
live Phala calls, operator live tests, real credentials, generated artifacts,
DCAP/PCCS/JWKS/TLS work, benchmark output, accepted Evidence Ledger mutation,
and claims above `Attested`.
The opt-in provider-client implementation is recorded in
[docs/102-phala-operator-live-provider-client-implementation-notes.md](docs/102-phala-operator-live-provider-client-implementation-notes.md).
It adds a feature-gated concrete client, allowlisted environment credential
provider, and HTTP transport seam while preserving hermetic normal tests. It is
still not a live Phala run, local DCAP/PCCS/JWKS/TLS verification, benchmark
evidence, accepted Evidence Ledger mutation, or a claim above `Attested`.
The operator-only live runner is recorded in
[docs/105-phala-operator-live-runner-implementation-notes.md](docs/105-phala-operator-live-runner-implementation-notes.md)
and
[docs/106-phala-cloud-api-live-artifact-implementation-notes.md](docs/106-phala-cloud-api-live-artifact-implementation-notes.md).
The Phala DCAP/PCCS collateral materialization path is
[docs/107-phala-dcap-pccs-collateral-implementation-notes.md](docs/107-phala-dcap-pccs-collateral-implementation-notes.md).
The Phala local DCAP/QVL verification artifact path is
[docs/108-phala-local-dcap-qvl-verification-notes.md](docs/108-phala-local-dcap-qvl-verification-notes.md).
The managed JWKS fetch artifact path is
[docs/109-managed-jwks-fetch-artifact-notes.md](docs/109-managed-jwks-fetch-artifact-notes.md).
The Phala local PCCS-compatible service artifact path is
[docs/110-phala-local-pccs-service-artifact-notes.md](docs/110-phala-local-pccs-service-artifact-notes.md).
The Phala direct Intel PCS artifact path is
[docs/111-phala-intel-pcs-direct-artifact-notes.md](docs/111-phala-intel-pcs-direct-artifact-notes.md).
The next transport boundary is
[docs/112-phala-tls-channel-binding-artifact-boundary-spec.md](docs/112-phala-tls-channel-binding-artifact-boundary-spec.md).
It specifies a future operator-only TLS 1.3 `tls-exporter` artifact from the
same connection as a Phala verification response. This docs-first slice adds no
TLS code, network call, generated artifact, RA-TLS claim, official evidence, or
accepted Evidence Ledger mutation.
That operator-only path is now implemented and exercised in
[docs/113-phala-tls-channel-binding-artifact-implementation-notes.md](docs/113-phala-tls-channel-binding-artifact-implementation-notes.md).
It recorded one TLS 1.3 RFC 9266 exporter and accepted Phala verification
response from the same client connection as digest-only repo-external metadata.
It is client-local connection evidence, not RA-TLS, an attested server
certificate, proof, official benchmark evidence, or accepted evidence.
These provide operator-owned live artifact wiring, but this repository still
has no committed live artifact, no credential, and no normal test that calls a
live provider.

## Non-Goals

- No cloned external repos in this foundation.
- No fabricated benchmark numbers.
- No official benchmark claims.
- No formal-verification claims without scoped machine-checked evidence.
- No one-size-fits-all backend model.
- No dashboard before the evidence model works.
- No aggregate score that hides weak soundness evidence.

## Claim Boundary Warning

A benchmark pass is not a proof. A local replay is not official benchmark evidence. A formal proof about one layer is not a formal proof about the full system. A recursion proof is not semantic proof. A backend rejection is not automatically semantic correctness. A timeout is not automatically a soundness failure. A successful proof is not automatically evidence that the source spec was meaningful.

zk-Harness dry-run plans are not benchmark results. Manual handoff bundles are not benchmark results. External execution is disabled by default. Result import candidates are quarantined or pending review until validated.

Synthetic result candidates are not benchmark results. Evidence append proposals are not accepted evidence. Evidence-record candidates are not accepted evidence. Append previews are not accepted evidence and do not mutate the accepted Evidence Ledger. Level2 eligibility reports are not Level2 evidence. Proposal ledgers and review ledgers are review artifacts only.

Local soak telemetry is not official benchmark evidence. Internal timing telemetry is not ZK backend performance. Failure corpus entries are reproduction aids, not accepted evidence. Future agents must not use soak timing as prover/verifier timing.

Managed-attestation captured artifact validation is not proof, not benchmark
evidence, and not local DCAP quote verification. The first accepted
HSAI-owned real artifact authorizes only the bounded Phase 4 anchor-registry
crate.
Managed-attestation challenge packets and capture manifests are capture inputs
only, not attestation evidence or independent Phase 4 authorization.

## Validation Checklist

- Exact planned file tree exists.
- Rust workspace files are limited to the Level 1 foundation.
- No JavaScript package manager files are introduced.
- No external adapter runtime code is introduced.
- Every file is non-empty.
- This README links every created file.
- The repo integration map classifies every named source.
- The DSL schema includes required entities and examples.
- The Rust module layout documents the current crate surface.
- The scoring rubric prevents overclaiming.
- The semantic/oracle doc defines expected verdicts and claim boundary levels.
- No benchmark results are fabricated.
