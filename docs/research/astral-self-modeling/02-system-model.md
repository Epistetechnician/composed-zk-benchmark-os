# System Model

## Components

\[
y,z = M_\theta(x)
\]

\[
G_{\mathrm{trace}} = \mathcal{T}(M_\theta,x,y,z)
\]

\[
\widehat{\Delta}_{\psi} = S_\psi(x,z,I)
\]

\[
\widehat{G},\widehat{\Delta y},c =
O_\phi(x,y,\operatorname{select}(z))
\]

where:

- `M_theta` is the actor;
- `x` and `y` are the task input and original output;
- `z` is a bounded telemetry record;
- `T` is a frozen external tracer;
- `I` is a preregistered intervention operator and target;
- `S_psi` is a learned or fixed intervention-effect estimator;
- `Delta_hat_psi` is its prediction of directly measured intervention effects;
- `G_trace` is an approximate traced representation;
- `O_phi` is the observer;
- `G_hat` is its mechanism prediction;
- `Delta y_hat` is its predicted intervention effect;
- `c` is calibrated confidence.

`G_trace`, not `G*`, is used because an external trace is not automatically
ground truth. Synthetic known-circuit tasks may use a distinct
`G_ground_truth`.

The intervention runner is the canonical label source. Attribution `A` is only
a proposal-generating approximation. Stage 0C trains and evaluates `S_psi`
before `O_phi` is authorized; the observer cannot validate its own target.
Activation magnitude is a mandatory baseline, not a causal explanation.

## Data Flow

```text
task input x
    |
    v
frozen actor M --------> original output y --------> task score
    |
    +-------- bounded telemetry z
                         |
                         v
                observer O_phi
                  |      |      |
                  v      v      v
              G_hat  effect  confidence
                  \      |      /
                   correction policy
                          |
                          v
                    revised output

frozen external tracer T ----> G_trace
intervention runner ----------> measured effects
independent auditor ----------> disagreement checks
```

## Target Representation

A candidate trace is:

\[
G_{\mathrm{trace}}=(F,E,A,C)
\]

- `F`: tracer-defined sparse features;
- `E`: tracer-defined directed dependencies;
- `A`: attribution weights under a named method;
- `C`: measured effects under named interventions.

Feature identity and edge structure may not be identifiable across learned
dictionaries. Comparisons must use alignment-aware matching and place primary
weight on reproducible intervention effects.

The primary representation should remain machine-readable. Natural-language
labels are a lossy interface retained for inspection and human audit, not the
canonical mechanism record.

## Candidate Run Records

Mechanistic run record:

- task, prompt, system prompt, completion, final action, reward, and failure
  type;
- activation reference, feature nodes, causal edges, attribution values, and
  error-node mass;
- interventions and measured effects;
- observer reports, confidence, correction, and revised reward.

Feature record:

- stable feature and dictionary identifiers;
- layer, position, activation, and attribution;
- auto-interpretation label;
- source and target tokens;
- tracer and checkpoint identifiers.

Stable machine identifiers must be retained beside human-readable labels.

## Candidate Intervention Record

For approximately the five highest-ranked features on a failed run, select two
or three of:

- ablation;
- amplification;
- patching from a successful run;
- replacement with an alternative state;
- targeted steering.

Record effects on logits, selected root cause, tool calls, task reward,
trajectory length, and confidence. The conversation suggested an initial corpus
of 1,000-5,000 intervention examples; feasibility and statistical adequacy are
unverified.

## Telemetry Contract

Every experiment declares:

- layers, positions, tensors, and derived features exposed;
- whether gradients, attention states, logits, or residual streams are included;
- normalization, quantization, sparsification, and truncation;
- whether the observer shares actor weights;
- what the text-only and capacity-matched controls receive;
- privacy and retention rules;
- the exact information unavailable to each baseline.

## Failure and Threat Model

| Failure | Detection |
|---|---|
| Tracer incompleteness or replacement-model error | Synthetic known-circuit controls, perturbations, and cross-method agreement |
| Observer learns tracer artifacts | Alternate tracer or intervention method; checkpoint and dictionary transfer |
| Actor encodes information for easy observation | Frozen-actor phase; independent auditor; telemetry bottleneck |
| Verbal plausibility substitutes for causal fidelity | Held-out intervention prediction and shuffled-report controls |
| Correction succeeds without mechanism use | Matched reflection, random-report, and incorrect-report baselines |
| Capability or safety regression | Separate held-out safety suite and per-domain reporting |
| Leakage between train and evaluation traces | Split by prompt family, intervention family, and checkpoint |
| Observer capacity confound | Same-scale and compute-matched observers |
| Intervention-operator or corruption-choice dependence | Freeze zero, mean/resample, and patch operators; report each separately |
| Activation magnitude explains the ranking endpoint | Mandatory activation-only estimator and practical-margin gate |
| Attribution ignores learned parameters or labels | Progressive parameter-randomization and label-randomization sanity checks |
| Coarse head intervention hides feature or path effects | Compare preregistered head, token, MLP, path, or subspace granularity on development data |

## Architecture Variants

The initial comparison includes:

1. actor text self-report;
2. same-scale text-only external observer;
3. stronger text-only observer;
4. same-scale telemetry observer;
5. shared-backbone observer head;
6. shuffled-telemetry control.

No variant is called a "self-model" solely because it predicts feature labels.
