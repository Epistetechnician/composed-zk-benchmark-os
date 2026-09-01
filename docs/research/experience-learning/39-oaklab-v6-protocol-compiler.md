# Oak Lab constrained update policy V6 executable protocol

State slice: `oaklab-experience-learning-constrained-update-policy-v6`

Status: `frozen_pending_independent_review`

Claim ceiling: `LocalDevelopmentOakLabConstrainedUpdatePolicyV6ProtocolCompilerOnly`

## Purpose

V6 is a new protocol identity after the terminal V5 review rejection. It does
not patch or import V5 scientific artifacts. The scientific object is the
complete constrained update-policy trajectory, compared with fixed batch-one
SGD on identical ordered streams. The candidate is not claimed to work until
the protocol is accepted, implemented, qualified, and independently validated.

## Executable contract

The source specification emits exactly seven closed-world sections:

1. byte-exact hashing, PRNG, generator-draw, and rational action assignment;
2. indexed controller transitions, complete pending state, and simultaneous
   recurrence updates;
3. generator rosters, unconditional draw order, framed source identifiers,
   stream equations, and segment boundaries;
4. typed operation ASTs, numeric rules, logical byte layouts, and resource
   separation;
5. exact arm participation, paired endpoints, Holm groups, missing rules, and
   gate predicates;
6. shift-segment-bounded adaptation lag with explicit censoring;
7. complete lock, counter, control, validator, and assessment-absence schemas.

The compiler and independent validator are compiler-only. They import no
learner, stream runner, backend, provider, energy, or Astral module. Assessment
materialization is explicitly absent.

## Execution boundaries

Independent review must accept the exact frozen source, compiler, compiled
artifact, validator, tests, `AGENTS.md`, and digest packet before any learner
implementation. Acceptance authorizes only the synthetic implementation slice.
Fit/tune locking, synthetic qualification, separate real execution review,
fresh real custody, and a workload-specific privileged energy receipt remain
required in sequence. GiveMeANode/H100 provisioning is not authorized by this
compiler identity. The plasticity guard remains a historical comparator and
Astral remains isolated.

## Files

- `experiments/experience_learning/v6_protocol_spec.json`
- `experiments/experience_learning/compile_v6_protocol.py`
- `experiments/experience_learning/validate_v6_protocol_compilation.py`
- `experiments/experience_learning/v6_compiled_protocol.json`
- `experiments/experience_learning/tests/test_v6_protocol_compiler.py`

## Local verification

```text
python -m experiments.experience_learning.compile_v6_protocol \
  experiments/experience_learning/v6_protocol_spec.json \
  --output experiments/experience_learning/v6_compiled_protocol.json
python -m experiments.experience_learning.validate_v6_protocol_compilation \
  experiments/experience_learning/v6_protocol_spec.json \
  experiments/experience_learning/v6_compiled_protocol.json
python -m pytest -q experiments/experience_learning/tests/test_v6_protocol_compiler.py
```

The compiler and independent validator pass locally; the five hermetic tests
pass. This is not an independent review or scientific result.
