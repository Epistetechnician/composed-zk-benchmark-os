# Gemma3 FineWeb-Edu replication V15 protocol

State slice: `continual-learning-gemma3-fineweb-edu-replication-v15`.

## Purpose and claim ceiling

V15 is a fresh, offline local replication attempt for the one-additional-
iteration recurrence in [Recirculation, arXiv:2608.17981](https://arxiv.org/abs/2608.17981).
It uses the cached Gemma3 1B PT BF16 MLX conversion and a fresh FineWeb-Edu
cohort. The reported Gemma3 `(source=11, destination=4)` pair is an expected
replication target, never a forced selection. The maximum claim is
`LocalDevelopmentGemma3FineWebEduReplicationV15`.

V14 is preserved as historical context, not as a scientific input. Its
independent `ACCEPT` became stale when implementation bytes changed during the
run; the runner discarded the in-progress result and published nothing. The
V14 stale-review failure is pinned in the V15 custody history. V15 requires a
new independent review of the exact current bytes before any model load or
effect.

No benchmark, production, provider/H100, training, Evidence Ledger,
introspection, self-modeling, or general scientific claim is permitted.

## Fixed custody and fresh disjoint data

- The exact model is
  `/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16`.
- Runtime versions are MLX `0.31.2`, MLX-LM `0.31.3`, and PyArrow `24.0.0`.
- Raw input is restricted to the two pinned FineWeb-Edu Parquet shards at
  revision `87f09149ef4734204d70ed1d046ddc9ca3f2b8f9`. Their exact byte
  lengths and SHA-256 values remain contract-pinned.
- The prior local pilot uses rows `[0,2048)` per shard. The discarded V14
  cohort used `[2048,18432)`. V15 uses only rows `[18432,34816)` per shard,
  producing 16,384 fresh normalized rows per source split. The source validator
  rederives every row from the pinned Parquet and rejects prior or duplicate
  document IDs.
- V15 source, corpus, and result roots are exact external PrimaryED paths.
  Raw input and prior pilot roots are exact pinned external paths. No symlink,
  unsupported file, alternate root, or alternate model path is accepted.
- The V15 contract pins every extant V1–V14 protocol, packet, acceptance,
  rejection, and failure record. V2–V6 have no extant canonical rejection
  receipt and are not invented.

## Review and execution gates

1. An independent reviewer reads exactly the seven files named in the V15
   packet, accesses no model or external data, recomputes the protocol,
   packet, and implementation-manifest digests, and returns `ACCEPT` only when
   all seven packet findings are true. The parent creates no receipt for a
   rejection or missing report.
2. The source packer validates the accepted receipt, pinned Parquet shards,
   prior pilot, complete history, and all input snapshots before publishing a
   no-overwrite external source root. A changed reviewed byte or input stops
   the phase and discards staging.
3. The corpus stage re-tokenizes the first 64 eligible windows in source order
   for each split, round-trips them, and independently requires each window to
   equal the first 1,024 tokenizer IDs of its claimed source row. Canonical
   paths, order, hashes, and exact 1,024-token shape are fail-closed.
4. The macOS native sandbox must deny outbound network before any model or
   tokenizer load. Python guards deny DNS, socket sends, file-descriptor
   transfer, every available process-launch surface, fork, and startfile.
   Model stable/cache manifests and runtime versions are checked exactly.
   BF16 parameter custody recognizes the qualified `mlx.core.bfloat16` dtype,
   converts only a materialized copy to float32 for digest serialization, and
   retains the original dtype tag without modifying model weights.
5. Review metadata is kept separate from the canonical code snapshot. The
   runner snapshots protocol, packet, receipt, implementation, and V1–V14
   history and rechecks them before and after every gate, including the
   independent validator. Any change invalidates the run.

## Locked recurrence and estimand

- Fit evaluates exactly `((7,2),(9,3),(11,4),(12,5))` with alpha `0.10` and
  beta `0.90`. The minimum fit mean NLL selects the pair; ties use the listed
  lexicographic order.
- Assessment evaluates the selected pair with alpha `0.15`, beta `0.85`, and
  source-to-destination L2 norm adjustment. No candidate, layer, alpha, beta,
  split, or control is changed after fit selection.
- Controls are native baseline, zero-alpha identity, all candidate evaluations,
  temperature `1.20` baseline/intervention, deterministic repeat, frozen model
  file manifest, and frozen model parameter digest. Controls cannot win the
  primary decision.
- The primary statistic is paired per-document NLL delta
  `selected_minus_baseline`, retained in canonical assessment order. The
  uncertainty rule is a 10,000-resample SHA-256-counter nearest-rank 95%
  bootstrap with the fixed contract seed. Only mean `< 0` and upper `< 0`
  yields `ReplicationCandidate`; otherwise the result is `NoCandidate`.
- The independent validator rederives custody, windows, parity, all candidate
  metrics, locked assessment, controls, model parameter identity, per-document
  provenance, bootstrap, and decision in a separate process. Publication is
  allowed only after it returns a valid receipt and all post-validator custody
  checks pass.

## Prohibited actions and terminal handling

V15 permits no downloads, network during execution, training, adapter or
weight updates, model shopping, adaptive tuning, prior scientific-artifact
reuse as data, Evidence Ledger mutation, benchmark evidence, provider calls,
production traffic, or claims above the V15 ceiling. Any custody, review,
qualification, lock, control, validator, snapshot, or publication failure
discards staging and terminates the V15 attempt. A `NoCandidate` result is
reported without tuning around it.
