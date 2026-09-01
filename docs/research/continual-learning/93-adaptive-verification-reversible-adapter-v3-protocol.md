# Adaptive verification with reversible adapters v3

Date: 2026-08-28.

State slice: `continual-learning-adaptive-verification-reversible-adapter-v3`.

Status: `ProtocolDraft / ModelExecutionClosedPendingIndependentReview`.

## New identity and claim boundary

This is a new state slice. V1 and V2 are immutable protocol rejections and
are not amended. Astral V48, Stage 0C, Stage 1, V82, and every prior Astral
causal-target, activation, adapter, corpus, and result artifact are excluded.

The single falsifiable theory is:

> With one frozen causal language model, one reversible LoRA adapter, a fixed
> training budget, and document-disjoint Project Gutenberg data, selecting one
> update window per fit document by a predeclared frozen-base surprisal-plus-
> lexical-novelty score produces lower held-out language-model loss than
> selecting the first window in each document.

This is bounded controller evidence if it passes. The score is a measurable
selection rule, not semantic evidence, proof, epistemic access, or an Astral
result.

## Exact actor and runtime contract

The only model actor is the already-cached MLX BF16 Gemma 3 text checkpoint:

```yaml
actor: google/gemma-3-1b-pt
model_path: /Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16
model_type: gemma3_text
layer_count: 26
hidden_size: 1152
dtype: bfloat16
base_weights: frozen
runtime: mlx-0.31.2
mlx_lm: 0.31.3
python: 3.14.5
tokenizer_policy: model-config-bound-v1
```

The runner reads `config.json` before loading weights and rejects any model
whose declared model type, layer count, hidden size, or dtype differs. The
implementation contract records the SHA-256 of every stable model file,
`config.json`, tokenizer files, runner, validator, acquisition script, Python
executable, runtime packages, and command arrays.

The adapter contract is fixed:

```yaml
fine_tune_type: lora
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
mask_prompt: false
save_every: 16
```

The rank, dropout, and scale are supplied in the sealed MLX-LM configuration
file rather than left to an implicit library default. Training data use only
the MLX-LM `text` feature. Each JSONL row is exactly `{"text": STRING}`;
`prompt`, `completion`, chat templates, and prompt masking are forbidden. The
string is the tokenizer decode of exactly 256 token IDs, and the runner rejects
the row unless re-encoding with `add_special_tokens=False` returns the same 256
IDs. The train, valid, and test files contain the selected fit windows only;
custom NLL evaluation, not MLX-LM test output, produces scientific metrics.

The exact training command is the following, with absolute paths substituted
for the uppercase variables and with the sealed YAML configuration digest:

```text
python -m experiments.continual_learning.safe_mlx_lora --model MODEL --train --data DATA --fine-tune-type lora --optimizer adamw --num-layers 8 --batch-size 2 --iters 16 --learning-rate 0.0001 --steps-per-report 16 --steps-per-eval 16 --val-batches -1 --max-seq-length 256 --adapter-path ADAPTER --save-every 16 --seed SEED --config CONFIG
```

Model execution must set `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, and
`TOKENIZERS_PARALLELISM=false`. The runner installs a fail-closed socket guard
that raises on any network connect attempt during model loading, scoring, or
training. No base-weight update, adapter merge, remote judge, or model
download is permitted.

## Fresh corpus and exact window construction

The acquisition script creates a new external root for this state slice and
downloads exactly these Project Gutenberg sources:

| Split | IDs |
|---|---|
| fit | `1342, 2701, 2554, 84, 1661, 16328, 11, 1727, 43, 1513, 100, 345` |
| tune | `46, 76, 1260, 1232, 5200, 98` |
| assessment | `1400, 215, 209, 16, 35, 36` |

For numeric ID `N`, the only source URL is
`https://www.gutenberg.org/cache/epub/N/pgN.txt`. The source manifest records
URL, HTTP status, content type, raw byte length, raw SHA-256, normalized byte
length, normalized SHA-256, acquisition timestamp, and the state slice.

Normalization is deterministic and exact: strict UTF-8 decode; CRLF/CR to LF;
Unicode NFKC; remove the first `*** START OF THE PROJECT GUTENBERG EBOOK` line
and its preceding text when present; remove the final `*** END OF THE PROJECT
GUTENBERG EBOOK` line and following text when present; strip leading/trailing
whitespace; append one LF. No generated cleaning, sentence splitting,
deduplication, or spelling correction is allowed.

The runner tokenizes normalized text with the bound actor tokenizer and takes
the first two non-overlapping windows at token offsets `0` and `256`. Every
document must have at least 512 tokens and both windows must re-encode to
exactly 256 IDs. The split therefore contains 24 fit windows, 12 tune windows,
and 12 assessment windows. A document contributes exactly two windows and no
window crosses a document boundary. The source validator reads normalized
files before retention cleanup and recomputes their digests; the aggregate
validator later validates only the retained manifests and digests.

## Fixed reliability cases

The sealed case panel is four training seeds crossed with two order seeds:

```yaml
training_seeds: [20260901, 20260902, 20260903, 20260904]
order_seeds: [6101, 6102]
```

For order seed `o` and numeric document ID `d`, the fit order key is exactly
the lowercase hexadecimal SHA-256 of UTF-8 bytes for
`fit-order-v3|o|d`. Documents sort by that key and then numeric ID. The case
identity is `seed-S|order-O`; the case set has exactly eight entries. Tune and
assessment document order is ascending numeric ID. Repeated cases estimate
runtime and adapter reliability; they are not counted as new documents.

## Exact selection functions

Every fit document has windows `w0` and `w1`, and every arm selects exactly one
window from each of the 12 fit documents. Thus every arm trains on exactly 12
windows and exactly 3,072 source tokens.

For a 256-token window `w`, frozen-base surprisal is:

`nll(w) = -(1/255) * sum(i=1..255) log_softmax(logits(w)[i-1])[tokens(w)[i]]`.

All arithmetic after logits is IEEE-754 binary64. Lexical vocabulary is the
set of matches from Python's Unicode regular expression
`[^\\W_]+(?:'[^\\W_]+)?` applied to `casefold()` text. For a window `w` in
document `d`, `V_other(w)` is the union of vocabulary sets from every other fit
window, and:

`novelty(w) = 1 - |V(w) intersection V_other(w)| / max(|V(w)|, 1)`.

For the two values `x0` and `x1` in one document, min-max normalization returns
`0.5` for both when `x0 == x1`; otherwise it returns
`(x-min(x0,x1))/(max(x0,x1)-min(x0,x1))`. The adaptive score is:

`score(w) = 0.75 * norm(nll(w0), nll(w1)) + 0.25 * norm(novelty(w0), novelty(w1))`.

The adaptive arm selects the larger score; exact ties select lower ordinal and
then lower lowercase `text_sha256`.

The fixed primary arm selects ordinal `0` in every document. Descriptive
controls use the same one-window-per-document and 3,072-token budget:

- `shuffled_score`: for document ID `d`, swap the two adaptive score values iff
  the integer represented by the first 16 hexadecimal characters of
  `sha256("shuffle-v3|20260908|d")` is odd;
- `constant_score`: set both scores to `0.5`, which selects ordinal `0`;
- `text_only_novelty`: score with weight `1.0` novelty and `0.0` NLL;
- `surprisal_only`: score with weight `1.0` NLL and `0.0` novelty;
- `matched_energy`: an audit label for the fixed selection, requiring the
  same 12 document IDs, 12 windows, and 3,072 tokens as adaptive.

The runner writes all score components, selected/rejected IDs, token counts,
and selection digests before any adapter training. No score, selection,
threshold, or arm may change after the fit/tune lock.

## Metrics and estimand

For every document and adapter, each of the two 256-token windows is scored
with the adapter loaded. Window NLL is the mean negative log probability over
target positions `1..255`. Document NLL is the arithmetic mean of its two
window NLLs. Case NLL is the arithmetic mean over the six assessment documents.
No token-weighted alternative exists.

For assessment document `d` and case `c`, define:

`D(c,d) = (L0(c,d) - La(c,d)) - (L0(c,d) - Lf(c,d))`.

`L0` is the native frozen-base NLL, `Lf` is the fixed-adapter NLL, and `La` is
the adaptive-adapter NLL. Document effect is `D(d) = mean_c D(c,d)` over all
eight cases. The one primary estimand is:

`Delta_adaptive = mean_d D(d)` over the six assessment documents.

The bounded result requires all conditions:

- `Delta_adaptive >= 0.020` NLL per token;
- deterministic six-document bootstrap 95% percentile lower bound `>= 0.000`;
- `D(d) > 0` for at least four of six assessment documents;
- each primary arm's assessment NLL is no more than 5% worse than its own
  frozen-base NLL;
- for each primary arm, the maximum relative NLL increase on the 12 rejected
  fit windows is no more than 5% versus native base NLL;
- all custody, repeatability, adapter, compute, and validator gates pass.

A positive subthreshold or control-only result is `DevelopmentNoCandidate`.

## Bootstrap, missingness, multiplicity, and reliability

The document bootstrap has exactly 10,000 replicates. For bootstrap replicate
`b` and draw `k` in `0..5`, compute

`j = int.from_bytes(sha256("bootstrap-v3|20260908|b|k" UTF-8)[:8], "big") mod 6`.

The replicate statistic is the arithmetic mean of `D(j)` over the six draws.
The lower and upper endpoints are sorted values at zero-based indexes 249 and
9,749. No imputation, studentization, subgroup correction, or resampling of
tokens is used.

The sole confirmatory comparison is adaptive versus fixed. Controls are
descriptive falsifiers and decomposition checks. A missing case/document,
non-finite metric, failed subprocess, incomplete adapter, duplicate split
identity, or digest mismatch invalidates the campaign. No missing value is
imputed. Reliability is defined mechanically as: repeated native NLL maximum
absolute difference `<= 1e-8`; every adapter reload aggregate difference
`<= 1e-6`; identical selection digest on repeated scoring; and 8/8 complete
case scores for every primary arm/document pair.

## Power calibration

The independent validator runs exactly 10,000 synthetic simulations before
assessment. For simulation `s`, document `d`, case `c`, and mean `mu`, define

`Z(h) = sqrt(-2*ln(U1(h))) * cos(2*pi*U2(h))`,

where `U1(h) = (int(sha256("power-v3|20260908|s|h")[:8])+1)/(2^64+1)` and
`U2(h)` uses bytes `8:16` with the same denominator. The simulated effect is:

`D(c,d) = mu + 0.015*Z(document d) + 0.004*Z(case c) + 0.010*Z(case c, document d)`.

The validator forms the six document means over eight cases and applies an
inner 1,000-replicate version of the exact bootstrap index rule. It records
the fraction whose lower endpoint is at least zero for `mu=0.030` and
`mu=0.000`. Calibration passes only when alternative rejection is at least
`0.80` and null rejection is at most `0.05`. The alternative exceeds the
decision threshold so this is a sensitivity calibration, not a boundary claim.
Failure stops before model assessment and cannot change the threshold or panel.

## Custody and append-only event schema

The external artifact root is absolute, absent before creation, outside the
repository, and on the registered research volume. Its fixed layout is:

```text
ROOT/
  contract.json
  source-manifest.json
  corpus-manifest.json
  events.jsonl
  fit-tune-lock.json
  cases/CASE/selection.json
  cases/CASE/adapters/ARM/adapters.safetensors
  cases/CASE/aggregates.json
  aggregate-result.json
  validator-receipt.json
  retention-receipt.json
```

All files except `events.jsonl` are write-once. `events.jsonl` is append-only;
each line is a JSON object with `sequence`, `event`, `timestamp`, `state_slice`,
`contract_sha256`, and `payload_sha256`. The required event sequence is
`acquisition_complete`, `corpus_sealed`, `qualification_passed`,
`scores_sealed`, `power_calibration_passed`, `fit_tune_lock_sealed`,
`assessment_review_passed`, `assessment_started`, `assessment_complete`,
`aggregate_validation_passed`, `raw_retention_complete`. The immutable lock
file always contains `assessment_started: false`; the transition is represented
only by the append-only event.

Before raw retention cleanup, the source validator reads normalized files and
recomputes source and corpus digests. After cleanup, the aggregate validator
reads only the manifests, lock, events, aggregate result, and validator
receipt. Raw text, token IDs, logits, activations, adapter tensors, and
training logs are deleted from the external root at the recorded retention
deadline; only aggregate NLLs, selection IDs, digests, gate booleans, and
receipts remain.

## Prediction lock and pre-assessment review

The fit/tune lock contains the exact contract digest, model/corpus digests,
case IDs, score vectors, selected/rejected IDs, training command digests,
fixed/tune document NLLs, control diagnostics, the fixed prediction
`predicted_assessment_delta: 0.020`, the fixed prediction
`predicted_positive_document_count: 4`, and `assessment_started: false`.
These prediction values are preregistered directional targets, not tune-fitted
parameters. The lock is written before any assessment adapter is loaded or
assessment NLL is computed.

An independent reviewer must check the contract digest, score and selection
digests, event sequence through `fit_tune_lock_sealed`, custody manifests,
control completeness, prediction lock, and retention fields. Assessment cannot
open without an `ACCEPT` receipt whose reviewed digest equals the lock digest.

## H100 and GiveMeANode boundary

The primary model actor uses MLX/Metal and therefore has no runtime-equivalent
CUDA execution in this state slice. No H100 model run is authorized by V3.
GiveMeANode may run only the pure-Python power simulation or aggregate
validator, with no model or corpus access, and its receipt is infrastructure
provenance only. Any H100 model execution would require a later state slice
with a separately reviewed PyTorch model/runtime contract, new source and
model custody, and fresh validation; it cannot be appended to V3 results.

## Qualification and terminal classification

Qualification runs after independent protocol review and implementation
authorization, before fit/tune or assessment. It checks:

1. source, model, runtime, command, and contract digests;
2. offline environment and zero network-connect attempts;
3. native reload logit parity `<= 1e-5`;
4. repeated frozen-base NLL difference `<= 1e-8`;
5. no-adapter reload parity `<= 1e-5`;
6. adapter tensor shape and declared eight trainable layers;
7. save/reload adapter NLL difference `<= 1e-6`;
8. adapter unload returns to native NLL within `1e-5`;
9. a two-iteration qualification adapter changes probe NLL or logits by a
   finite nonzero amount;
10. source/corpus manifest and independent validator preflight pass.

Any failure stops the slice as `InstrumentFeasibilityFailure`. No adaptive
repair is allowed.

After qualification, fit/tune, lock, and review, the only possible results are:

- `InstrumentFeasibility`: qualification passes and assessment is not opened;
- `DevelopmentNoCandidate`: assessment opens but the primary or guard fails;
- `BoundedAdaptiveVerificationResult`: every declared primary, control,
  uncertainty, custody, and validator gate passes.

The maximum claim is
`LocalDevelopmentAdaptiveVerificationReversibleAdapterV3`. No classification
establishes general continual learning, transformer-wide transfer,
cryptographic verification, Astral evidence, introspection, causal
self-modeling, Stage 0C, Stage 1, benchmark superiority, or production
readiness.
