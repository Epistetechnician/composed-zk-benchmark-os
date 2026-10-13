# Aligned RSI BillSum chat-template adaptation V5 execution closure

State slice: `aligned-rsi-billsum-chat-template-adaptation-v5`.

Governance slice: `global-experiment-assurance-lifecycle-v1`.

Disposition: `ExecutionFailedMPSOutOfMemory`. V5 is terminal.

## Result

The single frozen offline Apple MPS run failed on the first selected-arm
training batch for seed 17. PyTorch reported:

~~~text
RuntimeError: MPS backend out of memory
MPS allocated: 46.85 GiB
other allocations: 20.81 MiB
max allowed: 47.74 GiB
Tried to allocate 3.07 GiB on shared pool
~~~

No optimizer step completed. The adapter was not saved. The run did not train
the random-control arm, evaluate either updated arm, execute the layer patch,
write an aggregate report, or issue local acceptance. Its scientific
disposition is `INCOMPLETE_NO_CANDIDATE_DISPOSITION`; neither `Candidate` nor
`NoCandidate` is supported.

Before the failure, the run loaded the pinned local model, scored all 512 fit
documents, selected the loss-ranked roster in process memory, and completed
untouched-base evaluation for all 64 held-out documents under each of the
three paired generation seeds. These intermediate values were not persisted.
The run's external directory contains only its owner-only execution status.
The V5 repository release directory was never created. The cached model and
dataset file manifests still match their prepared-input manifests. No model
weights, raw rows, generations, fit losses, or adapter weights were written
to the repository.

## Frozen identity and evidence

- Repository revision: `62bf2bfb5b6775327eb635d722bd2a715a2c6a42`; the
  worktree was already dirty.
- Run ID: `run-20261006T201627257019Z`; started at
  `2026-10-06T20:16:27.257019Z` and recorded failure at
  `2026-10-06T20:33:11.493835Z`.
- Prepared-input SHA-256:
  `ed41acda9a557b29283f7d42d6bf4b6a1e5873af6f7231248c19580af53888d4`.
- Fit roster SHA-256:
  `9dab518511424ce830a4598bc45dd96f61be4de51839a3252866c750b84ca6eb`.
- Assessment roster SHA-256:
  `abc9cfbebdbc4cb24c4d271e3aeb70070d419bba3e29537e9f3ca4cdd51b13c1`.
- Pinned model manifest SHA-256:
  `e77990a87387a8bd81db5a96b8ec8b2853d08b1c4b7fa65c8a34d768eab6459b`.
- Pinned dataset manifest SHA-256:
  `03ff3ea855c3e5840722315fb7a986da0001b2a3a932b5e6cd98b34eb967eda1`.
- Runner SHA-256:
  `2c6b90e3623ae43414ed0616f631a1871c8ea28458a4782c7ea644663e62c931`.
- Protocol SHA-256:
  `37fa77850e4122f6ca34322423672ad26bdb3b330e8aad6c4c1881f3a77c685a`.
- Protocol-manifest SHA-256:
  `8f1269fe22f2e08626bbcc8b7bc0292f84a4f213c15da76c2553e963484ea0ee`.
- Focused-test SHA-256:
  `947fdd840b1dbac5efe49cfe3029426ce7f77fb4ce1210efb97100d7c6fae0ed`.
- Requirements-lock SHA-256:
  `847e6395a804c5c1f451295183a2237d0eace75b51d8511f02efb2c56bb1dd50`.
- Prepared fresh cohorts: 512 fit and 64 assessment documents. Eight
  repeated-source groups (16 train rows) and no test source groups were
  excluded. Token bounds passed without truncation; fit prompt/target ranges
  were 526-1,279 / 14-496 tokens, and assessment ranges were 719-1,279 /
  18-489 tokens.
- Focused V5 contract tests passed 12/12; `uv pip check` passed for 131
  packages. These checks do not turn the failed model execution into a pass.
- Run root mode was `0700`; execution status mode was `0600`. The V5 release
  directory is absent. No process remains active.

## Assurance and claim boundary

- End-to-end assurance: not achieved. `INTERNAL_PASS` applies only to the
  focused local contract-test and dependency-check scope; it does not apply to
  the V5 experiment.
- Reviewer status: local acceptance not issued; independent acceptance was
  not requested or performed.
- Reproducibility status: one local execution failed; `REPRODUCED_LOCAL` was
  not achieved.
- Data custody: pinned Qwen3-0.6B revision
  `c1899de289a04d12100db370d81485cdf75e47ca` and federal BillSum revision
  `3d8510441c06a3d9dfb32eb0d7f80151730bcc4f` remained in the existing
  owner-only cache. Prepared receipt and failed-run status remain under the
  V5 `0700` owner root. No acceptance receipt or aggregate release exists.
- Claim ceiling: `LocalDevelopmentBillSumChatTemplateCurriculumQualificationV5`
  was not earned. This run establishes no curriculum benefit, model-update
  utility, alignment, recursive self-improvement, mechanism, benchmark, or
  production result.
- Next blocked gate: the V5 instruction makes this failure terminal. Any
  continuation needs an explicitly authorized new state slice and a fresh
  memory-safe training/evaluation packet. This closure does not authorize a
  retry, a changed batch size, or another model execution.
