# Aligned RSI local BillSum adaptation V1 execution

State slice: `aligned-rsi-local-billsum-adaptation-internal-v1`.

## Disposition

- Assurance level: `INTERNAL_PASS`.
- Reviewer status: `LOCAL_ACCEPTANCE_ONLY_NO_INDEPENDENT_ACCEPT`.
- Reproducibility: `SINGLE_LOCAL_EXECUTION`; no clean second environment was run.
- Scientific disposition: `NoCandidate`.
- Claim ceiling: `LocalDevelopmentBillSumAdaptiveCurriculumQualificationV1`.
- Paid provider cost: USD 0.00.
- Independent acceptance: false.

The local verifier accepted the exact run receipt and aggregate release. This
acceptance covers local protocol, roster, digest, custody, output-completeness,
and report-reconstruction checks. It does not change the negative scientific
result.

The focused local suite passed 8 tests, including deterministic metric-property
cases and rejection checks for duplicate JSON keys, symlinked inputs, and an
incomplete assessment. Python syntax compilation and `git diff --check` also
passed. These are bounded local checks, not an independent review or a broad
security assessment.

The bounded threat review treated the pinned Hub downloads, cached files,
Parquet rows, private run record, and public report as trust boundaries. The
runner checks pinned revisions and content digests, allows only the federal
train/test files, rejects symlinks and duplicate JSON keys, loads model files
with `local_files_only=True` and `trust_remote_code=False`, validates complete
rosters and finite outputs, and reconstructs aggregate claims before local
acceptance. The run sets the Hugging Face offline switches, but no OS-level
network firewall was applied. Hub account/repository compromise and host
compromise were not assessed.

## Frozen identity and custody

- Repository revision: `62bf2bfb5b6775327eb635d722bd2a715a2c6a42`; the checkout was
  dirty before and during execution.
- Runner SHA-256: `501ce774a65d078087c21202ac243f671e6de062396b6b2c999bfbca1a2b13df`.
- Focused test file SHA-256:
  `4efb1473b4adf1642825e7898f69268c7ecee2f904cebe4c3a47c1e7c6a1807d`.
- Protocol SHA-256: `a19c9ceaf593ea5fd1968988cfeca7331929172b923823dacb6d85cd518fb055`.
- Machine-readable contract SHA-256:
  `af2e30f7edb179c9939779c67257e8810ef2b07edc0ecedd8e34777fa8bcabbb`.
- Run ID: `run-20261006T151344571388Z`.
- Prepared model/data bundle SHA-256:
  `7d7afc33d5343c2d543648de9cfc73f523d94b7606bf879b7d600deae68c79f1`.
- Private run record SHA-256:
  `a89c461bdce2aba98cc7319a3712fa17ce28bc12c6bccd79ecc5d037393ff54e`.
- Public evaluation report SHA-256:
  `a93bbe15c7b1835902c4642c649b3cd0a765474d575d42cd075a5a9f7993f619`.
- Local acceptance receipt SHA-256:
  `f6390380e22f89db770793df19ab1f9f83bfc76bf124f738ddaf8a9794ef4588`.
- Source data was the pinned `FiscalNote/billsum` federal `train` and `test`
  splits: 18,949 and 3,269 unique rows. `ca_test` was not downloaded.
- Model was the pinned `Qwen/Qwen3-0.6B` checkpoint. Adapter weights, document
  text, generated summaries, per-document scores, and activations remain under
  `/Users/shaanp/.local/share/aligned-rsi-local-billsum-adaptation-v1/`, whose
  custody directories are mode `0700`. The repository release contains only
  aggregate results and digests.
- No automatic expiry or deletion was configured for the private run root; it
  remains owner-controlled for reproduction until the owner removes it. This
  retention duration was not time-bounded in the frozen protocol and is a
  documented packet limitation.

## Measured results

The run used 512 fit-pool documents, 128 held-out documents, three seeds, two
128-example LoRA arms per seed, and 96 layer-patch diagnostic rows. Elapsed
model-run time was 2,070.99 seconds (34 minutes 31 seconds) on Apple MPS.
Energy and peak memory were not measured.

| Arm | Mean held-out ROUGE-L F1 | Mean target NLL | Output/reference token ratio |
| --- | ---: | ---: | ---: |
| Untouched base | 0.17338 | 2.60342 | 0.85791 |
| Loss-selected LoRA | 0.15118 | 2.00075 | 0.44275 |
| Random-control LoRA | 0.16675 | 1.98817 | 0.57374 |

The preregistered paired ROUGE-L effect (loss-selected minus random) was
`-0.01557`, with a paired document-bootstrap 95% interval
`[-0.02179, -0.00926]`. The selected arm also fell below the untouched base.
Both conditions make the frozen candidate rule fail.

| Seed | Loss-selected ROUGE-L | Random-control ROUGE-L | Paired difference |
| ---: | ---: | ---: | ---: |
| 17 | 0.13700 | 0.17044 | -0.03343 |
| 29 | 0.13729 | 0.15437 | -0.01707 |
| 43 | 0.17923 | 0.17545 | +0.00378 |

Selected-arm target NLL was `0.60266` below the untouched base on average,
while its output/reference token ratio was lower. That pattern is consistent
with shorter completions; it does not establish why the ROUGE-L result fell.
The layer-14 identity patch had maximum absolute NLL error `0.0`. Replacing
adapted activations with base activations changed target NLL by `+0.13673` on
average and recovered about `24.88%` of the measured base-to-adapted NLL gain.
This is a layer-level intervention result only.

Per-seed training losses (selected/random) were `2.72128/2.14212`,
`2.72137/2.13409`, and `2.71942/2.10181`. Output/reference token ratios by
seed were selected `0.40423`, `0.33345`, `0.59058` and random `0.64387`,
`0.45462`, `0.62272`.

## Limits and next gate

This is one local experiment on one summarization task, one small base model,
one data split, and one three-seed run. It is not a public leaderboard result,
a clean-room reproduction, general alignment evidence, general recursive
self-improvement, feature-level mechanistic attribution, or production
readiness. The local acceptance is not independent review.

The next research step is a fresh, preregistered state slice if the owner wants
to test a different adaptation hypothesis. This V1 result must remain
`NoCandidate` and may not be retuned on the same assessment cohort. Any claim
above the stated local qualification ceiling requires new evidence and its
applicable review or operational authority; no independent acceptance was
requested for this local release.
