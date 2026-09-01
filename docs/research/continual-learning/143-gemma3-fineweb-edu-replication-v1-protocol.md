# Gemma3 FineWeb-Edu fresh-cohort replication protocol V1

State slice: `continual-learning-gemma3-fineweb-edu-replication-v1`

Status: protocol frozen pending independent review. No fresh assessment
effects are authorized until the review packet receives an explicit accepted
receipt.

## Objective and claim boundary

Replicate the positive bounded FineWeb-Edu `r1` signal on a larger,
document-disjoint cohort using the same cached Gemma3 checkpoint and locked
recirculation intervention. The primary metric is assessment mean NLL,
selected intervention minus untouched baseline; lower is better.

This protocol can produce only a local development replication result. It
cannot establish exact C4 identity, full paper replication, general
recirculation efficacy, benchmark superiority, causal self-modeling,
production readiness, or accepted Evidence Ledger evidence.

## Immutable r1 inputs

The existing `r1` result is preserved without modification:

- Source manifest:
  `9e6311b8a88b879c2b8d102cc1b1d4093312c796633571d00c928738327b33d3`
- Corpus manifest:
  `e06941cd85b4b2c3e75ba0561f9980a63cb74f7c708f30acb80510a4869fee85`
- Configuration:
  `89dc928e78c7b18fc6f1a8a59608dff1e584e1c2b9231890446fb533443725c2`
- Results:
  `151d56568a6c90b3c1b090a3cdb2c571e046abb2f497b87306df27430e472f68`
- Receipt:
  `58764e9dd927eea2f2eb3539a29020f62ec6813bffa8b8a73656f20ac05083da`

The r1 result root remains:

`/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-recirculation-v1`

No r1 file is an input to fresh model effects; only the pinned raw dataset
and cached model identity are reused for custody verification.

## Fresh cohort contract

The fresh cohort is derived from the already-custodied FineWeb-Edu raw shards;
no new download is needed for this protocol.

- Dataset revision:
  `87f09149ef4734204d70ed1d046ddc9ca3f2b8f9`
- Fit shard: `CC-MAIN-2013-20`, source rows `[2048, 18432)`.
- Assessment shard: `CC-MAIN-2024-10`, source rows `[2048, 18432)`.
- The r1 source used rows `[0, 2048)` in each shard, so the fresh source
  ranges are disjoint by source row and document identity.
- The fresh source bundle will retain all normalized text and available
  FineWeb-Edu metadata, with source row indices preserved.
- The staging rule selects the first 64 full 1,024-token windows in each
  fresh range after the fixed cached tokenizer is applied.
- Read-only eligibility audit before protocol freeze found 4,258 eligible
  fit rows and 5,065 eligible assessment rows in the 16,384-row ranges.
- Final staged panel: 64 fit windows and 64 assessment windows, exactly 1,024
  tokens each, with 65,472 next-token targets per split.

The fresh external roots are:

- Source:
  `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-source-v1`
- Corpus:
  `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-corpus-v1`
- Results, immutable `r2`:
  `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-r2`

## Locked intervention

- Model: cached `mlx-community/gemma-3-1b-pt-bf16`.
- The model manifest must remain byte-identical to r1:
  `69f078b42d4521d3e53f0c388a20fa6cf32b4df7ea6535b0eb9da6ccef75c256`.
- Candidate pairs remain exactly `(7,2)`, `(9,3)`, `(11,4)`, and `(12,5)`.
- Fit alpha remains `0.10`.
- Candidate selection is minimum fit mean NLL, with lexicographic pair order
  as the fixed tie-breaker.
- Assessment alpha remains `0.15` and beta remains `0.85`.
- Source-to-destination L2 norm adjustment remains enabled and unchanged.
- Temperature control remains `1.2`.
- Zero-alpha parity, native/MLX parity, deterministic repeat, baseline,
  temperature, and frozen-model controls are mandatory.
- No training, adapter update, weight mutation, network access during model
  execution, provider call, GiveMeANode submission, or Evidence Ledger
  mutation is allowed.

## Reporting and decision rule

The result must retain per-document aggregate rows for baseline, selected
intervention, temperature baseline, temperature selected, and deterministic
repeat. It must report failure cases, excluded records, exact digests, and
the selected pair.

The uncertainty procedure is fixed before effects: paired percentile bootstrap
over the 64 assessment documents, 10,000 resamples, RNG seed `20260829`, and
the 95% interval for the selected-minus-baseline NLL delta. No assessment pair
or threshold may be selected using that interval.

The proposed review gate is: classify as `ReplicationCandidate` only if the
selected-minus-baseline assessment NLL delta is negative and the upper bound
of its locked 95% interval is below zero; otherwise classify as
`NoCandidate`. An independent reviewer must accept this rule before execution.

## Stop conditions

Any failed custody, disjointness, tokenizer, parity, frozen-model, control,
repeatability, review, or validator gate stops the run without adaptive retry.
If the replication is classified `NoCandidate`, this mechanism closes for
this lane and no tuning around the result is permitted.

