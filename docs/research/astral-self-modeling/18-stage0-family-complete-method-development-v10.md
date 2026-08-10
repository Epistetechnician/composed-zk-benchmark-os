# Stage 0 Family-Complete Method Development V10

State slice: `astral-stage0-family-complete-method-development-v10`.

Status before execution: `PreregisteredExploratoryMethodCompletion`.
Evidence ceiling: `LocalExploratoryAttributionMethodDiagnostic`.

V10 completes the frozen V6 five-method development panel using the
V7-qualified `family-complete-2000` actor recipe. It uses exposed exploratory
seeds `157, 163, 167`, train families `0..159`, design-reporting families
`160..175`, and method-selection assessment families `176..191`. Every actor is
trained twice and must reproduce batch-plan, checkpoint, trajectory, and
selected-step digests with train/development accuracy at least `0.95`.

The method formulas, baselines, permutation controls, score-before-intervention
order, normalized regret, coverage threshold, practical margin, all-seed and
all-baseline intersection, descriptive-only patch endpoint, and deterministic
winner rule remain exactly V6. The legacy signed-dot method cannot be selected.

No family `>=192` may be materialized. Seeds `173, 179, 181` and families
`512..575` remain sealed unless V10 selects exactly one method and its complete
bundle validates. A later confirmation requires a separate preregistration
before either reserve is accessed.

V10 can only nominate a method. It cannot reverse V5 `Null`, pass Stage 0,
establish causal fidelity or self-modeling, or unblock Stage 1.

## Execution Record — 2026-07-26

Classification: `ExploratoryNoSelection`.

All three actors reproduced the family-complete batch plan, checkpoint,
trajectory, and selected step with train/development accuracy `1.0/1.0`.
The complete score phase was locked before intervention, and the semantic
validator accepted all 1,536 records.

Assessment-fold mean regret advantage against activation norm:

| Method | Mean advantage | Per-seed advantages | Eligible |
|---|---:|---|---|
| `signed_dot_legacy` | `-0.2231` | `-0.1939, -0.2027, -0.2727` | No; legacy |
| `absolute_product_l1` | `-0.0881` | `-0.1907, -0.0794, 0.0058` | No |
| `absolute_product_l2` | `-0.0765` | `-0.1521, -0.0751, -0.0024` | No |
| `absolute_product_linf` | `-0.1357` | `-0.1704, -0.1197, -0.1169` | No |
| `sign_coherent_mass` | `-0.1442` | `-0.2094, -0.1058, -0.1172` | No |

Every method had informative coverage `1.0` and the new methods beat their
permutation controls, attention mass, and gradient norm in most or all cells.
None beat activation norm under the frozen intersection rule. No method was
nominated, so confirmation seeds `173, 179, 181` and families `512..575`
remain untouched.

Runtime was `56.78` seconds. Final manifest SHA-256:
`642597af25cedd25d477eedd9ad5b30a8a23de982743e97b9b122c6fbc7d0a2a`.

The result reinforces V5 rather than reversing it: activation magnitude remains
the strongest tested head selector. V5 stays `Null`, Stage 1 stays blocked, and
no fresh-holdout confirmation is authorized.
