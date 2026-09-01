# Gemma3 local recirculation mechanics pilot execution V1

Date: 2026-08-27

State slice: `continual-learning-gemma3-local-pilot-v1`.

Claim ceiling: `LocalDevelopmentGemma3NewsroomRecirculationMechanicsPilot`.

## Execution result

The frozen local pilot completed on the cached pretrained
`gemma-3-1b-pt-bf16` MLX conversion with `network_access=false`,
`training=false`, and `weights_frozen=true`.

- Fit: 2 NEWSROOM documents, one 256-token window each.
- Assessment: 2 different NEWSROOM documents, one 256-token window each.
- Fit-selected pair: `source=7`, `destination=2`, `alpha=0.10`.
- Locked assessment: `source=7`, `destination=2`, `alpha=0.15`,
  `beta=0.85`.
- Paper expected pair `(11,4)`: not recovered; no post-hoc forcing was used.
- Assessment baseline mean NLL: `4.143198529`.
- Assessment recirculation mean NLL: `4.078056749`.
- Selected-minus-baseline mean NLL: `-0.065141780`.
- Assessment baseline perplexity: `63.004019719`.
- Assessment recirculation perplexity: `59.030646940`.
- Selected-minus-baseline perplexity: `-3.973372779`.
- Native/zero-alpha parity: passed on all 4 windows, maximum logit delta
  `0.0` against tolerance `1e-5`.
- Deterministic assessment repeat: passed with maximum metric delta `0.0`.
- PrimaryED and DAed artifact trees: 12 files each, identical SHA-256 maps,
  224 MB each.

## Custody

PrimaryED artifact root:

`/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/continual-learning-gemma3-local-pilot-v1-20260827-r1`

DAed immutable mirror:

`/Volumes/DAed/Archives/composed-zk-benchmark-os/continual-learning-gemma3-local-pilot-v1-20260827-r1`

The retained NEWSROOM input is 234,986,970 bytes with SHA-256:

`ba76df2170e941a9098686b2f241dde487dfcd3169f68b4b26f609f56ed3651c`.

Receipt digests:

- `config.json`: `ceda67312a124362a09119c23e6ce05c074e334e7f459b275403ef0e3481774d`
- `results.json`: `a0e6d12a68ba5c0d7796c19864a19dcbbc9468ed38001f263a41f557c69deb95`
- `receipt.json`: `684f2160c7cf606b4cb9b81c174a0e9a5ae29da5dacd9e3a72e2e5ea8c5e3093`
- `model-manifest.json`: `69f078b42d4521d3e53f0c388a20fa6cf32b4df7ea6535b0eb9da6ccef75c256`
- `corpus-manifest.json`: `8487a3f8f3560cfc09a815baa433cfbad116f113bb9819635f684c2e869803de`
- `input-manifest.json`: `11f203e825265c9bc1d60e2f633de93bd2e7402a37161fb54b438b1bde79925a`

The independent validator returned `valid=true` for both published roots.

## Boundary

This result is a local fixture signal that the declared Gemma3 recurrence ran
and survived custody, parity, aggregate-metric, and repeat checks. It is not
proof that recirculation improves language modeling, not a replication of the
paper's C4 or ten-dataset Gemma3 evaluation, not accepted scientific evidence,
not an Astral result, and not a benchmark, provider, or production claim.

The full paper-aligned lane remains separately gated on the required C4,
arXiv, PG19, and ten-dataset assessment inputs.
