# Phase 799 — Memory Architecture Sustainability and Serving Efficiency Boundary

Status: docs-first boundary complete. Authorization complete. No execution authorized.

Named state slice: `phase-799-memory-architecture-sustainability-serving-efficiency-boundary`.

Claim boundary: `Level0DesignNote`.

This boundary locks the repository's durable memory architecture stance and opens
an evaluation-only lane for future serving-efficiency improvements. It adds no
code, changes no deployment, acquires no model, runs no benchmark, and creates no
evidence. It exists so future agents and future phases cannot silently drift on
either layer.

## 1. Two Distinct Memory Problems

The repository touches two things that could both be called "memory". This phase
pins both and forbids conflating them.

1. **Durable system memory** — evidence, admission, journals, traces, campaign
   state. This is log-structured by design: append-only ledgers and journals
   chained by SHA-256 digests, bounded typed records, repository-external raw
   payloads. Its design goal is integrity, replayability, and auditability — not
   inference efficiency.
2. **Model inference memory** — the context a served model retains. Classic
   per-token KV cache grows linearly with sequence length and concurrency and is
   the dominant memory wall for long-context, agentic, high-concurrency serving.
   Fixed-size recurrent-state architectures (Kimi KDA-class, Gated DeltaNet-
   class) and KV-centric storage/routing systems (Mooncake-class) are the public
   answers to that problem.

The durable layer must never be traded away to optimize the inference layer, and
inference-layer state must never be treated as durable memory. A KV cache is
transient process state; it is never a source of truth in this repository.

## 2. Recorded Baseline (repository-sourced facts)

Durable layer:

- `zkbench-core` evidence ledgers, proposal ledgers, review ledgers, append
  previews, soak checkpoints, failure corpora, and trace/cost structures are
  append-only and digest-chained.
- `hsai-agent-admission` admission journals and gateway/admission metadata are
  append-only and digest-chained.
- Raw payloads remain repository-external; repository records carry bounded
  digests and typed metadata.

Serving reference baseline:

- The Phase 57+ Phala CVM attestation fixture
  (`crates/hsai-attestation-phala/tests/fixtures/phala_trust_center_app_2026_06_16.json`)
  embeds the fidaro dev-CVM manifest serving
  `Qwen/Qwen3-Next-80B-A3B-Thinking-FP8` through vLLM with fp8 weights,
  `--kv-cache-dtype auto`, `--max-model-len 131072`, `--max-num-seqs 256`,
  `--enable-prefix-caching`, and MTP speculative decoding, single instance.
- The served model's public architecture is hybrid attention: a majority of
  Gated DeltaNet linear-attention layers with periodic full attention. That is
  the same fixed-size-state memory class as KDA-class designs. This
  architectural fact comes from the model's public documentation and is not
  verified by this repository.
- Deployment configuration is owned by the product repository. This repository's
  authority is the evidence and boundary layer only.

## 3. Standing Policy (what this phase authorizes)

1. **Durable memory lock-in.** Log-structured append-only digest-chained memory
   is and remains the repository's only durable memory architecture. Cache-based,
   KV-based, or mutable state is never a source of truth for evidence, admission,
   journal, trace, or campaign state.
2. **Bounded records, external payloads.** Durable repository records remain
   bounded typed metadata and digests. Raw payloads, transcripts, model weights,
   and bulk artifacts remain repository-external with digest references.
3. **Fixed-size-state serving preference.** Future model and serving choices
   blessed by this repository (reference manifests, attestation fixtures,
   meta-harness model lanes) prefer fixed-size-state hybrid-attention
   architectures for long-context and high-concurrency lanes unless a future
   reviewed phase records measured evidence for a different choice.
4. **Evidence before adoption.** Future serving-efficiency candidates must be
   justified by measured full economic cost per verified utility, pass-all-k
   reliability, p95 latency, and concurrency ceilings under the prospective
   Recursive Meta-Harness evaluation regimes (`docs/research/recursive-meta-harness-p0-roadmap.md`,
   uncommitted at authoring time). Vendor claims, social posts, and architecture
   resemblance are not adoption evidence.
5. **Separated cost lines.** Cached and uncached input tokens remain separate
   cost lines with versioned price tables. Missing telemetry fails closed and is
   never silently zero.

## 4. Future Candidate Classes (evaluation-only, no adoption)

| Class | Examples | Disposition |
|---|---|---|
| C1 KDA-class hybrid-attention model lanes | Kimi Linear/K3-class, Gated DeltaNet-class | REFERENCE-ONLY |
| C2 Serving-side KV management | vLLM KV offload, KV-cache quantization, prefix-cache policy, multi-tier HBM/DRAM/SSD caching | REFERENCE-ONLY |
| C3 Disaggregated serving and KV-centric routing | Mooncake-class disaggregated prefill/decode and cluster-wide KV storage | REFERENCE-ONLY |
| C4 Agent context/memory policy modes | full-transcript versus retrieval versus episodic/procedural/summary memory under a future memory plane | REFERENCE-ONLY |

No candidate is claimed better for our workloads. Resemblance to an efficient
architecture is not measured efficiency.

## 5. Adoption Preconditions For Any Future Phase

A future phase may adopt a candidate only with:

- an explicitly named state slice, exact candidate version, and source identity;
- license and supply-chain review for any new model weights (weights are supply
  chain);
- attestation-compatibility review for any Phala CVM lane change;
- measured evaluation under a normalized causal regime, separately labeled from
  any native-best deployment regime and never pooled with it; and
- no claim above the measured evidence ceiling.

## 6. Long-Term Sustainability Note For The Durable Layer

Append-only logs grow without bound. Future compaction, archival, or snapshot
policy is permissible only if it preserves append-only lineage, digest chaining,
and replayability, and never destructively rewrites accepted history. That work
is future and not authorized here.

## 7. Prohibitions In This Slice

This phase does not permit Rust or Python changes, Cargo changes, CVM manifest
changes, deployment changes, model download or acquisition, provider spend,
benchmark execution, accepted Evidence Ledger mutation, accepted evidence,
Level2+ evidence, benchmark evidence, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims,
independent-audit claims, full-security claims, global-uniqueness claims, or
action authority.

## 8. Nonclaims

- This boundary does not claim Kimi KDA, Mooncake, or any named candidate is
  better for our workloads.
- It does not claim the repository has verified the served model's architecture.
- It changes no deployment.
- It does not claim the durable layer is cost-free: log growth is unbounded
  until a reviewed compaction/archival phase exists.

## 9. Next Slice (not authorized here)

A possible inert-metadata phase: serving-efficiency lane descriptors, candidate
class enums, and evaluation request/report contracts bound to the baseline
fixture digest.
