# Gemma3 FineWeb-Edu replication on H100 — V4 protocol

State slice: `continual-learning-gemma3-fineweb-edu-replication-h100-v4`.

## Status and scope

This is a fresh replication protocol. H100 V1 is terminal historical
evidence. H100 V2 is contract-only and never authorized model or provider
execution. H100 V3 is terminally rejected and may not be patched, rerun, or
used as scientific input. V4 uses a fresh source/corpus identity and a fresh
external custody chain.

The only scientific question is whether the locked one-token Gemma3
recirculation intervention reproduces the paper-shaped target pair `(11, 4)`
on the fresh cohort. A result is either `ReplicationCandidate` under the
local development ceiling below or `NoCandidate`. No benchmark, production,
breakthrough, kernel-observability, or generalization claim is authorized.

Every mutation in this phase names this state slice. No Evidence Ledger
mutation, training, adapter update, weight update, model download, or data
acquisition is performed by the model runner.

## Gate order

1. Freeze this protocol, the review packet, the V4 implementation manifest,
   the exact `AGENTS.md` bytes, and all implementation/provider bytes.
2. Obtain a non-empty independent packet-bound signed Ed25519 `ACCEPT`.
   Silence, a missing response, a prose response, a stale response, or an
   operator-generated receipt is not acceptance. The independent reviewer
   reads only the packet allowlist and performs no effects.
3. After `ACCEPT`, acquire the exact provider allocation quote and the
   provider's attestation key identity. Build the reviewed provider image
   from the reviewed bytes and record its actual OCI digest.
4. Custody a fresh external model copy, raw dataset shards, normalized source,
   and tokenized corpus. Validate every digest and require owner-only `0700`
   external roots. The model runner is offline.
5. Create one launch manifest binding code, runtime, model, raw/source/data
   custody, image digest, review receipt, provider key, node shape, and the
   exact hard ceiling `USD 100.00`. The estimate must equal
   `quoted_gpu_usd_per_minute * max_runtime_minutes` exactly and be at most
   `100.00`.
6. Run no-spend preflight. If any gate fails, stop and do not submit.
7. Submit exactly one GiveMeANode `h100-1` batch job with clock lock, no
   fallback, no sweep, no interactive session, and the sealed maximum
   duration.
8. Independently validate the provider receipt, result receipt, custody,
   controls, uncertainty, and publication order. Delete raw traces within
   72 hours after validation. Retain aggregate and digest artifacts only.

## Frozen model/runtime contract

The model identity is the original PyTorch `google/gemma-3-1b-pt` checkpoint,
not an MLX conversion. The launch manifest names the exact external copied
model root and its read-only sealed-file-tree digest. Every regular file is
hashed; symlinks, mutable entries, alternate model roots, and unbound path
components fail closed.

The provider image is based on
`nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04` with the reviewed base-image
digest. Dependencies are installed only during image build from the reviewed
lock. Runtime installation and network access are forbidden. The runtime lock
binds Python 3.11, PyTorch 2.6.0, Transformers 4.51.3, Accelerate 1.6.0,
Safetensors 0.5.3, Tokenizers 0.21.1, PyArrow 24.0.0, Cryptography 44.0.2,
CUDA 12.4, bfloat16, one NVIDIA H100, and `network-none-v4`.

The runner must prove one CUDA device whose name contains `H100`, the exact
driver version in the launch manifest, the locked runtime versions, a network
namespace containing only loopback with no IPv4 or IPv6 routes, and equal
before/after model-parameter digests. Any missing proof stops execution.

## Fresh data and disjointness

The only data source is the pinned Hugging Face FineWeb-Edu dataset
`HuggingFaceFW/fineweb-edu`, revision
`87f09149ef4734204d70ed1d046ddc9ca3f2b8f9`, config
`fineweb-edu-crawl-shards`, split `train`. The two raw parquet files and
checksums are frozen in the packer and validator:

| split | crawl | raw path | rows used |
|---|---|---|---|
| fit | `CC-MAIN-2013-20` | `data/CC-MAIN-2013-20/train-00000-of-00014.parquet` | `[67584, 83968)` |
| assessment | `CC-MAIN-2024-10` | `data/CC-MAIN-2024-10/000_00000.parquet` | `[67584, 83968)` |

Each split contributes exactly 64 documents and the first valid 1024-token
window from each document. The validator rederives normalized rows from the
raw parquet bytes and re-tokenizes every retained window using the copied
model tokenizer. Fit and assessment IDs must be disjoint. The excluded ranges
are `[0, 2048)` prior pilot, `[2048, 18432)` prior V31, `[18432, 34816)`
discarded material, `[34816, 51200)` prior H100 V1, and `[51200, 67584)`
prior H100 V3. No V1, V2, or V3 source, corpus, activation, result, or model
artifact is an input.

Raw parquet, normalized source, tokenized corpus, copied model, and raw
traces remain outside the repository. Raw traces are deleted within 72 hours
of independent validation.

## Locked intervention and controls

For each document, tokens are evaluated left-to-right. The source activation
from the previous token at layer `source_layer` is norm-matched into the
current token's destination layer `destination_layer`:

`h' = 0.85 h_destination + 0.15 h_source * ||h_destination|| /
max(||h_source||, 1e-6)`.

The fixed candidate pairs are `(7,2)`, `(9,3)`, `(11,4)`, and `(12,5)`. Fit
uses `alpha=0.10`, `beta=0.90`; evaluation uses `alpha=0.15`, `beta=0.85`.
Fit selects the minimum mean token NLL with deterministic candidate-order
tie-breaking. The selected pair is locked before assessment. The paper target
`(11,4)` is reported as recovered only if the locked selection equals it; the
selection is never forced.

Controls are fixed before effects: native baseline, zero-alpha identity for
every candidate, all candidate evaluations, temperature-1.20 baseline and
intervention, deterministic repeat, frozen model manifest, and frozen model
parameters. Assessment uses the locked pair, the 1.20 temperature controls,
and a repeat with identical inputs and weights. Missing rows, nonfinite NLL,
nonzero reach failure, zero-alpha mismatch, repeat mismatch, or changed
parameters terminate the job.

## Uncertainty and claim ceiling

The estimand is the mean paired per-document NLL delta
`selected_minus_baseline` over 64 assessment documents. The fixed bootstrap
uses 10,000 SHA-256-counter resamples, seed `20260829`, 95% percentile
interval, and one-indexed nearest-rank quantiles. `ReplicationCandidate`
requires mean delta `< 0` and upper bound `< 0`; otherwise the disposition is
`NoCandidate`.

The maximum local claim is
`LocalDevelopmentGemma3FineWebEduReplicationH100V4`. A candidate is not a
paper replication, benchmark result, production result, or breakthrough.

## Provider custody and attestation

The provider is GiveMeANode only. The provider receipt must be created from
the actual provider job/allocation response before result publication and
must contain the exact job ID, allocation ID, node ID, UTC start/stop times,
allowed stop reason, quote, charge, hard ceiling, estimate, launch digest,
and OCI image digest.

The provider receipt must also contain a GiveMeANode-issued Ed25519
attestation over the canonical provider payload. The launch manifest records
the provider-issued key ID and public key. The independent validator verifies
the issuer, key ID, payload digest, signature, and receipt self-digest. The
operator may not generate, replace, or weaken this attestation. If the
GiveMeANode API does not return a verifiable attestation, the protocol stops
with no provider submission or scientific result; no local substitute is
accepted.

The result root must already contain only this read-only provider receipt
before model loading. The runner never creates, replaces, or edits that
receipt. It appends `result.json` and `result-receipt.json` with exclusive
creation, and the independent validator checks the exact three-file final
set and all launch/provider/result bindings.

## Prohibited actions

No provider action occurs before independent `ACCEPT`, actual image digest,
fresh custody validation, a launch manifest, and no-spend preflight. No
second H100 attempt, retuning, candidate shopping after seeing assessment,
fallback runtime, raw-data publication, Evidence Ledger mutation, or claim
above the named ceiling is permitted. A rejected review, unavailable
attestation, custody failure, runtime failure, budget boundary, or scientific
failure closes V4 as `NoCandidate` without adaptive retry.
