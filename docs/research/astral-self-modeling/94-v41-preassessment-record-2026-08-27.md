# V41 Preassessment Record — Directional-Block Qwen3.6 Target

State slice: `astral-stage0c-qwen36-directional-block-target-v41`.

Status: `DevelopmentNoCandidate / AssessmentClosed`.

V41 completed fresh external Gutenberg custody, independent corpus validation,
Qwen3.6 qualification, panel sealing, independent panel validation, and the
fit/tune preassessment. The fixed tune utility gate failed. The reviewer
packet therefore refused to open and no independent-review receipt or
assessment intervention effects were created.

## External custody

| bundle | external root | digest |
|---|---|---|
| corpus manifest | `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v41-corpus-r1-2026-08-27` | `e1f39343ce53c3f1c4b3ceb27e871442b45943b5696cd77b9cebf3c93e5d8df1` |
| corpus validator receipt | same corpus root | `e43d4d9af36f40aea4ef3c2ad2816d007e236f2e837864fbe25b0d72cdf8c1c3` |
| qualification result | `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v41-qualification-r3-2026-08-27` | `562f991c0e24701fa8c86c03e2e95cfaa43639a1a002538b5554f667a8e61198` |
| qualification validator receipt | same qualification root | `1249636e194c1a411bed79e8f6a3719f217c46f5a5935b9e428685070639c684` |
| panel manifest | `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v41-panel-r1-2026-08-27` | `0f0af28e55da1dce4336d323532c3dd1c82ae3d39b94dfcd7621ff4072c14334` |
| panel validator receipt | same panel root | `882166df25d995519562844c4be8a9a6965df226fbc168a9bac16ddaed857eef` |
| preassessment run manifest | `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v41-preassessment-r1-2026-08-27` | `8f1b5f818283ec370070c6db82e5ceb268e3e96232262d28d050b9460a8559a8` |
| preassessment validator receipt | same preassessment root | `4917c3e13733aa719f8455c4a850ab1817faa0e01a0af292d4946c5fdfbb1977` |

The corpus contains 18 fresh Project Gutenberg documents and the panel
contains 144 families: 48 fit, 48 tune, and 48 assessment. Qualification
passed as `InstrumentFeasibility`; the corpus, panel, and preassessment
validators all returned `valid: true` with no errors. The model manifest was
`a95dc0f89c98c82331865ef0f51fc52ee832e41d6a97bd9b76351d37cec1e9e4`, the
feature-map digest was
`f1363030e8068225e38972945f8ba9f60346dbbbfdf23326bed090ce1506ac4c`, and the
final V41 protocol digest was
`b8c21e9b23a7d9fb6e5d436bc51d6eee06706435635cecfc3e1f06e80527f03c`.

## Fixed tune result

The preregistered primary metric is
`delta_rmse = RMSE(directional_block_primary) - RMSE(constant)`, with a
required tune value of at most `-0.01`.

| panel | tune RMSE |
|---|---:|
| directional-block primary | `0.1196272021` |
| constant | `0.1024599769` |
| clean activation only | `0.1120581241` |
| shuffled | `0.1108343000` |
| text only | `0.1039231654` |

The observed tune delta was `+0.0171672252`, failing the fixed utility gate
by `0.0271672252`. The target remained non-degenerate (`std = 0.1015437182`)
and matched-donor construction had zero violations, but those facts do not
override the failed primary gate. No adaptive feature, threshold, panel, or
donor change was made.

## Lock and boundary

Assessment predictions were materialized in memory and sealed before any
assessment effects. The validated preassessment bundle records
`assessment_effects_present: false`, `assessment_effects_measured: false`,
`prediction_locked_before_assessment: true`, and aggregate-only retention with
per-family effects and predictions not retained. Because the fixed tune gate
failed, review packet preparation stopped before review acceptance and the
assessment runner was not invoked.

The narrow classification is `DevelopmentNoCandidate` at ceiling
`LocalDevelopmentV41DevelopmentNoCandidate`. This is a local negative
development result. It does not establish target validity, introspection,
causal self-modeling, Stage 0C, Stage 1, benchmark evidence, or production
readiness. V28-V29, V25, V30-V37, V61, V82, and the Neural Chameleon branch
remain at their previously recorded boundaries.
