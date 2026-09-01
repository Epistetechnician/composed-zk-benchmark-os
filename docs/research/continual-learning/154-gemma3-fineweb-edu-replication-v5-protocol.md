# Gemma3 FineWeb-Edu replication V5 protocol

State slice: `continual-learning-gemma3-fineweb-edu-replication-v5`

Status: proposed and sealed for a fresh independent implementation review.
V1, V2, V3, and V4 are immutable rejected records. V5 is a new protocol and
does not reclassify or use any rejected protocol as an approved protocol or
scientific result. No V5 source, corpus, model effect, or result is permitted
until an independent `ACCEPT` receipt binds this document, the review packet,
and the complete implementation manifest.

Claim ceiling: `LocalDevelopmentGemma3FineWebEduReplicationV5`.

## Custody and exact roots

Every root below is an exact lexical path. The implementation rejects symlink
components, symlink entries, unrecognized files, and path aliases. The final
roots are published with a no-overwrite directory creation followed by moves
into the empty directory. A pre-existing final root is terminal for this run.

- Raw root: `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-raw-v1`
- Prior-pilot source root: `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-source-v1`
- V5 source root: `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v5-source`
- V5 corpus root: `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v5-corpus`
- V5 result root: `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v5-result`
- Model path: `/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16`

The raw non-cache file set is exactly the two pinned Parquet files below. The
existing Hugging Face cache metadata is permitted only under `.cache/` and is
not used as identity.

| crawl | relative path | bytes | SHA-256 |
| --- | --- | ---: | --- |
| `CC-MAIN-2013-20` | `data/CC-MAIN-2013-20/train-00000-of-00014.parquet` | `2369456837` | `fb989c566f6fba00ab61decc5f7aa1538a07d9b142e58a52ff790154528ffd03` |
| `CC-MAIN-2024-10` | `data/CC-MAIN-2024-10/000_00000.parquet` | `1911528585` | `89c802096c8adb54cdcfad567c13838814d83dbb4dbcda008a0f740e73f8a484` |

Dataset identity is `HuggingFaceFW/fineweb-edu`, revision
`87f09149ef4734204d70ed1d046ddc9ca3f2b8f9`, config
`fineweb-edu-crawl-shards`, split `train`. V5 re-derives the prior pilot from
raw rows `[0,2048)` and the fresh source from rows `[2048,18432)` in each
shard. The prior source manifest SHA-256 is
`9e6311b8a88b879c2b8d102cc1b1d4093312c796633571d00c928738327b33d3`.

The model stable-file manifest must equal
`69f078b42d4521d3e53f0c388a20fa6cf32b4df7ea6535b0eb9da6ccef75c256`.
V5 checks that exact model path and manifest before importing or calling the
tokenizer or model loader. It hashes loaded parameter tensors before and after
effects and requires equality. Runtime versions are MLX `0.31.2`, MLX-LM
`0.31.3`, and PyArrow `24.0.0`.

## Review receipt and implementation closure

The receipt path is
`docs/research/continual-learning/156-gemma3-fineweb-edu-replication-v5-independent-review-2026-08-30.json`.
It must be canonical self-digested JSON containing a nonblank reviewer,
canonical second-resolution UTC timestamp, `review_decision: ACCEPT`,
`effects_run: false`, the recomputed protocol and packet SHA-256 values, the
recomputed implementation-manifest SHA-256, and exactly the seven required
true findings named in the review packet. The validator recomputes the
protocol, packet, and implementation-manifest hashes from the files on disk;
a stale hard-coded receipt constant cannot pass.

The reviewed implementation file set is exactly the two documents, four V5
Python modules, and the V5 test module named by
`IMPLEMENTATION_FILES`. The review receipt is outside that implementation
closure. Every execution snapshot includes the protocol bytes, packet bytes,
receipt bytes, and every implementation-file digest. A changed reviewed file
or receipt stops the run.

## Source and corpus construction

After review acceptance, the packer writes exactly these source files:
`acquisition-manifest.json`, `fit/fineweb_edu.jsonl`, and
`assessment/fineweb_edu.jsonl`. It re-derives every record from the pinned
Parquet rows, snapshots the complete raw/prior input trees before and after
extraction, checks the prior-pilot content and IDs, and validates the staged
source before no-overwrite publication. The publication function itself
rechecks the exact staging file set inside the no-replace boundary.

After source acceptance, the stage step loads the exact tokenizer only after
model custody and native offline proof. It chooses the first 64 eligible
windows of exactly 1024 IDs per split, checks decode/encode round-trip, and
writes exactly 128 text files plus `manifest.json`:
`fit/window-000000.txt` through `fit/window-000063.txt` and the corresponding
assessment paths. Each manifest entry binds document ID, source text digest,
window text digest, source row/path, byte length, and token count. The
validator independently re-tokenizes source rows and requires the manifest IDs
to equal the first 64 eligible rows in each split, not merely any 64 members.
Fit and assessment IDs are disjoint and are independently rechecked from
source.

## Offline boundary

On macOS the entrypoint must prove native denial of `network-outbound` with
`sandbox_check`. If direct execution is not denied, it re-enters once through
`sandbox-exec` with `(deny network*) (allow default)`; a second unproven
process fails closed. An environment marker prevents a re-entry loop but is
never accepted as proof. Python socket connect/send, DNS, URL, child-process,
shell, and spawn paths are additionally blocked around tokenizer and model
operations. No model or dataset download is allowed.

## Locked recurrence and controls

V5 directly implements the paper-aligned one-additional-iteration recurrence
from [Recirculation, arXiv:2608.17981](https://arxiv.org/abs/2608.17981). At
destination layer `d` it computes
`beta * destination + alpha * source * destination_l2 / max(source_l2,epsilon)`.
The only fit candidates, in order, are `(7,2)`, `(9,3)`, `(11,4)`, and
`(12,5)` with `alpha=0.10`, `beta=0.90`. Selection minimizes fit mean NLL
with lexicographic `(mean_nll, source, destination)` tie-breaking. The
selected pair is locked before assessment with `alpha=0.15`, `beta=0.85`.
The paper pair `(11,4)` is an expected replication target, recorded and
reported as recovered or not recovered; it is never forced.

The final result retains and the independent validator recomputes native
baseline, zero-alpha identity for all 128 windows, all four candidates,
selected and locked configurations, temperature-1.20 baseline and
intervention controls, deterministic repeat, nonzero intervention reach, the
exact model-file manifest, and before/after parameter digests. Metrics bind
temperature, configuration, dataset, path, source digest, window digest, and
per-document NLL. The validator recomputes all controls from the reviewed V5
runner after structural checks; it does not trust result aggregates.

## Uncertainty and decision

For each assessment document, `delta = selected_nll/1023 - baseline_nll/1023`.
All values must be finite non-boolean numbers. The primary statistic is the
arithmetic mean of the 64 paired deltas. V5 uses exactly 10,000 resamples,
seed `20260829`, and for resample `r`, position `j` uses
`int.from_bytes(SHA256(UTF8("20260829:r:j"))[:8], "big") % n`. The 95% interval
uses one-indexed nearest rank with clamped `ceil(q*10000)` indices and no
interpolation. A result is `ReplicationCandidate` only when both the mean and
upper bound are strictly negative. Otherwise it is `NoCandidate`.

## Prohibitions

V5 forbids model or dataset downloads, network during model use, training,
adapter or weight updates, adaptive candidate/control/threshold tuning,
GiveMeANode/H100/provider calls, Astral or Evidence Ledger mutation,
benchmark or production claims, and introspection or causal-self-modeling
claims. It cannot promote Stage 0C or Stage 1. Any review, custody, offline,
configuration, validator, or publication failure stops the run without tuning
around the failure.
