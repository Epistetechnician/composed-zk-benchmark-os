# Astral V46 execution record — 2026-08-28

State slice: `astral-stage0c-qwen36-answer-aligned-causal-target-v46`.

## Disposition

V46 completed fresh corpus intake, independent corpus validation,
qualification, independent qualification validation, panel construction,
independent panel validation, fit/tune measurement, and independent aggregate
validation. The final disposition is:

```text
classification: AnswerAlignedNoCandidate
selected_target: null
assessment_opened: false
assessment_effects_present: false
claim_ceiling: LocalDevelopmentV46AnswerAlignedNoCandidate
```

This is a valid negative development result. It is not instrument failure, a
Stage 0C result, evidence of introspection, or evidence of causal
self-modeling.

## External custody

| artifact | path | digest or result |
|---|---|---|
| model | `/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit` | manifest `a95dc0f89c98c82331865ef0f51fc52ee832e41d6a97bd9b76351d37cec1e9e4` |
| corpus | `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v46-corpus-r1-2026-08-28` | manifest `1870da0ef647cca068cf1ea2371133af0598c9908e55b573b280e46a083ba9d5` |
| corpus selection | external `selection-manifest.json` | `bca524e62726bebe832ebfbca414ae39133ca914f90ec1bb322bccd4de1f29f0` |
| corpus receipt | external `validator-receipt.json` | `FreshCorpusValidated`, valid, independent |
| panel | `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v46-panel-r1-2026-08-28` | manifest `ec1d71a807b08d9b55f0c372bc8c442ba87a6bcd6f8fe70d89242398df5155cb` |
| panel receipt | external `validator-receipt.json` | `PanelSealedForAnswerAlignedTask`, valid, independent |
| qualification | `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v46-qualification-r1-2026-08-28` | result `560ace0dabff03d855b7540f4ea73fd7947848bcec233290ab9f177726c8b8b3` |
| qualification receipt | external `validator-receipt.json` | `QualificationValidated`, valid, independent |
| measurement | `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v46-answer-aligned-r1-2026-08-28` | result `4b6de83345402411bc12ac88dc75efe675135ea300b98eb8560b861ebd2c546f` |
| configuration lock | external `configuration-lock.json` | `4c610b8222f1c816cea51d3430d063a2fd545d56bd7010747940b7465e975a90` |
| measurement receipt | external `validator-receipt.json` | `AnswerAlignedValidated`, valid, independent |

## Qualification result

All qualification gates passed:

- native parity, deterministic repeat, no-op replacement, and zero-replacement
  reach were valid;
- nonzero intervention reach passed at layers 12, 19, and 26;
- the observed model had 40 layers and hidden width 2048;
- model and config custody passed; and
- runtime custody was Python 3.14.5, MLX 0.31.2, MLX-LM 0.31.3, with Qwen
  source digests bound in the result.

Observed nonzero replacement maximum logit deltas were 16.890625 at layer 12,
14.216796875 at layer 19, and 8.96875 at layer 26. Qualification therefore
classifies only as `InstrumentFeasibility` with ceiling
`LocalDevelopmentV46InstrumentFeasibilityOnly`.

## Fit/tune result

The fresh panel had 32 fit families and 32 tune families. Target effects were
non-degenerate at every layer: fit standard deviations were 0.121220, 0.074418,
and 0.074674 for layers 12, 19, and 26; tune standard deviations were 0.318855,
0.211351, and 0.090752.

The best tune correlation was at layer 12, but it failed the other fixed
prediction gates:

| layer | alpha | correlation | sign agreement | bootstrap lower 95% | disposition |
|---:|---:|---:|---:|---:|---|
| 12 | 0.1, 1, 10, 100 | 0.302357 | 0.437500 | -0.394886 to -0.447046 | fail |
| 19 | 0.1, 1, 10, 100 | -0.237289 | 0.468750 | -0.553022 to -0.587147 | fail |
| 26 | 0.1, 1, 10, 100 | 0.177594 | 0.500000 to 0.562500 | -0.098146 to -0.104193 | fail |

All alpha cells failed the fixed sign-agreement and bootstrap gates; layers 19
and 26 also failed correlation. No target passed the complete tune gate, so no
review receipt or assessment effect was permitted.

## Validation and next boundary

The independent V46 validator returned zero errors and confirmed protocol and
state-slice identity, upstream receipts, model/panel/qualification digests,
source custody, aggregate-only retention, lock integrity, prediction ordering,
assessment closure, and no raw intermediate fields.

V46 is permanently closed as `AnswerAlignedNoCandidate`; it must not be
retuned or reopened. Stage 0C and Stage 1 remain
blocked. V82 remains isolated and blocked for missing Gemma/oracle/monitor
artifacts. Any further Astral scientific work requires another fresh slice,
new rationale, new data identity, power/reliability analysis, unchanged claim
discipline, and separate authorization. The successor must be a genuine
measurement audit, not another parameter variation; if no stronger theory is
available, Astral experimentation stops.
