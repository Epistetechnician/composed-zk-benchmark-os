# Gemma3 FineWeb-Edu replication V6 protocol

State slice: `continual-learning-gemma3-fineweb-edu-replication-v6`.

This is a new protocol after the V5 independent static rejection. V1, V2,
V3, V4, and V5 remain rejected or void and are not scientific inputs. V6 is
not an acceptance receipt and does not authorize execution until an
independent reviewer returns `ACCEPT` for this exact byte-frozen packet and
implementation manifest.

## Purpose and claim ceiling

The protocol is a local, offline replication attempt for the one-additional-
iteration recurrence described in [Recirculation, arXiv:2608.17981](https://arxiv.org/abs/2608.17981), using the already cached Gemma3 1B PT BF16 MLX conversion and a fresh, document-disjoint FineWeb-Edu cohort. The paper's reported Gemma3 1B PT pair `(source=11, destination=4)` is an expected replication target, never a forced selection.

The maximum claim is `LocalDevelopmentGemma3FineWebEduReplicationV6`.
No benchmark, production, H100/provider, introspection, training, Evidence
Ledger, or general scientific claim is permitted.

## Fixed custody

- Model path is exactly `/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16`.
- Raw FineWeb-Edu files are the two pinned Parquet objects from revision
  `87f09149ef4734204d70ed1d046ddc9ca3f2b8f9`, with the byte hashes in the
  V6 contract.
- The fresh source uses rows `2048..18431` from each pinned crawl. The prior
  pilot is rows `0..2047`; source IDs are recomputed from the raw Parquet and
  must be disjoint.
- Source, corpus, and result roots are fixed external PrimaryED paths. No
  repository or GiveMeANode path is an input.
- The model manifest binds every expected stable and Hugging Face cache file;
  every other entry, symlink, or symlinked path component fails custody.
- The V1 rejection JSON and V2–V4 protocol/packet records are pinned by exact
  SHA-256 in the contract. Their bytes must remain unchanged. V5 has no
  acceptance receipt and is preserved as a rejected review outcome in this
  protocol history.

## Fixed procedure

1. A reviewer reads exactly the seven V6 files in the packet, recomputes all
   three implementation digests, and returns `ACCEPT` only if all seven
   findings are true. The receipt must bind reviewer identity, canonical UTC
   time, protocol, packet, implementation manifest, and findings.
2. The packer rechecks the receipt, prior history, raw pins, source snapshots,
   and native network denial before creating a no-overwrite external source.
3. The corpus stage loads the fixed tokenizer only after review and input
   snapshots are sealed. It chooses the first 64 eligible 1024-token windows
   independently within each split, round-trips the text, records source and
   text hashes, and validates the exact 128-window manifest.
4. The runner rechecks all custody and snapshots immediately before model load,
   each effect block, validator invocation, and final publication. It uses the
   native macOS network sandbox plus Python-level DNS, socket, process, shell,
   fork, exec, and spawn denials. It does not train or mutate weights.
5. Fit evaluates exactly `CANDIDATE_PAIRS = ((7,2),(9,3),(11,4),(12,5))` at
   `alpha=0.10, beta=0.90`. The minimum fit mean NLL, with lexicographic pair
   tie-break, selects the pair. Assessment uses only the selected pair at
   `alpha=0.15, beta=0.85`.
6. Assessment retains native baseline, zero-alpha parity, every candidate,
   temperature `1.20` baseline/intervention, deterministic repeat, frozen
   model file and parameter digests, and one row per assessment window.
7. The primary estimand is the mean paired per-document NLL delta
   `selected_minus_baseline`. The fixed 10,000-resample SHA-256-counter
   nearest-rank 95% bootstrap is computed without adaptive changes. A
   candidate requires mean `< 0` and upper bound `< 0`; otherwise the result
   is `NoCandidate`.
8. An independent validator recomputes source, corpus, model, parity, all
   candidates, controls, reach evidence, selected pair, assessment metrics,
   parameter custody, per-document deltas, bootstrap, and decision from the
   locked inputs. Any mismatch rejects the result.

## Prohibited actions

No downloads, network access during execution, training, adapter or weight
updates, adaptive tuning, model shopping, assessment before review, reuse of
rejected scientific artifacts, Evidence Ledger mutation, benchmark evidence,
provider calls, production traffic, or claim above the V6 local ceiling.

