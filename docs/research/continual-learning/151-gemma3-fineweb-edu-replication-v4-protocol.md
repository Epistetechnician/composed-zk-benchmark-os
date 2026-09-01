# Gemma3 FineWeb-Edu replication V4 protocol

State slice: `continual-learning-gemma3-fineweb-edu-replication-v4`

Status: proposed and sealed for a fresh independent implementation review.
V3 is an immutable rejected record. V4 does not edit, reclassify, or use V3
as an approved protocol or scientific result. No V4 source, corpus, model, or
result effect is authorized until a fresh independent `ACCEPT` receipt binds
this protocol and the complete implementation manifest.

Claim ceiling: `LocalDevelopmentGemma3FineWebEduReplicationV4`

## Frozen custody

All V4 roots are exact lexical paths. Every path component and every file below
an exact root must be free of symlinks; path resolution cannot substitute for
this check.

- Raw root: `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-raw-v1`
- Prior-pilot source root: `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-source-v1`
- V4 source root: `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v4-source`
- V4 corpus root: `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v4-corpus`
- V4 result root: `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v4-result`
- Model path: `/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16`

The dataset is `HuggingFaceFW/fineweb-edu`, revision
`87f09149ef4734204d70ed1d046ddc9ca3f2b8f9`, config
`fineweb-edu-crawl-shards`, split `train`. The only Parquet inputs are the
two already-cached pinned shards:

- `data/CC-MAIN-2013-20/train-00000-of-00014.parquet`, `2369456837` bytes,
  SHA-256 `fb989c566f6fba00ab61decc5f7aa1538a07d9b142e58a52ff790154528ffd03`
- `data/CC-MAIN-2024-10/000_00000.parquet`, `1911528585` bytes, SHA-256
  `89c802096c8adb54cdcfad567c13838814d83dbb4dbcda008a0f740e73f8a484`

V4 reads rows `[2048,18432)` from each shard. The prior pilot
is bound by manifest SHA-256
`9e6311b8a88b879c2b8d102cc1b1d4093312c796633571d00c928738327b33d3`; its
normalized files, declared digests, complete records, and first `[0,2048)`
raw rows are independently checked before V4 records are accepted.

The cached model stable-file manifest must equal SHA-256
`69f078b42d4521d3e53f0c388a20fa6cf32b4df7ea6535b0eb9da6ccef75c256`.
Symlinks anywhere in the model tree reject before tokenizer or model loading.
Loaded parameter tensors are hashed before and after inference and must be
byte-identical. The runtime is pinned to MLX `0.31.2`, MLX-LM `0.31.3`, and
PyArrow `24.0.0`.

## Review binding and native offline boundary

The independent review receipt is a canonical self-digested JSON file with
reviewer identity, canonical UTC timestamp, `effects_run:false`, the exact
protocol and packet hashes, the complete implementation-manifest hash, and
exactly seven required true findings. The runner snapshots the receipt bytes,
protocol bytes, packet bytes, and every implementation-file digest before any
tokenizer or model operation. It rechecks the same snapshot before staging,
before model effects, before validator execution, and before publication. The
validator rechecks the snapshot copy bound into the staged result.

On macOS, the entrypoint must prove that the current process is denied
`network-outbound` by the native `sandbox_check` API. If proof is absent, it
executes once through `sandbox-exec` with `(deny network*)`; if proof still is
absent, it fails closed. An environment variable is never accepted as proof.
Python socket, URL, and child-process network paths are additionally denied
inside the model/tokenizer block. The validator is invoked as a repository
module (`python -B -m ...`) so its import root is deterministic.

## Source and corpus

After review acceptance, the V4 packer writes the fresh source root once. It
re-derives every selected normalized record from the pinned Parquet row and
refuses overwrite. It writes exactly `16384` records per split. After review
acceptance, the stage step loads the exact tokenizer only after model-file
custody validation, selects the first `64` eligible windows per split, and
requires exactly `1024` tokenizer IDs plus decode/encode round-trip equality.
Paths are exactly
`{fit,assessment}/fineweb_edu/window-{ordinal:06d}.txt`; all paths, source IDs,
source rows, source text digests, window text digests, bytes, and token counts
are checked. Fit and assessment maps are split-specific; a document from one
split cannot satisfy the other split.

## Locked intervention and controls

The self-contained reviewed runner implements the Gemma3 text forward seam and
the residual operation directly. At destination layer `d`, it computes
`normalized_source = source * destination_l2 / max(source_l2,epsilon)` and
uses the explicit operation `beta * destination + alpha * normalized_source`.
The only candidates, in order, are `(7,2)`, `(9,3)`, `(11,4)`, `(12,5)` with
fit `alpha=0.10`, `beta=0.90`. Selection is the minimum fit mean NLL with
lexicographic `(mean_nll,source,destination)` tie-break. The selected pair is
locked before assessment at `alpha=0.15`, `beta=0.85`. The paper target
`(11,4)` is recorded as an expected replication target and is never forced.

The result retains and the independent validator recomputes from model
outputs: native baseline, zero-alpha parity for all 128 windows, all four fit
candidates, selected and locked equality, temperature `1.20` baseline and
intervention controls, deterministic repeat, nonzero candidate reach, exact
model-file and parameter custody, and all metric aggregates from retained
per-document rows. Each metric binds its temperature and intervention config.

## Exact uncertainty and decision

For every assessment document, define
`delta = selected_nll / target_count - baseline_nll / target_count`. Values are
strict finite numbers. The primary statistic is the arithmetic mean of these
paired deltas. Use exactly `10000` resamples and seed `20260829`. For resample
`r` and position `j`, index
`int.from_bytes(SHA256(UTF8(f"20260829:{r}:{j}"))[:8], "big") % n`.
Sort resample means. The 95% interval uses one-indexed nearest rank with
`ceil(q*10000)` clamped to one at `q=.025` and `.975`; no interpolation.
Nonfinite input or output rejects. A result is `ReplicationCandidate` only if
both mean delta and upper bound are strictly negative; otherwise it is
`NoCandidate`.

## Prohibitions and evidence ceiling

V4 forbids model or dataset downloads, network during model/tokenizer use,
training, adapter or weight updates, adaptive candidate/control/threshold
tuning, GiveMeANode/H100/provider calls, Astral or Evidence Ledger mutation,
benchmark or production claims, and introspection or causal-self-modeling
claims. It cannot promote Stage 0C or Stage 1. A valid result supports only
`LocalDevelopmentGemma3FineWebEduReplicationV4` for this exact model, cohort,
implementation, and protocol. Any review, custody, lock, validator, or native
offline failure stops the phase without retry or adaptive tuning.
