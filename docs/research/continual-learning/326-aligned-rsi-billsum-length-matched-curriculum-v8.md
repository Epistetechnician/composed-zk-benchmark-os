# Aligned RSI BillSum length-matched curriculum V8

State slice: `aligned-rsi-billsum-length-matched-curriculum-v8`.

Governance slice: `global-experiment-assurance-lifecycle-v1`.

Status: one frozen, offline local Apple MPS qualification and local report reconstruction are authorized by the user's continuing end-to-end instruction. V7 remains terminal `NoCandidate`; this is a new hypothesis and identity.

## Question and hypothesis

V7's fit-loss-selected arm scored below its random control. V8 tests whether that result persists when loss-selected examples and random controls are matched across the same total-token-length strata.

Primary hypothesis: selecting the 16 highest untouched-base assistant-target-NLL examples within each of eight fixed fit-pool token-length bins improves held-out BillSum ROUGE-L F1 by at least 0.02 over selecting 16 examples uniformly from each same bin, at equal example and optimizer-step budgets.

The estimand is the mean per-document difference in ROUGE-L F1 between the length-stratified loss-selected and length-stratified random arms, after averaging four paired adapter-seed outcomes for each held-out document. The 95% interval is a 10,000-resample document bootstrap with fixed seed 20261010.

Candidate requires all of the following: mean primary effect at least +0.02; bootstrap 95% lower bound above zero; the length-stratified loss arm's mean ROUGE-L is not below untouched base; its mean assistant-target NLL is at most 0.05 above base; all locked generations, scores, training losses, activation diagnostics, and adapter receipts are complete and finite; and the frozen identity-patch tolerance passes. Otherwise the complete run is `NoCandidate`. The global-loss versus global-random contrast and other secondary metrics are diagnostic only and cannot replace or retune the primary test.

Variance sources include held-out document composition, four fixed adapter seeds, per-seed curriculum composition for random arms, sampled decoding, and MPS/runtime numeric behavior. All arms use identical per-document generation seeds within each training seed. The document bootstrap does not treat four training seeds as broad model or population replication.

## Frozen source and cohorts

- Model: `Qwen/Qwen3-0.6B`, revision `c1899de289a04d12100db370d81485cdf75e47ca`, Apache-2.0.
- Data: `FiscalNote/billsum`, revision `3d8510441c06a3d9dfb32eb0d7f80151730bcc4f`, CC0-1.0. Only federal `train` and `test` Parquet files are read; `ca_test` is excluded.
- Both inputs are the immutable pinned bytes in the existing V1 owner-only cache. No network access, download, or input mutation occurs during preparation or model execution.
- Document IDs are SHA-256 of UTF-8 source bill text. Every repeated source hash within a split is excluded. Fit and assessment must be split-disjoint.
- Reconstruct and exclude the V1 fit and assessment rosters from the first 512 train and 128 test rows ordered by SHA-256 of `text || NUL || summary`. Verify the owner-only prepared-input receipts for V4, V5, V6, and V7, then exclude every source ID in each fit and assessment roster. Those receipts are used only to prevent overlap. No earlier model weights, adapter, score, generation, activation, or scientific conclusion is an input. V2 stopped before a roster was materialized; V3 stopped before producing a prepared-input receipt or loading the model.
- From remaining duplicate-free eligible documents, order by SHA-256 source ID. The first 768 federal train documents form the fit pool; the first 128 federal test documents form assessment. Preparation must reconstruct and match the exact roster digests and token ranges frozen in the machine contract.
- Eligibility uses the pinned Qwen3 chat template. Prompt length is at most 1,280 tokens and assistant target length at most 512 tokens. No source or target truncation is allowed. The assistant loss includes the summary and `<|im_end|>` token 151645 and excludes exactly the trailing template newline token 198.
- The read-only feasibility audit found 899 eligible train documents and 254 eligible test documents after V1 and V4-V7 exclusions and duplicate filtering; no train/test source overlap. The frozen cohort selects 768 and 128 respectively. These counts and exact roster digests are included in the machine contract.

## Arms and selection

1. `untouched_base`: no parameter update; four paired assessment repeats.
2. `global_loss_selected`: the 128 highest fit-pool assistant-target NLL documents, descending NLL and ascending source ID as the tie-breaker.
3. `global_random_control`: 128 documents sampled uniformly without replacement from the fit pool for each fixed seed.
4. `length_stratified_loss_selected`: sort the 768 fit documents by `(prompt_token_count + assistant_target_token_count, source_id)`, split into eight consecutive bins of 96, then select the 16 highest untouched-base assistant-target-NLL documents from each bin, with source ID as the tie-breaker.
5. `length_stratified_random_control`: for each fixed training seed, sample 16 documents uniformly without replacement from each of those same eight bins in bin order, using Python `random.Random(seed XOR 0x53545241)`. The arm uses 128 unique fit documents and exactly the same bin counts as the length-stratified loss arm. Global random selection uses `random.Random(seed)`.

The bins are formed from fit data only before scoring outcomes. Assessment documents, references, generations, and assessment metrics cannot influence selection, training, or any packet choice.

## Training and evaluation

- Four fixed adapter seeds: 211, 307, 401, and 503. Each trained arm receives 128 examples and exactly 32 AdamW optimizer steps per seed, with four examples per effective update. Each arm roster is shuffled once with `random.Random(seed XOR 0x5A17)` before batching. One epoch is used; no early stopping or retuning.
- Qwen3 base weights remain immutable. PEFT LoRA rank 8, alpha 16, dropout 0, target modules `q_proj` and `v_proj`; learning rate 1e-4, betas (0.9, 0.999), epsilon 1e-8, weight decay 0.01, and gradient clip norm 1.0.
- Each forward processes one unpadded sequence; vocabulary projection is limited to assistant target-prediction positions; non-reentrant layer activation checkpointing is enabled. Four example losses are accumulated token-weighted before each optimizer step. Focused tests compare this path's losses and LoRA gradients with the full causal-loss path.
- Generation uses the pinned non-thinking Qwen3 chat template, temperature 0.7, top-p 0.8, top-k 20, repetition penalty 1.0, and at most 512 new tokens. It produces 2,560 paired held-out completions: five arms × four seeds × 128 assessment documents.
- Secondary measurements include ROUGE-1/2/L, assistant-target NLL, output/reference token ratio, per-seed ROUGE-L, exact training roster and total token counts, layer-14 residual activation patching with identity control for the first 16 assessment bills per trained arm and seed, elapsed time, peak process RSS, and MPS memory counters. The layer patch is a diagnostic only; it does not support a feature-level mechanism claim.

## Execution, cost, custody, and stopping

- One local Apple MPS run is permitted after source, protocol, manifest, dependency lock, and prepared-input receipt are frozen and digest-bound. All model and dataset libraries run offline.
- Hard wall-clock limit: 480 minutes for model loading, fit-pool scoring, four-arm training, assessment, and diagnostics. No CPU fallback, retry, or continuation is allowed. OOM, timeout, missing/non-finite output, failed custody, changed source/input identity, or local report reconstruction failure closes V8 terminally.
- No provider calls, remote workers, paid execution, user data, external reviewer, independent acceptance, Evidence Ledger mutation, or public deployment. Provider spend is none because there are no provider calls. Energy and total local compute cost are recorded as `not_measured`, never zero.
- Model and dataset bytes remain in the existing owner-only cache. Prepared IDs, raw rows, fit scores, generated summaries, adapters, activations, and private run receipts remain under a V8 owner-only `0700` directory with private files `0600`. Automatic expiry is disabled and retention remains owner-controlled.
- Repository release contains only `evaluation_report.json`, `local_acceptance.json`, and `release_manifest.json`. It must not contain raw text, references, source IDs, generations, activations, fit ranking, or adapter/model weights.

## Assurance and claim boundary

Local assurance target is `INTERNAL_PASS` for the frozen local procedure and exact report reconstruction. Reviewer status is local acceptance only; no independent acceptance is requested or claimed. Reproducibility status is `SINGLE_LOCAL_EXECUTION`; no clean second environment is run.

The maximum claim ceiling is `LocalDevelopmentBillSumLengthMatchedCurriculumQualificationV8`. This experiment does not establish general alignment, general recursive self-improvement, a leaderboard result, a feature-level mechanism, production readiness, user-data performance, independent acceptance, or clean second-environment reproduction. Any stronger claim requires a new exact evidence packet and its applicable authority.

## Frozen packet and local commands

Machine contract: `experiments/continual_learning/aligned_rsi_billsum_length_matched_v8.json`.

Runner: `experiments/continual_learning/aligned_rsi_billsum_length_matched_v8.py`.

Focused tests: `experiments/continual_learning/tests/test_aligned_rsi_billsum_length_matched_v8.py`.

Run preparation, the single local execution, and report reconstruction with the existing locked `.venv`; do not install packages or use the network:

~~~sh
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m pytest -q experiments/continual_learning/tests/test_aligned_rsi_billsum_length_matched_v8.py
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_billsum_length_matched_v8 prepare
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_billsum_length_matched_v8 run
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m experiments.continual_learning.aligned_rsi_billsum_length_matched_v8 verify
~~~

Preparation is read-only with respect to pinned model/data bytes and creates only the private V8 prepared-input receipt. The `run` command is the sole model-bearing execution. Any failed V8 identity or execution gate is terminal.
