# Gemma3 FineWeb-Edu replication on H100 — V5 protocol

State slice: `continual-learning-gemma3-fineweb-edu-replication-h100-v5`.

## Scope and terminal history

This is a fresh replication protocol. H100 V1 is terminal historical
evidence. H100 V2 is contract-only and never authorized model or provider
execution. H100 V3 and V4 are terminally rejected and may not be patched,
rerun, or used as scientific input. V5 has a fresh source interval, corpus
identity, implementation identity, and external custody chain.

The scientific question is whether the locked one-token Gemma3 recirculation
intervention recovers the paper-shaped target pair `(11, 4)` on the fresh
cohort. The only dispositions are `ReplicationCandidate` and `NoCandidate`.
The claim ceiling is local development evidence. No paper replication,
benchmark, production, breakthrough, or generalization claim is authorized.

Every mutation in this phase names this state slice. No Evidence Ledger
mutation, training, adapter update, weight update, model download, or data
acquisition is performed by the model runner.

## Gate order

1. Freeze this protocol, the review packet, the V5 implementation manifest,
   the exact `AGENTS.md` bytes, and every implementation/provider byte.
2. Obtain a non-empty independent packet-bound signed Ed25519 `ACCEPT`.
   Silence, a missing response, prose, a stale response, or an
   operator-generated receipt is not acceptance. The reviewer reads only the
   packet allowlist and performs no effects.
3. After `ACCEPT`, obtain a documented GiveMeANode trust-root registry
   snapshot and an allocation quote. The registry snapshot must be an
   immutable external file with an HTTPS source URL, source digest, root key
   ID, and root public key. If the provider cannot supply a verifiable
   attestation chain, stop without a job.
4. Build the reviewed provider image from the reviewed bytes and record its
   actual OCI digest. Dependencies are installed only during image build.
5. Custody a fresh external model copy, raw dataset shards, normalized source,
   and tokenized corpus. Validate every digest and require owner-only `0700`
   external roots. The model runner is offline.
6. Create one launch manifest binding code, runtime, model, raw/source/data
   custody, image digest, review receipt, provider trust root, node shape, and
   the exact hard ceiling `USD 100.00`. The estimate must equal
   `quoted_gpu_usd_per_minute * max_runtime_minutes` exactly and be at most
   `100.00`.
7. Run no-spend preflight. Any failure stops the slice and prevents
   submission.
8. Submit exactly one GiveMeANode `h100-1` batch job with clock lock, no
   fallback, no sweep, no interactive session, and the sealed maximum
   duration. The provider is not contacted before steps 1–6 are complete.
9. Independently validate the provider receipt, result receipt, custody,
   controls, uncertainty, and publication order. Delete raw traces within 72
   hours after validation. Retain aggregate and digest artifacts only.

## Frozen model and runtime

The model is the original PyTorch `google/gemma-3-1b-pt` checkpoint, not an
MLX conversion. The exact model revision is a 40-hex revision recorded in the
external model manifest and launch manifest. The manifest also records
`Gemma3ForCausalLM`; `config.json` must independently declare `model_type`
`gemma3` and that architecture. Every regular model file is hashed. Symlinks,
mutable entries, alternate roots, and unbound path components fail closed.

The provider image is based on the reviewed digest of
`nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04`. Its exact Python dependency
closure is installed from the reviewed 44-line lock with `--no-deps`, then
checked with `pip check`. Runtime installation is forbidden. The runtime lock
binds Python 3.11, PyTorch 2.6.0, Transformers 4.51.3, Accelerate 1.6.0,
Safetensors 0.5.3, Tokenizers 0.21.1, PyArrow 24.0.0, Cryptography 44.0.2,
CUDA 12.4, bfloat16, one NVIDIA H100, and `network-none-v5`.

The entrypoint and runner must prove one CUDA device whose name contains
`H100`, the exact driver version in the launch manifest, all locked runtime
versions, a namespace containing only loopback, no IPv4 route, and no IPv6
route. Missing route or device proof is failure. The runner additionally
blocks Python socket, process-spawn, and environment network paths during
effects; the container network mode is `none`.

## Fresh data and disjointness

The only source is the pinned Hugging Face FineWeb-Edu dataset
`HuggingFaceFW/fineweb-edu`, revision
`87f09149ef4734204d70ed1d046ddc9ca3f2b8f9`, config
`fineweb-edu-crawl-shards`, split `train`. The two raw Parquet objects and
checksums are frozen in the packer and validator:

| split | crawl | raw path | rows used |
| --- | --- | --- | --- |
| fit | `CC-MAIN-2013-20` | `data/CC-MAIN-2013-20/train-00000-of-00014.parquet` | `[83968, 100352)` |
| assessment | `CC-MAIN-2024-10` | `data/CC-MAIN-2024-10/000_00000.parquet` | `[83968, 100352)` |

Each split contributes exactly 64 documents and the first valid 1024-token
window from each document. The validator rederives normalized rows from raw
Parquet custody and re-tokenizes every retained window with the copied model
tokenizer. Fit and assessment IDs must be disjoint. The excluded ranges cover
the prior pilot, prior V31 material, discarded material, H100 V1, H100 V3,
and H100 V4. No V1, V2, V3, or V4 source, corpus, activation, result, or
model artifact is an input.

Raw Parquet, normalized source, tokenized corpus, copied model, and raw traces
remain outside the repository. Raw traces are deleted within 72 hours of
independent validation. The repository contains no raw data.

## Locked recurrence and controls

For each document, tokens are evaluated left-to-right. The source activation
from the previous token at `source_layer` is norm-matched into the current
token's `destination_layer`:

`h' = 0.85 h_destination + 0.15 h_source * ||h_destination|| / max(||h_source||, 1e-6)`.

The fixed candidate pairs are `(7,2)`, `(9,3)`, `(11,4)`, and `(12,5)`. Fit
uses `alpha=0.10`, `beta=0.90`; evaluation uses `alpha=0.15`, `beta=0.85`.
Fit selects minimum mean token NLL with candidate-order tie-breaking. The
selected pair is locked before assessment. The paper target `(11,4)` is
reported as recovered only when the locked selection equals it; the result
never forces that pair.

Controls are fixed before effects: native baseline, zero-alpha identity for
every candidate, all candidate evaluations, temperature-1.20 baseline and
intervention, deterministic repeat, frozen model manifest, and frozen model
parameters. Assessment uses the locked pair, temperature controls, and a
repeat with identical inputs and weights. Missing rows, nonfinite NLL,
nonzero reach failure, zero-alpha mismatch, repeat mismatch, or changed
parameters terminate the job.

## Estimand, uncertainty, and claims

The estimand is the mean paired per-document NLL delta
`selected_minus_baseline` over 64 assessment documents. The fixed bootstrap
uses 10,000 SHA-256-counter resamples, seed `20260829`, a 95% percentile
interval, and one-indexed nearest-rank quantiles. `ReplicationCandidate`
requires mean delta `< 0` and upper bound `< 0`; otherwise the disposition is
`NoCandidate`.

The maximum local claim is
`LocalDevelopmentGemma3FineWebEduReplicationH100V5`. A candidate is not a
paper replication, benchmark result, production result, or breakthrough.

## Provider custody and attestation

GiveMeANode is the only permitted provider. Before launch, the operator must
place an immutable provider trust-root registry snapshot outside the
repository and bind its path and SHA-256 to the launch manifest. The snapshot
has the closed schema `givemeanode-attestation-trust-root-v1`, issuer
`givemeanode`, root ID, base64 Ed25519 root public key, HTTPS source URL,
source SHA-256, and its own canonical SHA-256. The launch root key must match
the snapshot exactly.

The actual provider receipt must contain the exact job, allocation, node,
UTC start/stop, quote, charge, hard ceiling, estimate, launch digest, and
OCI image digest. Its attestation contains an issuer, leaf key ID, root ID,
leaf Ed25519 public key, certificate signature from the launch-bound provider
root, payload digest, and leaf signature. The independent validator checks
the root certificate, leaf signature, payload digest, receipt self-digest,
and all budget/identity bindings. A provider response without this chain is
not accepted and cannot be replaced by a locally generated receipt.

The result root must already contain only the immutable provider receipt
before model loading. The runner never creates, replaces, or edits that
receipt. It appends `result.json` and `result-receipt.json` with exclusive
creation. The independent validator checks the exact three-file final set and
all launch/provider/result bindings.

## Prohibited actions

No provider action occurs before independent `ACCEPT`, the immutable provider
trust-root snapshot, actual image digest, fresh custody validation, launch
manifest, and no-spend preflight. No second H100 attempt, retuning, candidate
shopping after assessment, fallback runtime, raw-data publication, Evidence
Ledger mutation, or claim above the named ceiling is permitted. A rejected
review, unavailable attestation, custody failure, runtime failure, budget
boundary, or scientific failure closes V5 as `NoCandidate` without adaptive
retry.
