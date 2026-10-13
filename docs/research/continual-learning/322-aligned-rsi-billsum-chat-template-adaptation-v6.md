# Aligned RSI BillSum chat-template adaptation V6

State slice: `aligned-rsi-billsum-chat-template-adaptation-v6`.

Governance slice: `global-experiment-assurance-lifecycle-v1`.

Status: one frozen, offline, local Apple MPS qualification and local-only
acceptance are authorized by the user's continuing end-to-end instruction.
Independent acceptance is not requested.

Claim ceiling: `LocalDevelopmentBillSumChatTemplateCurriculumQualificationV6`.

## Question and preregistered decision rule

V1 was `NoCandidate`; V2 and V3 stopped during preparation; V4 reached its
wall-clock limit during training; and V5 failed on its first adapter-training
batch with MPS out-of-memory. Each identity is terminal. V6 is a fresh
qualification. It reuses only the pinned raw model and federal BillSum files.
V1 source IDs and the V5 fit/assessment rosters are reconstructed from those
raw inputs only to exclude overlapping documents. No earlier score, adapter,
generation, activation, private run, or outcome is an input to V6.

The hypothesis is that selecting the 32 highest untouched-base assistant
target-NLL examples from a fresh 512-document fit pool yields at least `+0.02`
paired held-out ROUGE-L F1 over a uniform 32-example curriculum after the same
number of optimizer steps. The untouched model is a separate baseline. The
experiment uses three adapter-training seeds (`59`, `71`, `97`) and 64 fresh
held-out federal bills. For each training seed and held-out bill, base,
selected, and random arms share the same sampling seed.

The primary estimate is the mean document-level difference between selected
and random ROUGE-L F1, averaging the three paired training-seed outcomes for
each document. A 10,000-resample document bootstrap uses seed `20261008`.
`Candidate` requires all of these gates:

- the mean paired effect is at least `+0.02`;
- the bootstrap 95% lower bound is above zero;
- selected mean ROUGE-L is at least the untouched-base mean;
- selected assistant-target NLL is no more than `0.05` above base; and
- every required generation, NLL, adapter, and layer-diagnostic value is
  complete and finite, with the identity-patch error at most `1e-5`.

A complete run that misses any scientific gate is `NoCandidate`. Preparation,
execution, custody, memory, wall-clock, or validation failure is terminal and
has no scientific candidate disposition. Assessment data cannot be used to
retune the protocol.

Variance sources are held-out document composition, curriculum composition,
three fixed adapter-training seeds, sampled decoding, and MPS/runtime numeric
behavior. Pairing shares decoding randomness across arms for each document
and training seed. The document bootstrap is the uncertainty procedure; three
training seeds are not represented as broad model or population replication.

## Frozen inputs and disjoint cohorts

- Model: `Qwen/Qwen3-0.6B`, revision
  `c1899de289a04d12100db370d81485cdf75e47ca`, Apache-2.0.
- Data: `FiscalNote/billsum`, revision
  `3d8510441c06a3d9dfb32eb0d7f80151730bcc4f`, CC0-1.0. Only federal `train`
  and `test` Parquet files are included; `ca_test` is excluded.
- Runtime: exact locally installed package set is recorded in the machine
  contract and hash-locked V6 requirements file. It matches the previously
  qualified local runtime; V6 does not install or fetch packages.
- Raw model and data bytes are read only from the existing owner-only V1 input
  cache. Execution disables network access and uses local-only model loading.
- A document ID is SHA-256 of the UTF-8 source bill text. All rows belonging
  to a repeated source hash are excluded within each split.
- V1 exclusions are rebuilt from the first 512 train and 128 test rows sorted
  by SHA-256 of `text || NUL || summary`. V5 exclusions are rebuilt by
  reapplying V5's frozen source-hash order and no-truncation token limits to
  raw pinned inputs, then excluding its 512 fit and 64 assessment IDs.
  Exclusion IDs are summarized by count and digest; no V5 scientific output
  is read.
- After those exclusions, V6 selects 512 train fit documents and 64 test
  assessment documents in ascending source-hash order. The tokenizer audit
  found 1,923 eligible unique train rows and 382 eligible unique test rows;
  selected cohorts are disjoint from V1 and V5 and have no cross-split source
  overlap.
- Prompt eligibility is at most 1,280 chat-template tokens; assistant target
  eligibility is at most 512 tokens. No source or reference is truncated.
  The target contains the assistant summary and `<|im_end|>` token `151645`;
  the Qwen3 trailer newline token `198` is checked and excluded from loss.

The protocol binds the exact chat-template digest, tokenizer termination
behavior, raw input manifests, duplicate exclusions, and selected roster
digests before model loading.

## Treatment, control, training, and measurement

The untouched base is the baseline. The selected arm ranks the 512 fit
documents by assistant-target NLL under the untouched base, descending with
source digest as the tie-breaker, and trains on the top 32. For every training
seed, the random arm samples 32 fit documents uniformly without replacement.
Each updated arm receives one epoch, the same eight AdamW optimizer steps,
and the same four-example effective update groups.

PEFT LoRA rank 8 targets `q_proj` and `v_proj` with alpha 16 and dropout 0.
AdamW uses learning rate `1e-4`, betas `(0.9, 0.999)`, epsilon `1e-8`, weight
decay `0.01`, and one gradient clip at `1.0` per optimizer step. Only LoRA
parameters are trainable. The base checkpoint is re-digested after all arms.

To address the V5 MPS allocation failure, V6 makes each training forward pass
one unpadded example, applies the vocabulary projection only to assistant
target-prediction positions, and uses non-reentrant transformer-layer
activation checkpointing. Four per-example summed cross-entropies are divided
by the accumulation group's total target-token count and backpropagated before
one clip and optimizer step. This is the same token-weighted mean objective as
the ordinary four-row causal batch. A tiny Qwen3/PEFT parity test compares
both loss and LoRA gradients before execution. MPS OOM is terminal; CPU
fallback and retry are disabled.

Generation uses the pinned Qwen3 non-thinking chat template, sampling at
temperature `0.7`, top-p `0.8`, top-k `20`, repetition penalty `1.0`, and at
most 512 new tokens. Standard `rouge-score==0.1.2` ROUGE-1/2/L F1 uses no
stemming. Secondary measures include held-out assistant-target NLL,
output/reference token ratio, per-seed ROUGE-L, training loss, and a fixed
layer-14 residual activation patch with an identity control on the first 16
held-out documents for each updated arm and seed. The patch is a layer-level
diagnostic and does not identify features or establish a mechanistic
explanation.

The report records wall time, peak process RSS, MPS memory counters, and
energy as `not_measured`. The run has a hard 360-minute limit spanning model
loading, fit scoring, training, and held-out evaluation. A local MPS failure
or limit breach is terminal. There are no provider calls, remote workers,
paid execution, network access during model execution, or fallback device.
No measured energy or full economic-cost claim is made.

## Custody, verification, and release

Raw rows, fit losses, generations, adapter files, residual captures, and
private receipts remain under
`$HOME/.local/share/aligned-rsi-billsum-chat-template-adaptation-v6/` with
owner-only directory and file modes. Repository output is aggregate-only.
The cached model and raw data remain in the existing owner-only V1 input
directory; V6 does not copy them. Automatic expiry is disabled and retention
remains under owner control.

The private run binds the repository revision and dirty state, V6 runner,
focused tests, this protocol, machine contract, requirements lock, current
`AGENTS.md`, prepared-input digest, model/data manifests, roster digests,
adapter file digests, and complete per-arm measurements. The local verifier
reconstructs the report from that private run and pinned references, checks
all arm/seed/document cells and controls, and only then writes an
`INTERNAL_PASS` local acceptance receipt. A local result is not independent
acceptance.

Expected release directory:
`release/aligned_rsi_billsum_chat_template_v6/`. It may contain only the
aggregate report, local acceptance receipt, and release manifest. If the run
fails, its owner-only terminal status is retained and no release is created.
Do not retry or alter V6 after its execution starts. Any continuation after a
failure requires a new state slice and a newly frozen packet.

## Reproduction commands

Use the existing `.venv`; do not install packages or access the network.
From the repository root, run focused tests, then freeze the exact input
receipt, then execute the one authorized run and its local verifier:

~~~sh
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m pytest -q experiments/continual_learning/tests/test_aligned_rsi_billsum_chat_template_v6.py
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_billsum_chat_template_v6 prepare
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_billsum_chat_template_v6 run
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_billsum_chat_template_v6 verify
~~~

Preparation is local and read-only with respect to the raw cache. The `run`
command is the sole model execution. The frozen contract refuses an existing
V6 release directory and writes failed run status outside the repository.

## Assurance and claim boundary

The intended assurance is `INTERNAL_PASS` for this exact local qualification
only if all focused checks, the complete single execution, and report
reconstruction pass. Reviewer status is local acceptance only;
`INDEPENDENT_ACCEPT` is not requested or claimed. `REPRODUCED_LOCAL` is not
claimed because no clean second environment is run. Data custody is limited to
the owner-only pinned public model and federal BillSum files plus the V6
owner-only run directory.

The ceiling is `LocalDevelopmentBillSumChatTemplateCurriculumQualificationV6`.
The result does not establish general alignment, recursive self-improvement,
a leaderboard result, feature-level mechanism, production readiness,
user-data performance, or independent acceptance. The next authority gate
for any higher claim is a fresh exact evidence packet and the authority
required for that claim.
