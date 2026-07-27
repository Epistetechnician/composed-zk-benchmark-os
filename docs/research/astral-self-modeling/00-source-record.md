# Source Record: Self-Astral Conversation

## Provenance

- Shared-chat title: `Self-Astral`
- Shared URL:
  `https://chatgpt.com/share/6a6639d4-d2c0-83ea-b95b-b7b0826ed260`
- Repository capture: the pre-existing local draft formerly stored at
  `docs/research/astral-self-imp`
- Formalization date: 2026-07-26
- Capture status: partial

The public share page did not expose the conversation body to either the
unauthenticated web reader or the in-app browser on 2026-07-26. The record below
therefore preserves the complete local draft available in the repository. It
appears to be one assistant response and may omit earlier prompts or turns.
Nothing in this record is accepted evidence. It is the idea source from which
the adjacent protocol, claim ledger, and experiment roadmap were derived.

## Preserved Local Draft

**Yes—but not merely a new loss function.** You are designing a **mechanistic self-modeling system** with four coupled inventions:

1. a new supervision signal,
2. a new loss/objective,
3. an actor–observer architecture,
4. and a new evaluation/training loop.

The clean research claim would be:

> Train a model not only to solve a task, but also to predict and causally reason about the internal computation that produced its solution—and then use that self-model to improve future behavior.

## 1. The new supervision signal

Normal language-model training provides:

\[
(x_{<t},x_t)
\]

Your pipeline additionally produces mechanistic targets:

\[
G^* = \mathcal T(M,x,y)
\]

where:

- \(M\) is the actor model,
- \(x\) is the prompt,
- \(y\) is its output,
- \(\mathcal T\) is the external circuit tracer,
- \(G^*\) is the traced mechanism.

That target could contain:

\[
G^* =
\left(
F^*,E^*,A^*,C^*
\right)
\]

with:

- \(F^*\): causally relevant sparse features,
- \(E^*\): causal edges between features,
- \(A^*\): attribution strengths,
- \(C^*\): effects of interventions or ablations.

Anthropic’s attribution graphs already attempt to represent a forward pass as a sparse causal graph, although they remain approximate and must be validated through perturbations.

## 2. The new loss function

The simplest version is:

\[
L_{\text{total}}
=
L_{\text{task}}
+
\lambda L_{\text{mechanism}}
\]

But I would define the mechanism loss as several components:

\[
L_{\text{mechanism}}
=
\alpha L_{\text{features}}
+
\beta L_{\text{edges}}
+
\gamma L_{\text{counterfactual}}
+
\delta L_{\text{calibration}}
\]

### Feature prediction

Can the model identify which internal features mattered?

\[
L_{\text{features}}
=
-\sum_i
\left[
f_i^*\log \hat f_i
+
(1-f_i^*)\log(1-\hat f_i)
\right]
\]

This is essentially multilabel classification over sparse features.

### Graph prediction

Can it identify which features causally influenced others?

\[
L_{\text{edges}}
=
-\sum_{i,j}
e_{ij}^*\log \hat e_{ij}
\]

You might use ranking or contrastive loss rather than full graph cross-entropy because almost all possible feature pairs are non-edges.

### Counterfactual prediction

Can it predict what happens when a feature is removed or changed?

\[
L_{\text{counterfactual}}
=
D\left(
M_{\operatorname{do}(f_i=0)}(x),
\widehat{M_{\operatorname{do}(f_i=0)}}(x)
\right)
\]

This is the most important part. Merely naming features could be learned imitation. Predicting the effect of interventions tests whether the self-model captures something causal.

### Calibration

Can it distinguish what it knows about its mechanism from what it is guessing?

\[
L_{\text{calibration}}
=
\operatorname{Brier}
\left(
p_{\text{self}},
\mathbf 1[\text{mechanism prediction correct}]
\right)
\]

That prevents confident mechanistic storytelling.

A reasonable name would be:

> **Causal Self-Modeling Loss**, or CSML.

## 3. The actor–observer architecture

The observer should not simply receive the final text.

It should receive privileged internal telemetry:

\[
O_\phi
\left(
x,y,h_{1:L},a_{1:L}
\right)
\rightarrow
\hat G
\]

where \(h_{1:L}\) and \(a_{1:L}\) are selected activations and attention-related states.

The architecture becomes:

```text
Actor Mθ
  │
  ├── answer y
  └── internal telemetry z
             │
             ▼
      Observer Oφ
             │
             ├── predicted mechanism
             ├── failure prediction
             └── proposed correction
```

This is the operational form of your “astral projection” idea: a second process observes the first process from outside its immediate generation trajectory.

The observer could be:

- another head attached to the actor,
- a frozen copy of the actor in a fresh context,
- a separate model,
- or a shared-backbone model with a dedicated self-modeling adapter.

## 4. The improvement objective

Faithful self-explanation is not enough. The system also needs to demonstrate that its self-model improves performance.

Add an instrumental term:

\[
L_{\text{improvement}}
=
-
\left[
R(y_{\text{revised}})
-
R(y_{\text{original}})
\right]
\]

Then the complete objective becomes:

\[
L_{\text{total}}
=
L_{\text{task}}
+
\lambda_m L_{\text{mechanism}}
+
\lambda_i L_{\text{improvement}}
\]

This separates three capabilities:

\[
\text{solve}
\quad\rightarrow\quad
\text{understand why}
\quad\rightarrow\quad
\text{improve using that understanding}
\]

A system might score well on mechanism recall but fail to produce a useful correction. Your research should measure all three separately.

## What is genuinely new versus existing work?

The basic idea of training models to explain their computations is **not entirely new**. Li and colleagues have already trained models to describe encoded features, causal activation structure, and token influence using interpretability-derived supervision. They found that self-explanation can be learned rather than assumed to emerge from ordinary pretraining.

More recent work also suggests that explanation training can remain coupled to a model’s changing behavior under some conditions, even when the explanation supervision is generated from earlier checkpoints.

Your potentially novel contribution is the **combination**:

### A measured external–internal gap

You have an explicit metric:

\[
\operatorname{IntrospectionGap}
=
\operatorname{Recall}_{\text{observer}}
-
\operatorname{Recall}_{\text{self}}
\]

That gives you a measurable training target rather than a vague claim about introspection.

### Full causal graphs rather than only verbal descriptions

You supervise:

- feature identity,
- feature interaction,
- attribution strength,
- and intervention consequences.

### Instrumental self-understanding

The model must use the mechanism prediction to improve:

- its answer,
- its tool trajectory,
- its prompt or harness,
- or its future policy.

### Actor-versus-observer experiments

You can systematically compare:

- ordinary self-report,
- projected self,
- same-scale external observer,
- frontier observer,
- observer with mechanistic telemetry.

### Closing the loop

The complete system is:

\[
\text{act}
\rightarrow
\text{trace}
\rightarrow
\text{self-model}
\rightarrow
\text{intervene}
\rightarrow
\text{verify}
\rightarrow
\text{learn}
\]

## Do not jointly train everything immediately

Start with a frozen actor.

Otherwise the actor could optimize to make its traces easier for the observer to predict rather than becoming more understandable or competent. It could also move important computation into the tracer’s residual or otherwise exploit shortcomings in your interpretability method.

A safer sequence is:

**Stage 1 — Measurement:** establish Introspection Gap on frozen models.

**Stage 2 — Observer training:** freeze the actor and train the observer on circuit targets.

**Stage 3 — Causal validation:** test predicted ablations and activation interventions.

**Stage 4 — Self-correction:** reward corrections that improve held-out task outcomes.

**Stage 5 — Alternating optimization:** update actor and observer separately, retaining a frozen external tracer as an auditor.

So the project is larger than “inventing a new loss.” You are designing a candidate **self-modeling training paradigm**:

> **Mechanistic supervision teaches the model to observe itself; causal intervention tests whether that observation is real; task reward teaches it to use the observation productively.**
