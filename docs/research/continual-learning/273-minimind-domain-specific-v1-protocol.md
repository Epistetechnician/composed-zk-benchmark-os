# MiniMind domain-specific continual-learning protocol V1

State slice: `continual-learning-minimind-domain-specific-v1`.

## Boundary

This is a fresh small-model continual-learning lane. It is separate from all
Gemma, Qwen, Oak Lab, adapter-bank, plasticity-recovery, and closed
`NoCandidate` artifacts. None of those scientific artifacts are inputs.

The upstream MiniMind source is pinned to:

- URL: `https://github.com/jingyaogong/minimind.git`
- commit: `7a6fddd63a30c06b2fdd5fac4089922b29bc841b`
- license: Apache-2.0

The V1 model configuration is the dense MiniMind-3-shaped configuration with
`hidden_size=768`, `num_hidden_layers=8`, `vocab_size=6400`, and no MoE. The
historical MiniMind2-small checkpoint and the MoE variant are not V1 inputs.

## Scientific object

The object is a single base model exposed to an ordered stream of three
domains: `domain_a`, `domain_b`, and `domain_c`. Each domain has disjoint fit,
tune, and assessment data. Model-bearing data must be public or explicitly
licensed, document- and author-disjoint across splits, and represented by an
external custody manifest before execution.

The fixed arms are:

- `untouched`: no update;
- `joint_oracle`: all domain data available jointly;
- `sequential_full`: full-parameter sequential update;
- `sequential_lora`: one cumulative LoRA state updated sequentially;
- `sequential_replay`: sequential update with fixed prior-domain replay;
- `domain_adapters`: one independently addressable adapter per domain.

All updating arms use the same domain order, token budget, optimizer-step
budget, sequence length, replicate seeds, and checkpoint boundaries. Forward
and reverse order are both required. The domain-adapter arm is a conditional
specialization control and is not, by itself, evidence of general continual
learning.

## Endpoint and guards

The primary endpoint is the final macro-average held-out BPB improvement
relative to the untouched base after the complete domain sequence. Higher is
better. Tune selects the arm; assessment is evaluated only after the selection
lock.

Hard guards are maximum prior-domain forgetting, reverse-order sensitivity,
exact checkpoint restoration, complete stage coverage, deterministic
repeatability, and zero missing or attrited cases. Thresholds are fixed in
this protocol and may not be changed from assessment results: maximum
forgetting `0.25`, maximum forward/reverse order delta `0.20`, and maximum
checkpoint restoration absolute error `1e-12`.

The exact-synthetic fixture uses 3 replicate seeds, 3 order seeds, both order
directions, and all 3 splits, producing 108 trials. Its vector loss is a
qualification fixture only; it is not a language-model result.

## Execution and custody

The deterministic fixture may run offline without a model. Its canonical
artifact is outside the repository at:

`/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v1-synthetic-20260902-r2`

The real MiniMind path is implemented but sealed. It requires a fresh,
packet-bound, independently signed Ed25519 `ACCEPT` receipt, a clean source
checkout at the pinned commit, a fresh corpus manifest, and an external
owner-only artifact root. The runner sets offline flags and performs no model
or dataset download. Once opened, it runs the same 108-trial factorial as the
fixture across the six arms, three splits, three replicate seeds, and both
order directions. Checkpoint boundaries are verified with in-memory exact
snapshots; raw model weights are not retained in the aggregate output root.

No operator self-signature is accepted. No real model training, assessment,
provider call, production traffic, benchmark promotion, or Evidence Ledger
mutation is authorized by this protocol alone.

## Claim ceiling

The canonical fixture is capped at
`LocalDevelopmentMiniMindDomainSequenceSyntheticOnly`. A future accepted
model-bearing qualification may claim no more than
`LocalDevelopmentMiniMindDomainSequenceQualificationV1`; it cannot establish
general continual-learning superiority, production readiness, or benchmark
evidence without a separate protocol.

Every mutation in this phase names state slice
`continual-learning-minimind-domain-specific-v1`.
