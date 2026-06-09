# External ZK Source Index

This index records intended source use. It does not claim fresh facts. Future maintainers must verify current repo state, license, version, and capabilities before implementing adapters.

| Source | Category | Current Intended Use | Integration Class | Evidence Value | Verification Needed | Notes |
|---|---|---|---|---|---|---|
| zk-Harness | Benchmark runner | Primary benchmark substrate; Phase G dry-run adapter preparation only | wrap | Level0DesignNote for dry-run plans; future benchmark/replay evidence only after validation | Verify current runner structure, metrics, license, and backend support before live integration | Phase G does not clone or execute zk-Harness and does not import results. |
| clean | Lean formal DSL | Formal-circuit proof lane | wrap | Future scoped machine-checked proof | Verify current API and proof examples | Use for tiny property first. |
| zkLean | Lean ZK semantics DSL | Formal semantics lane | wrap | Future scoped proof/semantics evidence | Verify current import/export and examples | Treat lowering boundary as trusted until proved. |
| formal-land/garden | Rocq proof environment | Trace/property proof lane | wrap | Future formal proof evidence | Verify current supported circuit/proof workflow | Start with tiny trace property. |
| gnark std/recursion | Recursion/proof library | Recursion-envelope adapter | wrap | Future verifier-acceptance evidence | Verify current module version and security caveats | Later phase only. |
| zkonduit/zkml-framework-benchmarks | zkML benchmark repo | Narrow zkML workload metrics | wrap | Future workload benchmark evidence | Verify dependency requirements and metric outputs | Do not use as core semantic oracle. |
| zkp-gravity/zkml-benchmark | Legacy zkML benchmark repo | Historical reference | reference | Design note only | Verify age and assumptions before citing | No first-pass adapter. |
| awesome-zk | Curated source index | Discovery | discovery-only | No direct evidence | Verify candidate repos directly | Do not cite as implementation evidence. |
| awesome-zero-knowledge-proofs | Curated source index | Discovery | discovery-only | No direct evidence | Verify candidate repos directly | Do not cite as implementation evidence. |

## Source Verification Rule

Before adapter implementation:

1. Verify repo URL and license.
2. Verify current maintained state.
3. Verify expected input/output surfaces.
4. Verify whether negative tests are supported.
5. Verify artifact hashing and replay manifest feasibility.
6. Record capability flags.
7. Set maximum Claim Boundary.

## Phase G zk-Harness Note

Phase G keeps zk-Harness as an external source requiring verification. It creates an internal candidate mapping from local benchmark packs to zk-Harness dry-run plans. It does not clone zk-Harness, execute zk-Harness, import zk-Harness results, or claim official schema compatibility.
