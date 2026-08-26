# V37 optimizer-seed policy boundary

Status: `DocsOnlyFreshCampaignPolicyFrozen;ExecutedSlicesRecordedSeparately`.

State slice: `continual-learning-qwen25-optimizer-seed-policy-v37`.

## Purpose

V37 freezes the next Qwen2.5 acquisition campaign policy after the V36
task-seed versus optimizer-seed diagnosis. It does not execute a model,
training, assessment, retention, interference, provider, production, or
network operation.

## Evidence carried forward

The independently revalidated V36 campaign established:

- the fixed V34-failing task seed `20260857` passed with optimizer seeds
  `20260856` and `20260858`;
- the same task seed failed with optimizer seed `20260857`;
- holding optimizer seed `20260857` fixed caused all three tested task seeds
  to fail the T0 train-above-baseline and held-out-floor gates;
- repeated train and held-out readouts were byte-stable for the inspected pass
  and fail adapters.

This is local optimizer-seed sensitivity evidence for the cached Qwen2.5 T0
route. It is not a model-quality claim, seed-mining justification, or
campaign-level acquisition result.

## Frozen next-campaign policy

The next separately authorized campaign MUST use:

- the unchanged cached `Qwen2.5-0.5B-Instruct-4bit` model;
- the unchanged raw-text update serialization and route-bound prompt;
- the unchanged optimizer, learning rate, batch size, LoRA configuration,
  update budget, task order, readout, and eligibility gates;
- one optimizer seed, `20260856`, fixed before task construction and reused
  for every case;
- three fresh task seeds, `20260859`, `20260860`, and `20260861`, fixed before
  execution;
- three complete four-task acquisition cases, with independent validation
  before campaign aggregation;
- campaign eligibility only when every case passes every frozen gate.

The seed choice is a preregistered diagnostic repair hypothesis selected by a
deterministic minimum-seed rule over the V36 optimizer-seed candidate set. It
MUST NOT be changed after inspecting any V37 case. A passing V37 campaign would
support only a local acquisition-eligibility result under this frozen policy;
it would not establish retention, interference, general continual learning,
provider delivery, production readiness, SOTA, or breakthrough evidence.

## Fail-closed rules

- No per-case optimizer-seed changes.
- No seed expansion, seed deletion, adaptive tuning, or assessment-based
  selection after the campaign starts.
- No retention or interference run unless every case passes the campaign-wide acquisition gate and a separate phase authorizes it.
- No use of V36 assessment labels to tune V37 prompts, optimizer settings,
  task construction, or gates.
- Any incomplete, failed, or validator-invalid case makes the campaign
  ineligible and requires quarantine of the incomplete root.
- All generated artifacts remain repository-external and digest-bound.

## Execution authorization

This record freezes a protocol boundary only. The later V37 fixed-optimizer
repair validation and V40 fresh-task campaign are separate executed slices;
their records carry the execution results and narrower claim ceilings. This
boundary record itself contains no model execution. Its claim ceiling is
`LocalDevelopmentOptimizerSeedSensitivityDiagnosis`.
