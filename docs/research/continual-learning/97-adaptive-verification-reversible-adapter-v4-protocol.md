# Adaptive verification with reversible adapters v4

Date: 2026-08-28.

State slice: `continual-learning-adaptive-verification-reversible-adapter-v4`.

Status: `ProtocolDraft / ModelExecutionClosedPendingIndependentReview`.

## Purpose and exclusions

V1, V2, and V3 are immutable protocol rejections. V4 is a new reproducibility
audit of one bounded continual-learning controller. It does not amend or
consume those slices. Astral, V48, V82, and all other research lanes are
excluded.

The falsifiable theory is:

> For one frozen causal language model and one fixed reversible LoRA training
> contract, selecting the higher-scoring member of each predeclared pair of
> fit windows, where the score is frozen-base surprisal plus lexical novelty,
> improves held-out NLL relative to selecting the first member of each pair
> under an equal-token budget.

The result, if positive, is bounded controller evidence for this actor and
corpus. It is not evidence of semantic understanding, introspection,
self-modeling, general continual learning, benchmark superiority, or
production readiness.

## Exact actor, source, and execution custody

The sole model actor is the already-cached local checkpoint:

```yaml
actor: google/gemma-3-1b-pt
model_root: /Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16
model_type: gemma3_text
layer_count: 26
hidden_size: 1152
dtype: bfloat16
base_weights: frozen
python_executable: /Users/shaanp/.pyenv/shims/python
python_version: 3.14.5
mlx: 0.31.2
mlx_lm: 0.31.3
tokenizer_policy: model-config-bound-v1
```

The implementation records a model manifest before loading weights. It walks
`model_root` recursively, rejects symlinks, includes every regular file except
files below a directory named `.cache`, sorts relative POSIX paths by UTF-8
bytes, and records path, byte length, and SHA-256. The manifest digest is the
SHA-256 of canonical JSON with sorted keys and separators `(',', ':')`. A
changed, missing, extra, or unreadable stable file fails custody.

The external root is fixed and must be absent before acquisition:

`/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/continual-learning-adaptive-verification-reversible-adapter-v4-20260828`

It must be on the registered research volume, outside the repository, and
created with mode `0700`. No repository path is an output or input root.

The fixed root layout is:

```text
ROOT/
  protocol-copy.md
  contract.json
  model-manifest.json
  source-manifest.json
  corpus-manifest.json
  sources/raw/ID.txt
  sources/normalized/ID.txt
  panels/fit.jsonl
  panels/tune.jsonl
  panels/assessment.jsonl
  events.jsonl
  cases/CASE/selection.json
  cases/CASE/adapters/adaptive/adapters.safetensors
  cases/CASE/adapters/fixed/adapters.safetensors
  cases/CASE/aggregates.json
  fit-tune-lock.json
  assessment-aggregate.json
  validator-receipt.json
  retention-receipt.json
```

All files except `events.jsonl` are write-once. A pre-existing root, duplicate
file, changed write-once file, or path outside this layout fails custody. The
protocol copy is byte-identical to this protocol and its SHA-256 is recorded
in `contract.json`.

## Runtime and adapter contract

Every model subprocess has exactly these environment values:

```yaml
HF_HUB_OFFLINE: "1"
TRANSFORMERS_OFFLINE: "1"
TOKENIZERS_PARALLELISM: "false"
```

The parent process installs a socket guard before importing MLX or MLX-LM; any
`socket.socket.connect` or `socket.create_connection` call raises and records
the attempted address class. A non-empty attempt fails the slice. The process
uses one full-sequence forward pass per 256-token window:

```text
ids = tokenizer.encode(text, add_special_tokens=False)
logits = model(mx.array([ids], dtype=mx.int32))
mx.eval(logits)
```

The runner rejects any tokenizer output other than exactly 256 IDs. It converts
the evaluated logits to NumPy `float64` without recomputing or rounding them,
then computes for token IDs `t[0:256]`:

`NLL(text) = -mean(i=1..255, logit[i-1,t[i]] - logsumexp(logit[i-1,:]))`.

`logsumexp` is evaluated in `float64` as `max + log(sum(exp(x-max)))`; a
non-finite value fails. No KV cache, sampling, temperature, chat template,
special token, padding, truncation, or batching is used for scientific NLL.

The fixed training serialization is one JSON object per line with no extra
keys: `{"text": STRING}`. `STRING` is the tokenizer decode of the exact 256
IDs with `skip_special_tokens=False`; re-encoding with
`add_special_tokens=False` must reproduce the IDs exactly. The MLX-LM dataset
directory contains exactly `train.jsonl`, `valid.jsonl`, and `test.jsonl`; all
three contain the selected fit windows in sealed case order. MLX-LM test output
is ignored; the runner computes the NLL above.

The adapter contract is:

```yaml
fine_tune_type: lora
num_layers: 8
target_layer_indices: [18, 19, 20, 21, 22, 23, 24, 25]
target_module_suffixes: [self_attn.q_proj, self_attn.k_proj, self_attn.v_proj, self_attn.o_proj, mlp.gate_proj, mlp.up_proj, mlp.down_proj]
lora_rank: 8
lora_dropout: 0.0
lora_scale: 20.0
optimizer: adamw
optimizer_config: {}
learning_rate: 0.0001
batch_size: 2
gradient_accumulation_steps: 1
iterations: 16
max_sequence_length: 256
mask_prompt: false
save_every: 16
```

The runner enumerates `model.layers[index].named_modules()` and requires the
exact seven suffixes above, each exactly once, for each of the eight target
layers, with no other LoRA key. The sealed MLX-LM YAML contains the same
`lora_parameters` and an explicit `keys` list containing those seven suffixes;
the runner records resolved full keys. No resume file, full fine-tune, merge,
adapter update after save, or remote callback is allowed. After each case the
adapter is discarded and a newly loaded native model is used for the next arm.

## Fresh corpus and retrieval

The corpus identity is `gutenberg-v4-retrieval-20260828T000000Z`; the exact
UTC timestamp is a fixed protocol identity, not the wall-clock acquisition
time. The source IDs are the following 24 IDs. V1, V2, and V3 executed no
acquisition, so the new root and source manifest are a fresh data identity:

| Split | IDs |
|---|---|
| fit | `1342, 2701, 2554, 84, 1661, 16328, 11, 1727, 43, 1513, 100, 345` |
| tune | `46, 76, 1260, 1232, 5200, 98` |
| assessment | `1400, 215, 209, 16, 35, 36` |

For ID `N`, the only request URL is
`https://www.gutenberg.org/cache/epub/N/pgN.txt`. The client uses `GET`, User-
Agent `astral-independent-research/v4`, a 30-second timeout, and accepts only
one `200` response with media type `text/plain` (parameters allowed). It
follows at most five redirects; all redirect URLs and statuses are recorded,
and the final URL must equal the request URL. Compression, partial content,
and responses over 20 MiB are rejected. The raw response is saved exactly to
`sources/raw/N.txt` before decode.

Normalization is exact: strict UTF-8; CRLF and CR to LF; Unicode NFKC; remove
the first line beginning exactly `*** START OF THE PROJECT GUTENBERG EBOOK` and
all preceding text; remove the last line beginning exactly
`*** END OF THE PROJECT GUTENBERG EBOOK` and all following text; strip leading
and trailing Unicode whitespace; append one LF. Normalized bytes are saved to
`sources/normalized/N.txt`. The source manifest records ID, requested URL,
redirects, final URL, status, content type, raw and normalized byte lengths and
hashes, normalized path, acquisition time, and state slice. Both source paths
are included in the corpus manifest and rehashed before cleanup.

The runner tokenizes each normalized document and takes only offsets `0:256`
and `256:512`. It rejects fewer than 512 IDs and any non-exact re-encoding.
Panels therefore contain exactly 24 fit windows, 12 tune windows, and 12
assessment windows. Split membership is immutable and document-disjoint. A
freshness validator rejects any source or normalized digest equal to a file in
any prior state-slice manifest supplied to it.

## Cases, selection, and controls

The eight cases are the Cartesian product of:

```yaml
training_seeds: [20260901, 20260902, 20260903, 20260904]
order_seeds: [6101, 6102]
case_id: seed-S|order-O
```

For order seed `O` and document ID `D`, the order key is lowercase SHA-256 of
UTF-8 `fit-order-v4|O|D`; fit documents sort by that key, then numeric ID.
Tune and assessment sort by numeric ID. The exact case spelling is
`seed-20260901|order-6101`.

Each fit document has windows `w0` and `w1`. Fixed chooses `w0`. Adaptive
chooses the larger of:

`score(w) = 0.75*minmax(NLL_base(w0),NLL_base(w1)) + 0.25*minmax(novelty(w0),novelty(w1))`.

Min-max returns `0.5` when its two values are equal, otherwise
`(x-min)/(max-min)`. Novelty uses the literal Python source string
`r"[^\\W_]+(?:'[^\\W_]+)?"` on `text.casefold()`; the vocabulary is the set
of matches. `V_other(w)` is the union of matches from the other 23 fit
windows, and novelty is `1-len(V(w)&V_other(w))/max(len(V(w)),1)`. Adaptive
ties choose ordinal `0`, then lower lowercase text SHA-256. Scores, components,
selected/rejected IDs, token counts, and the selection digest are written
before training.

Descriptive controls use the same documents, one window per document, 3,072
training tokens, seeds, command, and evaluation:

```yaml
shuffled_score: swap adaptive score labels iff int(sha256("shuffle-v4|20260908|D")[:16], 16) % 2 == 1
constant_score: both scores are 0.5, hence ordinal 0
text_only_novelty: 1.0 novelty + 0.0 NLL
surprisal_only: 1.0 NLL + 0.0 novelty
matched_energy: diagnostic only; asserts equal token/document budgets and creates no adapter or metric
```

The confirmatory comparison is adaptive versus fixed only. Controls cannot be
selected as winners. No arm, score, layer, module, threshold, or control may
change after the lock.

## Estimand and complete decision rule

For case `c` and assessment document `d`, let `L0(c,d)` be native base NLL,
`La(c,d)` adaptive NLL, and `Lf(c,d)` fixed NLL, each the arithmetic mean of
the document's two windows. Define `D(c,d) = Lf(c,d)-La(c,d)`. `D(d)` is the
mean over the eight cases and `Delta` is the mean over the six assessment
documents. The exact primary gate is:

```yaml
delta_min: 0.020
bootstrap_lower_min: 0.000
positive_documents_min: 4
assessment_guard_relative_max: 0.05
rejected_fit_guard_relative_max: 0.05
```

The assessment guard for arm `a` is
`(mean_{six documents} L_a-mean_{six documents} L0)/mean_{six documents} L0`.
The rejected-fit guard is the maximum over the 12 rejected windows of
`(L_a(w)-L0(w))/L0(w)`. Every denominator must be finite and strictly
positive, otherwise the result is `InvalidMetric`. Both primary arms must
pass both guards. A document is positive exactly when `D(d)>0`. Every listed
gate must pass; any subthreshold, control-only, or guard failure is
`DevelopmentNoCandidate`.

The document bootstrap has 10,000 replicates. For `b` and `k` in `0..5`,
`j=int.from_bytes(sha256("bootstrap-v4|20260908|b|k")[:8],"big")%6`. The
replicate is the mean of `D(j)` over six draws; endpoints are sorted indexes
249 and 9749. No imputation, token resampling, studentization, subgroup
correction, or alternate interval is allowed.

Missing documents, cases, windows, non-finite metrics, duplicate identities,
failed subprocesses, changed adapters, or digest mismatches invalidate V4.
Reliability uses exactly three independent full reload repeats for every native
probe and every adapter/case/arm aggregate. Maximum native NLL difference is
`<=1e-8`; maximum adapter aggregate difference is `<=1e-6`; all eight cases and
six assessment documents must be complete.

## Power calibration

The independent validator runs 10,000 simulations before assessment. Outer
simulation indexes are `s=0..9999`, document indexes `d=0..5`, and case indexes
`c=0..7`. For UTF-8 `power-v4|s|tag`, define `Z` from SHA-256 bytes 0:8 and
8:16 with `U=(integer+1)/(2^64+1)` and
`Z=sqrt(-2*ln(U1))*cos(2*pi*U2)`. Tags are exactly `doc|d`, `case|c`, and
`cell|c|d`. Generate
`D(c,d)=mu+0.015*Z(s,doc|d)+0.004*Z(s,case|c)+0.010*Z(s,cell|c|d)`.

For each simulation, compute six document means and apply a 10,000-draw
bootstrap using `power-bootstrap-v4|s|b|k`, with `b=0..9999`, `k=0..5`, and
the same modulo-six index rule. Mark confirmatory rejection iff
`Delta>=0.020` and the lower endpoint is `>=0`. The alternative is `mu=0.030`
and the null is `mu=0.000`. Calibration passes iff alternative rejection is at
least `0.80` and null rejection is at most `0.05`. This calibrates only the
confirmatory Delta gate; document positivity and loss guards remain fixed
safety gates and are not tunable power parameters.

## Event custody, lock, and review ordering

`events.jsonl` is append-only UTF-8 JSON Lines. Sequence starts at `0`; each
line has exactly `sequence`, `event`, `timestamp`, `state_slice`,
`contract_sha256`, and `payload_sha256`. Timestamps are UTC RFC3339 with `Z`
and second precision. Payloads are canonical JSON with sorted keys and no
NaN/Infinity. Required order is:

```text
0 theory_review_accepted
1 implementation_authorized
2 acquisition_complete
3 corpus_sealed
4 qualification_passed
5 scores_sealed
6 power_calibration_passed
7 fit_tune_lock_sealed
8 assessment_review_passed
9 assessment_started
10 assessment_complete
11 aggregate_validation_passed
12 raw_retention_complete
```

Every event binds a receipt or manifest named in its payload. The first two
events bind the independent theory receipt and separate implementation
authorization. `assessment_started` is the only assessment-open transition.
The write-once `fit-tune-lock.json` always contains
`assessment_started:false`; the event is the sole transition.

The lock binds protocol, contract, model, corpus, source, panel, case,
selection, control, adapter, NLL, threshold, bootstrap, power, retention,
validator, review-receipt, and command digests. It contains exact fit/tune
aggregates and preregistered predictions
`predicted_assessment_delta=0.020` and
`predicted_positive_documents=4`. No assessment model load or assessment NLL
is permitted before this lock exists.

An independent pre-assessment reviewer checks the lock digest, event order
through event 7, custody, controls, prediction values, retention, validator
digest, and claim ceiling. Its receipt names the lock SHA-256 exactly. Only
event 8 opens assessment. The source validator reads raw and normalized files
before cleanup; the aggregate validator reads only manifests, lock, events,
aggregate result, and receipts after cleanup.

Raw text, token IDs, logits, activations, adapter tensors, training data,
training logs, and per-window scientific outputs are deleted at
`2026-09-04T00:00:00Z`. The retention receipt records deletion paths, hashes,
and validator identity. Only aggregate NLLs, document effects, selection IDs,
control summaries, digests, gate booleans, and receipts remain.

## Qualification and classification

After theory review and implementation authorization, qualification runs with
no fit/tune or assessment:

1. protocol, source, model, runtime, command, and implementation digests;
2. root absence, external-volume custody, mode `0700`, and write-once policy;
3. offline environment and zero socket-connect attempts;
4. native full-sequence logit repeat parity `<=1e-5`;
5. three native probe NLL repeats with maximum difference `<=1e-8`;
6. exact-256 tokenizer encode/decode/re-encode behavior;
7. exact 26-layer/1152-hidden/bfloat16 shape and seven-module target set on
   exactly layers 18 through 25;
8. zero-iteration/no-adapter reload parity `<=1e-5`;
9. two-iteration adapter save/reload aggregate difference `<=1e-6`;
10. two-iteration adapter has a finite nonzero probe logit or NLL effect;
11. adapter unload returns native probe NLL within `1e-5`;
12. fresh-source manifests, panels, event schema, and validator preflight;
13. 10,000-simulation power calibration passes both thresholds.

Any failure before event 4 is `InstrumentFeasibilityFailure` with one gate
name. No repair or retry is allowed within V4. A failure after event 4 but
before assessment review is `ProtocolExecutionFailure`; a lock, review, or
retention failure is `GovernanceFailure`; an opened assessment with any
invalid metric or primary/guard failure is `DevelopmentNoCandidate`; only
every primary, reliability, control, custody, retention, and validator gate
passing yields `BoundedAdaptiveVerificationResult`. These classes are
mutually exclusive by event position and terminal precedence.

The maximum claim is
`LocalDevelopmentAdaptiveVerificationReversibleAdapterV4`. No V4 outcome
promotes Stage 0C or Stage 1, creates Astral evidence, establishes
self-modeling, proves general continual learning, or establishes production
readiness. H100 or GiveMeANode model execution is not part of V4. A later CUDA
actor requires a separate state slice, model/runtime custody, and review.
