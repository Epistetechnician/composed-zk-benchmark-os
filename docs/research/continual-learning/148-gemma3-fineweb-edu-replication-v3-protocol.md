# Gemma3 FineWeb-Edu replication V3 protocol

State slice: `continual-learning-gemma3-fineweb-edu-replication-v3`

Status: proposed and sealed for independent review. No source, corpus, model,
or result effect is authorized until a fresh independent `ACCEPT` receipt
binds this file and the V3 implementation.

Claim ceiling: `LocalDevelopmentGemma3FineWebEduReplicationV3`

## Separation from rejected revisions

V1 and V2 are immutable rejected records. V3 does not edit them, does not
reclassify them, and does not use them as approved protocols or scientific
results. V3 uses only the pinned raw FineWeb-Edu files and the prior pilot's
manifest/document identities for an explicit disjointness audit. The V3
source, corpus, review, and result roots have new schemas and names.

## Frozen custody and fresh cohort

The only data input is the already-present raw root
`/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-raw-v1`:

- Dataset: `HuggingFaceFW/fineweb-edu`
- Revision: `87f09149ef4734204d70ed1d046ddc9ca3f2b8f9`
- Config: `fineweb-edu-crawl-shards`; split: `train`
- Fit shard: `data/CC-MAIN-2013-20/train-00000-of-00014.parquet`, bytes `2369456837`, SHA-256 `fb989c566f6fba00ab61decc5f7aa1538a07d9b142e58a52ff790154528ffd03`
- Assessment shard: `data/CC-MAIN-2024-10/000_00000.parquet`, bytes `1911528585`, SHA-256 `89c802096c8adb54cdcfad567c13838814d83dbb4dbcda008a0f740e73f8a484`

V3 selects source rows `[2048,18432)` from each shard in source order. The
prior bounded pilot is bound by source manifest SHA-256
`9e6311b8a88b879c2b8d102cc1b1d4093312c796633571d00c928738327b33d3` and its
rows `[0,2048)` are excluded. The V3 validator re-reads each selected
Parquet row and compares the complete normalized record, not only an ID.

The exact model path is
`/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16`. Any other
path is invalid. Any symlink anywhere below that model root is invalid. The
stable-file manifest excludes only `.cache` files, and the exact pre/post
manifest must match the frozen model manifest SHA-256
`69f078b42d4521d3e53f0c388a20fa6cf32b4df7ea6535b0eb9da6ccef75c256`.

## Source and corpus contract

The offline V3 packer writes a new source root once and refuses to overwrite
it. It emits exactly `16384` records per split at
`fit/fineweb_edu.jsonl` and `assessment/fineweb_edu.jsonl`, with exact raw-row
lineage and no V1/V2 source reuse. Publication is write-once and
digest-bound; V3 makes no unverifiable OS-filesystem immutability claim.

After review, the stage step loads only the frozen tokenizer under the same
offline process sandbox, takes the first 1024 tokenizer IDs from each source
record, requires decode/encode round-trip equality, and emits exactly `64`
fit and `64` assessment windows. Every window path is unique and fixed to
`{split}/fineweb_edu/window-{ordinal:06d}.txt`; every entry binds source
document ID, source row index/path, source text digest, window text digest,
and exactly 1024 re-tokenized IDs. The corpus validator independently loads
the frozen tokenizer and rechecks all 128 files, paths, token counts, hashes,
and source bindings.

## Intervention and fixed controls

Teacher-forced evaluation uses the cached Gemma3 text model. At destination
layer `d`, the previous-token source residual from layer `s` is L2-normalized
to the destination norm and mixed as

`(1-alpha) * destination + alpha * normalized_source`.

The only fit candidates, in this order, are `(7,2)`, `(9,3)`, `(11,4)`, and
`(12,5)`. Fit uses `alpha=0.10`; selection is the minimum aggregate fit mean
NLL with lexicographic `(mean_nll, source_layer, destination_layer)` tie-break.
The selected pair is locked before assessment and uses `alpha=0.15`, with
`beta=0.85` and source-to-destination norm adjustment recorded explicitly.
The paper's Gemma3 1B PT `(source=11,destination=4)` is an expected target,
never a forced selection.

The result must retain and the validator must verify native baseline,
zero-alpha identity/parity, all four candidate evaluations, selected
configuration, locked configuration, temperature `1.20` baseline and
intervention controls, deterministic repeat, nonzero intervention reach,
frozen model files, and frozen model-parameter digests. All metric rows must
bind to the exact 64/64 corpus document sets.

## Exact uncertainty rule

For each assessment document, define
`delta = selected_nll / target_count - baseline_nll / target_count`. All values
must be finite. The primary statistic is the arithmetic mean of these paired
deltas. Use exactly 10000 resamples and seed `20260829`. For resample `r` and
position `j`, compute the index as

`int.from_bytes(SHA256(UTF8(f"20260829:{r}:{j}"))[:8], "big") % n`.

The resample value is the arithmetic mean of its selected deltas. Sort the
10000 resample values. The 95% interval uses one-indexed nearest rank with
`ceil(q*10000)` clamped to one, at `q=0.025` and `q=0.975`; there is no
interpolation. Any nonfinite input or output rejects the run. A result is
`ReplicationCandidate` only if mean delta and the upper bound are both
strictly negative. Otherwise it is `NoCandidate`.

## Review, snapshot, and sandbox gates

Before tokenizer loading, model loading, staging, or effects, an independent
reviewer must inspect the exact protocol, packet, packer, validator, runner,
common contract, and tests. The receipt must be self-digested canonical JSON,
bind the recomputed protocol and packet hashes plus implementation manifest,
contain all seven required true findings, identify the reviewer and timestamp,
and set `effects_run=false`.

The runner snapshots the accepted review bytes and protocol hash before any
model/tokenizer operation and rejects any change before publication. It also
requires the exact model path and manifest. On macOS, the command entrypoint
must re-exec itself under `sandbox-exec` with `deny network*`; if that native
process sandbox is unavailable, the runner fails closed. Inside the sandbox,
Python socket/URL and subprocess network paths are denied as defense in depth.

The independent validator recomputes protocol/packet/implementation digests,
revalidates the review receipt, tokenizer counts, raw lineage, model path and
symlink policy, all result controls, self-digests, per-document bindings, and
the exact bootstrap. It runs before the external result root is published.

## Evidence ceiling

Even a fully valid positive result supports only
`LocalDevelopmentGemma3FineWebEduReplicationV3`: a bounded local result for
this model, source cohort, implementation, and protocol. It is not proof of
the paper, general recirculation, continual learning, benchmark performance,
production readiness, GiveMeANode/H100 behavior, or Astral claims.
