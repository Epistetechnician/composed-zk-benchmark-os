# Aligned RSI BillSum chat-template adaptation V2

State slice: aligned-rsi-billsum-chat-template-adaptation-v2.

Governance slice: global-experiment-assurance-lifecycle-v1.

Status: LOCAL_EXECUTION_AUTHORIZED_BY_USER.

Assurance target: INTERNAL_PASS. The user requested local acceptance and no
independent acceptance.

Claim ceiling: LocalDevelopmentBillSumChatTemplateCurriculumQualificationV2.

## Hypothesis and scope

V1 is terminal NoCandidate. Its run used a raw text prompt and greedy decoding,
while the pinned Qwen3 model documents a chat-template path and sampling
configuration. V2 is a new hypothesis and a fresh execution; it does not
change V1's source, report, acceptance receipt, or interpretation.

The hypothesis is that, under the frozen Qwen3 chat-template and decoding
path, a fit-loss-selected 128-example curriculum improves held-out BillSum
ROUGE-L F1 over an equal-budget random curriculum by at least +0.02.
Assessment runs use three paired generation seeds and a paired document
bootstrap. There is one primary metric and no assessment-based retuning.

This is a real local model update on public federal legislation. It is not a
general alignment or recursive self-improvement result. The receipt contains
measured outcomes, adapter and source digests, and a layer-level intervention;
it does not contain hidden chain of thought or claim a feature-level
mechanistic explanation.

## Frozen identities and open-source components

- Base model: Qwen/Qwen3-0.6B, revision
  c1899de289a04d12100db370d81485cdf75e47ca, Apache-2.0.
- Dataset: FiscalNote/billsum, revision
  3d8510441c06a3d9dfb32eb0d7f80151730bcc4f. Only federal train and test
  Parquet files are read; ca_test is excluded.
- Qwen chat-template bytes are pinned by SHA-256 in the manifest. Preparation
  fails if the locally cached template differs.
- LoRA adapters use Hugging Face PEFT 0.21.2, with rank 8, alpha 16, dropout
  0, and q_proj/v_proj targets. Google Research's rouge-score 0.1.2 supplies
  ROUGE-1, ROUGE-2, and ROUGE-L F1 without stemming.
- The locked Python 3.14.5 / macOS arm64 runtime is listed in the protocol
  manifest and
  [requirements lock](../../../experiments/continual_learning/aligned_rsi_billsum_chat_template_v2_requirements.lock).

The pinned model and dataset bytes are reused from V1's owner-only raw-input
cache. V2 validates their full file manifests and leaves that cache unchanged.
V1's trained adapters, generated outputs, fit scores, mechanistic results, and
assessment results are not V2 inputs.

## Fresh cohorts

V2's new document identifier is SHA-256 of source text only. For exclusion,
the runner reconstructs V1's first 512 sorted federal training rows and first
128 sorted federal test rows using V1's original
SHA-256(text || NUL || summary) ordering. These identifiers are used only to
prevent cohort overlap; V1 scientific outputs are not read.

After those exclusions, rows are sorted by the V2 source-only identifier. The
first 512 training rows and first 128 test rows whose chat-template prompt is
at most 2,048 tokens form the fit and assessment cohorts. No source or
reference summary is truncated. The fit and assessment rosters must be
disjoint and are frozen by prepare before any model forward pass.

The fit pool's assistant-target NLL is scored with the untouched base model.
For each seed (17, 29, 43), the selected arm receives the 128 largest
fit-pool NLL rows, tie-broken by source identifier. The random control receives
128 rows sampled uniformly from the same fit pool. Both train for exactly one
epoch and 128 optimizer steps.

## Chat formatting and training

The user and system messages are rendered by the pinned tokenizer's
apply_chat_template with enable_thinking=False. Training sequences use the
same template with an assistant summary message. The runner verifies that the
generation prompt is an exact prefix of the completed conversation, masks
system and user tokens with label -100, and computes loss only on assistant
summary and end-of-turn tokens.

The base model is loaded offline in float16 on Apple MPS. Only PEFT LoRA
parameters are trainable. Each arm resets the adapter with its locked seed,
uses AdamW at 1e-4 with betas (0.9, 0.999), epsilon 1e-8, weight decay 0.01,
batch size one, and gradient clipping at 1.0. Adapter
weights are saved with PEFT safe serialization outside the repository. The
base checkpoint file manifest must remain unchanged.

Held-out generation uses the pinned Qwen3 non-thinking settings:
temperature 0.7, top-p 0.8, top-k 20, repetition penalty 1.0, and at most
768 new tokens. Within each
training seed, a source-derived per-document generation seed is shared across
the base, selected, and random arms. This pairs sampling noise across arms.
The three-seed run remains one local execution; it is not a clean second
environment reproduction.

## Metrics and locked decision rule

The primary outcome is the mean per-document difference in ROUGE-L F1,
averaged across the three selected and random training seeds. The 95%
confidence interval resamples assessment documents as paired clusters 10,000
times with seed 20261007. A Candidate requires all of the following:

- selected minus random mean ROUGE-L is at least +0.02;
- the paired bootstrap lower bound is above zero;
- selected ROUGE-L is not below the untouched base;
- selected mean assistant-target NLL is no more than 0.05 above base; and
- every locked completion and NLL is present and finite.

Otherwise the disposition is NoCandidate. The report also includes ROUGE-1/2,
output/reference token ratio, per-seed aggregates, training losses, elapsed
time, process peak RSS, and a layer-14 residual activation patch on the first
16 assessment rows per updated arm and seed. The patch includes an identity
control with maximum absolute NLL error 1e-5. It is a layer-level diagnostic
only.

## Custody, stops, and local acceptance

The V1 raw-input cache remains under its original owner-only root. V2 run
records, raw rows, references, fit scores, generated summaries, adapter
weights, and activation captures stay below
$HOME/.local/share/aligned-rsi-billsum-chat-template-adaptation-v2/, with
directories mode 0700 and files mode 0600. The repository release contains
aggregate metrics and digests only. There is no automatic expiry; the owner
controls retention and may remove this V2 root after preserving any needed
reproduction evidence.

prepare verifies exact model and dataset bytes and writes the frozen fresh
cohort roster. run turns on Hugging Face offline mode, performs one bounded
local execution, and writes a private run receipt plus an aggregate report.
verify reconstructs metrics from the private outputs and pinned references,
checks source, roster, adapter, and base-model digests, and writes a
digest-bound local acceptance receipt. It does not create an independent
review decision.

The runner stops on a changed input or source digest, an empty or duplicate
row, template-prefix mismatch, non-finite loss, failed adapter or patch
control, incomplete assessment, base-weight change, custody violation, MPS
failure, or the 180-minute wall-clock limit. A failed run remains failed; do
not retry under this identity. Any change to the model, data, protocol,
runtime, cohort, threshold, or measurement starts a new state slice.

## Reproduction

First acquire the pinned raw inputs if they are not already cached:

~~~sh
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_local_billsum_v1 prepare
~~~

Install the hash-checked V2 dependency closure and run from the repository root:

~~~sh
uv pip install --python .venv/bin/python --require-hashes -r experiments/continual_learning/aligned_rsi_billsum_chat_template_v2_requirements.lock
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_billsum_chat_template_v2 prepare
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_billsum_chat_template_v2 run
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_billsum_chat_template_v2 verify
~~~

run requires the prepared roster and uses local files only. verify accepts only
the exact completed run bound by the aggregate report. Local acceptance is
INTERNAL_PASS and is explicitly not INDEPENDENT_ACCEPT.

## References

- [Pinned Qwen3-0.6B model card](https://huggingface.co/Qwen/Qwen3-0.6B/blob/c1899de289a04d12100db370d81485cdf75e47ca/README.md)
- [Hugging Face PEFT configuration and model guide](https://huggingface.co/docs/peft/main/tutorial/peft_model_config)
- [Google Research ROUGE scorer package](https://pypi.org/project/rouge-score/)
