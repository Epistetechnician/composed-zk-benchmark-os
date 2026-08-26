# Literature Index

Observed 2026-08-24. This is a seed index, not a systematic review. Source IDs
map to the claim ledger. Each entry states what it supports and what it does not
establish.

## S001 — Circuit Tracing

Emmanuel Ameisen et al., "Circuit Tracing: Revealing Computational Graphs in
Language Models," Transformer Circuits Thread, 2025.

- URL: https://transformer-circuits.pub/2025/attribution-graphs/methods.html
- Evidence class: primary technical report.
- Supports: attribution graphs derived from an interpretable replacement model
  can generate mechanistic hypotheses about individual forward passes, with
  associated validation tools.
- Does not establish: exact recovery of the original model's complete causal
  graph, global circuit identity, or automatic faithfulness of a trace.

## S002 — Biology of a Large Language Model

Wes Gurnee et al., "On the Biology of a Large Language Model," Transformer
Circuits Thread, 2025.

- URL: https://transformer-circuits.pub/2025/attribution-graphs/biology.html
- Evidence class: primary empirical technical report.
- Supports: attribution graphs can be used to form and perturbationally test
  hypotheses for multiple behaviors in a frontier language model.
- Does not establish: universal coverage. The authors describe the graphs as
  partial and report important methodological limitations.

## S003 — Training Models to Explain Their Computations

Belinda Z. Li, Zifan Carl Guo, Vincent Huang, Jacob Steinhardt, and Jacob
Andreas, "Training Language Models to Explain Their Own Computations," 2025.

- URL: https://arxiv.org/abs/2511.08579
- Evidence class: primary preprint.
- Supports: models were fine-tuned with interpretability-derived supervision to
  describe feature information, causal activation structure, and token
  influence; the paper reports non-trivial generalization and an own-model
  advantage in tested settings.
- Does not establish: complete causal self-modeling, reliable intervention-effect
  prediction, or downstream self-correction from the explanations.

## S004 — Looking Inward

Felix J. Binder et al., "Looking Inward: Language Models Can Learn About
Themselves by Introspection," 2024.

- URL: https://arxiv.org/abs/2410.13787
- Evidence class: primary preprint.
- Supports: behavior-prediction experiments in which a model can outperform
  another model at predicting its own tendencies in some simple settings.
- Does not establish: mechanistic access, complex-task introspection,
  out-of-distribution generalization, consciousness, or faithful causal
  explanations.

## S005 — Emergent Introspective Awareness

Jack Lindsey, "Emergent Introspective Awareness in Large Language Models,"
arXiv:2601.01828, 2026.

- URL: https://arxiv.org/abs/2601.01828
- Full text: https://arxiv.org/html/2601.01828v1
- Evidence class: primary empirical preprint.
- Supports: activation-injection experiments in which several Claude models
  sometimes detect and identify injected concepts, distinguish injected
  representations from text inputs, and modulate concept representations when
  instructed or incentivized.
- Protocol consequence: distinguish causal influence on a self-report from
  prediction of externally measured intervention effects; preserve unrelated-
  injection, post-prefill, exact-text, and early-report controls.
- Does not establish: reliable general introspection, a specific mechanism, a
  directly observed metacognitive representation, held-out causal-effect
  prediction, consciousness, or faithful explanation.

## Required Review Expansion

Before any novelty claim, add and compare:

- causal abstraction and causal representation learning;
- activation patching, attribution patching, and causal tracing;
- sparse autoencoder and crosscoder identifiability limits;
- process supervision and critique/reflection baselines;
- self-prediction, metacognition, calibration, and abstention;
- monitor gaming, steganography, and interpretability evaluation;
- self-explaining and inherently interpretable architectures.

The novelty review must record databases, queries, dates, inclusion criteria,
excluded near-matches, and a feature-by-feature prior-work matrix.

## S016 — Introspection Reality Check

Shashwat Singh, Tal Linzen, and Shauli Ravfogel, "Can LLMs Introspect? A
Reality Check," 2026.

- URL: https://arxiv.org/abs/2605.26242
- Evidence class: primary preprint.
- Supports: input-only classifiers can match hidden-label prediction in tested
  biofeedback settings; open models in the tested steering setting did not
  reliably distinguish activation interventions from textual gaslighting.
- Protocol consequence: require exact-text activation/no-intervention pairs,
  an input-level perturbation class, relabel-safe outputs, and explicit
  activation-versus-none reporting.
- Does not establish: that every activation-report paradigm is impossible or
  that a positive controlled result identifies a general introspective
  mechanism.

## V11 Primary-Source Expansion

## S017 — Metacognition in LLMs

Gabrielle Kaili-May Liu, Areeb Gani, Jacqueline Lu, Jordan Thomas, Mark
Steyvers, and Arman Cohan, "Metacognition in LLMs: Foundations, Progress, and
Opportunities," 2026.

- URL: https://arxiv.org/abs/2607.11881
- Evidence class: survey and taxonomy.
- Supports: separating monitoring, confidence/reporting, and control; treating
  confidence-method choice, task/domain specificity, and report faithfulness as
  explicit experimental variables; using metacognitive metrics as complements
  to ordinary calibration.
- Protocol consequence: a metacognition claim requires more than reflection or
  self-report; it needs a locked monitor target, held-out evaluation, and a
  measured control effect with safety and calibration reporting.
- Does not establish: any local actor's metacognition, mechanistic access,
  faithful self-report, causal self-model, consciousness, or Stage 0C/Stage 1.

## S018 — Full-Bandwidth Transformer

Xi Wang, Ziyang Cai, Zheng Zhan, Harry Dong, Ying Fan, Gustavo de Rosa, Tim
Pearce, and John Langford, "Full-bandwidth transformer," arXiv:2608.08888,
2026.

- URL: https://arxiv.org/abs/2608.08888
- Full text: https://arxiv.org/html/2608.08888v1
- Evidence class: primary empirical preprint.
- Supports: a latent-feedback architecture that fuses the previous top-layer
  hidden state with the next token embedding, plus reported improvements in
  validation loss, language-model evaluation, math and coding generation, and
  instruction-tuned performance in the tested settings.
- Protocol consequence: treat latent feedback as an architectural factor and
  separate state accessibility, actor reporting, held-out intervention-effect
  prediction, and downstream correction as distinct endpoints.
- Does not establish: that latent feedback is causally used for a target
  behavior, faithful introspection, self-modeling, held-out intervention-effect
  prediction, causal explanation, generalization, consciousness, or Stage 0C/
  Stage 1 authorization.

## S006 — Causal Abstractions of Neural Networks

Geiger et al., "Causal Abstraction: A Theoretical Foundation for Mechanistic
Interpretability," JMLR, 2025.

- URL: https://www.jmlr.org/papers/v26/23-0058.html
- Supports: mechanistic hypotheses can be evaluated as graded causal
  abstractions through interventions.
- Does not establish: that an attribution score is a faithful abstraction.

## S007 — Locating and Editing Factual Associations

Meng et al., "Locating and Editing Factual Associations in GPT," 2022.

- URL: https://arxiv.org/abs/2202.05262
- Supports: causal tracing measures restoration effects after corrupting and
  patching internal states.
- Does not establish: intervention independence or universal circuit identity.

## S008 — Activation Patching Best Practices

Zhang and Nanda, "Towards Best Practices of Activation Patching in Language
Models: Metrics and Methods," 2023.

- URL: https://arxiv.org/abs/2309.16042
- Supports: corruption and metric choices can materially change localization.
- Protocol consequence: freeze intervention construction and metric.

## S009 — Attribution Patching and AtP*

Syed, Rager, and Conmy, "Attribution Patching Outperforms Automated Circuit
Discovery," 2023; Kramár et al., "AtP*: An Efficient and Scalable Method for
Localizing LLM Behaviour to Components," 2024.

- URLs: https://arxiv.org/abs/2310.10348 and
  https://arxiv.org/abs/2403.00745
- Supports: gradient attribution is a fast linear approximation; ordinary AtP
  has identifiable false-negative modes.
- Does not establish: causal ground truth without direct intervention checks.

## S010 — Attribution Sanity and Invariance

Adebayo et al., "Sanity Checks for Saliency Maps," 2018; Kindermans et al.,
"The (Un)reliability of Saliency Methods," 2018.

- URLs:
  https://proceedings.neurips.cc/paper/2018/hash/294a8ed24b1ad22ec2e7efea049b8737-Abstract.html
  and https://openreview.net/forum?id=r1Oen--RW
- Supports: parameter/label randomization and behavior-preserving
  transformations expose explanations that ignore learned structure or depend
  on arbitrary references.
- Protocol consequence: make these disqualifying sanity gates.

## S011 — Integrated Gradients

Sundararajan, Taly, and Yan, "Axiomatic Attribution for Deep Networks," 2017;
Lundstrom, Huang, and Razaviyayn, "A Rigorous Study of Integrated Gradients
Method and Extensions to Internal Neuron Attributions," 2022.

- URLs: https://proceedings.mlr.press/v70/sundararajan17a.html and
  https://proceedings.mlr.press/v162/lundstrom22a.html
- Supports: sensitivity and implementation-invariance axioms, path integration,
  and internal-neuron attribution with explicit reference choices.
- Does not establish: empirical causal fidelity or a uniquely correct baseline.

## S012 — Necessity, Sufficiency, and Distribution Shift

Hooker et al., "A Benchmark for Interpretability Methods in Deep Neural
Networks," 2019; Gupta et al., "New Definitions and Evaluations for Saliency
Methods," 2022.

- URLs:
  https://proceedings.neurips.cc/paper_files/paper/2019/hash/fe4b8556000d0f0cae99daa5c5c5a410-Abstract.html
  and
  https://proceedings.neurips.cc/paper_files/paper/2022/hash/d6383e7643415842b48a5077a1b09c98-Abstract-Conference.html
- Supports: naive deletion can create distribution shift; completeness alone
  can miss soundness.
- Protocol consequence: report necessity and sufficiency under multiple
  operators rather than treating ablation ranking as ground truth.
