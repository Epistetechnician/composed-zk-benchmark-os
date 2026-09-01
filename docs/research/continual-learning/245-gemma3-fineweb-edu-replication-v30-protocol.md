# Gemma3 FineWeb-Edu replication V30 protocol

State slice: `continual-learning-gemma3-fineweb-edu-replication-v30`.

V30 is a fresh, offline local replication attempt for the one-additional-
iteration recurrence in [Recirculation, arXiv:2608.17981](https://arxiv.org/abs/2608.17981).
It uses the exact cached Gemma3 1B PT BF16 MLX conversion and a fresh
FineWeb-Edu cohort. The reported `(source=11, destination=4)` pair is an
expected replication target, never a forced selection. The claim ceiling is
`LocalDevelopmentGemma3FineWebEduReplicationV30`.

V14 became stale during execution and its in-progress result was discarded.
V15 was rejected for publication custody and shared validator measurement.
V16 omitted V15 protocol history. V17 repaired history but failed to make
reach and validator receipt binding hard gates. V18 added those gates but
omitted a final full validation pass. V19 added that pass but incorrectly
described the absence of undocumented V2-V6 rejection receipts as incomplete
history. V23 was rejected because parsed and staged artifacts were not all
stable-read bound. V24 was rejected because hashing and Parquet/model loads
were not descriptor-bound and evidence-ledger mutation was fail-open. V25 was
rejected because the validator CLI could load before review validation and an
existing model snapshot could be writable. V27 was rejected because snapshot
rollback could leave read-only failed trees. V28 was rejected because its
review packet named stale V27 paths and omitted V27 history. V29 was rejected
because the independent response was malformed JSON. V30 is a new identity;
it pins every prior protocol, packet, closure, and failed review as history
and does not treat any rejected artifact as approval or scientific evidence.

No benchmark, production, provider/H100, training, Evidence Ledger,
introspection, self-modeling, or general scientific claim is permitted.

## Fixed custody and data

- Exact model: `/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16`.
- Exact runtime: MLX `0.31.2`, MLX-LM `0.31.3`, PyArrow `24.0.0`.
- Exact raw FineWeb-Edu revision `87f09149ef4734204d70ed1d046ddc9ca3f2b8f9`,
  limited to the two contract-pinned Parquet shards and their pinned bytes.
- Prior pilot rows are `[0,2048)` per shard; discarded V14 rows are
  `[2048,18432)`; V30 uses only `[18432,34816)` per shard, yielding 16,384
  normalized rows per source split. Validators rederive every row and reject
  duplicate or prior document IDs.
- V30 source, corpus, and result roots, raw root, and prior root are exact
  external PrimaryED paths. Symlinks, alternate roots, and alternate model
  paths are rejected.
- The canonical cached checkpoint is never loaded by pathname after custody
  inspection. After review, the runner materializes a byte-identical V30 model
  snapshot at `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v30-model-snapshot`
  through descriptor-bound reads, verifies its complete manifest, marks its
  files and directory read-only, and loads only from that exact snapshot.
  Existing snapshots must match the canonical manifest exactly and have the
  required modes. Any failed snapshot publication first restores deletion
  permissions and then removes both read-only files and directories; cleanup
  failure aborts the phase.

## Gates

1. An independent reviewer reads exactly the seven files in the V30 packet,
   accesses no model or external data, recomputes all packet-bound digests,
   and returns a syntactically valid JSON `ACCEPT` only if every finding is
   true. Any malformed response or rejection produces no receipt.
2. The contract pins every extant V1-V29 protocol, packet, acceptance,
   rejection, and failure record. V2-V6 have no canonical rejection receipt;
   their absence is explicitly checked and no receipt is invented.
3. Source packing and corpus staging validate custody and use transactional
   post-move code/input checks with rollback on mismatch. Snapshot rollback is
   permission-safe and must leave no staging or published tree after failure.
4. Native macOS outbound network denial is proven before model/tokenizer load;
   exact model/cache/runtime/BF16 custody is checked, and every model load
   uses the verified byte-identical external snapshot.
5. Nonzero intervention reach is mandatory. If no fixed candidate changes fit
   NLL, the runner raises and publishes no result; the validator independently
   requires the reach flag to be true.
6. The first validator pass runs without a validator receipt and returns a
   complete validation object. The runner creates the receipt from that exact
   object, binds validity, decision, bootstrap, code snapshot, input snapshot,
   and custody recomputation, then runs the full validator a second time with
   the receipt required. Publication is forbidden unless that second pass
   returns valid and the final post-publication custody check passes.
7. The independent validator has its own local model/evaluation/parity seam;
   it does not import the runner or call runner recurrence/evaluation code.

## Locked recurrence and decision

- Fit candidates are exactly `((7,2),(9,3),(11,4),(12,5))`, alpha `0.10`,
  beta `0.90`; lowest fit mean NLL wins, with listed order as tie-break.
- Assessment uses the selected pair with alpha `0.15`, beta `0.85`, and
  source-to-destination L2 norm adjustment. No post-fit adaptation is allowed.
- Fixed controls are native baseline, zero-alpha identity, all candidates,
  temperature `1.20` baseline/intervention, deterministic repeat,
  frozen file manifest, and frozen parameter digest.
- The primary estimand is paired per-document selected-minus-baseline NLL.
  Uncertainty is the fixed 10,000-resample SHA-256-counter nearest-rank 95%
  bootstrap. Only mean `<0` and upper `<0` yields `ReplicationCandidate`;
  otherwise the result is `NoCandidate`.

Any review, custody, qualification, lock, control, validator, snapshot, or
publication failure discards staging and closes V30 without tuning.
