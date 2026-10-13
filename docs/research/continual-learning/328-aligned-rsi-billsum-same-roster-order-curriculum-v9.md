# Aligned RSI BillSum same-roster order curriculum V9

State slice: `aligned-rsi-billsum-same-roster-order-curriculum-v9`.

Governance slice: `global-experiment-assurance-lifecycle-v1`.

## Research question and claim ceiling

V9 tests whether presenting an identical fixed training set in easy-to-hard
order changes local held-out summarization quality relative to randomized
order. The treatment orders all 128 training bills by increasing untouched
base assistant-target negative log likelihood (NLL), with source ID as the
tie-breaker. The control shuffles those same 128 bills with a fixed
seed-derived permutation. The treatment and control therefore contain the
same source documents and exact same source and target tokens. Only
presentation order and the resulting four-example optimizer groups differ.

This tests one possible ordering effect on one model, corpus, local runtime,
and training procedure. It does not test general continual learning,
recursive self-improvement, alignment, or a feature-level mechanism. The
maximum claim ceiling is
`LocalDevelopmentBillSumSameRosterCurriculumOrderQualificationV9`.

V8 remains terminal `NoCandidate`. V8 outcome scores, generations, adapters,
activations, and scientific conclusions are not V9 inputs. The V1 and V4-V8
prepared-input receipts and source IDs are read only to bind the pinned raw
inputs and exclude previously used source documents.

## Frozen identity and local inputs

- Model: `Qwen/Qwen3-0.6B`, revision
  `c1899de289a04d12100db370d81485cdf75e47ca`, Apache-2.0. The pinned local
  model tree SHA-256 is
  `e77990a87387a8bd81db5a96b8ec8b2853d08b1c4b7fa65c8a34d768eab6459b`.
- Dataset: `FiscalNote/billsum`, revision
  `3d8510441c06a3d9dfb32eb0d7f80151730bcc4f`, CC0-1.0. The pinned local
  dataset tree SHA-256 is
  `03ff3ea855c3e5840722315fb7a986da0001b2a3a932b5e6cd98b34eb967eda1`.
  Only federal `train` and `test` Parquet files are read. `ca_test` is
  excluded.
- Pinned Qwen3 chat template SHA-256:
  `a55ee1b1660128b7098723e0abcd92caa0788061051c62d51cbe87d9cf1974d8`.
  Thinking is disabled. The assistant loss includes `<|im_end|>` token
  `151645` and excludes the exact trailing template newline token `198`.
- The runtime is the V8 resolved lock environment: Python 3.14.5 on macOS
  arm64, PyTorch 2.13.0, Transformers 5.14.1, PEFT 0.21.2, Datasets 5.0.1,
  and `rouge-score` 0.1.2. V9 binds the complete runtime inventory plus the
  exact V8 helper and lock digests in its source manifest.
- Model and dataset bytes are read from the existing V1 owner-only cache.
  No network access, package installation, download, or input mutation is
  allowed during V9 preparation or model execution.

## Cohort freeze

Document IDs are SHA-256 of UTF-8 source bill text. Every repeated source
group within each split is excluded. The old V1 fit and assessment IDs are
reconstructed from the pinned raw train and test bytes using V1's
`SHA256(text || NUL || summary)` order and excluded. V4-V8 prepared-input
receipts are checked against their frozen digests, model/data identities,
roster counts, and roster hashes. Their IDs are used only for exclusion.

Among remaining unique eligible documents, source IDs are sorted
lexicographically. The first 128 eligible federal train documents are the
fixed fit roster. The first 120 eligible federal test documents are the
assessment roster. Eligibility uses the pinned chat template, allows no
source or target truncation, caps prompt length at 1,280 tokens, and caps
assistant target length at 512 tokens. The rosters must be split-disjoint.

The read-only feasibility audit found 131 eligible fresh train documents and
126 eligible fresh test documents after all historical exclusions and
duplicate filtering. It found eight duplicate train-source groups (16 rows)
and no duplicate test-source groups. The frozen roster digests are:

- Fit roster: `7beba247d474ca17858aa7b156c863bf869ee3bec3f0f98ed045bcf2152771aa`.
- Assessment roster: `a0d2608ccc9af7aeaede2e13a07df0e6b29abaff7b831835211116d5411d1f09`.
- Fit prompt/source tokens: 148,590.
- Fit assistant target tokens: 22,561.
- Combined fit tokens: 171,151.

V9 preparation must reconstruct these exact identities. Fewer than 128 fit
rows, fewer than 120 assessment rows, a digest mismatch, changed tokenizer
identity, or changed token totals closes this packet before model loading.

## Arms and fixed training procedure

1. `untouched_base`: no parameter updates; four assessment repeats.
2. `easy_to_hard_order`: the exact fixed fit roster sorted by ascending
   untouched-base assistant-target NLL, then source ID ascending.
3. `random_order_control`: the exact same fit roster shuffled per seed with
   `random.Random(seed XOR 0x4F524439)`.

The four paired seeds are `607`, `701`, `809`, and `907`. Within each seed,
both trained arms start from the same LoRA initialization, use all 128 fit
examples once, and take exactly 32 AdamW optimizer steps. Batch size is four;
each update accumulates four one-example, unpadded forwards and computes a
token-weighted mean assistant-only cross entropy. The optimizer uses learning
rate `1e-4`, betas `(0.9, 0.999)`, epsilon `1e-8`, weight decay `0.01`, and
gradient clipping at `1.0`. The adapter is PEFT LoRA with rank 8, alpha 16,
dropout 0, and `q_proj`/`v_proj` targets. Base weights remain immutable.

The easy-to-hard and randomized orderings intentionally define different
four-example groups. The source IDs, source token sequences, target token
sequences, total token budgets, model, initialization within each seed,
optimizer, and update count remain paired. Loss is used only to order the
fixed roster; no examples are selected or removed by their score.

## Assessment and frozen candidate rule

Each of the three arms is evaluated on all 120 held-out bills for each of the
four paired seeds: 1,440 sampled completions total. Per-document generation
seeds are shared across arms within a training seed. Decoding is fixed to
temperature `0.7`, top-p `0.8`, top-k `20`, repetition penalty `1.0`, and at
most 512 new tokens.

The primary endpoint is the paired-document mean ROUGE-L F1 difference
`easy_to_hard_order - random_order_control`, averaging each document across
the four training seeds. The 95% percentile interval uses 10,000 document
bootstrap resamples and seed `20261011`. The meaningful-effect threshold is
`+0.02`.

`Candidate` requires all of the following: mean effect at least `+0.02`,
bootstrap lower bound above zero, easy-to-hard mean ROUGE-L not below the
untouched base, easy-to-hard assistant-target NLL no more than `0.05` above
the untouched base, all outputs and adapters complete and finite, and the
maximum identity-patch NLL error no greater than `1e-5`. Any unmet scientific
criterion yields `NoCandidate`; a failed execution or evidence gate is
recorded as a failure and is not converted into a scientific result.

Secondary metrics are ROUGE-1/2, assistant-target NLL, output-to-reference
token ratio, per-seed ROUGE-L, exact per-arm token budgets, wall time, peak
process RSS, and MPS memory counters. A layer-14 residual activation patch
with identity control is run on the first 16 assessment documents for each
trained arm and seed (128 diagnostic rows). It is a secondary diagnostic and
supports no feature-level or mechanistic claim.

## Execution, custody, and stop rules

One local Apple MPS execution is permitted after the runner, tests, protocol,
machine contract, V8 helper/lock, and prepared-input receipt are frozen and
digest-bound. The hard limit is eight hours from model-execution start through
assessment and intervention diagnostics. Network access, provider calls,
remote workers, paid execution, user data, Evidence Ledger mutation, and
public deployment are prohibited. Provider calls and spend are none; energy
and total local compute cost are `not_measured`.

The prepared receipt, source IDs, raw rows, fit NLLs, generated summaries,
adapter files, activations, and detailed run remain under
`$HOME/.local/share/aligned-rsi-billsum-same-roster-order-v9` with a `0700`
root/directories and `0600` files. The repository release is aggregate-only
and contains exactly `evaluation_report.json`, `local_acceptance.json`, and
`release_manifest.json`. It must contain no source IDs, raw text, references,
generated summaries, activations, model weights, or adapter weights.

Timeout, MPS OOM, custody failure, changed source or input identity,
incomplete/non-finite output, adapter-seal failure, or report reconstruction
failure is terminal for V9. Do not retry, retune, or modify this identity.

## Assurance and reproduction

The permitted local result is `INTERNAL_PASS` for the exact local procedure,
evidence custody, and aggregate report reconstruction only. Reviewer status
is `LOCAL_ACCEPTANCE_ONLY_NO_INDEPENDENT_ACCEPT`. Reproducibility status is
`SINGLE_LOCAL_EXECUTION`; no clean second environment or independent review
is authorized here. Local acceptance is not an independent acceptance or a
positive scientific result.

Machine contract: `experiments/continual_learning/aligned_rsi_billsum_same_roster_order_v9.json`.
Runner: `experiments/continual_learning/aligned_rsi_billsum_same_roster_order_v9.py`.
Focused tests:
`experiments/continual_learning/tests/test_aligned_rsi_billsum_same_roster_order_v9.py`.

Using the existing locked `.venv`, run the hermetic focused checks and read-only
preflight before the one-shot preparation and model run:

```sh
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m pytest -q experiments/continual_learning/tests/test_aligned_rsi_billsum_same_roster_order_v9.py
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_billsum_same_roster_order_v9 audit
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_billsum_same_roster_order_v9 prepare
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_billsum_same_roster_order_v9 run
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_billsum_same_roster_order_v9 verify
```
