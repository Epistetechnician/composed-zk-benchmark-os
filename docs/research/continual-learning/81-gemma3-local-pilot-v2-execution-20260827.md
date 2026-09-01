# Gemma3 local recirculation mechanics pilot V2 execution

Date: 2026-08-27

State slice: `continual-learning-gemma3-local-pilot-v2`.

Claim ceiling: `LocalDevelopmentGemma3NewsroomIndependentRecirculationPilot`.

## Execution result

The preregistered fresh-cohort run completed against the cached pretrained
`gemma-3-1b-pt-bf16` MLX conversion with `network_access=false`,
`training=false`, and `weights_frozen=true`.

- Selection offset: skip the first 4 eligible NEWSROOM records used by V1.
- Selected source lines: `6, 7, 8, 10`; V1 used `1, 2, 3, 5`.
- Fit: 2 documents, one 256-token window each.
- Assessment: 2 different documents, one 256-token window each.
- Fit-selected pair: `source=11`, `destination=4`, `alpha=0.10`.
- Locked assessment: `source=11`, `destination=4`, `alpha=0.15`,
  `beta=0.85`.
- Paper expected pair `(11,4)`: recovered in V2 without forcing.
- Assessment baseline mean NLL: `4.045710784`.
- Assessment recirculation mean NLL: `3.702620992`.
- Selected-minus-baseline mean NLL: `-0.343089792`.
- Assessment baseline perplexity: `57.151794199`.
- Assessment recirculation perplexity: `40.553455490`.
- Selected-minus-baseline perplexity: `-16.598338709`.
- Native/zero-alpha parity: passed on all 4 windows, maximum logit delta
  `0.0` against tolerance `1e-5`.
- Deterministic assessment repeat: passed with maximum metric delta `0.0`.
- PrimaryED and DAed artifact trees: 12 files each, identical SHA-256 maps,
  224 MB each.

## Custody

PrimaryED artifact root:

`/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/continual-learning-gemma3-local-pilot-v2-20260827-r1`

DAed immutable mirror:

`/Volumes/DAed/Archives/composed-zk-benchmark-os/continual-learning-gemma3-local-pilot-v2-20260827-r1`

The retained NEWSROOM input is 234,986,970 bytes with SHA-256:

`ba76df2170e941a9098686b2f241dde487dfcd3169f68b4b26f609f56ed3651c`.

Receipt digests:

- `config.json`: `324d560af78a9bc5619e6dc6bc6b30441c34ef5d84165c28be72b3f1f611b50e`
- `results.json`: `11b877b04c4e8f81b50a5741f6f82a0bf6c34bbf3f635b338a04c34e4e4765e0`
- `receipt.json`: `cb30407f7f3e908f38052e633f3d4b30f750bd08253e9efe66cd392b0bf85577`
- `model-manifest.json`: `69f078b42d4521d3e53f0c388a20fa6cf32b4df7ea6535b0eb9da6ccef75c256`
- `corpus-manifest.json`: `49330b11a58f1a58559431c7485d7170c36c42f815cb598e9f514c08cf955615`
- `input-manifest.json`: `bc7139d2f21c2d04d2473a7f8b874ab0dd8213f9fb437add8b7b77d6c445c960`

The independent validator returned `valid=true` for both published roots.

## Interpretation and boundary

V1 and V2 both produced negative held-out NLL deltas, but their selected pairs
were `(7,2)` and `(11,4)` respectively. This is a useful local robustness
signal for the declared mechanism, while showing that pair selection is not
stable on two tiny cohorts. It is not proof of a general recirculation effect,
not a replication of the paper's C4 or ten-dataset Gemma3 evaluation, not
accepted scientific evidence, not an Astral result, and not a benchmark,
provider, or production claim.

The next scientific gate is a larger preregistered disjoint corpus with enough
documents to estimate pair stability before attempting the full paper-shaped
run. The full lane remains blocked on C4 WebText-like and the remaining
paper-shaped panels.
