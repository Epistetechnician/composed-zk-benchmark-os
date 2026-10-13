# Aligned RSI BillSum chat-template adaptation V7 execution record

State slice: aligned-rsi-billsum-chat-template-adaptation-v7.

Governance slice: global-experiment-assurance-lifecycle-v1.

## Disposition

The one frozen local execution completed and its report reconstructed
successfully. Scientific disposition: NoCandidate. The selected curriculum
did not improve paired held-out ROUGE-L over the equal-budget random control.
Local process assurance: INTERNAL_PASS. Reviewer status is local acceptance
only; no independent acceptance was requested or performed.

The configured claim ceiling is
LocalDevelopmentBillSumChatTemplateCurriculumQualificationV7. It was not
earned because the candidate rule failed. V7 is terminal after this completed
qualification; this identity must not be rerun or retuned.

## Frozen identity and procedure

- Repository revision: 62bf2bfb5b6775327eb635d722bd2a715a2c6a42. The repository
  was already dirty; unrelated changes were preserved.
- State slice: aligned-rsi-billsum-chat-template-adaptation-v7.
- Run ID: run-20261007T132131001473Z, started 2026-10-07 13:21:31.001473 UTC.
- Elapsed execution time: 3,282.54 seconds (54 minutes, 42.54 seconds), within
  the frozen 21,600-second limit.
- Prepared-input receipt SHA-256:
  1fb1fab0b68e0cc1bad7bbe4a920e0c223a8238bfbebfc00be75551fb2cc9adc.
- Pinned model manifest SHA-256:
  e77990a87387a8bd81db5a96b8ec8b2853d08b1c4b7fa65c8a34d768eab6459b.
- Pinned dataset manifest SHA-256:
  03ff3ea855c3e5840722315fb7a986da0001b2a3a932b5e6cd98b34eb967eda1.
- Fresh fit roster: 512 documents, SHA-256
  20cf848ea84c1de6db9defda4e539083852509eab7ff8ff2adc10964767ecb13.
- Fresh assessment roster: 64 documents, SHA-256
  568e0de51fa481f912b1aef76b8ce2834a1e06cd1900cda0766f74e670336670.
- Reconstructed V1, V5, and V6 exclusions, duplicate counts, and split
  disjointness match the frozen protocol. Eight repeated train-source groups
  (16 rows) were excluded; the test split had no duplicate source groups.
  No prior scientific output was consumed.
- Runtime: Python 3.14.5, macOS arm64, PyTorch 2.13.0, Transformers 5.14.1,
  PEFT 0.21.2, datasets 5.0.1, and rouge-score 0.1.2; the complete runtime
  manifest is in the aggregate report.
- Focused V7 tests passed 13/13. The locked environment check passed for all
  131 installed packages.
- The run scored all 512 fit documents; completed three untouched-base
  assessment repeats; trained six adapters for eight optimizer steps each;
  generated and scored 576 paired held-out outputs; and completed 96
  layer-level diagnostic rows.
- Every adapter sealed and reconstructed with exactly README.md,
  adapter_config.json, and adapter_model.safetensors. The six private adapter
  tree digests are:
  - loss-selected seed 109:
    95b7efdf496c42dd0dbf6a37f4c007ec73b96527e10f62e3c9a55aed445d9393
  - loss-selected seed 127:
    48134de4d5ee501ca3c654bd36278c9dc8ed2360a464294990a5b632a328871e
  - loss-selected seed 149:
    4be0cd6dd81e638d0d4e827d4ba28af749efddb169006a2b02a2c4053bc1f6f3
  - random control seed 109:
    02d8b48e36430caeef56d8b4764b22c82e1ce73847ea34da3d5081142c57804f
  - random control seed 127:
    85ba98c57e943c5e6a34ced82e69bd5f9db3a2cfebecfb5dae7783c7df1b59fa
  - random control seed 149:
    d17926d95ecaa9f74f156bb909264490bf5b02dc17df8d6d470f7c13b0c1d376

## Evaluation

The locked paired document-bootstrap result was:

- Selected minus random mean ROUGE-L F1: -0.0330771.
- Bootstrap 95% interval: [-0.0553072, -0.0121977].
- Required mean effect: at least +0.02; failed.
- Selected mean ROUGE-L F1: 0.2328613.
- Random-control mean ROUGE-L F1: 0.2659384.
- Untouched-base mean ROUGE-L F1: 0.2034330.
- Selected minus base assistant-target NLL: -0.2601365, within the frozen
  ceiling.
- All locked outputs were finite; identity-patch maximum absolute NLL error
  was 0.
- Candidate rule: NoCandidate because the selected-vs-random effect and
  confidence-bound gates failed.

This is a result on one pinned model, one fresh BillSum cohort, three adapter
seeds, and one local MPS run. It does not support curriculum benefit,
generalization beyond this cohort, general alignment, recursive
self-improvement, feature-level mechanism, leaderboard, or production claims.

## Resource and custody record

- Device: local Apple MPS; no OOM or CPU fallback occurred.
- Peak process RSS: 5,005,541,376 bytes.
- End-of-run MPS current allocation: 1,203,520,512 bytes.
- End-of-run MPS driver allocation: 7,832,109,056 bytes. This is not a peak.
- Energy and total local compute cost: not measured.
- Provider calls and provider spend: none; there were no provider calls.
- The pinned model and dataset remained in the existing owner-only V1 cache.
  Prepared receipt, raw rows, generations, adapters, activation captures, and
  private run stayed under the V7 owner-only root. The root and run directory
  are mode 0700; private files are mode 0600.
- Repository output contains only evaluation_report.json,
  local_acceptance.json, and release_manifest.json. No rows, source IDs,
  summaries, activations, or adapter weights were released.
- Automatic expiry is disabled; private retention remains owner-controlled.

## Digest-bound local verification

The local verifier reconstructed the aggregate report from the private run
and pinned references, validated the adapter trees and locked source digests,
and wrote the local acceptance receipt.

- Assurance level: INTERNAL_PASS for local execution and exact-report
  reconstruction only.
- Reviewer status: LOCAL_ACCEPTANCE_ONLY_NO_INDEPENDENT_ACCEPT.
- Reproducibility status: SINGLE_LOCAL_EXECUTION. REPRODUCED_LOCAL was not
  performed.
- Private run SHA-256:
  0c7262fd3fcb6ec362b849f728e9d44a9c0e5bbbcd50dc53df6812e28ce10c82.
- Public aggregate report SHA-256:
  744ad97509a43fd18729c8fa1155fa79c1c9f7373032b65f4abee34c251c6474.
- Local acceptance receipt SHA-256:
  122ca72d24cb3a56d6e9f2df16eecdbb0e3e3d2336acd70c8873afe427c5339c.
- Accepted report core SHA-256:
  a76cb61108e5ed8b8541ce573fb8be6645d331aaaf70d1cc5d16e6d333408517.
- Source manifest SHA-256:
  5047273052fe6051293f5d2f536509209dd2cb029e2622ff64582653d1026ce5.
- Protocol SHA-256:
  a88b0964a25b80dff47953f84615e0ab6360ca84c024dbbf9f4c8bef543b1575.
- Machine contract SHA-256:
  e57636b8fee68e2030882b016295e52120bace21ee85498aebc1d5806fdbe22c.
- Runner SHA-256:
  e0e32618f43ea32711d96d4b9883995f34b86320a1239f7b13143820c08b510d.
- Focused tests SHA-256:
  1590361088b416597b130b597ee5edaa86e885c302ed0534c69cc1992e7d59fc.
- Requirements lock SHA-256:
  ecc7b3b3db1fc626612128839c416f2d21ab6e0672870983a368f6cd57c7b883.
- Repository instructions SHA-256 at execution:
  6c5b58433305dd3e351e6250e2e84c1dca2e44149443f93184dd2ca07132dca5.

After this local verification passed, the terminal V7 disposition was
appended to AGENTS.md. The receipt binds the execution-time instruction digest
above. The verifier was not rerun after that documentation update.

## Claim boundary and next gate

The local acceptance validates the completeness and digest binding of this
single local procedure. It is not independent acceptance and does not turn
NoCandidate into a positive scientific result. V7's configured ceiling,
LocalDevelopmentBillSumChatTemplateCurriculumQualificationV7, was not earned.
Any stronger claim requires a fresh evidence packet and the authority required
for that claim. No retry or retuning under V7 is permitted.
