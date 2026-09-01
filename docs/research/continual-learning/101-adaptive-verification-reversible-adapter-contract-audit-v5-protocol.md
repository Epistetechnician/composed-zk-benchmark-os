# Adaptive verification reversible-adapter contract audit v5

Date: 2026-08-28.

State slice: `continual-learning-adaptive-verification-reversible-adapter-contract-audit-v5`.

Status: `ProtocolDraft / NoModelNoCorpusNoTraining`.

## Scope and authorization boundary

This is a contract-remediation audit, not a new model, corpus, layer, wrapper,
alpha, optimizer, or position variation. The V5 implementation may only parse
fixed in-memory fixtures and validate a sealed contract. It must not:

- acquire or read Gutenberg data;
- load or inspect model weights;
- run MLX, MLX-LM, CUDA, H100, GiveMeANode, training, inference, or assessment;
- create the V5 external execution root;
- alter V1, V2, V3, V4, Astral, V48, V82, or any prior artifact;
- produce scientific, benchmark, continual-learning, Astral, or production
  evidence.

The only V5 claim is `LocalDevelopmentAdaptiveVerificationContractAuditOnly`.
The audit asks whether a future implementation contract is mechanically closed;
it does not say that the future experiment works.

V3 and V4 are explicitly historical exclusions. Their identities are recorded
for distinctness, not consumed as data:

```yaml
excluded_state_slices:
  - slice: continual-learning-adaptive-verification-reversible-adapter-v3
    protocol_sha256: 2f3c9562d9247abd75267e3de34ecd36ce5dfec5b353520f8976291d487134e0
    status: ProtocolRejectedBeforeImplementation
  - slice: continual-learning-adaptive-verification-reversible-adapter-v4
    protocol_sha256: 6991f8ce5f9d98a0f2728e894ae9fa5897551d5cd9096ba2273652e09cd0df35
    status: ProtocolRejectedBeforeImplementation
```

## V5 audit object and canonical digest

The validator accepts exactly one top-level JSON object with these keys:

```text
schema, state_slice, claim_ceiling, execution_mode, excluded_slices,
actor, custody, corpus, selection, estimator, reliability, power,
events, lock, retention, classification
```

No unknown key is accepted. JSON is UTF-8; duplicate keys are rejected during
parsing; numbers must be finite; booleans are not numbers. Canonical bytes are
produced by Python `json.dumps(value, ensure_ascii=False, sort_keys=True,
separators=(",", ":"), allow_nan=False).encode("utf-8")`. The contract digest
is SHA-256 of those bytes. The validator records the digest and never accepts
a caller-supplied digest without recomputing it.

V5's fixed contract identity is:

```yaml
schema: continual-learning-adaptive-verification-reversible-adapter-contract-v5
state_slice: continual-learning-adaptive-verification-reversible-adapter-contract-audit-v5
claim_ceiling: LocalDevelopmentAdaptiveVerificationContractAuditOnly
execution_mode: NO_MODEL_NO_CORPUS_NO_TRAINING
```

## Exact future actor contract (not executed by V5)

The future implementation contract names one actor and one runtime:

```yaml
actor:
  name: google/gemma-3-1b-pt
  model_root: /Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16
  model_type: gemma3_text
  layers: 26
  hidden_size: 1152
  model_dtype: bfloat16
  python: /Users/shaanp/.pyenv/shims/python
  python_version: 3.14.5
  mlx: 0.31.2
  mlx_lm: 0.31.3
  tokenizer_policy: model-config-bound-v1
  execution_device: metal
```

Before a future model load, its manifest walks the absolute model root
recursively, rejects symlinks and non-regular files, excludes only files whose
relative path contains a directory component exactly `.cache`, sorts relative
POSIX paths by their UTF-8 bytes, and records exactly `path`, `byte_len`, and
`sha256` for every file. The model manifest has fields `root`, `files`, and
`manifest_sha256`; the digest is the canonical digest defined above. A missing,
extra, unreadable, changed, or symlinked file fails custody.

The future full-sequence call is exact:

```python
ids = tokenizer.encode(text, add_special_tokens=False)
assert len(ids) == 256
logits = model(mx.array([ids], dtype=mx.int32))
mx.eval(logits)
assert logits.shape[0] == 1
assert logits.shape[1] == 256
assert isinstance(logits.shape[2], int) and logits.shape[2] > 0
```

The batch axis is `0`, sequence axis is `1`, vocabulary axis is `2`. The
evaluated array is converted once to NumPy `float64`; NLL is
`-mean(i=1..255, logits[i-1,t[i]] - logsumexp(logits[i-1,:]))`, with
`logsumexp(x)=max(x)+log(sum(exp(x-max(x))))` in float64. No cache, batch
greater than one, padding, truncation, special token, sampling, temperature,
chat template, or alternate forward path is permitted.

The exact future training command is:

```text
/Users/shaanp/.pyenv/shims/python -m experiments.continual_learning.safe_mlx_lora --model MODEL --train --data DATA --fine-tune-type lora --optimizer adamw --num-layers 8 --batch-size 2 --iters 16 --learning-rate 0.0001 --steps-per-report 16 --steps-per-eval 16 --val-batches -1 --max-seq-length 256 --adapter-path ADAPTER --save-every 16 --seed SEED --config CONFIG
```

`MODEL`, `DATA`, `ADAPTER`, and `CONFIG` are absolute paths bound in the
contract. The future subprocess must set `HF_HUB_OFFLINE=1`,
`TRANSFORMERS_OFFLINE=1`, and `TOKENIZERS_PARALLELISM=false`, and a parent
socket guard must reject and record every connect attempt. The adapter is LoRA
rank 8, dropout 0, scale 20, AdamW, learning rate `1e-4`, batch 2, one
accumulation step, 16 iterations, sequence length 256, and no prompt mask.

Exactly layers `[18,19,20,21,22,23,24,25]` are trainable. In each layer the
only target suffixes are exactly:

```text
self_attn.q_proj
self_attn.k_proj
self_attn.v_proj
self_attn.o_proj
mlp.gate_proj
mlp.up_proj
mlp.down_proj
```

The future runner must enumerate `model.layers[index].named_modules()`, require
each suffix exactly once and no other key, then bind the seven relative keys in
the MLX-LM `lora_parameters.keys` list. The resolved full keys and their digest
are part of the future contract. A target-path mismatch is a custody failure.

## Future custody root and corpus contract

The future root is fixed and must be absent before any future implementation:

`/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/continual-learning-adaptive-verification-reversible-adapter-v5-execution-20260828`

The required volume identity is `D53A2378-1B1E-3152-A36F-D5C68B522A84`.
Future code must compare the mounted volume UUID, not only its path. The root
must be outside the repository, mode `0700`, and write-once except for the
append-only event log. V5 does not create or probe this root.

The future source IDs and split identity are fixed but not acquired by V5:

```yaml
corpus_id: gutenberg-v5-retrieval-20260828T000000Z
fit: [1342, 2701, 2554, 84, 1661, 16328, 11, 1727, 43, 1513, 100, 345]
tune: [46, 76, 1260, 1232, 5200, 98]
assessment: [1400, 215, 209, 16, 35, 36]
```

The future layout must contain `sources/raw/ID.txt`,
`sources/normalized/ID.txt`, `panels/fit.jsonl`, `panels/tune.jsonl`, and
`panels/assessment.jsonl`; their paths, lengths, and hashes are required in
the source and corpus manifests. A fixed prior-manifest set is the two entries
in `excluded_slices` above; absence of either exclusion entry fails the
freshness check. V5's corpus status is always `NOT_ACQUIRED`.

For future acquisition, the only URL for ID `N` is
`https://www.gutenberg.org/cache/epub/N/pgN.txt`. The client uses GET, User-
Agent `adaptive-verification-contract/v5`, 30-second timeout, at most five
redirects, and accepts only a final `200`, media type `text/plain`, final URL
equal to the requested URL, no content encoding, no partial content, and
payload size at most 20 MiB. Every redirect URL/status is stored. Exactly one
start marker and exactly one end marker are required; missing, repeated, or
reversed markers fail acquisition.

Normalization is strict UTF-8, CRLF/CR to LF, Unicode NFKC, remove the first
start-marker line and preceding bytes, remove the last end-marker line and
following bytes, strip Unicode leading/trailing whitespace, append one LF.
Future code takes token offsets `0:256` and `256:512` only and rejects fewer
than 512 IDs or failed exact re-encoding. Split membership is immutable and
document-disjoint.

## Future selection, controls, and estimand

The eight future cases are the exact Cartesian product of training seeds
`[20260901,20260902,20260903,20260904]` and order seeds `[6101,6102]`. For
order `O` and ID `D`, the fit-order key is lowercase SHA-256 of UTF-8
`fit-order-v5|O|D`; sort by that key, then numeric ID. Case IDs are exactly
`seed-S|order-O`. Tune and assessment sort by numeric ID.

For every fit document, `w0` is IDs `0:256` and `w1` is IDs `256:512`.
`n0` and `n1` are their native base NLLs. With `minmax(a,b,x)` returning `0.5`
when `a==b`, otherwise `(x-min(a,b))/(max(a,b)-min(a,b))`, define the two
scores explicitly:

```text
score0 = 0.75*minmax(n0,n1,n0) + 0.25*minmax(v0,v1,v0)
score1 = 0.75*minmax(n0,n1,n1) + 0.25*minmax(v0,v1,v1)
```

The lexical pattern is the exact Python raw string
`r"[^\W_]+(?:'[^\W_]+)?"`; it is applied to `text.casefold()`, and vocabulary
is the set of matches. `V_other(w)` is the union from every other fit window;
`v(w)=1-len(V(w)&V_other(w))/max(len(V(w)),1)`. Adaptive chooses index `1`
only if `score1>score0`; otherwise it chooses index `0`. This closes both the
score-variable and tie rules without a text-hash fallback.

The fixed arm always chooses `w0`. The future descriptive controls are fixed
as follows: `shuffled` swaps score0 and score1 iff the integer represented by
the first 16 hex characters of SHA-256 UTF-8 `shuffle-v5|20260908|D` is odd;
`constant` uses score0=score1=0.5; `text_only` uses weights `(0,1)` for
`(n,v)`; `surprisal_only` uses `(1,0)`. `matched_budget` is a diagnostic
assertion only and creates no adapter, metric, or winner. All arms use exactly
12 documents and 3,072 source tokens.

For future arm `a`, document `d`, and case `c`, each document NLL is the
arithmetic mean of its two window NLLs. Let `L0` be native, `La` adaptive, and
`Lf` fixed. The sole confirmatory estimand is
`D(c,d)=Lf(c,d)-La(c,d)`, `D(d)=mean_c D(c,d)`, and
`Delta=mean_d D(d)` over six assessment documents. The fixed decision is:

```yaml
delta_min: 0.020
bootstrap_lower_min: 0.000
positive_documents_min: 4
assessment_guard_relative_max: 0.05
rejected_fit_guard_relative_max: 0.05
```

The assessment guard is
`(mean_d La-mean_d L0)/mean_d L0`. For adaptive,
`R_a={w_{1-s_a(d)}: d in fit}`; for fixed,
`R_f={w1: d in fit}`. The rejected-fit guard for arm `a` is
`max_{w in R_a or R_f, respectively} (La(w)-L0(w))/L0(w)`. Every denominator
must be finite and positive; otherwise the terminal class is `InvalidMetric`.
The primary gate requires Delta at least `0.020`, a 10,000-replicate
bootstrap lower endpoint at least zero, at least four positive `D(d)`, both
assessment guards at most `0.05`, both rejected-fit guards at most `0.05`, and
all custody/reliability/validator gates. A subthreshold or guard failure is
`DevelopmentNoCandidate`; controls cannot win.

The future bootstrap uses `j=int.from_bytes(sha256("bootstrap-v5|b|k")[:8],
"big")%6` for `b=0..9999`, `k=0..5`; sorted endpoints are indexes 249 and 9749.
Missingness is rejection: no imputation, token resampling, studentization,
subgroup correction, or alternative interval. Reliability is exactly three
separate OS processes per native probe and per adapter/case/arm aggregate,
each with a fresh model load, identical sealed command/environment, and a
distinct process ID recorded in the receipt. Native max NLL difference is
`1e-8`; adapter aggregate max difference is `1e-6`.

## Future power calibration

Power is a prequalification pure-Python calculation, not a model run. Use
simulation indexes `s=0..9999`, document indexes `d=0..5`, and case indexes
`c=0..7`. For tag `T`, `Z(s,T)` hashes UTF-8 `power-v5|s|T`; bytes `0:8` and
`8:16` become `(integer+1)/(2^64+1)`, then
`sqrt(-2*ln(U1))*cos(2*pi*U2)`. Tags are exactly `doc|d`, `case|c`, and
`cell|c|d`. Generate
`D(c,d)=mu+0.015*Z(s,doc|d)+0.004*Z(s,case|c)+0.010*Z(s,cell|c|d)`.

For each simulation compute six document means and use 10,000 bootstrap draws
with `power-bootstrap-v5|s|b|k`, `b=0..9999`, `k=0..5`, and the same modulo-six
index rule. Simulated rejection is exactly Delta at least `0.020` and lower
endpoint at least zero. Run `mu=0.030` and `mu=0.000`; pass requires alternative
rejection at least `0.80` and null rejection at most `0.05`. This calibrates
only Delta; positivity and loss guards remain fixed safety gates.

## Exact future event, payload, lock, and retention contract

The future external root is
`/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/continual-learning-adaptive-verification-reversible-adapter-v5-execution-20260828`,
on volume UUID `D53A2378-1B1E-3152-A36F-D5C68B522A84`, mode `0700`, and absent
before acquisition. V5 does not create it. All future files are write-once
except `events.jsonl`, which is append-only.

Every event line is exactly an object with keys
`sequence,event,timestamp,state_slice,contract_sha256,payload,payload_sha256`.
Sequence is contiguous from zero. Timestamp is UTC RFC3339 seconds with `Z`.
`payload` is an object; `payload_sha256` is the canonical digest of that
object. Events must occur in this exact order:

```text
0 theory_review_accepted
1 implementation_authorized
2 acquisition_complete
3 corpus_sealed
4 power_calibration_passed
5 qualification_passed
6 scores_sealed
7 fit_tune_lock_sealed
8 assessment_review_passed
9 assessment_started
10 assessment_complete
11 aggregate_validation_passed
12 raw_retention_complete
```

The write-once `fit-tune-lock.json` has the exact top-level keys:

```text
schema, state_slice, protocol_sha256, contract_sha256, model_manifest_sha256,
source_manifest_sha256, corpus_manifest_sha256, case_ids, selection_digest,
control_definitions, adapter_contract, command_digests, fit_aggregates,
tune_aggregates, threshold_config, bootstrap_config, power_config,
retention_config, validator_identity, theory_review_sha256,
implementation_authorization_sha256, assessment_review_sha256,
predicted_assessment_delta, predicted_positive_documents, assessment_started
```

All fields are required; no unknown keys are accepted; the file uses the V5
canonical JSON encoding and its digest is recomputed. Values are exact sealed
objects, with `predicted_assessment_delta=0.020`,
`predicted_positive_documents=4`, and `assessment_started=false`. Assessment
cannot load a model or compute an assessment NLL before event 8 and a review
receipt whose `reviewed_lock_sha256` equals the recomputed lock digest.

Before cleanup, the source validator reads raw and normalized files and
recomputes their hashes. After cleanup, the aggregate validator reads only
manifests, events, the lock, aggregate result, and receipts. Raw text, token
IDs, logits, activations, adapter tensors, training data, logs, and
per-window outputs are deleted at `2026-09-04T00:00:00Z`; retained fields are
aggregate NLLs, document effects, selection IDs, control summaries, digests,
gate booleans, and receipts.

## V5 audit fixtures and result rule

The V5 validator runs only hermetic fixtures stored in memory by the test
process. It must pass these checks:

1. duplicate-key, unknown-key, non-finite-number, canonical-JSON, and digest
   rejection/acceptance cases;
2. exact state-slice, excluded-slice, claim-ceiling, and no-execution values;
3. exact actor/runtime/output-axis, model-manifest, module-key, training-
   command, offline-environment, and volume-UUID rules;
4. exact corpus status, source URL, redirect, media type, boundary-marker,
   normalization, split, window, freshness, and path rules;
5. exact score0/score1, regex, novelty, tie, arm, rejected-window, guard,
   bootstrap, reliability, and power-hash rules;
6. exact event fields, payload digest, sequence, transition, lock-field set,
   lock digest, review binding, retention deadline, and validator input rules;
7. exact terminal classification precedence.

No fixture contains Gutenberg text, token IDs, weights, logits, activations,
adapter tensors, or training output. The validator's output is one aggregate
JSON receipt containing `state_slice`, validator code SHA-256, contract SHA-256,
fixture count, gate booleans, failed gate names, and the narrow claim ceiling.
It contains no source content or hidden raw payload.

V5 classification is deterministic and has no scientific-result branch:

```text
ProtocolRejectedBeforeAudit  = independent review rejects the V5 protocol
ContractAuditFailure          = any fixture or validator gate fails
ContractAuditPass             = every fixture gate passes
```

These classes are mutually exclusive by evaluation order. The audit cannot
produce `InstrumentFeasibility`, `DevelopmentNoCandidate`,
`BoundedAdaptiveVerificationResult`, Stage 0C, Stage 1, Astral, or production
status. A future model/data execution would require a separate authorized
state slice and a new independent review; V5 cannot open it by passing.

## Review and implementation gate

An independent reviewer must verify this protocol and its digest before any
V5 source file other than the review packet is written. The receipt must have:

```yaml
state_slice: continual-learning-adaptive-verification-reversible-adapter-contract-audit-v5
reviewed_protocol_path: docs/research/continual-learning/101-adaptive-verification-reversible-adapter-contract-audit-v5-protocol.md
reviewed_protocol_sha256: <computed-after-freeze>
reviewer_role: independent-theory-and-contract-reviewer
verdict: ACCEPT or REJECT
findings: <numbered finding for every section>
execution_authorized: false
review_date: 2026-08-28
```

`ACCEPT` permits only the pure fixture validator and hermetic tests described
above. `REJECT` closes V5 without implementation. A passing V5 audit does not
authorize data, model, training, assessment, provider, or H100 execution.
