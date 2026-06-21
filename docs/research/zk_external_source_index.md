# External ZK Source Index

This index records intended source use. It does not claim fresh facts. Future maintainers must verify current repo state, license, version, and capabilities before implementing adapters.

| Source | URL | Category | Current Intended Use | Integration Class | Evidence Value | Verification Needed | Notes |
|---|---|---|---|---|---|---|---|
| zk-Harness | https://github.com/zkCollective/zk-Harness | Benchmark runner | Primary benchmark substrate; Phase G dry-run adapter preparation only | wrap | Level0DesignNote for dry-run plans; future benchmark/replay evidence only after validation | Verify current runner structure, metrics, license, and backend support before live integration | Phase G does not clone or execute zk-Harness and does not import results. |
| clean | https://github.com/Verified-zkEVM/clean | Lean formal DSL | Formal-circuit proof lane | wrap | Future scoped machine-checked proof | Verify current API and proof examples | Use for tiny property first. |
| zkLean | https://github.com/GaloisInc/zk-lean | Lean ZK semantics DSL | Formal semantics lane | wrap | Future scoped proof/semantics evidence | Verify current import/export and examples | Treat lowering boundary as trusted until proved. |
| formal-land/garden | https://github.com/formal-land/garden | Rocq proof environment | Trace/property proof lane | wrap | Future formal proof evidence | Verify current supported circuit/proof workflow | Start with tiny trace property. |
| gnark std/recursion | https://github.com/Consensys/gnark and https://pkg.go.dev/github.com/consensys/gnark/std/recursion | Recursion/proof library | Recursion-envelope adapter | wrap | Future verifier-acceptance evidence | Verify current module version and security caveats | Later phase only. |
| zkonduit/zkml-framework-benchmarks | https://github.com/zkonduit/zkml-framework-benchmarks | zkML benchmark repo | Narrow zkML workload metrics | wrap | Future workload benchmark evidence | Verify dependency requirements and metric outputs | Do not use as core semantic oracle. |
| zkp-gravity/zkml-benchmark | https://github.com/zkp-gravity/zkml-benchmark | Legacy zkML benchmark repo | Historical reference | reference | Design note only | Verify age and assumptions before citing | No first-pass adapter. |
| Dstack-TEE/dstack | https://github.com/Dstack-TEE/dstack | Confidential-computing attestation framework | Managed-attestation provider reference | reference | Design/source reference only until a future verifier phase | Verify quote/report format, license, current API, and trust roots | Do not clone or vendor in current phase. |
| Phala-Network/dstack-cloud | https://github.com/Phala-Network/dstack-cloud | Confidential container deployment | Phala/dstack deployment and attestation context | reference | Design/source reference only | Verify current deployment and attestation APIs before integration | Current fixture validation remains local regression evidence only. |
| Phala-Network/trust-center | https://github.com/Phala-Network/trust-center | Managed TEE verification platform | Captured-artifact and managed-verifier reference | reference | Managed-verifier reference only | Verify schema, license, trust roots, and API behavior before use | Trust Center evidence is not local DCAP verification. |
| Phala Cloud verify application | https://docs.phala.com/phala-cloud/attestation/verify-your-application | Phala managed-verifier documentation | Future Phala live managed-verifier boundary | reference | Provider documentation only until a future live-verifier implementation phase | Recheck response schema, endpoint behavior, trust roots, rate limits, and fixture license before implementation | No live Phala calls are authorized by Phase 78 docs. |
| Phala Cloud attestation overview | https://docs.phala.com/phala-cloud/attestation/overview | Phala attestation documentation | Provider-level attestation context for Phala live managed-verifier planning | reference | Provider documentation only | Verify current trust model and API claims before implementation | Does not create local DCAP evidence. |
| dstack overview | https://docs.phala.com/dstack/overview | dstack runtime documentation | dstack runtime and remote-attestation context | reference | Provider documentation only | Verify current runtime report fields and security assumptions before implementation | Does not authorize dstack deployment orchestration. |
| Phala get attestation | https://docs.phala.com/phala-cloud/attestation/get-attestation | Phala quote documentation | Quote/report-data capture-shape reference | reference | Provider documentation only | Verify current request/response format and report-data binding before implementation | No quote generation is authorized by Phase 78 docs. |
| Phala attestation fields reference | https://docs.phala.com/phala-cloud/attestation/attestation-fields | Phala quote-field documentation | TDX quote fields, RTMRs, and report-data reference | reference | Provider documentation only | Verify current field names, lengths, and measurement semantics before implementation | No local DCAP implementation is authorized by Phase 78 docs. |
| Phala end-to-end attestation verification | https://docs.phala.com/phala-cloud/attestation/verification-guide | Phala verification-flow documentation | Future verification flow boundary reference | reference | Provider documentation only | Verify which steps are local, managed, hybrid, or operator-supplied before implementation | No live verifier implementation is authorized by Phase 78 docs. |
| Microsoft Azure Attestation | https://learn.microsoft.com/en-us/azure/attestation/basic-concepts | Managed JWT attestation provider | Future managed-JWT verifier backend | reference | Provider documentation only until fixture-backed implementation | Verify OpenID metadata, JWKS, claims, issuer, algorithms, and TEE mode | No Azure integration in current phase. |
| Intel Trust Authority | https://docs.trustauthority.intel.com/main/articles/articles/ita/concept-attestation-tokens.html | Managed JWT attestation provider | Future managed-JWT verifier backend | reference | Provider documentation only until fixture-backed implementation | Verify token claims, JWKS/cert retrieval, PS384/RS256 policy, issuer, and TDX/EAT mapping | No Intel integration in current phase. |
| Intel Trust Authority EAT profile | https://portal.trustauthority.intel.com/eat_profile.html | Managed JWT claim profile | Future claim mapping reference | reference | Provider documentation only | Verify exact claim names and lengths for target TEE | No implementation in current phase. |
| flashbots/attested-tls | https://github.com/flashbots/attested-tls | Transport-bound attestation reference | Future channel-binding reference | reference | Design/source reference only | Verify crate split, license, DCAP/PCCS behavior, and TLS trust boundaries | No TLS, PCCS, DCAP, or transport implementation in current phase. |
| awesome-zk | https://github.com/ventali/awesome-zk | Curated source index | Discovery | discovery-only | No direct evidence | Verify candidate repos directly | Do not cite as implementation evidence. |
| awesome-zero-knowledge-proofs | https://github.com/matter-labs/awesome-zero-knowledge-proofs | Curated source index | Discovery | discovery-only | No direct evidence | Verify candidate repos directly | Do not cite as implementation evidence. |

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
