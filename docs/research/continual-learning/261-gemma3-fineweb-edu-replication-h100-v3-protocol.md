# Gemma3 FineWeb-Edu H100 V3 execution protocol

State slice: continual-learning-gemma3-fineweb-edu-replication-h100-v3.

This is a fresh execution identity. The rejected H100 V1 slice is terminal
historical evidence. The accepted V2 slice is contract-only. Neither slice's
scientific corpus, model bundle, activations, metrics, results, provider
receipts, or launch artifacts is an input to V3.

## Scope and claim ceiling

V3 tests one bounded CUDA/PyTorch replication of the Recirculation paper's
one-additional-iteration target on the original Gemma 3 1B PT checkpoint. The
paper's `(11,4)` pair is an expected target, not a forced result. The maximum
claim is LocalDevelopmentGemma3FineWebEduReplicationH100V3. A positive result
is not a breakthrough, benchmark, production, cross-runtime, or general
recirculation claim.

The only permitted remote workload is one GiveMeANode `h100-1` batch job. No
interactive node, multi-GPU allocation, sweep, fallback, training, adapter,
quantization, or unbounded shell is allowed. The exact hard ceiling is USD
100.00. The quote, maximum runtime, and estimated total must be sealed in a
launch manifest with estimated total no greater than USD 100.00.

## Fresh custody and disjoint data

The model source is the already downloaded original PyTorch bundle at
`/Users/shaanp/.lmstudio/models/google/gemma-3-1b-pt`. It must be copied to a
new external owner-only read-only custody root and represented by a complete
file manifest. Runtime model downloads are forbidden.

The dataset is HuggingFaceFW/fineweb-edu at revision
`87f09149ef4734204d70ed1d046ddc9ca3f2b8f9`, config
`fineweb-edu-crawl-shards`, split `train`. The two pinned Parquet shards must
be re-custodied and independently hashed. V3 uses rows `[51200,67584)` from
the first shard for fit and the second shard for assessment, taking the first
64 valid 1024-token windows in each split.

The excluded row ranges are `[0,2048)` prior pilot, `[2048,18432)` prior V31,
`[18432,34816)` discarded, and `[34816,51200)` prior H100 V1. Source IDs,
source-row digests, normalized records, and window digests are rederived from
the pinned raw objects. Missing raw objects, changed bytes, duplicate IDs,
overlap, insufficient rows, or any split/corpus mismatch is a hard failure.
All raw, source, corpus, and result roots remain outside the repository under
the external custody namespace. Raw text, token IDs, hidden states, logits,
and per-token arrays are deleted before final result sealing.

## Locked runtime and recurrence

The provider image is pinned to
`nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04` with its reviewed OCI digest.
Python 3.11, PyTorch 2.6.0, Transformers 4.51.3, Accelerate 1.6.0,
Safetensors 0.5.3, Tokenizers 0.21.1, PyArrow 24.0.0, CUDA 12.4, BF16,
and one NVIDIA H100 are fixed by the runtime lock and image build. Locked
packages are installed only while building the image; runtime installation is
forbidden. The runner uses inference mode, frozen parameters, deterministic
evaluation, and local-files-only model loading.

The container uses network mode `none` and the runner proves loopback-only
interfaces and routes. Python socket/DNS and child-process network paths are
blocked during effects. Any network, package drift, model download, or
mutable custody entry fails closed.

Fit candidates are exactly `(7,2)`, `(9,3)`, `(11,4)`, and `(12,5)` with
alpha 0.10 and beta 0.90. The lowest fit mean NLL wins, with listed order as
the tie-break. Assessment uses only the selected pair with alpha 0.15 and
beta 0.85, source-to-destination L2 normalization, temperature 1.20 controls,
zero-alpha identity for every candidate, deterministic repeat, and frozen
parameters. The primary estimand is paired per-document selected-minus-
baseline NLL over 64 assessment windows. The fixed 10,000-resample
SHA-256-counter nearest-rank 95% bootstrap requires mean and upper bound both
below zero for `ReplicationCandidate`; otherwise the result is `NoCandidate`.

## Review and execution gates

Before any image build, provider quote, launch manifest, model load, or paid
action, an independent reviewer must read exactly the V3 packet allowlist,
recompute every SHA-256 and the implementation-manifest self-digest, inspect
the provider receipt and result-root guards, and return one canonical,
non-empty packet-bound `ACCEPT`. The reviewer must not edit, delegate, create
a receipt file, load a model, acquire data, build an image, or contact a
provider. Any rejection, empty response, malformed response, or byte drift
closes this packet without adaptive repair.

After `ACCEPT`, the operator may preserve that exact response as a review
receipt, obtain one provider quote, build the reviewed image, record its actual
OCI digest, create the USD 100.00 launch manifest, and run no-spend preflight.
Only a passing preflight may submit exactly one bounded `h100-1` batch job.
The provider receipt must bind the launch manifest, node/allocation identity,
quote, charge, stop reason, runtime, and attestation. Independent validation
must pass before classification or publication. Any gate failure is terminal
`NoCandidate` or execution failure; no tuning or retry is allowed.

Every mutation in this phase names state slice
`continual-learning-gemma3-fineweb-edu-replication-h100-v3`.
