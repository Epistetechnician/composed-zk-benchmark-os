# Aligned RSI BillSum chat-template adaptation V5

State slice: `aligned-rsi-billsum-chat-template-adaptation-v5`.

Governance slice: `global-experiment-assurance-lifecycle-v1`.

Status: one offline local Apple MPS qualification and local acceptance are
authorized by the user. Independent acceptance is not requested.

Claim ceiling: `LocalDevelopmentBillSumChatTemplateCurriculumQualificationV5`.

## Question and fixed decision rule

V1 ended as `NoCandidate`. V2 ended as
`PreparationFailedDuplicateSourceIdentity`; V3 ended as
`PreparationFailedAssistantTurnTrailer`; and V4 ended as
`ExecutionFailedWallClockLimit`. Those experiment identities and all their
scientific outputs are closed. V5 is a fresh execution identity. It reuses
only the owner-cached pinned Qwen3 model and raw federal BillSum train/test
files, plus the V1 document IDs for exclusion. It does not consume V1-V4
scores, adapters, generations, activations, or outcomes.

The hypothesis is that a curriculum containing the 32 highest base-model
assistant-target-NLL examples in a fixed 512-document fit pool achieves at
least `+0.02` paired held-out ROUGE-L F1 over a uniform 32-example curriculum
trained for the same number of optimizer steps. The untouched base is a
separate baseline. There are three training seeds (`17`, `29`, `43`), 128
fresh held-out documents, and one paired generation seed per document and
training seed shared across all three arms.

The primary statistic is the mean document-level ROUGE-L difference between
selected and random, averaging scores over the three seed pairs within each
document. The locked document bootstrap has 10,000 resamples and seed
`20261007`. `Candidate` requires all of the following: estimate at least
`+0.02`; bootstrap 95% lower bound above zero; selected ROUGE-L not below the
untouched base; selected mean assistant-target NLL no more than `0.05` above
base; and complete, finite outputs and NLLs. Otherwise a complete run is
`NoCandidate`. A failed or incomplete run has no scientific candidate
disposition. No assessment-based retuning is allowed.

Variance sources include document composition, selected-versus-random
curriculum composition, three fixed adapter initialization/training seeds,
sampled decoding, and MPS/runtime numerical behavior. The paired document
bootstrap and per-document/per-seed generation seeds are fixed before model
execution. The run is one same-owner local execution, not a second-environment
reproduction.

## Pinned inputs and fresh cohorts

- Base model: `Qwen/Qwen3-0.6B`, revision
  `c1899de289a04d12100db370d81485cdf75e47ca`, Apache-2.0.
- Dataset: `FiscalNote/billsum`, revision
  `3d8510441c06a3d9dfb32eb0d7f80151730bcc4f`, CC0-1.0. Only federal `train`
  and `test` Parquet files are read; `ca_test` is excluded.
- Runtime and dependency versions are fixed in the V5 machine-readable
  contract and hash-locked requirements file.
- Source identity is SHA-256 of UTF-8 bill text. Rows with a repeated source
  identity are excluded in full within each split. The V1 fit and assessment
  source identities are reconstructed from the V1 legacy source-plus-summary
  ordering and excluded. Remaining rows are traversed in ascending source
  digest order.
- The fresh fit pool contains 512 train documents; held-out assessment
  contains 64 test documents. The read-only feasibility audit found enough
  eligible, unique, V1-disjoint documents for both cohorts.
- The complete Qwen chat-template prompt must be at most 1,280 tokens and the
  assistant completion at most 512 tokens. Oversized rows are skipped before
  selection. Source and reference text are never truncated. Every selected
  assistant completion includes `<|im_end|>` token `151645`; the template's
  final newline token `198` is excluded from loss.

The tokenizer template digest and termination behavior are checked during
preparation and again before execution. The generation prompt must be an exact
prefix of the completed conversation. Fit and assessment sources must be
disjoint, and both cohorts must remain disjoint from V1 source IDs.

## Frozen treatment, control, and measurement

The untouched-base model is the baseline. For the selected treatment, score
assistant-target NLL for all 512 fit documents with the untouched base and
select the 32 highest scores, breaking ties by source digest. For each seed,
sample 32 fit documents uniformly without replacement as the random control.
Each updated arm trains for one epoch over those 32 rows in a seed-shuffled
order.

Training uses only disposable PEFT LoRA rank-8 adapters (`q_proj` and
`v_proj`, alpha 16, dropout 0), AdamW at `1e-4`, betas `(0.9, 0.999)`, epsilon
`1e-8`, weight decay `0.01`, and gradient clipping at `1.0`. Batch size is
exactly four, yielding eight optimizer steps per updated arm and seed. Each
batch is dynamically right-padded to that batch's longest sequence. Attention
mask padding is zero and label padding is `-100`; the model's mean causal
cross-entropy therefore includes only non-ignored assistant target tokens.
Loss includes the final `<|im_end|>` marker. Only LoRA parameters are
trainable; the base checkpoint manifest must remain unchanged. The model runs
in float16 on the local Apple MPS device, with no CPU fallback.

Held-out generation uses the pinned non-thinking chat template, sampling at
temperature `0.7`, top-p `0.8`, top-k `20`, repetition penalty `1.0`, and at
most 512 new tokens. Within each training seed, each assessment document has
the same source-derived generation seed in base, selected, and random arms.
The release reports standard ROUGE-1/2/L F1 without stemming, target NLL,
output/reference token ratio, per-seed ROUGE-L, training loss, elapsed time,
peak process RSS, and MPS memory counters. Energy is recorded as
`not_measured`; no zero-energy or full economic-cost claim is made.

A fixed layer-level diagnostic captures the 14th block residual stream on the
first 16 assessment documents for each updated arm and seed. It compares
unpatched adapted target NLL with an intervention that replaces the selected
block's target-prediction positions with corresponding untouched-base
activations. An identity patch must preserve NLL within `1e-5`. This is a
layer-level diagnostic only; it does not identify features or establish a
mechanistic explanation.

## Execution, custody, and stop rule

The only permitted run is a local, offline, bounded evaluation on explicitly
authorized public federal BillSum data and on Apple MPS. The pinned model and
raw dataset remain in the existing V1 owner-only input cache. V5
prepared rosters, raw rows, generations, fit scores, adapter weights,
activation captures, and private receipts live only under
`$HOME/.local/share/aligned-rsi-billsum-chat-template-adaptation-v5/` with
owner-only directory/file modes. Repository output is aggregate metrics and
digests only. Automatic expiry is disabled; private retention remains under
owner control.

One hard 360-minute wall-clock limit covers execution. Any preparation,
custody, MPS, adapter, finite-value, paired-output, activation-control,
base-immutability, or time-limit failure is terminal under V5. Retain the
failure status; do not retry or modify V5 after execution begins. A different
protocol, runtime, cohort, metric, threshold, harness, or retry requires a
new explicitly authorized state slice and packet. There are no provider calls,
remote workers, paid execution, network access during model execution, public
deployment, or Evidence Ledger changes.

The complete run must first produce a private, digest-bound receipt and an
aggregate-only report. The local verifier reconstructs the report from the
private run, frozen references, adapter digests, and source/input digests.
Only then may it write a local acceptance receipt. This local receipt is
`INTERNAL_PASS`, not independent acceptance.

## Reproduction

The required local input cache already exists. Do not download or refresh
inputs. From the repository root, install the frozen dependencies if needed,
then run the three lifecycle commands once:

~~~sh
uv pip install --python .venv/bin/python --require-hashes -r experiments/continual_learning/aligned_rsi_billsum_chat_template_v5_requirements.lock
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_billsum_chat_template_v5 prepare
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_billsum_chat_template_v5 run
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_billsum_chat_template_v5 verify
~~~

The expected aggregate release directory is
`release/aligned_rsi_billsum_chat_template_v5/`. It must contain only the
aggregate evaluation report, local acceptance receipt, and their release
manifest. The private run and adapter files stay outside the repository.

## Claim boundary

The maximum claim is
`LocalDevelopmentBillSumChatTemplateCurriculumQualificationV5`, and only if
the complete run and local verifier pass. The result is a single local
qualification on this pinned model, data cohort, runtime, and harness. It
does not establish general alignment, recursive self-improvement, a benchmark
leaderboard result, feature-level mechanism, production readiness, user-data
performance, independent acceptance, or clean second-environment
reproducibility. The next authority gate for anything above this ceiling is a
fresh exact evidence packet and whatever independent review or operational
authorization that claim requires; neither is requested here.
