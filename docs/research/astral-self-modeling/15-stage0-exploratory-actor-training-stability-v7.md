# Stage 0 Exploratory Actor-Training Stability V7

State slice: `astral-stage0-exploratory-actor-training-stability-v7`.

Status before execution: `PreregisteredExploratoryTrainingStudy`.
Evidence ceiling: `LocalExploratoryActorTrainingDiagnostic`.

V7 addresses deterministic actor basin failures. It does not score attribution
methods or run interventions. Only train families `0..159` and development
families `160..191` may be materialized.

The actor, task, AdamW learning rate `0.003`, weight decay `0.01`, batch size
128, clipping `1.0`, checkpoint interval 25, lowest-development-loss selection,
earliest exact tie, and `0.95/0.95` eligibility floor remain frozen.

The fixed recipe panel is:

1. `iid-2000`: existing random row sampling for 2,000 updates;
2. `family-complete-2000`: sample eight train families per update and include
   all 16 packed-bit examples from each family;
3. `family-complete-4000`: the same family-complete sampler for 4,000 updates.

Selection seeds are the already exposed V6 seeds `157, 163, 167`, each twice.
Every recipe is run on every seed. A recipe is eligible only if all six runs
meet accuracy and same-seed selected-step, checkpoint, trajectory, and
batch-plan reproducibility gates. Select the first eligible recipe in the fixed
order above. If none qualify, classify `TrainingRecipePanelFailed`.

The selected recipe is locked before fresh qualification seeds `191, 193, 197`
run twice each. The first failed pair stops qualification without substitution.
All three passing yields `ActorTrainingRecipeQualified`.

Seed `227` is test-only. Seeds `173, 179, 181` and families `512..575` remain
reserved and untouched. Multi-initialization best-of-N, conditional restarts,
curricula, method scoring, interventions, and family `>=192` access are
prohibited.

V7 success means only that one named local training procedure reproducibly met
the train/development eligibility floor on the named panels. It permits a new
separately preregistered method-development run. It does not reverse V5
`Null`, retroactively complete V6, pass Stage 0, establish generalization,
validate attribution, or unblock Stage 1.

## Execution Record — 2026-07-26

Classification: `ActorTrainingRecipeQualified`.

Selection results:

| Recipe | Seed 157 | Seed 163 | Seed 167 | Eligible |
|---|---|---|---|---|
| `iid-2000` | `1.0 / 1.0` | `1.0 / 1.0` | `0.75 / 0.75` | No |
| `family-complete-2000` | `1.0 / 1.0` | `1.0 / 1.0` | `1.0 / 1.0` | Yes |
| `family-complete-4000` | `1.0 / 1.0` | `1.0 / 1.0` | `1.0 / 1.0` | Yes |

The frozen minimal-change rule selected `family-complete-2000`.

Fresh qualification:

| Seed | Train / development | Step | Checkpoint SHA-256 |
|---:|---|---:|---|
| `191` | `1.0 / 1.0` | `2000` | `ce091c841f98c6b079804a83513391142cd7c8c2eaba2285abb124f298ea52c7` |
| `193` | `1.0 / 1.0` | `2000` | `7ef5e22fff571a33679df3822e3683cb05a1100b110c39107ec48ccd2a9d7f67` |
| `197` | `1.0 / 1.0` | `2000` | `445e035057f23abd8ca96b0137853bf39a9e85b2c20f9bfed7148983e357840a` |

Every seed reproduced identical batch-plan, checkpoint, trajectory, and
selected-step digests. The V7 semantic validator accepted the complete bundle.
Manifest SHA-256:
`a5f712c50b33b7d22ca3f3c85f23563925ec36e7d063f94167b119824188b26b`.

The bounded conclusion is that family-complete batching removed the observed
seed-dependent qualification failure on both the exposed selection panel and
the fresh qualification panel. This does not establish population-wide
training reliability. The V6 five-method panel remains unevaluated and requires
a new protocol using this frozen recipe.
