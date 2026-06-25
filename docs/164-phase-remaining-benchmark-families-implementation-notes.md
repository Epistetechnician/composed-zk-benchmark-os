# Phase 164 Remaining Benchmark Families Implementation Notes

Status: complete.

## Shipped

Four deterministic local generators over the existing Surface DSL:

| Family | Generator helper | Stress focus |
|---|---|---|
| `RecursiveEnvelope` | `build_recursive_envelope` | recursion envelope digest + bounded unfold |
| `MemoryHeavyStateMachine` | `build_memory_heavy_state_machine` | multi-slot write/read ordering |
| `PublicPrivateBoundaryStress` | `build_public_private_boundary_stress` | witness-policy nonce binding |
| `ZkMlControlFlowMixed` | `build_zkml_control_flow_mixed` | confidence/threshold control flow |

Also updated: `FamilyKind::is_implemented`, template registry, `GeneratorConfig`
constructors, soak `generator_config_for_case`, zk-Harness candidate labels,
`full_pipeline_stress`, and tests in `phase_154_new_families.rs` /
`phase_164_remaining_families.rs`. The generator config validation also checks
derived resource use for the newly implemented families, including nested-loop
trace growth and memory-heavy field growth.

## Validation

- `cargo test -p zkbench-core --test phase_154_new_families` passes.
- `cargo test -p zkbench-core --test phase_164_remaining_families` passes.
- `cargo test -p zkbench-core --test generator_determinism` passes, including
  derived resource-limit rejection for the new family shapes.

## Claim boundary

All generated instances remain `ClaimBoundary::Level1LocalReplay`. No zkML
execution occurs.
