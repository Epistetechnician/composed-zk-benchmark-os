# Pilot and Conversation Inventory

## Provenance and Claim Ceiling

This inventory formalizes substantive content recovered from the shared
`Self-Astral` conversation on 2026-07-26. The numerical results below were
reported in that conversation. No underlying run artifacts were present in the
repository or independently inspected. They are pilot claims, not accepted
evidence, benchmark results, or replicated findings.

## P001 — Reported Introspection-Gap Pilot

Reported design:

- subjects: `gemma-2-2b`, `qwen3-4b`, and `gpt-oss-20b`;
- 24 prompts per subject except `gpt-oss-20b`, reported as `n=19`;
- tracer target: ten sparse causal features with auto-interpretation labels;
- reporters: actor self-report, scale-matched external reporter, frontier
  reporter, and mismatched-prompt control;
- blind language-model judge for mechanism recall;
- paired bootstrap 95% confidence intervals;
- `IntrospectionGap = recall(observer) - recall(self)`.

Reported aggregate results:

| Subject | Self | Matched external | Frontier | Control | Frontier minus self |
|---|---:|---:|---:|---:|---:|
| gemma-2-2b | 0.358 | 0.371 | 0.454 | 0.113 | +0.096 `[0.013, 0.175]` |
| qwen3-4b | 0.458 | 0.458 | 0.537 | 0.054 | +0.079 `[0.013, 0.154]` |
| gpt-oss-20b | 0.200 | 0.168 | 0.233 | 0.022 | +0.042 `[-0.011, 0.100]` |

Additional reported observations:

- within Qwen 1.7B to 4B, self recall changed by `-0.004`, while external
  observer explainability changed by `+0.111 [0.025, 0.202]`;
- a 4B observer explaining a 20B subject changed by
  `-0.032 [-0.058, -0.005]`;
- multihop cases were described as most narratable;
- latent intermediary concepts were frequently missed;
- small-model arithmetic self recall was reported near `0.07-0.08`;
- comparison prompts showed the widest frontier advantage;
- one `gpt-oss-20b` multihop cell reportedly had self `0.37` versus frontier
  `0.32`.

Reported limitations:

- only transcoder-captured computation was evaluated;
- error-node mass was approximately 9-24%;
- the evaluator was a language model;
- control scores were approximately 0.05-0.11;
- prompt counts were small;
- cross-family and within-family scale trends conflicted.

The conversation inferred that observer capability may explain the results
better than subject identity or privileged self-access. That inference is C011
and remains Proposed.

## P002 — Reported SRE Harness Pilot

Reported design:

- 40 deterministic incident-triage tasks: 20 training and 20 held out;
- actor/optimizer family: `qwen3:4b`, with a frontier Claude optimizer
  comparison;
- same feedback and iteration count across optimizer comparisons.

Reported held-out accuracy:

| Condition | Accuracy |
|---|---:|
| Baseline | 0.50 |
| Self-designed prompt | 0.60 |
| Qwen evaluation-iterated | 0.65 |
| Frontier evaluation-iterated | 0.85 |

Reported optimizer trajectories:

- Qwen: `0.55 -> 0.65 -> 0.60 -> 0.60`;
- frontier: `0.55 -> 0.75 -> 0.95`.

The conversation inferred that the capability consuming feedback mattered more
than feedback plumbing. That inference is C012 and remains Proposed because the
tasks, logs, prompts, exact models, and run artifacts were not available.

## Central Hypothesis and Evidence Chain

Conversation formulation:

> A projected-self observer trained with causal mechanistic supervision can
> improve an actor's behavior more effectively than text-only self-reflection.

Required evidence chain:

\[
\text{mechanistic access}
\rightarrow
\text{better causal diagnosis}
\rightarrow
\text{better intervention}
\rightarrow
\text{better held-out outcome}
\]

Failure at any link prevents the complete claim.

## Conversation-Derived Work Order

1. Reproduce the small introspection pilot at larger prompt and seed counts.
2. Add projected observers with and without labels, graphs, and telemetry.
3. Expand and lock the deterministic SRE hidden split.
4. Version the mechanistic run-record and feature-record schemas.
5. Generate causal interventions for failed runs.
6. Train a frozen-actor LoRA observer on feature and counterfactual targets.
7. Compare self-correction methods under equal budgets.
8. Run telemetry randomization, capability, and representation ablations.
9. Scale the actor only after the narrow study shows instrumental value.
10. Update the actor only after reliable causal-effect prediction, retaining a
    frozen tracer, evaluation observer, and audits.

This order is a proposal. It does not authorize model downloads, training,
network execution, or resource expenditure.

## Open Research Questions

- Can observer-scale effects be separated from telemetry access?
- How should features be aligned across seeds, widths, and dictionaries?
- How much computation remains outside the tracer's replacement model?
- Does natural-language explanation help, or merely launder plausible stories?
- Can a self-model remain valid after actor updates?
- Does alternating training cause computation to move into tracer residuals?
- What continual-learning method prevents self-model staleness or forgetting?
- How do open and closed models change the economics and reproducibility of the
  program?
- Can harness improvement be attributed to mechanism use rather than a stronger
  general optimizer?

## Deferred or Rejected Initial Framings

- Consciousness and self-awareness are outside the initial claim.
- Dreaming, world models, memory, RLVR, and self-distillation may improve
  behavior but do not independently establish mechanistic self-modeling.
- Cross-entropy remains suitable for next-token prediction; the project only
  claims it is incomplete for the proposed auxiliary target.
- A new loss alone is not the project. Measurement, architecture, causal
  validation, and instrumental testing are all required.

## Publication Frame

Candidate title:

> From Self-Report to Self-Model: Training Language Models to Use Mechanistic
> Interpretability for Self-Correction

Candidate contributions:

1. expanded and better-controlled Introspection Gap measurement;
2. a trained projected observer with privileged mechanistic telemetry;
3. held-out causal intervention validation;
4. deterministic SRE or harness utility under fixed compute and feedback.

All four remain candidate contributions. Novelty and empirical success are
unestablished.

## Source-Coverage Map

| Conversation topic | Formal destination |
|---|---|
| Harness and software defensibility thesis | This inventory; economic motivation remains an open question |
| Mechanistic-self-modeling terminology | README and protocol |
| Pilot metrics and caveats | P001 and P002 above; C011-C012 |
| Actor-observer-tracer architecture | System model |
| Loss components and calibration | Protocol |
| Counterfactual supervision priority | Protocol and roadmap |
| Data and feature records | System model |
| SRE task design and sizes | Protocol |
| Intervention types and corpus size | System model |
| Baselines, ablations, and equal budgets | Roadmap |
| Provisional numeric gates | Protocol, explicitly not preregistered |
| Joint-training and tracer-gaming risk | System model, roadmap, risk register |
| Staleness and continual learning | Open questions above |
| Source and novelty references | Literature index; unresolved items remain below |
| Publication framing | This inventory |
| Consciousness, dreaming, RLVR, memory, world models | Deferred framings above |

## Unresolved Source Leads

The conversation mentioned the following, but exact primary sources have not
yet been verified:

- "Introspective Coupling: Self-Explanation Training Tracks Behavioral Change
  Despite Fixed Supervision";
- natural-language autoencoder or activation verbalizer-reconstructor work;
- Neuronpedia as supporting infrastructure;
- exact primary sources for RLVR, process supervision, continual learning,
  dreaming/world models, DSPy, and evaluation-driven iteration;
- an Ilya Sutskever-Dwarkesh statement comparing evaluation performance with
  useful work.

These leads cannot support claims until resolved in the literature index.
