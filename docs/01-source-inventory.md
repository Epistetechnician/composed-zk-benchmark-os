# Source Inventory

This inventory lists sources to wrap, reference, or mine for patterns. It does not claim current benchmark results or formal evidence.

| Source | Type | Expected Role | Evidence Value | Integration Risk | Why Not Copied | First Useful Artifact | Future Adapter Possibility |
|---|---|---|---|---|---|---|---|
| zk-Harness | External benchmark repo | Primary benchmark runner pattern | Replay and metric normalization model | Framework-specific assumptions | Existing runner is a substrate, not the semantic core | `docs/integrations/zk_harness_adapter.md` | Yes |
| clean | External Lean DSL | Formal-circuit proof lane | Scoped machine-checked property evidence in future | Backend maturity and proof scope | Formal lane only; not runtime oracle | `docs/integrations/formal_semantics_lanes.md` | Yes |
| zkLean | External Lean DSL | ZK-statement semantics lane | Scoped proof and constraint semantics in future | Trusted conversion boundary | Independent evidence lane only | `docs/integrations/formal_semantics_lanes.md` | Yes |
| formal-land/garden | External Rocq environment | Trace/property proof lane | Scoped trace correctness evidence in future | WIP and proof engineering cost | Use as evidence lane, not project base | `docs/integrations/formal_semantics_lanes.md` | Yes |
| gnark std/recursion | External Go library | Recursion-envelope and proof aggregation lane | Verifier-acceptance evidence in future | Recursion is not semantic proof | Keep out of Rust core initially | `docs/integrations/gnark_recursion_adapter.md` | Yes, later |
| zkonduit/zkml-framework-benchmarks | External zkML benchmark repo | Narrow zkML workload metric reference | zkML metric and manifest shape | Heavy dependencies and non-semantic focus | zkML is workload class, not center | `docs/integrations/zkml_benchmark_manifest.md` | Yes, narrow |
| zkp-gravity/zkml-benchmark | External legacy zkML repo | Legacy reference | Historical accuracy/proof-time patterns | Old assumptions and narrow coverage | Reference only | `docs/integrations/zkml_benchmark_manifest.md` | No first-pass adapter |
| awesome-zk | External index | Discovery source | Source discovery only | List churn | No executable behavior | `docs/research/zk_external_source_index.md` | No |
| awesome-zero-knowledge-proofs | External index | Discovery source | Source discovery only | List churn | No executable behavior | `docs/research/zk_external_source_index.md` | No |
| ZAQOS | Local repo | Semantic contract, evidence ladder, reward/scoring discipline | Claim-boundary and verifier discipline | Active evidence state may drift | Reuse concepts, not codebase wholesale | Repo integration map entry | Possible local evidence adapter |
| ecdsafail frontier checkout | Local benchmark checkout | Benchmark harness wrapper target after live verification | Executable harness evidence in future | Latest score and cleanliness must be verified | Harness target only | Repo integration map entry | Yes, after verification |
| Mesh | Local/project family | Orchestration and Merkle log patterns | Run/evidence lifecycle patterns | Domain mismatch | Pattern source only | Architecture references | No first-pass adapter |
| Orbital Mesh | Local/project family | Cleaner orchestration pattern source | Bounded run lifecycle pattern | Domain mismatch | Pattern source only | Architecture references | No first-pass adapter |
| Mesh Intelligence | Local/project family | Read-only tool loop and run API patterns | Investigation harness pattern | SRE-specific tool registry | Pattern source only | Architecture references | No first-pass adapter |
| MeshQRC | Local repo | Benchmark-pack and artifact discipline | Benchmark contract structure | QRC domain mismatch | Use discipline, not QRC assumptions | Benchmark taxonomy references | No first-pass adapter |
| Recoverable Ghost States | Local repo | Evidence taxonomy and claim-boundary model | Publication/evidence discipline | Domain mismatch | Pattern source only | Claim-boundary doc references | No first-pass adapter |

