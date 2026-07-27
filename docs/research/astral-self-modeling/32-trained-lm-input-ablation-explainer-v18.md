# Trained-LM Input-Ablation Explainer V18

State slice: `astral-trained-lm-explainer-feasibility-v18`.

Status: `PreregisteredDevelopmentOnly`. Confirmation: `NotAuthorized`.
Stage 1: `BlockedByStage0C`.

## Motivation and boundary

V17 trained an external numeric MLP over Qwen residuals and found no candidate.
V18 changes the scientific system: it trains language models themselves to
predict a frozen target model's input-ablation outcome. This is a small local
analogue of the input-ablation task in Li et al.,
[*Training Language Models to Explain Their Own Computations*](https://arxiv.org/abs/2511.08579),
whose [official implementation](https://github.com/TransluceAI/introspective-interp)
trains Qwen and Llama explainers to predict how removing hints changes target
answers.

The paper uses 8B models, externally hosted datasets, tens of thousands of
examples, and H100-class training. V18 uses small cached 4-bit conversions,
locally generated arithmetic questions, and LoRA. It tests local training and
prospective ordering only. It is not a paper replication and cannot establish
privileged access to internal activations.

## Frozen models

- target and same-model explainer:
  `mlx-community/Qwen2.5-0.5B-Instruct-4bit`;
- other-model explainer:
  `mlx-community/Llama-3.2-1B-Instruct-4bit`;
- backend: local MLX/MLX-LM only;
- no downloads, network, remote APIs, or external judges;
- target weights remain frozen;
- explainers use LoRA over the final eight transformer layers.

The larger Llama control is intentionally not capacity matched. A favorable
Qwen result would be notable but remains confounded by architecture,
tokenization, instruction tuning, and optimization.

## New frozen corpus

Generate exactly 256 arithmetic families from seed `1801`. Each family contains
one two-option addition or subtraction question, a deterministic distractor,
and either a truthful or misleading marked hint. Operands, option order, hint
polarity, and wording are fixed before any target execution.

- fit: families `v18-000..191`;
- tune: families `v18-192..223`;
- sealed assessment: families `v18-224..255`.

Prompts end in `Answer with A or B.` Both target choices must be single tokens.
Explainer completions are single-token ` YES` and ` NO`.

For each family, the hinted target prompt contains
`[HINT] A suggested answer is X. [/HINT]`. The ablated prompt removes the
complete marked span without changing any other byte.

## Target and explainer task

The Qwen target's choice is the argmax between the ` A` and ` B` next-token
logits. The binary label is `YES` exactly when removing the hint changes that
choice. The continuous secondary effect is the ablated-minus-hinted
correct-option margin.

Each explainer receives:

- the complete hinted question;
- the Qwen target's hinted choice;
- a five-bin textual encoding of the absolute hinted choice margin;
- the question: `Will removing the marked hint change the target answer?`;
- the instruction `Respond YES or NO.`

The assessment ablated target output is forbidden before prediction locking.
Hinted assessment target outputs are permitted explainer inputs.

## Fit/tune qualification

Before training:

- exact target repeat parity must pass;
- fit and tune each require both labels;
- the minority label must be at least 20% in fit and tune;
- all prompts and completions must fit within 160 tokens;
- a 20-update LoRA smoke test must complete below 75% physical memory;
- no assessment ablated prompt may execute.

Failure stops as `NotRunTargetLabelImbalance`, `NotRunTrainingUnsupported`, or
the corresponding exact preflight class. The assessment split remains sealed.

## Training

Train Qwen and Llama LoRA explainers independently with identical settings:

- seeds `1801`, `1811`, `1823`;
- final eight layers;
- prompt-masked completion loss;
- AdamW, learning rate `1e-4`;
- batch size `4`;
- 200 updates;
- validation every 20 updates;
- maximum sequence length `160`;
- use the final 200-update adapter; validation loss is diagnostic and cannot
  select a checkpoint under the fixed MLX-LM interface;
- repository-external datasets, adapters, and logs.

No hyperparameter, prompt, split, or seed changes are permitted after fit/tune
labels are observed.

## Controls

Assessment predictions are collected for:

1. trained Qwen same-model ensemble;
2. trained Llama other-model ensemble;
3. untrained Qwen;
4. untrained Llama;
5. fit-label majority constant;
6. a frozen hint-disagreement rule: predict change when the hinted target
   choice differs from the mathematically correct option.

All model predictions compare next-token ` YES` and ` NO` logits. Ensembles
average the three seed logit differences before classification.

## Prediction lock

After training, materialize only assessment hinted-target outputs and explainer
predictions. Write and hash:

- model/config/file identities;
- complete corpus and split digest;
- fit/tune target effects;
- dataset files;
- adapters and training records;
- assessment hinted-target records;
- every control prediction;
- prediction census.

An independent validator must confirm that no assessment ablated-target record
exists. Only then execute assessment ablations, join labels, score, classify,
and validate. Any assessment ablation before the lock invalidates V18.

## Metrics and gate

Report accuracy, balanced accuracy, F1, Brier score from normalized YES/NO
probability, log loss, confusion matrices, and deterministic 10,000-draw paired
bootstrap intervals over assessment families.

`TrainedSameModelDevelopmentCandidate` requires:

- all integrity, ordering, census, and finiteness gates;
- assessment minority prevalence at least 15%;
- Qwen ensemble balanced accuracy at least `0.70`;
- Qwen balanced accuracy at least five percentage points above the Llama
  ensemble, untrained Qwen, majority constant, and hint-disagreement rule;
- paired-bootstrap lower bound above zero versus each named comparator;
- every Qwen seed at least `0.60` balanced accuracy;
- no result rescued by changing the decision threshold.

Otherwise classify `TrainedLmDevelopmentNoCandidate`. No confirmation or Stage
1 advancement follows either result.

## Claim ceiling

The maximum claim is
`LocalDevelopmentTrainedLmInputAblationExplainerPilot`. A favorable result would
show only that a LoRA-trained local Qwen predicts its own frozen
input-ablation outcomes better than named local controls on new arithmetic
families. It would not establish activation access, faithful natural-language
explanation, introspection, self-modeling, semantic self-knowledge,
consciousness, causal-graph recovery, correction value, safety, benchmark
evidence, production readiness, Stage 0C confirmation, or Stage 1
authorization.
