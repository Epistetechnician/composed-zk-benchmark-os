# Gemma3 FineWeb-Edu replication V2 protocol

State slice: `continual-learning-gemma3-fineweb-edu-replication-v2`

Status: proposed and sealed for independent review. Execution is closed until
an independent `ACCEPT` receipt binds this exact file and the V2 implementation.

Claim ceiling: `LocalDevelopmentGemma3FineWebEduReplicationV2`

## Boundary

This is a new replication-specific revision. The rejected V1 protocol and its
review receipt remain immutable records. V2 does not modify V1 and does not
reuse V1 as an approved protocol. V2 may inspect the prior bounded pilot only
to prove row/document disjointness and to bind the untouched cached model
manifest.

This phase is offline after the existing FineWeb-Edu raw files are present. It
does not download data or a model, train, update weights or adapters, call
GiveMeANode or H100 infrastructure, mutate the Evidence Ledger, make a
benchmark or production claim, or establish Astral introspection or causal
self-modeling. A failed gate or negative replication is `NoCandidate`; there
is no adaptive retry or tuning around assessment results.

## Frozen custody

The already-cached raw source is the only admissible upstream input:

- Dataset: `HuggingFaceFW/fineweb-edu`
- Revision: `87f09149ef4734204d70ed1d046ddc9ca3f2b8f9`
- Source: <https://huggingface.co/datasets/HuggingFaceFW/fineweb-edu>
- Config: `fineweb-edu-crawl-shards`
- Split: `train`
- Raw root: `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-raw-v1`
- Fit shard: `data/CC-MAIN-2013-20/train-00000-of-00014.parquet`, byte length `2369456837`, SHA-256 `fb989c566f6fba00ab61decc5f7aa1538a07d9b142e58a52ff790154528ffd03`
- Assessment shard: `data/CC-MAIN-2024-10/000_00000.parquet`, byte length `1911528585`, SHA-256 `89c802096c8adb54cdcfad567c13838814d83dbb4dbcda008a0f740e73f8a484`
- Total pinned raw bytes: `4280985422`

The prior bounded pilot source is bound by path and manifest digest:

- Root: `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-source-v1`
- Manifest SHA-256: `9e6311b8a88b879c2b8d102cc1b1d4093312c796633571d00c928738327b33d3`
- Prior row ranges: `[0, 2048)` on each pinned shard

V2 selects rows `[2048, 18432)` on each shard, in source order. Each V2
normalized record is lineage-checked against the exact Parquet row, including
document ID, text, crawl, path, and row index. The V2 fit and assessment
cohorts are distinct from each other and from the prior pilot.

The model must be the already-cached `google/gemma-3-1b-pt` BF16 MLX
conversion at:

`/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16`

The execution binds its stable-file model manifest to the prior pilot's
manifest SHA-256
`69f078b42d4521d3e53f0c388a20fa6cf32b4df7ea6535b0eb9da6ccef75c256` and
requires the actual pre/post manifests to be identical.

## Corpus construction

The V2 packer is offline-only and writes an immutable external source root. It
refuses an existing output root, symlinked files, missing pinned raw files,
wrong raw hashes, missing prior-pilot binding, row overlap, and any network
fallback. It emits exactly `16384` normalized records for each split under:

- `fit/fineweb_edu.jsonl`
- `assessment/fineweb_edu.jsonl`

The corpus stage is also external and immutable. It tokenizes records with the
frozen cached Gemma3 tokenizer, takes the first `1024` tokens from each source
record, round-trips the selected tokens through decode/encode, and keeps the
first `64` eligible records per split. It emits exactly `64` fit and `64`
assessment windows, each with exactly `1024` tokens. The corpus manifest binds
the V2 source manifest and every window's source record and text digest.

No prior-pilot source, corpus, activation, result, or review artifact is an
input to V2. Only the prior manifest and its row/document identities are used
for the explicit disjointness audit.

## Frozen intervention and controls

The model is evaluated teacher-forced on each fixed 1024-token window. The
intervention reads a source residual at layer `s`, L2-normalizes it to the
destination residual norm, and replaces the destination residual with:

`(1 - alpha) * destination + alpha * normalized_source`

The candidate pair set is exactly:

`(7, 2), (9, 3), (11, 4), (12, 5)`

where each pair is `(source_layer, destination_layer)`. Fit uses `alpha=0.10`
and selects the lowest aggregate fit mean NLL, with lexicographic
`(mean_nll, source_layer, destination_layer)` tie-breaking. The selected pair
is locked before assessment and evaluated with `alpha=0.15` and `beta=0.85`
recorded as the fixed recurrence coefficient. The paper's Gemma3 1B PT target
`(source=11, destination=4)` is an expected replication target, never a
forced selection.

Required controls are fixed before assessment:

1. native baseline;
2. zero-alpha identity/parity;
3. selected intervention at `alpha=0.15`;
4. temperature-only baseline and intervention at temperature `1.20`;
5. deterministic repeat of the locked intervention;
6. frozen model-file manifest before and after execution.

Qualification must pass native/zero-alpha parity, deterministic repeat,
nonzero intervention reach, 26-layer Gemma3 text-model shape, and cached model
manifest custody before assessment metrics are accepted.

## Exact bootstrap and decision rule

The primary assessment statistic is the paired per-document NLL difference
`selected_minus_baseline`, where each document NLL is divided by its own
teacher-forced target count. Nonfinite NLLs, target counts, deltas, or
bootstrap values invalidate the run.

The confidence interval is frozen as follows:

- Resamples: `10000`
- Seed: integer `20260829`
- Confidence level: `0.95`
- PRNG: `sha256-counter-v1`
- Counter input: UTF-8 bytes of `f\"{seed}:{resample}:{position}\"`
- Index: unsigned big-endian first eight digest bytes modulo `n`
- Resample statistic: arithmetic mean of the selected paired deltas
- Percentile: one-indexed nearest rank, `ceil(q * 10000)`, clamped to at least 1
- Lower/upper quantiles: `q=0.025` and `q=0.975`
- Nonfinite policy: reject

The implementation must use this algorithm byte-for-byte, independent of
Python's `random` implementation. A `ReplicationCandidate` is permitted only
when the selected pair is evaluated on the untouched, disjoint assessment
cohort, the mean paired delta is strictly negative, and the bootstrap upper
bound is strictly negative. Otherwise the result is `NoCandidate`.

## Review and execution gates

Before any model loading, tokenization for the assessment panel, forward pass,
or result interpretation, an independent reviewer must inspect the protocol,
packer, runner, validator, tests, and implementation digests. The review must
return a canonical receipt with `review_status: ACCEPT` and true findings for:

- custody and exact pinned data identity;
- fit/assessment and prior-pilot disjointness;
- locked configuration and paper target treatment;
- controls and no-training/frozen-weight behavior;
- exact bootstrap algorithm and uncertainty decision rule;
- aggregate/per-document retention and validator behavior;
- prohibition of V1 approval-by-reuse, network fallback, Ledger mutation, and
  claims above the V2 ceiling.

The runner refuses to stage or execute without that receipt, the exact
protocol SHA-256, and matching implementation digests. The independent V2
validator must pass source, corpus, review, configuration, result, and receipt
checks before the external output root is published.

## Evidence ceiling

Even a fully valid positive result supports only
`LocalDevelopmentGemma3FineWebEduReplicationV2`: a local, bounded,
implementation- and corpus-specific replication result. It does not support a
paper replication claim, general continual-learning claim, model capability
claim, benchmark claim, production readiness, provider/H100 claim, or Astral
claim.
