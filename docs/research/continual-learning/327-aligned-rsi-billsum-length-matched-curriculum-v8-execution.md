# Aligned RSI BillSum length-matched curriculum V8 execution record

State slice: `aligned-rsi-billsum-length-matched-curriculum-v8`.

Governance slice: `global-experiment-assurance-lifecycle-v1`.

## Disposition

The single frozen offline local Apple MPS run completed and the local verifier
reconstructed the aggregate report and acceptance receipt. Scientific
disposition: `NoCandidate`. The primary length-stratified loss-selected arm
scored below its matched random control. Local procedure assurance:
`INTERNAL_PASS`. Reviewer status:
`LOCAL_ACCEPTANCE_ONLY_NO_INDEPENDENT_ACCEPT`; no independent acceptance was
requested or performed.

The configured claim ceiling is
`LocalDevelopmentBillSumLengthMatchedCurriculumQualificationV8`; it was not
earned. V8 is terminal under this identity. Do not rerun, retune, or alter its
threshold, cohort, runtime, data, or method. A materially new experiment
requires a separately authorized state slice and packet.

## Frozen identity and procedure

- Repository revision: `62bf2bfb5b6775327eb635d722bd2a715a2c6a42`. The worktree
  was already dirty; unrelated work was preserved.
- Run ID: `run-20261007T153154999313Z`, started at 2026-10-07 15:31:54.999313
  UTC. The runner recorded 14,125.03 seconds (3 hours, 55 minutes, 25.03
  seconds), within the 28,800-second limit.
- Prepared-input receipt SHA-256:
  `10c5f55d697a119c503b77237d0fc69778044a2f32b502e22d6363450139a084`.
- Model: `Qwen/Qwen3-0.6B`, revision
  `c1899de289a04d12100db370d81485cdf75e47ca`; model weights manifest SHA-256
  `e77990a87387a8bd81db5a96b8ec8b2853d08b1c4b7fa65c8a34d768eab6459b`.
- Dataset: `FiscalNote/billsum`, revision
  `3d8510441c06a3d9dfb32eb0d7f80151730bcc4f`; federal `train` and `test`
  only, excluding `ca_test`.
- Fresh fit pool: 768 documents, roster SHA-256
  `4876867a85986ec94a82b2b4e4e0b33839cfa92c4fbdf125448cf82ac285a212`.
- Fresh assessment: 128 documents, roster SHA-256
  `a8ba7aeb408bdad51bfe15a82a184309d9aa92fa7b4316a58d8f2d35b46e74cd`.
  The cohorts have zero overlap. Eight duplicate train-source groups (16
  rows) were excluded; the test split had no duplicate source groups.
- The runner reconstructed V1 exclusions and verified the V4-V7 prepared
  receipts and prior roster exclusions. No previous scientific outputs were
  used.
- Four trained arms (global loss, global random, length-stratified loss, and
  length-stratified random) used seeds 211, 307, 401, and 503. Each arm/seed
  used 128 examples and 32 optimizer steps. All 512 optimizer steps, 2,560
  held-out completions, 256 mechanistic diagnostic rows, and adapter receipts
  completed and were finite.
- Runtime: Python 3.14.5 on macOS arm64 with PyTorch 2.13.0, Transformers
  5.14.1, PEFT 0.21.2, datasets 5.0.1, and rouge-score 0.1.2. The exact
  package manifest is in `evaluation_report.json`.
- Before the model run, the 13 focused V8 tests passed, the locked environment
  reported 131 compatible packages, Python source validation passed, and
  `git diff --check` passed. These checks do not imply scientific success.

## Evaluation

The frozen primary metric was the paired per-document ROUGE-L F1 difference
between length-stratified loss selection and length-stratified random
selection, with a 10,000-resample document bootstrap.

- Mean effect (selected minus matched random): `-0.0413736`.
- Bootstrap 95% interval: `[-0.0551312, -0.0281227]`.
- Required minimum mean effect: `+0.02`; failed. The interval is entirely
  below zero.
- Mean ROUGE-L F1: selected `0.2727603`, matched random `0.3141338`, untouched
  base `0.2259883`.
- Selected-arm assistant-target NLL minus untouched-base NLL:
  `-0.5245532`; this component passed its ceiling but does not override the
  failed primary contrast.
- Global loss-selected versus global-random mean ROUGE-L difference:
  `-0.0343387` (95% interval `[-0.0478987, -0.0211087]`), secondary only.
- All locked outputs were finite; adapter receipts were complete; maximum
  identity-patch NLL error was `0`.
- The layer-14 residual-patch diagnostic had mean NLL delta `0.0608746` and
  recovered `0.1038686` of base activation on average. This is a diagnostic
  only and does not establish a feature-level or mechanistic claim.

The candidate rule therefore yields `NoCandidate`. On this one pinned model,
cohort, runtime, and local execution, the length-matched loss-selected
curriculum did not beat its random control. This result does not establish a
general result about curriculum learning, alignment, recursive
self-improvement, or other models and datasets.

## Resources and custody

- Device: local Apple MPS. Peak process RSS: 4,994,482,176 bytes. End-of-run
  MPS current allocation: 1,205,975,040 bytes; driver allocation:
  7,845,429,248 bytes. The latter two are end-of-run values, not peaks.
- Energy and total local compute cost: `not_measured`.
- Provider calls and provider spend: none; no provider calls occurred.
- Pinned model and dataset remained in the existing owner-only cache. Prepared
  receipt, raw rows, fit scores, generations, adapters, activation captures,
  and private run stayed under the owner-only V8 root. Automatic expiry is
  disabled; retention remains owner-controlled.
- The repository release is aggregate-only and contains exactly
  `evaluation_report.json`, `local_acceptance.json`, and
  `release_manifest.json`. It contains no raw data, source IDs, generated
  summaries, activations, or weights.

## Digest-bound local verification

The one `verify` invocation reconstructed and validated the report, private
run, adapter receipts, frozen source digests, and aggregate release.

- Assurance level: `INTERNAL_PASS` for local execution and exact-report
  reconstruction only.
- Reviewer status: `LOCAL_ACCEPTANCE_ONLY_NO_INDEPENDENT_ACCEPT`.
- Reproducibility status: `SINGLE_LOCAL_EXECUTION`; no clean second environment
  was run.
- Independent acceptance: `false`.
- Private run SHA-256:
  `5a6cdc81ab047aa45e736301afab318dd56c8b9038e8d3c24803c33296c08539`.
- Aggregate report SHA-256:
  `bc7f90e1f8882f21fcb6fad148f6d99d60390c0b901bcfd84bb4131bbff8e096`.
- Local acceptance receipt SHA-256:
  `cef4f9c581104b6a571d5ec2bc5ed4b516973b7ddd2723b8fa79cc161bc8a6bd`.
- Release manifest SHA-256:
  `40085987264261be0a166db73e47a72a1014070112ab0fb65e5709e6eaee9617`.
- Source manifest SHA-256:
  `8b292d4f10f81c3d291b4c9c277d9bb90bec74effdd9c8edbc1e743eb2002dbe`.
- Protocol SHA-256:
  `f00694b9a46d857ece4110cead28cbe6e6b7192d96b92b2565fd318313813028`.
- Machine contract SHA-256:
  `bf92cb8468a3d1647f357217ec92f376753ffee50942e312d9afb663454c2626`.
- Runner SHA-256:
  `a283132b28161dea1c6e1b389267f18b618f76d77cb3c1d213a1b237d7192e89`.
- Focused tests SHA-256:
  `adb8f6c0fe5b39dc65367390349ec09e7416c6494cce49791314117f01450438`.
- Requirements lock SHA-256:
  `e8c11d4a260328b27732188d1080891dd9da8cf253a6477e486b256fedcba085`.
- Repository instructions SHA-256 at execution:
  `ea6bd143df4f44591d8ac912bdd2f877db9c6cc1cfbfdc6587d36b762cb34234`.

The verifier reported `valid: true`, `INTERNAL_PASS`, `NoCandidate`, and
`independent_acceptance: false`. This is local acceptance of exact procedure
and evidence binding, not independent acceptance or a positive scientific
result.

## Claim boundary and next gate

The next blocked gate is any claim above the configured local qualification
ceiling or any deployment/publication decision requiring separate authority.
That would require a fresh evidence packet and the authority applicable to
that claim. V8 itself is terminal and cannot be retried or retuned.
