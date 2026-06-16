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

This is now a Level 1 local Rust foundation plus the original Level 0 architecture scaffold. It defines the architecture, vocabulary, repo integration decisions, DSL schema, Rust core crate, deterministic generator, v0 mutation engine, local JSON replay adapter, evidence ledger, benchmark pack skeleton, reproduction metadata attachments, zk-Harness dry-run adapter preparation, external-runner boundary contracts, manual handoff bundle schema, synthetic result import prototype, evidence append proposal workflow, proposal ledger primitives, reviewed proposal acceptance policy, inert gnark recursion adapter preparation, inert narrow zkML adapter preparation, scoring primitives, validation gates, and adapter roadmap.

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
| [docs/20-phase-l-local-soak-notes.md](docs/20-phase-l-local-soak-notes.md) | Phase L long local soak execution and sampled report-bundle review notes. |
| [docs/21-phase-j-reviewed-proposal-acceptance-policy-notes.md](docs/21-phase-j-reviewed-proposal-acceptance-policy-notes.md) | Phase J reviewed proposal acceptance policy notes. |
| [docs/22-phase-k-gnark-recursion-adapter-notes.md](docs/22-phase-k-gnark-recursion-adapter-notes.md) | Phase K inert gnark recursion adapter preparation notes. |
| [docs/23-phase-l-narrow-zkml-adapter-notes.md](docs/23-phase-l-narrow-zkml-adapter-notes.md) | Phase L inert narrow zkML adapter preparation notes. |
| [docs/24-phase-m-reproducible-benchmark-pack-notes.md](docs/24-phase-m-reproducible-benchmark-pack-notes.md) | Phase M reproduction metadata and inert external replay plan notes. |
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
- Deterministic generation exists for BaselineFsm, BranchingFsm, and BoundedCounterLoop.
- Concrete generated Benchmark Instances carry config, provenance, Surface DSL, Semantic IR, traces, expected verdicts, and Level1LocalReplay claim boundaries.
- Mutation engine v0 exists for MissingConstraints, CorruptedGuards, and BadCounters.
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
- Proposal ledger persistence exists and is separate from the accepted `EvidenceLedger`.
- Long local soak execution exists for implemented generator families and explicit seeds.
- Sampled report-bundle review exists for soak-produced benchmark packs.
- Result classification exists.
- Evidence and scoring primitives exist.
- No external adapters exist.
- No live zk-Harness execution exists.
- No live external execution exists.
- No real external result import exists.
- No evidence append proposal is accepted evidence.
- No external adapter evidence exists.
- No official benchmark evidence exists.
- No formal evidence exists.

## Next Implementation Slice

Phase P dashboard/reporting remains last. True Level2 pack promotion waits on reviewed external result candidates, reproducible external artifact digests, and deterministic replay verification through the H–J gate.

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

Synthetic result candidates are not benchmark results. Evidence append proposals are not accepted evidence. Proposal ledgers are review ledgers only and do not mutate the accepted Evidence Ledger.

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
