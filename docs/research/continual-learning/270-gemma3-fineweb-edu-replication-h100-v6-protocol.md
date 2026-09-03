# Gemma3 FineWeb-Edu replication on H100 — V6 protocol

State slice: `continual-learning-gemma3-fineweb-edu-replication-h100-v6`.

## Scope and terminal history

This is a fresh replication protocol. H100 V1 is immutable historical
evidence, H100 V2 is contract-only, and H100 V3, V4, and V5 are terminally
rejected. Their scientific data, model executions, effects, results, and
receipts are not V6 inputs. V6 has a fresh source interval, corpus identity,
implementation identity, provider bundle, and external custody chain.

The scientific question is whether the locked one-token Gemma3 recurrence
recovers the paper-shaped pair `(11, 4)` on a fresh cohort. The dispositions
are only `ReplicationCandidate` and `NoCandidate`. The claim ceiling is local
development evidence; no paper replication, benchmark, production,
breakthrough, or generalization claim is authorized.

Every mutation in this phase names this state slice. The runner does not
train, download, contact a provider, mutate the Evidence Ledger, or publish
raw data.

## Gate order

1. Freeze this protocol, packet, implementation manifest, exact `AGENTS.md`,
   and all provider/code bytes.
2. Obtain a non-empty independent packet-bound signed Ed25519 `ACCEPT` for
   the exact frozen bytes. Silence, stale output, prose, an empty response,
   or an operator-generated receipt is not acceptance.
3. Obtain an immutable external GiveMeANode trust-root registry snapshot and
   a signed allocation quote. Stop if the provider cannot verify its
   attestation chain.
4. Build the reviewed provider image and record its actual OCI digest.
5. Custody a fresh external PyTorch model copy, pinned raw Parquet shards,
   normalized source, and tokenized corpus. Validate all hashes and require
   owner-only `0700` roots. Model execution is offline.
6. Create one launch manifest binding code, runtime, model, data, image,
   review receipt, provider trust root, node shape, and the exact hard ceiling
   `USD 100.00`. Decimal arithmetic must satisfy
   `quote * max_runtime_minutes == estimated_max_total_usd` exactly, with the
   estimate no greater than the ceiling.
7. Run no-spend preflight. Any failure stops the slice.
8. Submit exactly one clock-locked GiveMeANode `h100-1` batch job, with no
   fallback, sweep, interactive session, or second attempt.
9. Independently validate custody, provider attestation, result bindings,
   controls, uncertainty, and publication order. Delete the temporary scalar
   ledger and raw traces after validation; retain aggregate and digest
   artifacts only.

## Frozen model and runtime

The model is the exact PyTorch `google/gemma-3-1b-pt` checkpoint. Its 40-hex
revision, `Gemma3ForCausalLM` architecture, every regular file, and canonical
manifest digest are frozen in an external `gemma3-model-manifest-v6` bundle.
`config.json` must independently declare `model_type` `gemma3` and the same
architecture. Symlinks, mutable entries, alternate roots, and unbound path
components fail closed.

The provider image is based on the reviewed digest of
`nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04`. Its full dependency closure is
installed during image build from the reviewed lock with `--no-deps`, then
checked with `pip check`; runtime installation is forbidden. The runtime lock
binds Python 3.11, PyTorch 2.6.0, Transformers 4.51.3, Accelerate 1.6.0,
Safetensors 0.5.3, Tokenizers 0.21.1, PyArrow 24.0.0, Cryptography 44.0.2,
CUDA 12.4, bfloat16, one NVIDIA H100, and `network-none-v6`.

The entrypoint and runner prove one CUDA device named H100, the exact driver
version, all locked runtime versions, a loopback-only namespace, no IPv4
route, and no IPv6 route. Missing proof fails. The container network mode is
`none`, and the runner blocks Python socket and process-spawn network paths.

## Fresh data and disjointness

The only source is the pinned Hugging Face FineWeb-Edu dataset
`HuggingFaceFW/fineweb-edu`, revision
`87f09149ef4734204d70ed1d046ddc9ca3f2b8f9`, config
`fineweb-edu-crawl-shards`, split `train`. The two raw Parquet objects and
their byte hashes are frozen in the packer and validator.

Fit uses `CC-MAIN-2013-20`, assessment uses `CC-MAIN-2024-10`. Each source
range is `[100352, 116736)`, yielding 64 documents per split and the first
valid 1024-token window per document. The validator rederives source rows
from raw custody and retokenizes each retained window with the copied model
tokenizer. Fit and assessment IDs are disjoint. All prior pilot, V31,
discarded, and prior H100 ranges, including rejected V5, are excluded. No
prior scientific artifact is an input.

Raw Parquet, normalized source, tokenized corpus, copied model, provider
registry, and traces remain outside the repository. Raw traces and the
temporary assessment ledger are deleted after independent validation and no
later than 72 hours.

## Locked recurrence and controls

Tokens are evaluated left-to-right. The source activation from the previous
token at `source_layer` is norm-matched into the current token's
`destination_layer`:

`h' = 0.85 h_destination + 0.15 h_source * ||h_destination|| / max(||h_source||, 1e-6)`.

The fixed candidate pairs are `(7,2)`, `(9,3)`, `(11,4)`, and `(12,5)`.
Fit uses `alpha=0.10`, `beta=0.90`; evaluation uses `alpha=0.15`,
`beta=0.85`. Fit selects minimum mean token NLL with candidate-order
tie-breaking. The selected pair is locked before assessment. The paper target
is reported as recovered only when the selected pair equals `(11,4)`.

Controls are fixed before effects: native baseline, zero-alpha identity for
each candidate, all candidate evaluations, temperature-1.20 baseline and
intervention, deterministic repeat, frozen model manifest, and frozen model
parameters. Missing rows, nonfinite or negative NLL, nonzero-reach failure,
zero-alpha mismatch, repeat mismatch, changed parameters, or changed launch
bytes terminate the job.

## Aggregate retention, estimand, and uncertainty

The final result is aggregate-only. It retains document-count and ordered
document-ID digests, target-token counts, mean NLL, perplexity, controls,
selection, reach, and uncertainty. It retains no per-document text, source
identity, or scalar NLL. During execution, a temporary owner-only JSONL ledger
outside the result root contains only assessment document IDs and paired
baseline/selected NLL scalars. Its SHA-256 is bound into the result and the
independent validator recomputes aggregates and bootstrap values from it,
then deletes it.

The estimand is mean paired per-document NLL delta
`selected_minus_baseline` over 64 assessment documents. The fixed bootstrap
uses 10,000 SHA-256-counter resamples, seed `20260829`, a 95% percentile
interval, and one-indexed nearest-rank quantiles. `ReplicationCandidate`
requires mean delta `< 0` and upper bound `< 0`; otherwise the disposition is
`NoCandidate`.

The maximum local claim is
`LocalDevelopmentGemma3FineWebEduReplicationH100V6`. A candidate is not a
paper replication, benchmark result, production result, or breakthrough.

## Provider custody and attestation

GiveMeANode is the only permitted provider. Its immutable external trust-root
registry uses schema `givemeanode-attestation-trust-root-v1`, issuer
`givemeanode`, a root ID, base64 Ed25519 public key, HTTPS source URL, source
hash, and canonical self-hash. The launch manifest binds the registry path,
hash, root ID, and public key.

The provider receipt must contain exact job, allocation, node, UTC start/stop,
quote, charge, hard ceiling, estimate, launch digest, and OCI digest. Its
attestation must contain the leaf key, root certificate, payload digest, and
leaf signature. The validator checks the root certificate, leaf signature,
payload, receipt digest, and exact decimal budget/identity bindings. A local
or unsigned provider receipt is invalid.

The result root contains only the pre-issued immutable provider receipt before
model loading. Final `result.json` and `result-receipt.json` are created
exclusively, sealed read-only, and validated as an exact three-file root. The
result binds provider job, allocation, node, charge, stop reason, and receipt
digest.

## Prohibited actions

No provider action occurs before independent `ACCEPT`, registry snapshot,
actual image digest, fresh custody validation, launch manifest, and preflight.
No second H100 attempt, retuning, post-assessment candidate shopping,
fallback runtime, raw-data publication, Evidence Ledger mutation, or claim
above the named ceiling is permitted. A rejected review, unavailable
attestation, custody failure, runtime failure, budget boundary, or scientific
failure closes V6 as `NoCandidate` without adaptive retry.
