# Adaptive verification with reversible adapters v2

Date: 2026-08-28.

State slice: `continual-learning-adaptive-verification-reversible-adapter-v2`.

Status: `ProtocolDraft / ModelExecutionClosedPendingIndependentReview`.

## Purpose and claim boundary

This is a new control-plane state slice. V1 is immutable and rejected; this
document does not amend V1. Astral V48, Stage 0C, Stage 1, V82, and all prior
Astral causal-target artifacts are excluded.

The falsifiable theory is:

> For one frozen causal language model and a fixed reversible-LoRA training
> budget, selecting one fixed-length update window per fit document using a
> predeclared frozen-base surprisal-plus-novelty score can improve document-
> averaged held-out language-model loss over fixed first-window selection.

This is a model-controller hypothesis. The score is a measurable selection
rule, not semantic truth, epistemic access, verification proof, or evidence of
introspection.

## Exact actor, runtime, and training contract

The only eligible actor is the cached Gemma 3 text model:

```yaml
actor: google/gemma-3-1b-pt
model_path: /Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16
model_type: gemma3_text
layer_count: 26
hidden_size: 1152
dtype: bfloat16
base_weights: frozen
adapter: LoRA
lora_rank: 8
lora_dropout: 0.0
lora_scale: 20.0
trainable_layers: 8
optimizer: adamw
learning_rate: 0.0001
batch_size: 2
gradient_accumulation_steps: 1
iterations: 16
max_sequence_length: 256
mask_prompt: true
save_every: 16
```

The LoRA rank, dropout, and scale are the MLX-LM `0.31.3` defaults and are
also written explicitly into the sealed configuration. The exact command is:

```text
python -m experiments.continual_learning.safe_mlx_lora --model MODEL --train --data DATA --fine-tune-type lora --optimizer adamw --mask-prompt --num-layers 8 --batch-size 2 --iters 16 --learning-rate 0.0001 --steps-per-report 16 --steps-per-eval 16 --val-batches -1 --max-seq-length 256 --adapter-path ADAPTER --save-every 16 --seed SEED
```

`safe_mlx_lora` is invoked only with `HF_HUB_OFFLINE=1` and
`TRANSFORMERS_OFFLINE=1`. The implementation contract must record the exact
Python executable, MLX `0.31.2`, MLX-LM `0.31.3`, source digests, model-file
manifest digest, configuration digest, and command digest. No base-weight
update, adapter merge, model download, network access, or remote judge is
permitted.

## Fresh corpus and exact split

The acquisition script downloads these 24 Project Gutenberg text sources into a
new external root named by this state slice. It writes raw bytes, normalized
UTF-8 text, source URL, response metadata, and SHA-256 digests. Existing
Gutenberg, Gemma, recirculation, V39--V48, and Astral artifacts are not inputs.

| Split | Gutenberg IDs |
|---|---|
| fit | `1342, 2701, 2554, 84, 1661, 16328, 11, 1727, 43, 1513, 100, 345` |
| tune | `46, 76, 1260, 1232, 5200, 98` |
| assessment | `1400, 215, 209, 16, 35, 36` |

The source URL for ID `N` is exactly
`https://www.gutenberg.org/cache/epub/N/pgN.txt`. The acquisition timestamp
and HTTP response headers are metadata only; the bytes and normalized text
digests define identity.

Normalization is exact: decode UTF-8 with strict errors; normalize CRLF and
CR to LF; apply Unicode NFKC; remove the first Project Gutenberg start marker
through its following newline when present; remove the final Project
Gutenberg end marker and preceding whitespace when present; strip leading and
trailing whitespace; append exactly one LF. No sentence rewriting, spelling
repair, deduplication, or model-generated cleaning is allowed.

The runner tokenizes normalized text with the actor tokenizer using
`add_special_tokens=False`. It takes non-overlapping 256-token windows from
each document starting at token offsets `0, 256, 512, ...`, retains the first
two windows with at least 224 tokens, and pads no window. Exactly two windows
per document are required. Thus fit has 24 windows, tune has 12, and
assessment has 12. Windows never cross document boundaries.

## Fixed reliability cases

The same sealed split is run for four training seeds crossed with two document
orders:

```yaml
training_seeds: [20260901, 20260902, 20260903, 20260904]
order_seeds: [6101, 6102]
```

For each case, fit-document order is the stable sort of the 12 fit document
IDs by SHA-256 of `610X|document_id|fit-order`; ties sort by numeric ID. Tune
and assessment order is manifest order. These eight cases are repeated model
and order reliability measurements, not eight independent corpora.

## Exact selection score and arms

For each fit document `d` with windows `w0` and `w1`:

1. Frozen-base surprisal `nll(w)` is the arithmetic mean negative log
   probability over target tokens `1..len(tokens)-1`, evaluated in float64
   from the frozen native logits at temperature `1.0`.
2. Let `V(w)` be the set of tokens matched by Python regular expression
   `[^\\W_]+(?:'[^\\W_]+)?` after Unicode `casefold()`. Let `V_other(w)` be
   the union of `V` from all other fit windows. Lexical novelty is
   `novelty(w) = 1 - |V(w) intersection V_other(w)| / max(|V(w)|, 1)`.
3. Within each document, min-max normalize the two values separately:
   `norm(x0,x1) = 0.5` for both entries if `x0 == x1`; otherwise
   `(x - min(x0,x1)) / (max(x0,x1)-min(x0,x1))`.
4. The fixed score is
   `score(w) = 0.75 * norm(nll(w0), nll(w1)) + 0.25 * norm(novelty(w0), novelty(w1))`.
5. The adaptive arm selects the window with the greater score. Exact ties
   select lower `window_ordinal`, then lower `text_sha256`.

The primary arm panel is:

- `fixed_cadence`: select ordinal `0` in every fit document;
- `adaptive_verification`: select the exact score winner above.

Controls use the same one-window-per-document budget and exact tie rule:

- `shuffled_score`: permute the two score values within each document with
  `random.Random(20260908)` before selection;
- `constant_score`: set both scores to `0.5`, which resolves to ordinal `0`;
- `text_only_novelty`: use novelty weight `1.0` and NLL weight `0.0`;
- `surprisal_only`: use NLL weight `1.0` and novelty weight `0.0`;
- `matched_energy`: select the fixed arm with the same six documents and
  exactly the same two-window token lengths.

All arms compute the frozen-base score components. Only the named selection
function differs. The runner records selected IDs, rejected IDs, score
vectors, token counts, and selection digests before any adapter training.

## Estimand, aggregation, and thresholds

For assessment document `d` in reliability case `c`, let `L0(c,d)` be the
frozen-base mean NLL, `Lf(c,d)` the fixed-adapter NLL, and `La(c,d)` the
adaptive-adapter NLL. Define the paired document effect:

`D(c,d) = (L0(c,d) - La(c,d)) - (L0(c,d) - Lf(c,d))`.

For each document, average over the eight fixed cases:

`D(d) = mean_c D(c,d)`.

The single primary estimand is the equal-document mean over the six assessment
documents:

`Delta_adaptive = mean_d D(d)`.

Tokens are used only inside each document's NLL. Documents have equal weight;
there is no token-weighted or case-weighted alternative primary estimand.

The bounded result gate requires all of:

- `Delta_adaptive >= 0.020` NLL per token;
- the lower endpoint of the deterministic 10,000-resample document bootstrap
  95% percentile interval is at least `0.000`;
- adaptive wins on at least four of six assessment documents;
- no arm's assessment NLL exceeds its own frozen-base NLL by more than 5%;
- protected fit-window NLL degradation is no worse than 5% for either primary
  arm;
- all custody, repeatability, equal-compute, and validator gates pass.

A positive subthreshold effect is `DevelopmentNoCandidate`.

## Uncertainty, missingness, multiplicity, and reliability

The validator performs the bootstrap exactly as follows. For each replicate,
seed a local `random.Random(20260908 + replicate)`; sample six assessment
document IDs with replacement; take the arithmetic mean of the sampled `D(d)`
values; and store the result. The 2,500th and 9,750th sorted values are the
95% percentile endpoints. No studentization, smoothing, imputation, or
subgroup correction is used.

The sole confirmatory comparison is adaptive versus fixed. All controls are
descriptive falsifiers. Missing document/case scores, non-finite NLL, failed
subprocesses, missing adapter files, or incomplete windows invalidate the
campaign; no missing value is imputed. Repeated cases are retained only to
measure reliability and are never treated as new documents.

Reliability gates are fixed before assessment:

- repeated native frozen-base NLL maximum absolute difference `<= 1e-8`;
- per-document fixed/adaptive repeated-case score completeness `8/8`;
- every adapter reload produces the same aggregate NLL within `1e-6`;
- all primary arms have identical selected-window count and training command
  except for data-selection digest and seed;
- no assessment document appears in fit or tune manifests.

## Power calibration

Power is a calibration statement for the predeclared estimator, not a claim
about the model. Before assessment, the independent validator runs exactly
10,000 simulations with:

```yaml
document_count: 6
case_count: 8
true_effect_under_alternative: 0.020
document_random_effect_sd: 0.015
case_random_effect_sd: 0.004
within_document_case_sd: 0.010
null_effect: 0.000
bootstrap_replicates: 1000
simulation_seed: 20260908
```

Each simulated `D(c,d)` equals the declared effect plus an independent
document random effect, an independent case random effect, and an independent
within-document case residual. For each simulation, document means are formed
over eight cases and the same six-document bootstrap gate is applied. The
calibration must show alternative rejection probability `>= 0.80` and null
rejection probability `<= 0.05`. A failure closes the slice before model
assessment; thresholds and sample counts cannot change.

## Custody, privacy, and validator contract

The external root layout is fixed:

```text
ROOT/
  contract.json
  source-manifest.json
  corpus-manifest.json
  fit-tune-lock.json
  cases/<case-id>/selection.json
  cases/<case-id>/adapters/<arm>/adapters.safetensors
  cases/<case-id>/aggregates.json
  aggregate-result.json
  validator-receipt.json
```

`ROOT` must be absolute, outside the repository, absent before creation, and
on the registered research artifact volume. Every file is write-once. The
source and adapter files remain external and are not copied into Git. Raw
texts, token IDs, logits, activations, and training logs are deleted after
independent validation under the recorded retention deadline; only digests,
aggregate NLLs, selected IDs, gate booleans, and validator receipts remain.

The validator is a separate process and source file. It independently checks
the source manifest, normalized text digests, split membership, two-window
shape, selection equations, command equality, model/runtime digests, case
completeness, prediction-lock ordering, NLL aggregation, bootstrap indices,
power-calibration results, privacy fields, and result digests. It must not
import runner metric functions or read raw text, token IDs, logits, or adapter
tensors when validating the aggregate result.

## Prediction lock and event order

The event order is immutable:

1. acquire and digest sources;
2. build and digest all windows and split manifests;
3. load the frozen model and compute native qualification;
4. compute all selection scores and controls;
5. run the power calibration;
6. write and digest `fit-tune-lock.json` with
   `assessment_started: false`;
7. train primary and control adapters only from locked fit selections;
8. compute fit/tune aggregates and digest predictions;
9. obtain independent pre-assessment review of the configuration and lock;
10. set `assessment_started: true` in a new append-only event and compute
    assessment aggregates;
11. run the independent aggregate validator;
12. perform the documented raw-artifact retention cleanup.

The assessment runner refuses to run if the lock digest, configuration digest,
review receipt, or event sequence is missing or changed.

## H100/GiveMeANode equivalence boundary

GiveMeANode/H100 use is optional and is not implied by this protocol. If used,
the provider receipt must bind the same source commit, runner and validator
digests, model manifest, corpus manifest, contract, container image digest,
CUDA version, driver version, Python/MLX/MLX-LM versions, environment flags,
command arrays, output root, and teardown time. It may provide more repetitions
of the eight declared cases only. It may not change the actor, training
contract, score formula, corpus, split, thresholds, controls, or estimator.
Provider identity and hardware are provenance fields, not scientific
covariates and not evidence of a positive result.

## Review, authorization, and stop rules

An independent reviewer must first accept this frozen protocol. Acceptance
permits implementation-contract drafting only. A separate implementation
authorization must then name actor, runtime, access operator, corpus root,
runner, validator, output root, and claim ceiling. Qualification runs next and
stops on any custody, parity, repeatability, shape, adapter, or nonzero-reach
failure. No adaptive repair is allowed.

After fit/tune, a second independent reviewer checks the configuration digest,
selection lock, event ordering, and retention fields. Assessment opens only
after that receipt. A failed assessment gate closes the slice as
`DevelopmentNoCandidate`; it does not authorize retuning.

Permitted classifications are:

- `InstrumentFeasibility`: qualification passes and assessment remains closed;
- `DevelopmentNoCandidate`: assessment runs but the primary or hard guards
  fail;
- `BoundedAdaptiveVerificationResult`: every declared scientific, control,
  custody, uncertainty, and validator gate passes.

The maximum claim is
`LocalDevelopmentAdaptiveVerificationReversibleAdapterV2`. No outcome under
this slice establishes general continual learning, transformer-wide transfer,
cryptographic verification, Astral evidence, introspection, causal
self-modeling, Stage 0C, Stage 1, benchmark superiority, or production
readiness.
