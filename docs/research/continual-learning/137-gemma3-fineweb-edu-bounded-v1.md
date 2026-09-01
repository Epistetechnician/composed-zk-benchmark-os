# Gemma3 FineWeb-Edu bounded recirculation protocol V1

State slice: `continual-learning-gemma3-fineweb-edu-bounded-v1`

Status: executed as a bounded local pilot. This protocol does not establish
exact C4 identity, full paper replication, general recirculation efficacy,
benchmark superiority, production readiness, or a change to the Evidence
Ledger.

## Purpose

Run the paper-shaped Gemma3 one-additional-iteration recirculation procedure
against a richer, smaller, independently citable web corpus while preserving
the existing custody and claim boundaries. The paper's reported Gemma3 1B PT
pair `(source=11, destination=4)` is an expected replication target, not a
forced selection.

## Corpus contract

- Dataset: Hugging Face FineWeb-Edu, bounded pilot only.
- Upstream revision: `87f09149ef4734204d70ed1d046ddc9ca3f2b8f9`.
- Fit shard: `data/CC-MAIN-2013-20/train-00000-of-00014.parquet`.
- Assessment shard: `data/CC-MAIN-2024-10/000_00000.parquet`.
- Fit and assessment are separated by crawl snapshot and document identity.
- Pinned LFS SHA256 values:
  - fit: `fb989c566f6fba00ab61decc5f7aa1538a07d9b142e58a52ff790154528ffd03`
  - assessment: `89c802096c8adb54cdcfad567c13838814d83dbb4dbcda008a0f740e73f8a484`
- Raw custody: `4,280,985,422` bytes across two shards and `1,407,665`
  source rows.
- Normalization retains text plus available FineWeb-Edu metadata and adds
  source crawl, source path, and source row index.
- The bounded normalized source contains 2,048 fit records and 2,048
  assessment records. It is not the full FineWeb-Edu release and is not
  relabeled as C4, WebText, or the paper's exact corpus.

External custody roots:

- Raw/source: `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-raw-v1` and
  `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-source-v1`
- Staged corpus: `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-corpus-v1`
- Results: `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-recirculation-v1`

## Locked execution

- Model: cached `mlx-community/gemma-3-1b-pt-bf16`, model bytes unchanged.
- Model execution is offline; no network, training, adapter update, or weight
  mutation is permitted.
- Every split contributes 16 full windows of exactly 1,024 tokens.
- Fit candidate pairs: `(7,2)`, `(9,3)`, `(11,4)`, `(12,5)`.
- Fit alpha: `0.10`.
- Locked assessment pair uses the fit-selected source/destination pair.
- Assessment alpha: `0.15`; baseline mixture coefficient beta: `0.85`.
- Source-to-destination activation norm adjustment is fixed.
- Native/MLX parity, zero-alpha identity, deterministic repeat, temperature,
  and looping controls are retained.
- The independent validator checks source pins, split disjointness, corpus
  shape, model custody, configuration/result/receipt digests, and the claim
  ceiling before a result is accepted.

## Claim ceiling

`LocalDevelopmentGemma3FineWebEduBoundedPilot`.

The ceiling permits reporting the bounded local outcome and its custody and
validation receipts. It does not permit extrapolation to the full paper,
other corpora, other model sizes, production systems, or a general claim that
recirculation has been proven.
