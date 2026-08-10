# Heterogeneous Natural-Text Residual Replication V21

State slice: `astral-heterogeneous-natural-text-replication-v21`.

Status: `NaturalTextResidualReplicationNoCandidate`. Confirmation:
`NotAuthorized`.
Stage 1: `BlockedByStage0C`.

## Purpose

V20's strongest method was a four-template mean. V21 removes that shortcut by
using heterogeneous repository-owned natural text, document-disjoint splits,
eight wrappers, and a canonical target residual after subtracting a fit-only
wrapper-by-hint mean.

## Sources and split

Extract Markdown prose lines from `docs/**/*.md`, excluding
`docs/research/astral-self-modeling/**`. Keep normalized lines containing 12-50
alphabetic words. An eligible document supplies at least five lines.

Order documents by SHA-256 of seed `2101` plus repository-relative path:

- first 80 documents: fit;
- next 20: tune;
- next 20: sealed assessment.

Take the first five globally unused normalized lines per document in source
order, skipping any document that cannot supply five after de-duplication. No
document, normalized line, or exact prompt may cross splits. Record every
source path and source file hash.

Each line supplies a prefix and two word continuations: the observed next word
and a deterministic same-length-bucket distractor from another fit-frozen
source line. Option order, one of eight wrappers, and hint option are fixed
before target execution.

## Target

The frozen cached Qwen target chooses between single-token ` A` and ` B`.
Measure the ablated-minus-hinted A-versus-B margin effect. Using fit effects
only, freeze the mean effect for each of 16 wrapper-by-hint cells. The canonical
target is raw effect minus that cell mean.

Assessment raw effects and residuals are forbidden before prediction locking.

## Ordinal training

Freeze five residual bins from fit 20/40/60/80 percentiles and their fit
centroids. Qwen and Llama LoRA explainers predict single-token categories
` A`-` E`; numeric predictions are expected frozen centroids.

- seeds `2101`, `2111`, `2131`;
- final eight layers;
- AdamW `1e-4`, batch size 4;
- 160 updates, validation every 20;
- maximum sequence length 224;
- prompt-masked loss;
- final adapters only.

## Qualification

Proceed only if there are exactly 400 fit, 100 tune, and 100 assessment rows
from 120 disjoint documents; repeat error is zero; fit/tune residual standard
deviation is at least `0.05`; every fit bin has at least 15%; tune occupies at
least three bins; all wrapper-by-hint fit cells have at least 10 rows; and the
20-update Qwen smoke test remains below 75% physical memory.

## Controls and gate

Compare trained Qwen ensemble with trained Llama ensemble, best Llama seed,
untrained Qwen, zero residual, fit-only hint mean, and fit-only source-length
bucket mean.

`NaturalTextResidualReplicationCandidate` requires Qwen MSE at least 10% below
every comparator with positive paired-bootstrap lower bounds, every Qwen seed
below zero-residual MSE, Pearson at least 0.40, and calibration slope in
`[0.5,1.5]`. Otherwise classify
`NaturalTextResidualReplicationNoCandidate`.

All predictions are hashed and independently validated before assessment
effects. No V18 result may rescue failure.

## Claim ceiling

The maximum claim is `LocalDevelopmentNaturalTextResidualReplication`. This
study cannot establish activation access, introspection, self-modeling,
faithful explanation, semantic self-knowledge, Stage 0C confirmation, Stage 1
authorization, benchmark evidence, or production readiness.

Execution and disposition are recorded in
[`39-v21-execution-record.md`](39-v21-execution-record.md).
