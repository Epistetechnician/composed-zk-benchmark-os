# Phase D/E Generator And Mutation Notes

## Implemented

Phase D/E adds deterministic local generation and the first mutation engine layer to `zkbench-core`.

Implemented generator primitives:

- `GeneratorConfig`
- `GeneratorSeed`
- `GeneratorProfile`
- `GeneratorTunables`
- `GeneratorLimits`
- `DeterministicGenerator`
- `GeneratedBenchmarkFamily`
- `GeneratedBenchmarkInstance`
- `InstanceParams`
- `GenerationProvenance`
- `FamilyTemplate`
- `FamilyKind`

Implemented mutation primitives:

- `MutationEngine`
- `MutationPass`
- `MutationPlan`
- `MutationApplication`
- `MutationProvenance`
- `MutationInput`
- `MutationOutput`
- `MutatedBenchmarkInstance`
- `MutationExpectedVerdict`
- `MutationSafetyClass`

## Generator Families Supported

Implemented locally:

- `BaselineFsm`
- `BranchingFsm`
- `BoundedCounterLoop`

Future placeholders remain unimplemented:

- `NestedLoop`
- `RecursiveEnvelope`
- `MemoryHeavyStateMachine`
- `GuardHeavyMachine`
- `PublicPrivateBoundaryStress`
- `ZkMlControlFlowMixed`

The generator creates Surface DSL, validates it, lowers through Parsed AST into Semantic IR, and attaches local traces and provenance. It does not bypass validation.

## Mutation Passes Supported

Implemented locally:

- `MissingConstraints`
- `CorruptedGuards`
- `BadCounters`

All other mutation classes remain future work. The v0 passes operate on generated local instances, mutate Surface DSL, revalidate, lower again, and carry provenance.

## Determinism Guarantees

Generation uses only `GeneratorSeed`, `GeneratorConfig`, `GeneratorTunables`, and `GeneratorLimits`. It does not use system randomness or wall-clock timestamps. Generated structures use a logical generator version marker: `phase-d-e-v0`.

Given the same config and seed, generated family and instance structures are identical. Different seeds or tunables change stable ids and, where applicable, selected branch behavior.

## Oracle Limitations

The local oracle remains a small v0 executable subset:

- `Int`, `Bool`, and `Text` values.
- equality, inequality, integer comparison, `and`, `or`, and `not` guards.
- `noop`, `assign`, `add_assign`, and `sub_assign` actions.
- invariant checks before execution and after each transition.

Raw-text guards/actions remain capability gaps. Witness aliasing, public/private boundary semantics, recursion metadata, formal semantics, zkML metrics, and backend artifacts are not executed.

## Claim Boundary Status

All generated families, generated instances, and mutation outputs remain Level1LocalReplay at most. A benchmark pass is not proof. A local replay is not official benchmark evidence. A recursion proof is not semantic proof.

An accepted mutated trace may be classified as an unsound acceptance candidate when paired with an expected rejection. That is not proof of exploit, not proof of backend unsoundness, and not formal evidence.

## Deliberately Unimplemented

Still not implemented:

- external adapters,
- zk-Harness integration,
- clean, zkLean, Garden, gnark, or zkML integration,
- backend artifact generation,
- benchmark result files,
- performance scoring,
- formal evidence,
- dashboards.

## Next Slice

Phase F has implemented:

- mock/local JSON adapter,
- replay manifest serialization,
- local evidence ledger persistence,
- benchmark pack skeleton.

The next slice should prepare a zk-Harness adapter contract in dry-run mode only. Do not integrate live zk-Harness execution until the dry-run adapter contract is reviewed and the local benchmark pack format is stable.
