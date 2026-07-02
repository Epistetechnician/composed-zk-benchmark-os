# Phase 265 HSAI Formal Verification Evidence Architecture Boundary

Status: complete for docs-first formal-verification evidence architecture
boundary.

## Purpose

Phase 265 defines the next HSAI research and implementation direction after the
gateway external-evidence acceptance boundary. It incorporates COBALT,
repository-scale Lean benchmarking, Rust-to-Lean extraction, federated
verification, certificate explanation, and formal-verification source indexes as
ranked external source candidates.

This phase does not implement any adapter or verifier. It exists to prevent a
research-stack discussion from turning into inflated claims, broad dependency
imports, or unbounded proof work.

The bounded target is:

```text
HSAI can grow from one reproducible, attestation-bound gateway admission path
into a scoped formal-verification evidence pipeline for selected gateway
admission invariants, with every future proof or solver result bound to a named
property, source digest, tool version, correspondence assumption, and claim
boundary.
```

This is not a claim that HSAI is SOTA, fully secure, production ready, or
semantically correct as a whole system.

## Research Stack To Incorporate

The future formal-verification track should combine these roles:

```text
gateway Rust surface
  -> extracted or hand-written formal obligation
  -> Lean / SMT / Coq / TLA+ / model-checking backend
  -> kernel-checked proof, solver certificate, or declared-only result
  -> optional certificate explanation
  -> adversarial/repository-scale benchmark replay
  -> local evidence packaging with explicit nonclaims
```

The architecture is useful only if the trusted boundary is strict:

- AI agents may search for proofs, propose formal statements, or explain
  failures.
- AI-generated proof text is never trusted by itself.
- Trust comes only from proof kernels, solver certificates, reproducible build
  gates, source-hash binding, and human-reviewed correspondence assumptions.
- A formal proof about one property is not a proof of the gateway, the model,
  the attestation provider, or HSAI as a whole.

## Ranked Source Candidates

### Tier 1 - Immediate Architecture Inputs

These sources should shape the next docs and future proof-lane design:

| Source | Role In HSAI | Claim Cap Before Implementation |
|---|---|---|
| COBALT, `https://arxiv.org/abs/2604.20496` | SMT/Z3 containment patterns for arithmetic and action-boundary invariants. | Source-cited design input only. |
| Aeneas, `https://github.com/AeneasVerif/aeneas` | Rust extraction path for small pure functions. | Future scoped proof only after local extraction and checker run. |
| Verified-zkEVM rust-lean, `https://github.com/Verified-zkEVM/rust-lean` | Reference workflow for Rust crypto/zkVM functions translated to Lean and verified. | Workflow reference only until reproduced locally. |
| VeriSoftBench, `https://arxiv.org/abs/2602.18307` | Repository-scale Lean benchmark model for measuring proof automation against cross-file dependencies. | Benchmark-design reference only. |
| Federated Formal Verification, `https://arxiv.org/abs/2606.02019` | Multi-backend citation, cross-axis convergence, and AI dispatch architecture. | Architecture reference only; correspondence certificates remain explicit assumptions. |

### Tier 2 - Later Audit And Debugging Inputs

These sources are valuable after a first scoped proof or solver certificate
exists:

| Source | Role In HSAI | Claim Cap Before Implementation |
|---|---|---|
| Cycle-consistent certificate explanation, `https://arxiv.org/abs/2606.24414` | Faithful explanations of proof, model-checking, SMT, or SAT certificates. | Explanation-layer reference only. |
| awesome-formal-verification, `https://github.com/ElNiak/awesome-formal-verification` | Ecosystem map for candidate tools and proof systems. | Discovery-only, never evidence. |
| EVMYulLean, `https://github.com/NethermindEth/EVMYulLean` | Ethereum/EVM semantics reference if HSAI later touches onchain execution semantics. | Out-of-core reference for current gateway work. |
| runtimeverification/evm-equivalence, `https://github.com/runtimeverification/evm-equivalence` | Cross-model EVM equivalence proof pattern. | Out-of-core reference unless HSAI opens an EVM semantics phase. |
| model-checking/rust-lean-models, `https://github.com/model-checking/rust-lean-models` | Lean models for Rust standard-library behavior. | Support-library candidate only. |
| Kha/electrolysis, `https://github.com/Kha/electrolysis` | Historical Rust-to-Lean extraction reference. | Historical reference only; not a first implementation target. |

## First Formal Targets

The first implementation target must be tiny. Acceptable candidates:

1. Gateway proposal digest binding is deterministic for one selected proposal
   shape.
2. Gateway attestation challenge binding changes when nonce, anchor id, public
   key, validity window, or proposal digest changes.
3. Accepted-evidence request validation rejects authority grants.
4. Accepted-evidence request validation rejects Level2+ or formal-evidence
   claims.
5. Accepted-evidence request validation rejects raw provider payload retention.

The first target must not be:

- full gateway correctness;
- all admission semantics;
- provider attestation correctness;
- model behavior correctness;
- production readiness;
- SOTA status;
- whole-system semantic correctness.

## Future Formal Evidence Shape

A future implementation phase may introduce a formal-evidence request that
records:

- property id;
- property statement;
- state slice;
- source file paths;
- source commit;
- source digest;
- extraction method;
- formal backend;
- backend version;
- proof or solver artifact digest;
- correspondence assumptions;
- trusted computing base;
- accepted nonclaims;
- maximum claim boundary.

The maximum claim boundary must follow the actual evidence:

| Evidence | Maximum Boundary |
|---|---|
| Design source reference only | `Level0DesignNote` |
| Declared formal property only | Level 4 formal statement, if the statement is explicit and scoped |
| Solver SAT witness | Scoped counterexample evidence for the encoded property only |
| Solver UNSAT result with reproducible certificate/checker | Scoped absence claim for the encoded domain only |
| Lean/Coq/kernel-checked theorem | Level 5 only for the named property |
| Independent reproduction of the same property and artifact | Level 6 only for the named property |

No formal evidence may upgrade the gateway bridge evidence class, accepted
Evidence Ledger state, score axes, production readiness, or public SOTA claim
without a separate reviewed phase.

## Required Future Verification Order

A future formal-evidence implementation must fail closed in this order:

1. Name the HSAI state slice.
2. Name the property.
3. Name the source files and source commit.
4. Compute source digests.
5. Declare extraction or hand-encoding method.
6. Declare correspondence assumptions.
7. Run or reference the formal backend in an explicit, reproducible way.
8. Record tool version and proof/certificate digest.
9. Reject unscoped proof claims.
10. Reject whole-system semantic-correctness claims.
11. Reject production-readiness claims.
12. Reject SOTA or breakthrough claims unless a separate benchmark comparison
    phase defines baselines and produces reproduced results.
13. Reject full-security claims.
14. Package the result as scoped local evidence or a declared-only design note.
15. Preserve explicit nonclaims with the result.

## Required Source Verification Rule

Before any implementation imports, clones, wraps, or executes one of the listed
sources, a future phase must verify:

1. current repository URL;
2. license;
3. maintained state;
4. required toolchain versions;
5. reproducible build command;
6. input and output artifact shape;
7. whether proof closure can be checked locally;
8. whether assumptions, axioms, or `sorry`-like placeholders are present;
9. whether source hashing and replay manifests are feasible;
10. maximum claim boundary.

## Explicit Nonclaims

Phase 265 does not claim:

- HSAI is SOTA;
- HSAI is fully secure;
- HSAI proves semantic correctness;
- HSAI is production ready;
- HSAI has formal evidence today beyond the existing declared-only formal lane;
- COBALT results are HSAI evidence;
- VeriSoftBench results are HSAI benchmark results;
- federated-verification claims reproduce inside this repo;
- certificate-explanation soundness is proof soundness;
- any external repository is current, safe, licensed for integration, or
  suitable without a future verification phase.

## Anti-Goals

This phase does not permit:

- Rust/source implementation changes;
- Cargo metadata changes;
- package runtime files;
- external repo clones;
- vendored source;
- proof assistant setup files;
- Lean, Coq, TLA+, SMT, Z3, CBMC, or model-checker execution;
- generated proof artifacts;
- accepted Evidence Ledger mutation;
- Level2+ evidence;
- score-axis population;
- benchmark evidence;
- official benchmark submission;
- live provider calls;
- credential handling;
- production-readiness claims;
- semantic-correctness claims;
- SOTA claims;
- breakthrough claims;
- full-security claims;
- global software-agent uniqueness claims.

## Follow-On Implementation Slice

Phase 266 implements the first local formal-evidence metadata adapter for this
tiny gateway property:

```text
Gateway attestation challenge binding is deterministic and input-sensitive for
one concrete gateway action proposal shape.
```

The next slice should stay docs-first unless explicitly authorized to run a real
formal backend. It should define the source-correspondence contract for mapping
that local metadata property into a future Lean, Rust-to-Lean, or SMT
obligation.
