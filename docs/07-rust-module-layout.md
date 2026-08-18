# Rust Module Layout

This document defines the first implementation shape. The Level 1 local Rust foundation now implements this shape in `crates/zkbench-core`.

## Current Layout

```text
crates/zkbench-core/src/
  dsl/
  generator/
  mutation/
  scoring/
  evidence/
  external_runner/
  adapters/
  experiment.rs
  replay/
  pack/
  registry/
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

## Module Responsibilities

| Module | Responsibility |
|---|---|
| `dsl/` | Parse Surface DSL into Parsed AST and lower to Semantic IR. |
| `generator/` | Expand MachineSpec into Benchmark Family and Benchmark Instance values. |
| `mutation/` | Apply MutationPass values and attach Expected Verdicts. |
| `scoring/` | Convert Evidence Records into Score Reports. |
| `evidence/` | Define Evidence Record, Claim Boundary, Backend Outcome, provenance, review decisions, acceptance policies, candidates, append previews, eligibility reports, review ledgers, and local evidence ledgers. |
| `external_runner/` | Define Phase H/I/J disabled/manual-only external-runner policy, manual handoff bundle, artifact capture contract, provenance contract, result import schema, quarantine schema, proposal workflow, and review-layer aliases. |
| `adapters/` | Define BackendAdapter traits and capability declarations. |
| `experiment.rs` | Compose static task, model/runtime, mechanism-collector, and evaluator seams into one validated ExperimentBundle. |
| `replay/` | Define Replay Manifest and ReplayRunner behavior. |
| `pack/` | Define local benchmark pack manifests, readers, writers, and validation. |
| `registry/` | Provide source, adapter, benchmark family, and scoring registry metadata. |

## Implemented Types

Public v0 Rust names:

```rust
SurfaceSpec
ParsedAst
SemanticIr
MachineSpec
StateSpec
FieldSpec
TransitionSpec
GuardSpec
ActionSpec
LoopSpec
InvariantSpec
OracleSpec
TraceSpec
WitnessPolicy
PublicInputSpec
PrivateWitnessSpec
MutationSpec
MutationVariant
BenchmarkFamily
BenchmarkInstance
BackendTarget
AdapterCapabilitySet
ReplayManifest
EvidenceRecord
ClaimBoundary
ScoreReport
ExternalRunnerPolicy
ManualHandoffBundle
ArtifactCaptureContract
ProvenanceContract
ExternalResultImportSchema
QuarantineManifest
EvidenceReviewDecision
EvidenceAcceptancePolicy
EvidenceRecordCandidate
EvidenceAppendPreview
Level2EligibilityReport
EvidenceReviewLedger
```

## Trait Surface

```rust
SpecParser
SemanticLowering
FamilyGenerator
MutationPass
OracleEvaluator
BackendAdapter
ReplayRunner
EvidenceNormalizer
ScoreCalculator
RegistryProvider
ExperimentTask
ExperimentModel
MechanismCollector
Evaluator
ExperimentPlugin
```

## Interface Ownership

| Interface | Owner Module | Notes |
|---|---|---|
| `SurfaceSpec`, `ParsedAst`, `SemanticIr` | `dsl/` | Must be backend-independent. |
| `BenchmarkFamily`, `BenchmarkInstance` | `generator/` | Must preserve source seed and tunables. |
| `MutationSpec`, `MutationVariant` | `mutation/` | Must carry expected verdict and provenance. |
| `OracleSpec`, `TraceSpec`, `WitnessPolicy` | `dsl/` and `evidence/` | Semantic spine for expected outcomes. |
| `BackendTarget`, `AdapterCapabilitySet` | `adapters/` | Describes capabilities, not promises. |
| `ReplayManifest` | `replay/` | Reproducible command plus artifact hashes. |
| `EvidenceRecord`, `ClaimBoundary` | `evidence/` | Caps claims from adapter results. |
| `EvidenceReviewDecision`, `EvidenceAcceptancePolicy`, `EvidenceRecordCandidate`, `EvidenceAppendPreview`, `Level2EligibilityReport`, `EvidenceReviewLedger` | `evidence/` | Review and candidate metadata only; no accepted evidence append. |
| `ScoreReport` | `scoring/` | Multi-axis report; aggregate optional and warned. |
| `ExternalRunnerPolicy`, `ManualHandoffBundle` | `external_runner/` | Boundary and manual handoff artifacts only; no live execution. |

## Error Types

Planned errors:

- `DslParseError`
- `SemanticLoweringError`
- `OracleDefinitionError`
- `GenerationError`
- `MutationError`
- `CapabilityGapError`
- `ReplayManifestError`
- `BackendOutcomeError`
- `EvidenceNormalizationError`
- `ExternalRunnerBoundaryError`
- `ScoreCalculationError`
- `ClaimBoundaryError`

Errors must distinguish malformed spec, semantic invalidity, backend capability gap, replay failure, timeout, unsupported feature, and inconclusive result.

## Implementation Order

1. `dsl/`: implemented `SurfaceSpec`, `ParsedAst`, `SemanticIr`, schema validation, YAML parsing, lowering, and a v0 local oracle.
2. `evidence/`: implemented `ExpectedVerdict`, `BackendOutcome`, `ResultClassification`, `EvidenceRecord`, and `ClaimBoundary`.
3. `mutation/`: implemented `MutationSpec`, `MutationVariant`, and mutation taxonomy metadata.
4. `generator/`: implemented `BenchmarkFamily` and `BenchmarkInstance` primitives only.
5. `scoring/`: implemented Score Report axes and missing-evidence handling only.
6. `adapters/`: implemented trait and capability declarations only.
7. `replay/`: implemented Replay Manifest and Replay Result metadata only.
8. `registry/`: implemented static metadata primitive only.
9. `pack/`: implemented local benchmark pack manifests, readers, writers, and validation.
10. `external_runner/`: implemented Phase H policy, handoff, artifact capture, provenance, result import, quarantine, validation, and serialization primitives.
11. `external_runner/`: implemented Phase I synthetic import, normalization, evidence append proposals, and proposal ledger primitives.
12. `evidence/`: implemented Phase J review decisions, acceptance policy, claim-boundary escalation guard, evidence-record candidates, append previews, Level2 eligibility reports, and review ledger primitives.

## Implementation Guardrails

- No external backend adapter until DSL and oracle evaluation work.
- No dashboard until Score Report and Evidence Record are stable.
- No gnark recursion until mutation, replay, and evidence normalization exist.
- No zkML adapter until public/private boundary cases are supported.
- No live external execution from Phase H handoff bundles.
- Manual handoff bundles are not benchmark results.
- Evidence append proposals are not accepted evidence.
- Evidence-record candidates are not accepted evidence.
- Append previews do not mutate EvidenceLedger.
- Level2 eligibility reports are not Level2 evidence.
- A benchmark pass is not a proof.
- A recursion proof is not semantic proof.
- A local replay is not official benchmark evidence.
