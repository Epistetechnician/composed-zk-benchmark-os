# Aligned RSI BillSum chat-template adaptation V7

State slice: aligned-rsi-billsum-chat-template-adaptation-v7.

Governance slice: global-experiment-assurance-lifecycle-v1.

Status: one frozen, offline, local Apple MPS qualification and local-only
acceptance are authorized by the user's continuing end-to-end instruction.
Independent acceptance is not requested.

Claim ceiling: LocalDevelopmentBillSumChatTemplateCurriculumQualificationV7.

## Question and fixed decision rule

V1 ended NoCandidate; V2 and V3 stopped during preparation; V4 hit its
wall-clock limit; V5 failed with MPS out-of-memory; and V6 stopped when adapter
sealing rejected the README emitted by the pinned PEFT serializer. Those
identities and outcomes are terminal. V7 is a fresh qualification. It reads
only the pinned raw Qwen3 model and federal BillSum train/test bytes. It
reconstructs V1, V5, and V6 source rosters from those raw inputs only to remove
overlapping documents. No previous score, adapter, generation, activation,
private run, or outcome is an input.

The hypothesis is that selecting the 32 highest untouched-base
assistant-target-NLL examples from a fresh 512-document fit pool yields at
least +0.02 paired held-out ROUGE-L F1 over a uniform 32-example curriculum
after the same number of optimizer steps. The untouched model is a separate
baseline. Three fresh adapter-training seeds are fixed at 109, 127, and
149; assessment contains 64 fresh federal bills. For each training seed and
held-out bill, base, selected, and random arms share the same sampling seed.

The primary estimate is the mean document-level difference between selected
and random ROUGE-L F1, averaging the three paired training-seed outcomes for
each document. The 10,000-resample document bootstrap uses seed 20261009.
Candidate requires every gate below:

- mean paired effect is at least +0.02;
- the bootstrap 95% lower bound is above zero;
- selected mean ROUGE-L is at least the untouched-base mean;
- selected assistant-target NLL is no more than 0.05 above base; and
- every required generation, NLL, adapter, and layer-diagnostic value is
  complete and finite, with identity-patch error at most 1e-5.

A complete run missing any scientific gate is NoCandidate. Preparation,
execution, custody, resource, wall-clock, or validation failure is terminal
under V7 and has no scientific candidate disposition. Assessment data cannot
be used to retune the protocol.

Variance sources are held-out document composition, curriculum composition,
three fixed adapter-training seeds, sampled decoding, and MPS/runtime numeric
behavior. Pairing shares decoding randomness across arms for each document
and training seed. The document bootstrap is the uncertainty procedure; three
training seeds are not broad model or population replication.

## Frozen inputs and fresh cohorts

- Model: Qwen/Qwen3-0.6B, revision
  c1899de289a04d12100db370d81485cdf75e47ca, Apache-2.0.
- Data: FiscalNote/billsum, revision
  3d8510441c06a3d9dfb32eb0d7f80151730bcc4f, CC0-1.0. Only federal train
  and test Parquet files are read; ca_test is excluded.
- Both inputs remain in the existing owner-only V1 cache. V7 does not fetch,
  copy, or modify those bytes. Execution sets the model and datasets libraries
  to offline mode.
- Document ID is SHA-256 of UTF-8 source bill text. Every row for a repeated
  source hash is excluded within its split.
- V1 exclusions are reconstructed from the first 512 train and 128 test rows
  sorted by SHA-256 of text, NUL, summary. V5 then V6 rosters are
  reconstructed in order by ascending source hash from the remaining
  duplicate-free, no-truncation eligible rows: 512 fit and 64 assessment
  documents per version. The reconstruction uses no V5 or V6 scientific
  output bytes.
- A read-only feasibility audit over the pinned raw inputs reconstructed all
  prior exclusions and found eight repeated train-source groups (16 rows), no
  repeated test sources, and enough remaining rows for fresh V7 cohorts.
  The pinned model and dataset manifest digests are
  `e77990a87387a8bd81db5a96b8ec8b2853d08b1c4b7fa65c8a34d768eab6459b` and
  `03ff3ea855c3e5840722315fb7a986da0001b2a3a932b5e6cd98b34eb967eda1`.
  Reconstructed V1 fit/assessment exclusion digests are
  `0d25ecc5c577397d131332be3bd4660381f47e4bfb9a3420f70e4cf7e63eae5a` and
  `cd5d8e89c50cef363544b9831fed09aba98703bba5efe30e5f67975cb89fc908`;
  V5 digests are
  `9dab518511424ce830a4598bc45dd96f61be4de51839a3252866c750b84ca6eb` and
  `abc9cfbebdbc4cb24c4d271e3aeb70070d419bba3e29537e9f3ca4cdd51b13c1`;
  V6 digests are
  `4288836f34fef9362ea66889b7e307bc285045b60ead44653542d750a5e00d66` and
  `eeff4c21fbe6dd7d6b116d365f322e6087b394f9067933da9875899a3e1d19c8`.
  V7's 512 fit source-ID digest is
  20cf848ea84c1de6db9defda4e539083852509eab7ff8ff2adc10964767ecb13;
  its 64 assessment source-ID digest is
  568e0de51fa481f912b1aef76b8ce2834a1e06cd1900cda0766f74e670336670.
  These digests bind sorted source IDs; the IDs and texts remain private.
- V7 fit prompts contain 778-1,280 tokens and assistant targets 17-503 tokens.
  Assessment prompts contain 880-1,279 tokens and targets 50-436 tokens.
  The eligibility ceiling remains 1,280 prompt tokens and 512 assistant
  target tokens. No source or reference is truncated.
- The pinned Qwen3 template must produce assistant end marker <|im_end|>
  token 151645, followed by exactly one trailer newline token 198. Loss
  includes the summary and end marker, and excludes the trailer.

The frozen packet binds the model and dataset file manifests, chat-template
digest, token termination behavior, duplicate counts, reconstructed V1/V5/V6
exclusion digests, and V7 roster digests before model loading. Expected
preparation manifests are checked against the pinned input bytes at runtime;
V6's historical manifest values are context only, not a substitute for that
check.

## Treatment, control, training, and measurement

The untouched base is the baseline. The selected arm ranks the 512 fit
documents by untouched-base assistant-target NLL, descending with source hash
as the tie-breaker, and trains on the top 32. The random arm samples 32 fit
documents uniformly without replacement for each training seed. Each updated
arm receives one epoch, four-example effective update groups, and exactly
eight AdamW optimizer steps.

PEFT LoRA rank 8 targets q_proj and v_proj with alpha 16 and dropout 0.
AdamW uses learning rate 1e-4, betas (0.9, 0.999), epsilon 1e-8, weight
decay 0.01, and one gradient clip at 1.0 per optimizer step. Only LoRA
parameters are trainable. The base checkpoint is re-digested after all arms.

Each training forward processes one unpadded example, projects vocabulary
logits only at assistant target-prediction positions, and uses non-reentrant
transformer-layer activation checkpointing. Four per-example summed
cross-entropies are divided by their group's total target-token count and
backpropagated before one clip and optimizer step. This is the token-weighted
mean objective of an ordinary four-row causal batch. Focused tests compare
both loss and LoRA gradients with the full causal-loss path.

Generation uses the pinned Qwen3 non-thinking chat template, temperature
0.7, top-p 0.8, top-k 20, repetition penalty 1.0, and at most 512 new
tokens. Standard rouge-score 0.1.2 ROUGE-1/2/L F1 uses no stemming.
Secondary measures include held-out assistant-target NLL, output/reference
token ratio, per-seed ROUGE-L, training loss, and a fixed layer-14 residual
activation patch with identity control on the first 16 held-out documents for
each updated arm and seed. This layer-level diagnostic does not identify
features or establish a mechanistic explanation.

The report records wall time, peak process RSS, MPS memory counters, and
energy as not_measured. One run has a hard 360-minute limit covering model
loading, fit scoring, training, and held-out evaluation. MPS out-of-memory,
wall-clock breach, or any other failed gate ends V7; there is no CPU fallback
or retry. No provider call, remote worker, paid execution, network access
during model execution, or energy or total-cost claim is made.

## Adapter serialization and custody

The pinned peft 0.21.2 serializer's expected adapter tree is exactly
README.md, adapter_config.json, and adapter_model.safetensors. All three
files are checked as regular private files, included in the tree digest, and
rechecked during local report reconstruction. The PEFT README is capped at
64 KiB and must decode as UTF-8. Adapter files remain private and are never
copied to the repository release.

Raw rows, fit losses, generations, adapter files, residual captures, and
private receipts stay under
$HOME/.local/share/aligned-rsi-billsum-chat-template-adaptation-v7/ with
owner-only directories and files. The pinned input cache is read-only. The
repository release is limited to aggregate metrics, local acceptance, and a
digest manifest. No raw bill text, reference, generated summary, source ID,
fit ranking, activation, or adapter weight is included. Automatic expiry is
disabled; private retention remains owner-controlled.

The private run binds repository revision and dirty state, V7 runner, focused
tests, this protocol, machine contract, requirements lock, current AGENTS.md,
prepared-input digest, model/data manifests, prior-exclusion and fresh-roster
digests, adapter file digests, and per-arm measurements. The local verifier
reconstructs the aggregate report from that private run and pinned references;
only after every check passes does it write the local INTERNAL_PASS acceptance
receipt. This is not independent acceptance.

Expected release directory:
release/aligned_rsi_billsum_chat_template_v7/. A failed run retains its
terminal status outside the repository and creates no release. Do not retry
or alter V7 after its execution starts.

## Reproduction commands

Use the existing .venv; do not install packages or access the network. Run
the focused tests, freeze the exact local input receipt, then execute the one
authorized MPS run and its local verifier:

~~~sh
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m pytest -q experiments/continual_learning/tests/test_aligned_rsi_billsum_chat_template_v7.py
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_billsum_chat_template_v7 prepare
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_billsum_chat_template_v7 run
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_billsum_chat_template_v7 verify
~~~

Preparation is local and read-only with respect to pinned model/data bytes.
The run command is the sole model execution. The frozen contract refuses an
existing V7 release directory and records failed status under the owner-only
root.

## Assurance and claim boundary

The target assurance is INTERNAL_PASS for this exact local qualification
only if the focused checks, the complete single execution, and report
reconstruction pass. Reviewer status is local acceptance only;
INDEPENDENT_ACCEPT is not requested or claimed. REPRODUCED_LOCAL is not
claimed because no clean second environment is run. Data custody is limited
to the owner-only pinned public model and federal BillSum files plus the V7
owner-only run directory.

The ceiling is LocalDevelopmentBillSumChatTemplateCurriculumQualificationV7.
The result does not establish general alignment, recursive self-improvement,
a leaderboard result, feature-level mechanism, production readiness,
user-data performance, or independent acceptance. The next authority gate
for any higher claim is a fresh exact evidence packet and the authority
required for that claim.
