# Aligned RSI BillSum chat-template adaptation V4 execution closure

State slice: `aligned-rsi-billsum-chat-template-adaptation-v4`.

Governance slice: `global-experiment-assurance-lifecycle-v1`.

Disposition: `ExecutionFailedWallClockLimit`. V4 is terminal.

## Result

The single V4 offline Apple MPS run reached the frozen 180-minute limit during
selected-arm seed-17 training. The last progress line reported 96/128
optimizer steps. The process then recorded:

~~~text
ExperimentError: 180-minute wall-clock limit reached during adapter training
~~~

The run completed fit-pool NLL scoring and the three untouched-base
assessment repeats before adapter training. Those intermediate measurements
were held only in process memory and were not written to a private run
receipt. The selected-arm adapter did not complete or save. Random-control
training, updated-arm assessments, the layer intervention, aggregate report
reconstruction, and local acceptance did not occur.

The external owner-only run directory contains only `execution_status.json`
and remains mode `0700`. The status is `FAILED`, phase
`local_execution_failed`, run ID `run-20261006T165330612799Z`, with the
wall-clock-limit error above. No adapter, raw example, generation, report,
release directory, or local acceptance receipt was retained. Scientific
disposition is `INCOMPLETE_NO_CANDIDATE_DISPOSITION`; neither `Candidate` nor
`NoCandidate` is supported by the incomplete comparison.

## Frozen V4 identity and local evidence

- Repository revision: `62bf2bfb5b6775327eb635d722bd2a715a2c6a42`; worktree
  was already dirty.
- Prepared-input SHA-256:
  `39a213c49db2373bd045ddf289b489f223206ffa403efc0005118966fda267f9`.
- Fit roster SHA-256:
  `ae7bdbacb3546c58b699633bfcc0de76f40b983450f57b7f292861e894674c9b`.
- Assessment roster SHA-256:
  `fb95bdc7900ba95ed354de044401940f6715cc0764f33443e3afc7b823188361`.
- Eight repeated-source groups (16 train rows) were excluded; no test source
  duplicates were found. The selected 512/128 rosters were disjoint and
  excluded V1 source documents.
- Runner SHA-256:
  `2a5d2bcc1831d476ff28b411985037a93e74a6114c8192d81dc9f521ab25483e`.
- Protocol SHA-256:
  `703acf3af19b1794a5ea3f73f8196bed9d4c112f9e12715cfdcc56641cfe1efd`.
- Protocol-manifest SHA-256:
  `0b9c64071e37818b17b468b2df03d9c752de9b372b3a9f542e2049239220f7d6`.
- Focused-test SHA-256:
  `e1522c7d8de915396db9a6241a16392099aecdb42448ca89782f4e7131d5ad18`.
- Requirements-lock SHA-256:
  `30055a286e08aa09b017f187a0aac685836c7570e97eba2de0beeb8a0150be3b`.
- Focused V4 checks passed 10/10; installed dependencies passed
  `uv pip check`. These local checks do not override the failed full run.
- Reviewer status: local acceptance was not issued; independent acceptance
  was not requested or performed.
- Reproducibility: one local execution failed at the frozen wall-clock bound;
  no second environment reproduction occurred.

## Claim ceiling and continuation

The V4 ceiling remains
`LocalDevelopmentBillSumChatTemplateCurriculumQualificationV4`; this ceiling
was not earned. No general alignment, recursive-self-improvement,
feature-mechanistic, leaderboard, or production claim follows.

Do not edit or retry V4. The continuing user request proceeds only under
fresh V5 state slice
`aligned-rsi-billsum-chat-template-adaptation-v5`, with a smaller frozen
sequence/update budget selected by a read-only feasibility audit before any
V5 model execution.
