# Gemma3 FineWeb-Edu replication V14 protocol

State slice: `continual-learning-gemma3-fineweb-edu-replication-v14`.

V14 is a fresh protocol after V13 reached its approved pre-effect execution
gate but stopped because the runtime reports BF16 as `mlx.core.bfloat16`,
which bypassed V13's literal `bfloat16` check and triggered MLX's known NumPy
buffer mismatch. V12 was rejected because its historical custody set omitted
the V1 protocol and packet and did not pin the absent early-review status as an
explicit boundary. V11 reached its approved pre-effect execution gate but
stopped in the same parameter-custody path. V7 remains independently accepted
but exposed a prior-manifest pin bug at execution. V8 corrected that bug but
was rejected for incomplete process-launch denial. V9 closed that denial but
was rejected because enriched review metadata was passed to an exact snapshot
comparator. V10 corrected the comparator but was rejected because corpus
windows were not independently rederived as source-row prefixes and the
assessment bootstrap accepted arbitrary row order. V13's pre-effect failure is
now preserved as a canonical record. V14 pins every extant V1-V13 protocol,
packet, acceptance, rejection, and pre-effect failure record. No undocumented
V2-V6 rejection receipt is invented; their extant protocol/packet records are
the complete custody records available. None is a V14 scientific input. V14
requires a new clean independent `ACCEPT` before execution.

## Purpose and claim ceiling

This is a local offline replication attempt for the one-additional-iteration
recurrence in [Recirculation, arXiv:2608.17981](https://arxiv.org/abs/2608.17981),
using the cached Gemma3 1B PT BF16 MLX conversion and a fresh FineWeb-Edu
cohort. The reported Gemma3 pair `(source=11, destination=4)` is an expected
replication target, not a forced outcome. The ceiling is
`LocalDevelopmentGemma3FineWebEduReplicationV14`.

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
- Every extant V1 through V13 protocol, packet, acceptance, rejection, and
  pre-effect failure record is pinned by exact SHA-256 in the V14 contract.
  V2-V6 have no canonical rejection receipt files in the worktree; V14 does
  not synthesize them or treat absent records as approvals. All pinned records
  are custody history only; no prior result is a V14 scientific input.

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
   independently requires each retained window's token IDs to equal the first
   1024 token IDs of its claimed raw source row. Manifest paths must be the
   unique canonical split paths, and the manifest must equal that sequence.
4. The native macOS sandbox is mandatory. The Python guard denies DNS, socket
   outbound methods, `sendfile`, shell, every available callable `os.exec*`
   and `os.spawn*` variant, `posix_spawn*`, fork, forkpty, and startfile
   surface. Model loading occurs only after exact stable/cache manifest and
   runtime checks.
   The parameter digest recognizes the fully qualified MLX BF16 dtype and
   canonicalizes those leaves through an exact float32 representation while
   retaining the original dtype tag, so custody checks remain executable on
   this runtime without changing model weights.
5. Review metadata is carried separately from the canonical code snapshot;
   snapshot comparison projects only the exact protocol, packet, receipt,
   implementation, and history fields. An enriched review snapshot must not
   make a valid run fail or silently weaken the comparison.
6. Fit evaluates exactly `((7,2),(9,3),(11,4),(12,5))` at `(0.10,0.90)`;
   minimum fit mean NLL and lexicographic pair order select the pair.
   Assessment uses the selected pair at `(0.15,0.85)`, with source-to-
   destination L2 norm adjustment.
7. The result retains native baseline, zero-alpha parity, all candidates,
   temperature 1.20 controls, deterministic repeat, frozen file and
   parameter digests, and one provenance-bound row per assessment window in
   the canonical corpus order. Every metric/control row and the retained
   per-document delta list is independently required to use that order before
   the index-seeded bootstrap runs.
8. The exact paired per-document NLL delta uses a 10,000-resample
   SHA-256-counter nearest-rank 95% bootstrap. Only mean `<0` and upper `<0`
   yields `ReplicationCandidate`; otherwise the outcome is `NoCandidate`.
9. The independent validator recomputes the tokenizer window sequence, model
   effects, controls, reach evidence, selection, metrics, parameter custody,
   per-document rows, uncertainty, and decision. Any mismatch rejects.

## Prohibited actions

No downloads, network during execution, training, adapter/weight updates,
adaptive tuning, model shopping, assessment before review, rejected-artifact
reuse as scientific input, Evidence Ledger mutation, benchmark evidence,
provider calls, production traffic, or claim above the V14 local ceiling.
