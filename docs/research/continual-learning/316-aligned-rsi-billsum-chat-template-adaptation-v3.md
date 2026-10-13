# Aligned RSI BillSum chat-template adaptation V3

State slice: `aligned-rsi-billsum-chat-template-adaptation-v3`.

Governance slice: `global-experiment-assurance-lifecycle-v1`.

Status: `LOCAL_EXECUTION_AUTHORIZED_BY_USER`.

Assurance target: `INTERNAL_PASS`. The user requested local acceptance and no
independent acceptance.

Claim ceiling: `LocalDevelopmentBillSumChatTemplateCurriculumQualificationV3`.

## Hypothesis and scope

V1 is terminal `NoCandidate`; V2 is terminal
`PreparationFailedDuplicateSourceIdentity`. V2 stopped before model loading
because the pinned federal training data contain repeated source texts. V3
is a new frozen qualification identity. It excludes repeated source groups,
excludes V1 source documents, and creates new disjoint rosters. It does not
change or reuse V1/V2 scientific outputs.

The hypothesis is that, under the pinned Qwen3 chat-template and decoding
path, a fit-loss-selected 128-example curriculum improves held-out BillSum
ROUGE-L F1 over an equal-budget random curriculum by at least `+0.02`.
Assessment uses three training seeds and a paired document bootstrap. There is
one primary metric and no assessment-based retuning.

This is a local model-update qualification on public federal legislation. It
does not establish general alignment or recursive self-improvement. The
activation intervention is a layer-level diagnostic and does not support a
feature-level mechanistic explanation.

## Frozen identities and open-source components

- Base model: `Qwen/Qwen3-0.6B`, revision
  `c1899de289a04d12100db370d81485cdf75e47ca`, Apache-2.0.
- Dataset: `FiscalNote/billsum`, revision
  `3d8510441c06a3d9dfb32eb0d7f80151730bcc4f`. Only federal `train` and `test`
  Parquet files are read; `ca_test` is excluded.
- The model chat-template bytes are pinned by SHA-256 in the machine-readable
  manifest. Preparation fails if cached bytes differ.
- LoRA adapters use Hugging Face PEFT `0.21.2`, rank 8, alpha 16, dropout 0,
  and `q_proj`/`v_proj` targets. `rouge-score==0.1.2` supplies ROUGE-1/2/L F1
  without stemming.
- The exact Python 3.14.5 / macOS arm64 runtime is listed in the manifest and
  [hash-locked requirements](../../../experiments/continual_learning/aligned_rsi_billsum_chat_template_v3_requirements.lock).

V3 reads the pinned model and dataset bytes from V1's owner-only input cache.
It verifies their file manifests and leaves that cache unchanged. V1/V2
adapters, generated outputs, fit scores, activation results, and assessment
results are not V3 inputs.

## Fresh cohorts

The source identifier is SHA-256 of UTF-8 source text. V3 first counts source
identifiers separately in federal `train` and `test`. Every row belonging to a
source identifier that occurs more than once in its split is excluded; the
protocol does not keep an arbitrary representative of a repeated source.

For V1 overlap prevention only, V3 reconstructs V1's first 512 training rows
and 128 test rows ordered by V1's SHA-256 of `text || NUL || summary`. It maps
those rows to source-text identifiers and excludes every mapped identifier
before V3 selection. These IDs are exclusion inputs only; V1 scientific
artifacts are not read.

Remaining rows are sorted by source-text SHA-256. V3 selects the first 512
training rows and first 128 test rows whose chat-template prompt is at most
2,048 tokens. No source or reference summary is truncated. The fit and
assessment IDs must be disjoint. Preparation records the duplicate-group
exclusion counts, exclusion digests, exact rosters, token-length bounds, and
input digests before any model forward pass.

The fit pool's assistant-target NLL is measured using the untouched base
model. For each seed (`17`, `29`, `43`), the selected arm receives the 128
largest fit-pool NLL rows, tie-broken by source identifier. The random control
receives 128 rows sampled uniformly from the same fit pool. Both update for
exactly one epoch and 128 optimizer steps.

## Chat formatting and training

System and user messages use the pinned tokenizer's
`apply_chat_template(enable_thinking=False)`. Training sequences use that
template with an assistant summary. The runner verifies that the generation
prompt is an exact prefix of the completed conversation, masks system/user
tokens with label `-100`, and computes loss on assistant summary and
end-of-turn tokens only.

The base model runs offline in float16 on local Apple MPS. Only PEFT LoRA
parameters are trainable. Each arm resets the adapter with its locked seed,
uses AdamW at `1e-4`, betas `(0.9, 0.999)`, epsilon `1e-8`, weight decay
`0.01`, batch size one, and gradient clipping at `1.0`. Adapters are stored
with safe serialization outside the repository. The base checkpoint file
manifest must remain unchanged.

Held-out generation follows the pinned Qwen3 non-thinking settings:
temperature `0.7`, top-p `0.8`, top-k `20`, repetition penalty `1.0`, and at
most 768 new tokens. Within each training seed, a source-derived generation
seed is shared across base, selected, and random arms for each document. The
three-seed execution is one local run, not a clean second-environment
reproduction.

## Metrics and locked decision rule

The primary outcome is the mean per-document difference in ROUGE-L F1,
averaged across the three selected and random training seeds. A paired
document bootstrap resamples assessment documents 10,000 times with seed
`20261007`. `Candidate` requires all of the following:

- selected minus random mean ROUGE-L is at least `+0.02`;
- the paired bootstrap 95% lower bound is above zero;
- selected ROUGE-L is not below untouched base;
- selected mean assistant-target NLL is no more than `0.05` above base; and
- every locked completion and NLL is present and finite.

Otherwise the disposition is `NoCandidate`. The report also includes
ROUGE-1/2, output/reference token ratio, per-seed aggregates, training losses,
elapsed time, process peak RSS, and a layer-14 residual activation patch on
the first 16 assessment rows per updated arm and seed. The patch has an
identity control with maximum absolute NLL error `1e-5`; it is a layer-level
diagnostic only.

## Custody, stops, and local acceptance

The pinned model and raw dataset remain under the V1 owner-only cache. V3 run
records, raw rows, references, fit scores, generated summaries, adapter
weights, and activation captures stay below
`$HOME/.local/share/aligned-rsi-billsum-chat-template-adaptation-v3/` with
directories mode `0700` and files mode `0600`. The repository release contains
aggregate metrics and digests only. Automatic expiry is disabled; retention
remains under owner control.

`prepare` verifies exact model and dataset bytes and writes the fresh V3
rosters. `run` enables Hugging Face offline mode, performs one bounded local
execution, and writes the private run record and aggregate report. `verify`
reconstructs metrics from private outputs and pinned references, checks
source, roster, adapter, and base-checkpoint digests, then writes a local-only
acceptance receipt. The execution limit is 180 minutes. A failure is retained
as terminal for V3; do not retry under this identity.

The runner stops on changed input or source digest, an empty or duplicate
selected row, template-prefix mismatch, non-finite loss, failed adapter or
patch control, incomplete assessment, base-weight change, custody violation,
MPS failure, or wall-clock limit. Any change to model, data, harness,
threshold, runtime, cohort, or measurement requires a new state slice.

## Reproduction

Acquire the pinned raw inputs only if the V1 cache is not already present:

~~~sh
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_local_billsum_v1 prepare
~~~

Install the hash-checked V3 dependency closure, then run from the repository
root:

~~~sh
uv pip install --python .venv/bin/python --require-hashes -r experiments/continual_learning/aligned_rsi_billsum_chat_template_v3_requirements.lock
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_billsum_chat_template_v3 prepare
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_billsum_chat_template_v3 run
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_billsum_chat_template_v3 verify
~~~

`run` requires the prepared roster and uses local model/data files only.
`verify` accepts only the exact completed run bound by the aggregate report.
Local acceptance is `INTERNAL_PASS`, not `INDEPENDENT_ACCEPT`.

## References

- [Pinned Qwen3-0.6B model card](https://huggingface.co/Qwen/Qwen3-0.6B/blob/c1899de289a04d12100db370d81485cdf75e47ca/README.md)
- [Hugging Face PEFT configuration and model guide](https://huggingface.co/docs/peft/main/tutorial/peft_model_config)
- [Google Research ROUGE scorer package](https://pypi.org/project/rouge-score/)
