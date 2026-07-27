# Stage 0 Exploratory Attribution-Method Development V6

State slice: `astral-stage0-exploratory-attribution-method-development-v6`.

Status before execution: `PreregisteredExploratoryMethodDevelopment`.
Evidence ceiling: `LocalExploratoryAttributionMethodDiagnostic`.

V6 is adaptive hypothesis generation after the V5 `Null`. It cannot reverse
V5, pass Stage 0, unblock Stage 1, or count as confirmation.

The frozen actor and 2,000-update training procedure remain unchanged.
Exploratory actor seeds are exactly `157, 163, 167`, each reproduced twice.
Train families are `0..159`. Method-development families are exactly `160..191`,
split by whole family into design-reporting families `160..175` and
selection-assessment families `176..191`. No family `>=192` may be
materialized. Seed `151` is test-only. Seeds `173, 179, 181` and families
`512..575` are reserved for a possible future confirmation and are forbidden
in V6.

For returned CLS head activation `h`, clean-margin gradient `g`, and
elementwise product `q=-g*h`, the frozen panel is:

1. `signed_dot_legacy`: `sum(q)`;
2. `absolute_product_l1`: `sum(abs(q))`;
3. `absolute_product_l2`: `sqrt(sum(q^2))`;
4. `absolute_product_linf`: `max(abs(q))`;
5. `sign_coherent_mass`: `max(sum(max(q,0)), sum(max(-q,0)))`.

The legacy method is descriptive and cannot be selected. Competitive baselines
remain activation norm, gradient norm, and causal-token attention mass.
Each new method also receives a deterministic within-prompt permutation
control. All scores and captures are serialized and hashed before any zero
ablation or patch intervention.

A new method is selection-eligible on the assessment fold only if informative
coverage is at least `0.80` for every seed; paired regret advantage exceeds
`0.05` in mean against every competitive baseline; advantage is positive for
every seed and baseline; and advantage over its permutation is positive in mean
and every seed. Patch results are descriptive and cannot select a method.

Among eligible methods, select the largest minimum seed-by-baseline advantage,
then largest mean across those cells, then the fixed panel order. If none is
eligible, classify `ExploratoryNoSelection`. Otherwise classify
`ExploratoryMethodSelected`.

All five candidates and every seed/fold result must remain in the record.
Intervals and comparisons are descriptive and not multiplicity-controlled.
V6 may only nominate one formula for a separately preregistered fresh-holdout
study. It cannot establish causal fidelity, mechanistic understanding,
introspection, self-modeling, correction, observer value, safety, benchmark
evidence, or accepted evidence.

## Execution Record — 2026-07-26

Classification: `ExploratoryQualificationFailed`.

| Seed | Eligible | Train / development | Selected step | Reproducible |
|---:|---|---|---:|---|
| `157` | Yes | `1.0 / 1.0` | `2000` | Yes |
| `163` | Yes | `1.0 / 1.0` | `2000` | Yes |
| `167` | No | `0.75 / 0.75` | `1550` | Yes |

Seed `167` produced checkpoint SHA-256
`d64e133918fa2303adb93bbcdd45e5ab833d7cd75ca147271ecf8d6f7ffe0745`
and trajectory SHA-256
`f70fd9094003e85c99a2ee32219d99187f3624eb8cad62d8c0957299850f3328`
in both reproductions. The failure is deterministic actor capability under the
frozen procedure, not nondeterminism.

The mandatory stop occurred before any method score, score lock, intervention,
or comparative method result. No V6 method was selected. Future families
`512..575` and seeds `173, 179, 181` remain untouched. The finalized
qualification-failure bundle passed the V6 validator with manifest SHA-256
`ee796c9b507da4c694e9022e53065e50c79bbfbf82db81ee93a2f3101c7f08b6`.

V5 remains `Null`, Stage 1 remains blocked, and the proposed five-method panel
has not yet been empirically compared.
