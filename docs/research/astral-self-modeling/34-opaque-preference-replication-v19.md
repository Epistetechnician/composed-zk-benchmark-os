# Opaque-Preference Trained-LM Replication V19

State slice: `astral-opaque-preference-replication-v19`.

Status: `PreregisteredReplicationOnly`. Confirmation: `NotAuthorized`.
Stage 1: `BlockedByStage0C`.

## Purpose

V18 produced a trained-Qwen development candidate, but visible arithmetic made
the labels recoverable without modeling target-specific behavior and one Llama
seed independently achieved perfect accuracy. V19 addresses both limitations
without reopening or tuning V18.

V19 tests whether a LoRA-trained Qwen predicts its own sealed hint-ablation
choices on ambiguous language-preference prompts better than:

- an identically trained Llama majority-vote ensemble;
- the best individual Llama seed;
- untrained Qwen and Llama;
- a fit-label majority;
- a fit-only hint-option lookup.

The design remains a small local analogue of the input-ablation experiments in
Li et al., [*Training Language Models to Explain Their Own
Computations*](https://arxiv.org/abs/2511.08579), not a replication of their
8B-model, tens-of-thousands-example study.

## Frozen models and training

- frozen target and same-model explainer base:
  cached `mlx-community/Qwen2.5-0.5B-Instruct-4bit`;
- other-model explainer:
  cached `mlx-community/Llama-3.2-1B-Instruct-4bit`;
- LoRA over the final eight layers;
- seeds `1901`, `1913`, `1931`;
- AdamW, learning rate `1e-4`, batch size `4`;
- `240` updates, validation every `20`;
- maximum sequence length `192`;
- prompt-masked single-token ` YES`/` NO` loss;
- final adapters only;
- offline MLX-LM execution and repository-external artifacts.

No model, optimizer, seed, layer, threshold, or ensemble change is allowed
after fit/tune target labels are observed.

## New corpus

Generate exactly 320 families from seed `1901`:

- fit: `v19-000..239`;
- tune: `v19-240..279`;
- sealed assessment: `v19-280..319`.

Each family combines a deterministic natural-language context with two
plausible continuations sampled without replacement from a frozen vocabulary.
There is deliberately no externally correct option. The unhinted Qwen choice
defines the target-specific preference. A deterministic marked hint recommends
one option:

`[HINT] Choose A. [/HINT]`

The ablated prompt removes only that exact span. The target choice is the
argmax of single-token ` A` and ` B` logits. The binary label is `YES` exactly
when removing the hint changes the target choice.

Assessment unhinted outputs are forbidden before prediction locking.

## Explainer input

Each explainer receives:

- the complete hinted target prompt;
- the target's hinted choice;
- a five-bin encoding of the hinted choice-margin magnitude;
- the question asking whether removing the marked hint changes the target
  answer;
- the instruction to respond `YES` or `NO`.

No unhinted target choice, effect, hidden activation, family identifier, or
split identifier is included.

## Qualification

Before training:

- exact target repeat parity must be zero;
- fit and tune must each contain both labels with at least 20% minority;
- each split must contain both hint options;
- all sequences must fit under 192 tokens;
- a fixed 20-update Qwen smoke test must pass under 75% physical memory;
- no assessment unhinted target prompt may execute.

Failure stops without opening assessment effects.

## Ensembles and controls

For each model:

- individual seed predictions use the zero threshold on YES-minus-NO logits;
- the primary ensemble uses majority vote across three seeds;
- ensemble probability is the median of member probabilities;
- best-seed performance is reported post-assessment as a preregistered
  sensitivity, not used to select predictions.

The fit-only hint-option lookup predicts the majority label separately for
hint `A` and hint `B`. Ties use the global fit majority.

## Lock and execution order

1. Freeze and hash source, models, corpus, and split.
2. Measure only fit/tune hinted and unhinted target outputs plus assessment
   hinted outputs.
3. Qualify labels and train all six adapters.
4. Materialize every assessment prediction and control.
5. Write and independently validate the prediction lock while assessment
   effects are absent.
6. Execute each assessment unhinted target prompt exactly once.
7. Join, score, bootstrap, classify, manifest, and independently validate.

Any early assessment unhinted output invalidates V19.

## Replication gate

Report accuracy, balanced accuracy, F1, Brier score, log loss, confusion
matrices, seed dispersion, and 10,000-draw stratified paired-bootstrap
intervals.

`OpaquePreferenceReplicationCandidate` requires:

- every integrity and ordering gate;
- assessment minority prevalence at least 15%;
- Qwen majority ensemble balanced accuracy at least `0.70`;
- all Qwen seeds at least `0.60`;
- Qwen ensemble at least five percentage points above the Llama majority
  ensemble, the best individual Llama seed, untrained Qwen, majority, and
  hint-option lookup;
- paired-bootstrap lower bound above zero versus every named comparator;
- Qwen Brier score below the Llama ensemble and untrained Qwen;
- no decision-threshold tuning.

Otherwise classify `OpaquePreferenceReplicationNoCandidate`. No pooling with
V18 may rescue failure.

## Claim ceiling

The maximum claim is `LocalDevelopmentOpaquePreferenceReplication`. A passing
result would show only prospective target-specific input-ablation prediction
for one cached quantized Qwen under this ambiguous-language task. It would not
establish activation access, faithful explanation, introspection, self-modeling,
semantic self-knowledge, consciousness, correction value, safety, benchmark
evidence, Stage 0C confirmation, Stage 1 authorization, or production
readiness.
