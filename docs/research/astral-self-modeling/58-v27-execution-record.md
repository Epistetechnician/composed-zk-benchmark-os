# V27-R1 Execution Record

State slice: `astral-rgs-v27-model-backed-qualification-r1`.

Protocol slice: `astral-rgs-nested-recoverable-update-v27`.

Status: `ImmutableNativeAuthorReplayPassed / ModelBackedAssessmentNotRun`.

Thesis status: `NotValidated`.

## Immutable source boundary

- Astral source commit:
  `900f5e23a8c80bea242a969f1cbb926509f7a87d`.
- RGS source commit:
  `12b36e9c0168f7e3adbc4e07f4c0879f80520f09`.
- RGS source tree:
  `aaa97f427167ef634e4a6817d2cfe823fdee693e`.
- Tencent CL-bench source commit recorded by the historical packet:
  `16bffd1cfa05927e72ec75c835177d6e23e82172`.
- Tencent dataset revision recorded by the historical packet:
  `b28a5832a09b0d96c0cf4c22e90d7c60ede25b80`.

The Astral and RGS sources are clean commits on the isolated branch
`codex/astral-rgs-v27-qualification-r1`. Unrelated dirty RGS changes in the
original checkout were not staged, normalized, or incorporated.

Those RGS identities are the validator sources bound into the immutable R1
release. The later native-arm implementation is RGS commit
`b80518c31c5830ab172fe1f5f6ff88ff1bd28810`, tree
`e0d0e2d961f93a0a30f1a490dd8473e816f4b4f0`. It requires a revised immutable
release before qualification.

## Implemented validator

The RGS V2 validator now requires:

- all six mandatory native arms over three seeds and three task orders;
- at least 12 family-disjoint assessment families;
- content-addressed prediction and configuration locks before outcomes;
- one Astral selector, six confirmatory nonprivileged selectors, and three
  null or specificity selectors over shared candidate outcomes;
- acquisition, protected retention, forgetting, calibration, recovery,
  resource-parity, and governance gates;
- byte-exact rollback and replay after an injected corruption causing at least
  `0.10` loss, with recovered-score loss at most `0.01`;
- future-unseen constrained selection regret, with infeasible selections
  assigned regret `1`;
- a paired, two-stage, equal-family bootstrap with 20,000 replicates and seed
  `270047`, plus the frozen Holm comparison sequence for C047, C048, and
  specificity;
- a V2 Tencent packet that rehashes the model, dataset, licenses, raw output,
  graded output, runtime inventory, and exact execution and grading commands.

Astral independently recomputes the scientific gates, selector regrets,
C047/C048 contrasts, bootstrap, Holm decisions, specificity, source censuses,
native-arm statuses, lock ordering, and final disposition. A supplied malformed
RGS packet is `Invalid`; an absent packet is explicitly `NotRun`.

## Immutable validation release

The release is stored outside both repositories at:

`/Users/shaanp/Documents/ResearchArtifacts/astral-rgs-v27-r1-dda916c83d326cc3`

Its top-level release manifest is:

`RELEASE-MANIFEST.sha256 = dda916c83d326cc3016f9ff01aa141d4a3b708304a3edab0d075024827e33839`

Additional release identities:

- `RELEASE.json` file SHA-256:
  `d82e36df0de5d1b120f05e6dcbd7592db4d329028399cc1def60773f05079965`;
- internal release digest:
  `sha256:8d9f98a0916ce2d65972ec883a80b8973156dc924bf2656a78de56b1e5f3fd06`;
- runtime-inventory digest:
  `sha256:d1013d71efad224b9350b81f655d4a03917f637e3bb00254402ddd13280840bc`.

The historical R1 release contains Git bundles and exact source inventories for both commits,
the digest-bound V25 historical validation report, runtime inventory, license
files, the historical Tencent packet and subset manifest, and every referenced
Tencent byte object. Its 5.63 GB model was hard-linked and content-manifested.
That made deletion of the source harmless but did not isolate the release from
later mutation of the shared inode. R1 is therefore retained as a historical
author replay and superseded by the copy-isolated release below.

## Clean detached replay

The author replay report is:

`/Users/shaanp/Documents/ResearchArtifacts/astral-rgs-v27-r1-dda916c83d326cc3-author-replay.json`

- file SHA-256:
  `ad51db2304fdfdc385b087d2c089f36e93b33c356fe29c9e64f259f451a75f65`;
- internal report digest:
  `sha256:64da549a1853bba9a59fc4e929d286275160b2468ba3a44f58b2d3a1fe077c54`;
- disposition: `pass`;
- errors: none.

The authoritative replay cloned both bundled repositories into detached
checkouts, verified the release manifest and source inventories, and completed:

- Astral V27 tests: `9 passed`;
- RGS holistic and adversarial tests: `15 passed`;
- RGS `lint:fast`: passed;
- Astral independent V2 validation: `ValidatedWithOpenGates`.

The replay's only open gates are:

- `tencent.valid_v2_packet_not_supplied`;
- `rgs.model_backed_report_not_supplied`.

This author-operated replay establishes deterministic artifact exercisability.
It is not an unaffiliated clean-room reproduction, independent review, or
independent implementation replication.

## Revised immutable native release and replay

The copy-isolated revised release is:

`/Users/shaanp/Documents/ResearchArtifacts/astral-rgs-v27-r2-2f1028dcab2e3b9d`

- release-manifest file SHA-256:
  `2f1028dcab2e3b9db7d0a1a809452ff9a5536895f615d206784c03aeb04962fe`;
- internal release digest:
  `sha256:5010fa9e6ff192c45589aec126d15410d3879d919fc4776e99e709b2dc505712`;
- Astral source commit:
  `2f5de3caf68c940f6197cd08658cfb4ff618592e`;
- RGS source commit:
  `d88b04213ddfbd03b3287fe5b8e2265be91a3fff`;
- native model inventory:
  `sha256:65bb07b694edadf0659e0e21af54872b709696a0c7225bd1d21609924ce13acc`.

Every source and evidence byte is copied rather than hard-linked. The release
contains the complete native Qwen model and smoke tree, exact source bundles,
runtime inventories, licenses, historical evidence, and a closed content
census.

The passing replay report is:

`/Users/shaanp/Documents/ResearchArtifacts/astral-rgs-v27-r2-2f1028dcab2e3b9d-author-replay.json`

- file SHA-256:
  `1c76c83e0b40272f0d97f470640b5c692d66107d6ca725e318d038cc77c206b3`;
- internal report digest:
  `sha256:ae2dc9c6b05b870912ef49737203e2522e3e9ed846df2380e493ada11da50b98`;
- status: `pass`;
- errors: none;
- supplied native smoke: `Validated`;
- detached native rerun: `Validated`;
- normalized native-probe match: true;
- Astral tests: 9 passed;
- RGS holistic and native tests: 26 passed;
- RGS `lint:fast`: passed;
- Astral validation: `ValidatedWithOpenGates`.

An earlier revised package at manifest `e7092764c6568197...` is retained with
its failed replay. It exposed pre-seed LoRA initialization and absolute-path
adapter metadata through `replay.native_probe_nondeterministic`. The corrected
RGS commit and release close those engineering defects without deleting the
negative execution record.

## Historical Tencent diagnostic

The release preserves the four-task historical Tencent observation and all its
referenced bytes. It does not promote that observation to a V2 packet because
the exact inference and grading commands were not recorded at execution time.
Reconstructing commands after the fact would weaken the provenance contract.
Its release status is
`HistoricalV1NonReplayableMissingExactCommands`.

The retained observation used Qwen3.5 9B Q4_K_M and recorded one locally judged
pass among four tasks. It remains noncanonical: it is not the official judge,
not a full benchmark, not leaderboard-comparable, and not a parametric
continual-learning result. CL-bench remains evaluation-only and cannot be used
for training, calibration, distillation, adaptation, or architecture selection.

## Commit-bound native-arm smoke

RGS executed all six frozen mechanisms on the cached Qwen2.5 0.5B 4-bit model
from clean deterministic implementation commit
`d88b04213ddfbd03b3287fe5b8e2265be91a3fff`. The authoritative development
artifact is:

`/Users/shaanp/Documents/ResearchArtifacts/astral-rgs-v27-native-smoke-qwen05b-s270001-r8`

- native-probe file SHA-256:
  `6c7320ee16df6fcb3e4242b5fe835b43bfa8df7c6b3b92297b23c02bcc0b4e46`;
- internal native-probe digest:
  `sha256:c7a086993ee13877e45885339afe8097fca05462cf185979bdb30157fa6e265d`;
- native-preflight file SHA-256:
  `e1e502cd068127d8bc6eddab1c4862efb6b15269495bff6d86cbedf9608e4b26`;
- internal native-preflight digest:
  `sha256:bc3779106490e7336366560886718c67ddd9af8f8e42121b21949b368b463807`;
- failures: zero;
- assessment opened: false.

The five updated arms each used six optimizer steps and 75 supervised tokens.
The nested fast, medium, and slow clocks executed 6, 3, and 1 times. Temporal
distillation applied a nonzero representation-preservation term on four steps.
The int8 recollection maximum absolute reconstruction error was
`0.00013274885714054108`.

This is mechanism exercisability, not efficacy. The three-example accuracy was
`2/3` for five arms and `1/3` for nested multiscale LoRA. It is not pooled with
qualification and cannot fill the 54-run execution registry.

## Heavy root-gate boundary

The RGS heavy root gate passed its preceding Phase 36-45, CL12, advisory-pilot,
PCSM-native, and V27 checks after reconstructing ignored inherited artifacts in
the isolated worktree. It then stopped at the pre-existing public-metrics check
because `docs/public-breakthrough-metrics.json` and its Markdown mirror are
stale against the inherited sidecar-ledger refresh. Those unrelated tracked
generated files were not changed. The focused V27 gates and immutable detached
replay passed; the inherited root gate is not represented as green.

## Claim disposition

- C046 remains `In test`: the author-side engineering machinery and immutable
  replay passed, but independent review is `NotRun`.
- C047 remains `In test`: a six-arm development smoke exists, but no native
  54-run qualification matrix or assessment result exists.
- C048 remains `In test`: no sealed model-backed selector comparison exists.
- model-backed assessment: `NotRun`;
- fresh Stage 0C confirmation: `Blocked`;
- Stage 1: `BlockedByStage0C`;
- independent human review: `NotRun`;
- independent implementation replication: `NotRun`;
- thesis: `NotValidated`.

The strongest supported conclusion is:

> V27-R1 provides a copy-isolated, author-replayable, fail-closed scientific
> validator whose detached replay exercises all six native update mechanisms
> with a normalized probe match. It does not yet provide qualification-scale model-backed
> continual-learning evidence, a valid
> Tencent V2 result, independent reproduction, recoverable self-improvement,
> introspection, self-modeling, Stage 0C, Stage 1, benchmark dominance, or
> thesis validation.
