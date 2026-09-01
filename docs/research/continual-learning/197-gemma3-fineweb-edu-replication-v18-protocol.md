# Gemma3 FineWeb-Edu replication V18 protocol

State slice: `continual-learning-gemma3-fineweb-edu-replication-v18`.

V18 is a fresh, offline local replication attempt for the one-additional-
iteration recurrence in [Recirculation, arXiv:2608.17981](https://arxiv.org/abs/2608.17981).
It uses the exact cached Gemma3 1B PT BF16 MLX conversion and a fresh
FineWeb-Edu cohort. The reported `(source=11, destination=4)` pair is an
expected replication target, never a forced selection. The claim ceiling is
`LocalDevelopmentGemma3FineWebEduReplicationV18`.

V14 became stale during execution and its in-progress result was discarded.
V15 was rejected for publication custody and shared validator measurement.
V16 corrected those defects but omitted the V15 protocol and packet from its
history. V17 corrected the history but was rejected because failed
intervention reach did not close the publication gate and because the
validator receipt was authored before validation without binding the returned
validation object. V18 is a new identity and pins complete V1–V17 history.
No prior scientific artifact is an input.

No benchmark, production, provider/H100, training, Evidence Ledger,
introspection, self-modeling, or general scientific claim is permitted.

## Fixed custody and data

- Exact model: `/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16`.
- Exact runtime: MLX `0.31.2`, MLX-LM `0.31.3`, PyArrow `24.0.0`.
- Exact raw FineWeb-Edu revision `87f09149ef4734204d70ed1d046ddc9ca3f2b8f9`,
  limited to the two contract-pinned Parquet shards and their pinned bytes.
- Prior pilot rows are `[0,2048)` per shard; discarded V14 rows are
  `[2048,18432)`; V18 uses only `[18432,34816)` per shard, yielding 16,384
  normalized rows per source split. Validators rederive every row and reject
  duplicate or prior document IDs.
- V18 source, corpus, and result roots, raw root, and prior root are exact
  external PrimaryED paths. Symlinks, alternate roots, and alternate model
  paths are rejected.

## Gates

1. An independent reviewer reads exactly the seven files in the V18 packet,
   accesses no model or external data, recomputes all packet-bound digests,
   and returns a syntactically valid `ACCEPT` only if every finding is true.
   A rejection or malformed report produces no receipt.
2. Source packing validates the accepted receipt, pinned shards, prior pilot,
   and complete history. Transactional publication performs a final code and
   input snapshot after moving bytes; mismatch rolls back the new root.
3. Corpus staging round-trips the first 64 eligible 1,024-token windows per
   split, validates source-row prefixes, and uses the same transactional
   publication check.
4. Native macOS outbound network denial is proven before loading any model or
   tokenizer. Python guards deny DNS, socket sends, descriptor transfer,
   process launch, fork, and startfile. Exact model/cache manifests, runtime
   versions, BF16 parameter tags, and materialized digest conversion are
   checked.
5. Nonzero intervention reach is a hard qualification gate. If no fixed
   candidate changes fit NLL, the runner raises and publishes no result; the
   validator independently requires the reach flag to be true.
6. The validator first recomputes the result without a validator receipt. The
   runner then creates a receipt from the exact returned validation object,
   including its validity, decision, bootstrap, code snapshot, input snapshot,
   and custody recomputation digest. A final validator pass requires this
   receipt and checks its self-digest and exact binding.
7. The independent validator runs a separate local measurement implementation;
   it does not import the runner or call runner recurrence, parity, or
   evaluation functions. It rederives all candidates, controls, model
   parameters, provenance, bootstrap, and decision.

## Locked recurrence and decision

- Fit candidates are exactly `((7,2),(9,3),(11,4),(12,5))`, alpha `0.10`,
  beta `0.90`; lowest fit mean NLL wins, with listed order as tie-break.
- Assessment uses the selected pair with alpha `0.15`, beta `0.85`, and
  source-to-destination L2 norm adjustment. No post-fit adaptation is allowed.
- Fixed controls are native baseline, zero-alpha identity, all candidates,
  temperature `1.20` baseline/intervention, deterministic repeat, frozen file
  manifest, and frozen parameter digest.
- The primary estimand is paired per-document selected-minus-baseline NLL.
  Uncertainty is the fixed 10,000-resample SHA-256-counter nearest-rank 95%
  bootstrap. Only mean `<0` and upper `<0` yields `ReplicationCandidate`;
  otherwise the result is `NoCandidate`.

Any review, custody, qualification, lock, control, validator, snapshot, or
publication failure discards staging and closes V18 without tuning.
