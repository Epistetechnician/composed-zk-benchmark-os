# Activation-versus-Input Perturbation Discrimination V22

State slice: `astral-privileged-information-boundary-v22`.

Status: `NotRunPerturbationDiscriminationQualification`. Confirmation:
`NotAuthorized`.
Stage 0C: `Blocked`. Stage 1: `BlockedByStage0C`.

## Research question

Can the cached Qwen target distinguish a residual-stream intervention from a
matched input-level manipulation and an unmodified forward pass at its first
report token?

V22 changes the information boundary rather than tuning V18-V21. Activation
and no-intervention trials use byte-identical prompts. Their condition label is
therefore unavailable to a text-only classifier. The third condition is a
textual gaslight manipulation, included because detecting generic anomaly is
not sufficient evidence of access to an internal intervention.

## Literature-driven boundary

Lindsey's activation-injection study causally connected injected concept
representations to model self-reports but reported unreliable,
context-dependent behavior and an unnatural intervention setting:
https://transformer-circuits.pub/2025/introspection/

Singh, Linzen, and Ravfogel's 2026 reality check found that open models did not
reliably distinguish activation-level interventions from input-level
manipulations and argued that input-only predictability defeats privileged
access claims:
https://arxiv.org/abs/2605.26242

V22 adopts the three-way location control and exact-text activation/no-change
pair. A positive result would still establish only construction-specific causal
coupling between an injected residual direction and a first-token report. It
would not identify a metacognitive mechanism.

## Frozen design

Use the existing cached Qwen2.5-0.5B-Instruct 4-bit conversion and the V17
controlled MLX forward seam. Completion tokens are single-token ` A`, ` B`,
and ` C`.

Use 16 neutral concepts, ordered and split before execution:

- fit: first eight;
- tune: next four;
- sealed assessment: final four.

For each concept, form a direction independently at residual sites 5, 11, and
17 by subtracting the final-token residual for a neutral reference prompt from
the final-token residual for a concept prompt. Normalize each direction to the
median fit residual norm at that site. Concept direction construction never
uses report logits.

Every trial states a deterministic permutation of:

- activation intervention;
- textual manipulation;
- no perturbation.

Four report wrappers are crossed with every concept and condition. Activation
and no-perturbation use exactly the same base prompt. The textual condition
adds one concept-specific gaslight sentence. Only the activation condition
adds its concept direction after the selected residual block at the final
prompt position.

## Selection and sealing

Fit evaluates sites `5/11/17` and strengths `0.5/1.0/2.0`. Select the
site-strength pair with highest fit macro balanced accuracy, breaking ties by
lower strength then earlier site. Tune is a qualification check only; it cannot
change the selected configuration.

Proceed to assessment only if:

- controlled/native parity, deterministic repeat, and zero-strength parity are
  exact;
- all report completions are single tokens;
- every direction is finite and nonzero;
- fit and tune each contain every condition, wrapper, and response position;
- selected fit macro balanced accuracy is at least `0.45`;
- tune macro balanced accuracy is at least `0.40`;
- tune activation recall is at least `0.25`;
- tune activation-versus-none accuracy on the byte-identical prompt pair is at
  least `0.60`.

Before assessment, write and independently validate a configuration lock
binding source, model inventory, corpus, directions, fit sweep, selected
configuration, tune results, and the absence of assessment results.

## Assessment and classification

Primary metrics are three-way macro balanced accuracy, per-condition recall,
activation-versus-none accuracy, confusion matrix, and a 10,000-draw
concept-cluster bootstrap interval.

`PerturbationDiscriminationFeasibilityObserved` requires:

- assessment macro balanced accuracy at least `0.50`;
- activation recall at least `0.35`;
- activation-versus-none accuracy at least `0.65`;
- positive bootstrap lower bound over three-way chance (`1/3`);
- all four wrappers have macro balanced accuracy at least `0.40`.

Otherwise classify `PerturbationDiscriminationNoCandidate`. Failure of a
qualification rule classifies `NotRunPerturbationDiscriminationQualification`
and leaves assessment unopened.

## Claim ceiling

The maximum claim is
`LocalDevelopmentPerturbationDiscriminationFeasibility`. V22 cannot establish
introspection, self-modeling, consciousness, faithful explanation, natural
mental-state access, mechanism identity, Stage 0C confirmation, Stage 1
authorization, benchmark evidence, or production readiness.

Execution and the assessment-preserving stop are recorded in
[`41-v22-execution-record.md`](41-v22-execution-record.md).
