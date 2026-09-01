# Gemma3 FineWeb-Edu replication V9 protocol

State slice: `continual-learning-gemma3-fineweb-edu-replication-v9`.

V9 is a fresh protocol after V8's independent review rejected the incomplete
Python process-launch denial. V7 remains independently accepted but exposed a
prior-manifest pin bug at execution. V8 corrected that bug but remains
rejected. V7 and V8 records are preserved as historical records and are not
scientific inputs. V9 requires a new clean independent `ACCEPT` before any
execution.

## Purpose and claim ceiling

This is a local offline replication attempt for the one-additional-iteration
recurrence in [Recirculation, arXiv:2608.17981](https://arxiv.org/abs/2608.17981),
using the cached Gemma3 1B PT BF16 MLX conversion and a fresh FineWeb-Edu
cohort. The reported Gemma3 pair `(source=11, destination=4)` is an expected
replication target, not a forced outcome. The ceiling is
`LocalDevelopmentGemma3FineWebEduReplicationV9`.

No benchmark, production, provider/H100, training, Evidence Ledger,
introspection, or general scientific claim is permitted.

## Fixed inputs and history

- The exact model path is `/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16`.
- Raw FineWeb-Edu is the two pinned Parquet files from revision
  `87f09149ef4734204d70ed1d046ddc9ca3f2b8f9`, with contract-pinned byte
  hashes, and no alternate source is allowed.
- Fresh source rows are `[2048,18432)` from each pinned crawl. The prior pilot
  is `[0,2048)` and all fresh document records are rederived from raw Parquet
  and checked against prior IDs.
- Source, corpus, and result roots are exact external PrimaryED paths. The
  model manifest covers every expected stable and Hugging Face cache file;
  unsupported entries and all symlinked components fail.
- V1 through V8 protocol and review history is pinned. The V7 acceptance and
  V8 rejection are custody records only; no prior result is a V9 scientific
  input.

## Frozen execution

1. The reviewer reads exactly the seven files listed in the packet, performs
   no mutation or model/data access, recomputes all three digests, and emits a
   canonical `ACCEPT` only when all seven findings are true.
2. The packer revalidates the receipt, history, raw Parquet, prior pilot, and
   snapshots before producing a no-overwrite external source. The prior
   manifest pin is checked against its recorded `manifest_sha256` field after
   independently validating that field's self-digest.
3. Before loading any tokenizer, the runner seals the complete source/corpus/
   raw/prior/model snapshot. It then chooses the first 64 eligible 1024-token
   windows in source order per split, re-tokenizes and round-trips them, and
   requires the corpus manifest to equal that independently derived sequence.
4. The native macOS sandbox is mandatory. The Python guard denies DNS, socket
   outbound methods, `sendfile`, shell, every available callable `os.exec*`
   and `os.spawn*` variant, `posix_spawn*`, fork, forkpty, and startfile
   surface. Model loading occurs only after exact stable/cache manifest and
   runtime checks.
5. Fit evaluates exactly `((7,2),(9,3),(11,4),(12,5))` at `(0.10,0.90)`;
   minimum fit mean NLL and lexicographic pair order select the pair.
   Assessment uses the selected pair at `(0.15,0.85)`, with source-to-
   destination L2 norm adjustment.
6. The result retains native baseline, zero-alpha parity, all candidates,
   temperature 1.20 controls, deterministic repeat, frozen file and
   parameter digests, and one provenance-bound row per assessment window.
7. The exact paired per-document NLL delta uses a 10,000-resample
   SHA-256-counter nearest-rank 95% bootstrap. Only mean `<0` and upper `<0`
   yields `ReplicationCandidate`; otherwise the outcome is `NoCandidate`.
8. The independent validator recomputes the tokenizer window sequence, model
   effects, controls, reach evidence, selection, metrics, parameter custody,
   per-document rows, uncertainty, and decision. Any mismatch rejects.

## Prohibited actions

No downloads, network during execution, training, adapter/weight updates,
adaptive tuning, model shopping, assessment before review, rejected-artifact
reuse as scientific input, Evidence Ledger mutation, benchmark evidence,
provider calls, production traffic, or claim above the V9 local ceiling.
