# Gemma3 FineWeb-Edu H100 replication — V9 protocol

State slice: `continual-learning-gemma3-fineweb-edu-replication-h100-v9`.

V9 is a fresh protocol and implementation identity. V8 and all earlier H100
identities are terminal historical records and provide no scientific inputs.
V9 tests one locked question: whether the one-token Gemma3 recurrence recovers
the paper-shaped candidate pair `(11, 4)` on a fresh, disjoint FineWeb-Edu
cohort. The only dispositions are `ReplicationCandidate` and `NoCandidate`.
The maximum claim is local development evidence; this is not a paper,
benchmark, production, breakthrough, or generalization claim.

The hashed exclusion range includes the V8 boundary
`prior-h100-v8: [100352, 116736)`, so the V8 fence is covered by
`excluded_id_sha256`. V6 is retained only as scalar historical identity
metadata for the same legacy interval; it is not a second hashed range. V9
does not read, copy, or reuse V8 data, model outputs, receipts, or other
scientific artifacts. The source manifest records the V6, V7, and V8 scalar
identity fences and the single effective V8 hashed range.

## Gate order

All digest-bound JSON uses canonical UTF-8 encoding: sorted object keys,
compact separators, preserved non-ASCII characters (`ensure_ascii=false`), and
a terminal newline. The packer and validator implement this same byte contract.

1. Freeze this protocol, the review packet, the V9 implementation/provider
   bytes, `AGENTS.md`, and the implementation manifest.
2. Obtain an independent packet-bound Ed25519 `ACCEPT`. The operator may not
   create, sign, or substitute this receipt.
3. Obtain and validate an immutable GiveMeANode trust-root snapshot and signed
   allocation quote. No provider call occurs earlier.
4. Custody the exact fresh model, raw Parquet objects, normalized source, and
   tokenized corpus below external owner-only roots. Recompute every digest.
5. Build the reviewed CUDA/PyTorch provider image and record its actual OCI
   digest.
6. Create and validate one launch manifest with an exact hard ceiling of
   `USD 69.00`; Decimal arithmetic must satisfy the quoted rate times the
   runtime exactly and remain at or below the ceiling.
7. Run no-spend preflight. Any failure closes V9 without retry.
8. Submit exactly one clock-locked `h100-1` batch job. No fallback, sweep,
   interactive session, second attempt, or adaptive tuning is allowed.
9. Independently validate the aggregate result, then delete raw traces and the
   temporary scalar ledger within 72 hours. Retain only aggregate receipts.

## Frozen scientific contract

The model is the exact PyTorch `google/gemma-3-1b-pt` checkpoint with its
40-hex revision, official `gemma3_text` config type,
`Gemma3ForCausalLM` architecture, tokenizer, regular-file manifest, and
parameter digest frozen before effects. V9 uses Python 3.11,
PyTorch 2.6.0, Transformers 4.51.3, CUDA 12.4, bfloat16, one NVIDIA H100,
and `network-none-v9`. Runtime installation and network access during effects
are forbidden. Training and Evidence Ledger mutation are forbidden.

The pinned source is Hugging Face `HuggingFaceFW/fineweb-edu`, revision
`87f09149ef4734204d70ed1d046ddc9ca3f2b8f9`, config
`fineweb-edu-crawl-shards`, split `train`. V9 uses the fixed row interval
`[133120, 149504)`, with 64 fit and 64 assessment documents, each with the
first valid 1024-token window. Fit and assessment IDs are disjoint, and all
prior pilot and H100 ranges through V7 are excluded. Raw files and normalized
bundles remain outside the repository.

For each previous-token/current-token pair, the source activation is
norm-matched into the destination activation:

`h' = 0.85 h_destination + 0.15 h_source * ||h_destination|| / max(||h_source||, 1e-6)`.

Candidates are `(7,2)`, `(9,3)`, `(11,4)`, `(12,5)`. Fit selection uses
`alpha=0.10`, `beta=0.90`; evaluation uses `alpha=0.15`, `beta=0.85`.
Candidate-order tie-breaking, native baseline, zero-alpha identity,
all-candidate evaluation, temperature-1.20 controls, deterministic repeat,
frozen model manifest, and frozen parameters are mandatory. The selected pair
is locked before assessment; `(11,4)` is reported as recovered only when it is
selected without forcing.

The estimand is mean paired per-document NLL delta
`selected_minus_baseline` over 64 assessment documents. Uncertainty is the
fixed 10,000-resample SHA-256-counter bootstrap with seed `20260829`, a 95%
percentile interval, and nearest-rank quantiles. `ReplicationCandidate`
requires mean delta `< 0` and bootstrap upper bound `< 0`; otherwise the
disposition is `NoCandidate`.

## V9 fail-closed corrections

V9 independently recomputes token counts from retained corpus text rather than
trusting a manifest field, rejects duplicate or cross-split paths, rederives
the selected pair and every control from retained aggregate inputs, binds all
provider/model/source/corpus fields and per-document identity digests, rejects
boolean counts, rejects symlinks and mutable ancestors, requires the exact
launch model path, and verifies the Ed25519 review signature over the canonical
receipt payload. Network interception is restored in `finally` blocks, and
temporary ledgers are deleted in `finally` blocks. Review bytes are snapshotted
and digest-bound before any effect.

Any missing custody, stale digest, review failure, provider-attestation
failure, qualification failure, control failure, uncertainty failure, budget
boundary, or scientific failure terminates V9 as `NoCandidate` without
retuning.
