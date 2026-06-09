# Repo Integration Map

Every named source is classified as exactly one class: fork, wrap, ignore, reference, discovery-only, local-pattern-source, or pending-verification.

| Source | Classification | Role | Phase | Evidence Class | Adapter Needed? | Risk | Decision Rationale |
|---|---|---|---|---|---|---|---|
| zk-Harness | wrap | Primary benchmark runner substrate; Phase G dry-run adapter preparation only | Phase G dry-run now; future live wrapper later | Level0DesignNote for dry-run plans; Level1LocalReplay only for referenced local packs | Yes, dry-run contract now; live wrapper future | Backend-specific metrics can be mistaken for semantics | Wrap runner/config/results later; current code creates inert candidate mappings only. No live wrapper, no source clone, no external result import, no Level2+ evidence. |
| clean | wrap | Lean formal-circuit proof lane | Phase 2 | Future machine-checked proof for scoped property | Yes | Formal scope can be overstated | Use for small scoped semantics/proof obligations only. |
| zkLean | wrap | Lean ZK-statement semantics lane | Phase 2 | Future machine-checked proof for scoped property | Yes | Trusted conversion boundary | Use as independent formal lane, not runtime truth. |
| formal-land/garden | wrap | Rocq trace/property lane | Phase 3 | Future formal or machine-checked proof evidence | Yes | Proof engineering cost and WIP maturity | Start with one tiny trace property. |
| gnark std/recursion | wrap | Recursion-envelope/proof aggregation lane | Phase 4 | Future verifier-acceptance evidence | Yes | Recursion proof is not semantic proof | Use after local benchmark and formal semantics lanes exist. |
| zkonduit/zkml-framework-benchmarks | wrap | Narrow zkML workload metrics | Phase 5 | Future benchmark evidence for zkML workload class | Yes | Heavy dependencies and non-core scope | Wrap manifests and metrics only. |
| zkp-gravity/zkml-benchmark | reference | Legacy zkML baseline reference | Phase 5 | Design note or historical reference | No first pass | Old assumptions and narrow calibration | Use only to understand legacy zkML benchmark shape. |
| awesome-zk | discovery-only | Source discovery index | Ongoing | Design note only | No | List churn and no executable evidence | Use to find candidates, not as evidence. |
| awesome-zero-knowledge-proofs | discovery-only | Source discovery index | Ongoing | Design note only | No | List churn and no executable evidence | Use to find candidates, not as evidence. |
| ZAQOS | local-pattern-source | Semantic contracts, evidence ladder, scoring discipline | Phase 0 | Design note until adapter exists | Possible later | Active repo state and symbolic scope | Mine patterns and claim boundaries; do not copy wholesale. |
| ecdsafail frontier checkout | pending-verification | Benchmark harness wrapper target | Phase 1 | Future local replay or benchmark evidence | Yes after verification | Latest score and checkout cleanliness must be verified | Do not claim latest or official evidence without live verification. |
| Mesh | local-pattern-source | Orchestration, Merkle logs, bounded tool loops | Phase 0 | Design note | No first pass | SRE domain mismatch | Reuse run/evidence lifecycle patterns. |
| Orbital Mesh | local-pattern-source | Cleaner control-plane pattern source | Phase 0 | Design note | No first pass | SRE domain mismatch | Prefer for architecture ideas if cleaner than main Mesh. |
| Mesh Intelligence | local-pattern-source | Read-only investigation harness pattern | Phase 0 | Design note | No first pass | Tool registry is SRE-specific | Replace SRE tools with benchmark/proof tools in future design. |
| MeshQRC | local-pattern-source | Benchmark-pack and artifact discipline | Phase 0 | Design note | No first pass | QRC assumptions do not transfer to ZK | Reuse benchmark pack structure only. |
| Recoverable Ghost States | local-pattern-source | Evidence taxonomy and claim-boundary model | Phase 0 | Design note | No first pass | Domain mismatch and active evidence state | Reuse claim discipline, not implementation. |
