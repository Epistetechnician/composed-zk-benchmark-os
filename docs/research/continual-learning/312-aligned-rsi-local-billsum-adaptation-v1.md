# Aligned RSI local BillSum adaptation V1

State slice: `aligned-rsi-local-billsum-adaptation-internal-v1`.

Status: `LOCAL_EXECUTION_AUTHORIZED_BY_USER`.

Assurance target: `INTERNAL_PASS`; no independent acceptance is requested or
claimed.

Claim ceiling: `LocalDevelopmentBillSumAdaptiveCurriculumQualificationV1`.

## Purpose

Run one bounded, local-only learning loop on real U.S. federal legislation.
The loop scores training examples with the frozen Qwen3-0.6B model, selects a
loss-guided curriculum, trains disposable LoRA adapters, measures held-out
summarization quality, and records a layer-14 activation-patching diagnostic.
The random-selection arm receives the same number of examples, training steps,
and optimizer budget. The base model remains byte-identical.

This is a local model-learning qualification. It is not a general alignment,
recursive-self-improvement, benchmark-leaderboard, or deployment result. The
receipt stores measured evidence and decisions; it does not store hidden chain
of thought.

## Frozen inputs

- Model: `Qwen/Qwen3-0.6B`, revision
  `c1899de289a04d12100db370d81485cdf75e47ca`, Apache-2.0.
- Dataset: `FiscalNote/billsum`, revision
  `3d8510441c06a3d9dfb32eb0d7f80151730bcc4f`.
- Data: only the U.S. federal `train` and `test` splits. The California
  `ca_test` split is excluded because its source license is unresolved in the
  dataset card. The card identifies the federal bills as GPO material under
  CC0-1.0.
- Runtime: the existing repository virtual environment, Python 3.14.5,
  PyTorch 2.13.0 with Apple MPS, Transformers 5.14.1, Datasets 5.0.1,
  Hugging Face Hub 1.27.0, Safetensors 0.8.0, NumPy 2.5.1, and PyArrow
  25.0.0. Execution requires macOS arm64 with MPS available.
- Custody: model, source rows, generated summaries, adapter weights, and
  intermediate activations remain under the owner-only external root
  `/Users/shaanp/.local/share/aligned-rsi-local-billsum-adaptation-v1/`.
  The root and all descendants are mode `0700`; no raw data or weights enter
  the repository.

## Experiment

The runner identifies each source document as SHA-256 of its UTF-8 text and
summary separated by a NUL byte. It sorts by that identifier and freezes the
first 512 U.S. federal training rows as the fit pool and the first 128 U.S.
federal test rows as assessment. Duplicate identifiers, split overlap, missing
fields, and non-finite loss values fail closed. Assessment rows are never used
for selection or optimization.

The frozen model scores all fit-pool rows with teacher-forced token NLL. For
each seed (`17`, `29`, `43`), the runner trains two disposable adapters on 128
examples for one pass:

| Arm | Selection | Purpose |
| --- | --- | --- |
| `loss_selected` | 128 highest fit-pool NLL values, tie-broken by document digest | Receipt-guided curriculum |
| `random_control` | 128 uniformly sampled fit-pool rows with the same seed | Equal-budget selection control |

Both arms use LoRA rank 8 and alpha 16 on every attention `q_proj` and
`v_proj`, dropout 0, AdamW at `1e-4`, batch size 1, max source length 384
tokens, max target length 128 tokens, and one epoch. Greedy generation is
limited to 128 new tokens. Training, evaluation order, seeds, model, and
selection logic are fixed before assessment.

## Measures and decision rule

Primary metric: paired held-out ROUGE-L F1 for `loss_selected` minus
`random_control`, averaged over the three training seeds and 128 assessment
documents. The smallest meaningful effect is `+0.02` absolute ROUGE-L. A
candidate requires a point estimate at least `+0.02`, a 95% paired document
bootstrap lower bound above zero (10,000 resamples, seed `20261006`), no
decrease versus the untouched base model, selected-arm target NLL no more than
`0.05` above the untouched base, and finite non-empty outputs for all locked
cells. ROUGE-L tokenization is frozen to lowercased Unicode word tokens and
punctuation tokens (`\\w+|[^\\w\\s]`), with no stemming. Otherwise disposition
is `NoCandidate`; there is no retuning on assessment data.

Secondary measures are paired reference NLL, output/reference length ratio,
training loss, per-seed results, and complete local elapsed time. The runner
uses the same assessment documents and deterministic decoding for every arm.

The mechanistic diagnostic runs on the first 16 assessment documents by frozen
document digest. It intervenes on the layer-14 residual-stream output during
teacher-forced scoring: replace adapted-run activations at summary-prediction
positions with the corresponding frozen-base activations. It also runs an
identity-patch control. The receipt reports the per-token NLL change and the
fraction of the base-to-adapted NLL gain recovered by that intervention,
computed only on rows with nonzero base-to-adapted gain. This is a layer-level
causal diagnostic, not feature-level attribution or a general mechanistic
explanation. A failed identity control invalidates the diagnostic and the
local acceptance packet.

## Local acceptance and stops

The user's instruction authorizes local acceptance without independent
acceptance. `run` emits a pending aggregate report; the separate `verify`
command checks the frozen input revisions, exact model and dataset file
digests, disjoint rosters, selected and random rosters, adapter digests,
immutable base checkpoint, equal-budget arms, finite complete assessment
cells, patch identity control, receipt reconstruction, and aggregate-only
repository outputs. Only after these checks pass does `verify` write the
digest-bound local acceptance receipt and change the report to
`INTERNAL_PASS`. A valid local contract may have disposition `NoCandidate`;
local acceptance does not turn a negative result into a learning claim.

The run stops on a missing or mismatched digest, unsupported MPS operation,
non-finite loss, incomplete assessment, base-weight mutation, output or
custody violation, or 180-minute wall-clock limit. No provider, paid service,
remote worker, network service, user data, or independent-review service is
used. Public input acquisition is limited to the two pinned Hugging Face
revisions above.

## Reproduction

From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_local_billsum_v1 prepare
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_local_billsum_v1 run
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_local_billsum_v1 verify
```

`prepare` downloads only the pinned model and the federal train/test Parquet
files into the external owner-only root. `run` is offline after preparation.
`verify` reconstructs the aggregate receipt. Exact environment, source, model,
dataset, selection, adapter, and output digests are retained in the external
run record; the repository receives only the protocol, runner, tests, and
aggregate evaluation report.
