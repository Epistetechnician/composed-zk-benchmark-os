# Capability-Tier Perturbation Replication V23

State slice: `astral-capability-tier-replication-v23`.

Status: `NotRunCapabilityTierPerturbationQualification`. Confirmation:
`NotAuthorized`.
Stage 0C: `Blocked`. Stage 1: `BlockedByStage0C`.

## Purpose

V22's cached 0.5B Qwen failed three-way activation/input/no-change
qualification. V23 tests whether the same construction-controlled capability
appears in the locally cached Llama-3.2-1B-Instruct 4-bit model. This is a
fresh-model, fresh-concept replication, not a V22 prompt or strength search.

The local 4B Nemotron checkpoint is excluded prospectively. Its hybrid
Mamba/attention architecture does not share the exact controlled transformer
forward seam, so using it would change model capability and intervention
instrument simultaneously.

## Frozen changes from V22

- target: cached Llama-3.2-1B-Instruct 4-bit;
- 16 layers, hidden width 2048;
- proportional post-block sites `3`, `7`, and `11`;
- 16 fresh neutral concepts with 8/4/4 fit/tune/assessment split.

Everything else is inherited unchanged from V22:

- strengths `0.5/1.0/2.0`;
- four report wrappers;
- activation, textual gaslight, and no-intervention conditions;
- byte-identical activation/no-intervention prompts;
- deterministic response-position permutation;
- concept direction normalization by fit median residual norm;
- fit selection by macro balanced accuracy, then lower strength, then earlier
  site;
- tune qualification without reselection;
- assessment absence before independent lock validation;
- primary metrics and candidate thresholds.

Fresh concepts are:

- fit: `birch`, `cello`, `fjord`, `beacon`, `prairie`, `bronze`, `marina`,
  `satin`;
- tune: `ravine`, `granite`, `lilac`, `astrolabe`;
- sealed assessment: `poplar`, `subway`, `turmeric`, `mooring`.

## Qualification and assessment

The V22 qualification gates remain:

- exact controlled/native, repeat, and zero-strength parity;
- fit macro balanced accuracy at least `0.45`;
- tune macro balanced accuracy at least `0.40`;
- tune activation recall at least `0.25`;
- tune activation-versus-none accuracy at least `0.60`.

If qualified, lock configuration and predictions before assessment. The V22
assessment gate remains: macro balanced accuracy at least `0.50`, activation
recall at least `0.35`, activation-versus-none accuracy at least `0.65`,
positive concept-bootstrap lower bound over chance, and every wrapper at least
`0.40`.

## Claim ceiling

The maximum claim is
`LocalDevelopmentCapabilityTierPerturbationReplication`. A positive result
would establish only construction-specific causal coupling in one cached 1B
model. It cannot establish introspection, self-modeling, consciousness,
faithful explanation, natural mental-state access, mechanism identity, Stage
0C confirmation, Stage 1 authorization, benchmark evidence, or production
readiness.

Execution and the assessment-preserving stop are recorded in
[`43-v23-execution-record.md`](43-v23-execution-record.md).
