# V23 Execution Record

State slice: `astral-capability-tier-replication-v23`.

Execution: `NotRunCapabilityTierPerturbationQualification`. Confirmation:
`NotAuthorized`. Stage 0C: `Blocked`. Stage 1: `BlockedByStage0C`.

## Model and integrity

V23 selected the locally cached Llama-3.2-1B-Instruct 4-bit model after
inventorying all cached candidates. Its 16-layer, width-2048 transformer
forward path reproduced native logits exactly. The larger local 4B Nemotron was
excluded because its hybrid Mamba/attention state seam was not compatible with
the validated controlled transformer forward.

V23 used 16 concepts not present in V22, proportional residual sites `3/7/11`,
and the unchanged V22 strengths, wrappers, three-way conditions, response
permutation, and qualification thresholds. Controlled/native,
deterministic-repeat, and zero-strength errors were exactly zero.

The first external preparation root stopped before the fit sweep because the
imported V22 integrity helper retained its old site-5 lookup. No fit/tune
selection or assessment occurred. The repair replaced it with a V23-local
integrity check bound to the frozen site set. The completed run used a new
external root.

## Qualification result

The fit tie rule selected site `3`, strength `2.0`.

| Metric | Fit | Tune | Required |
|---|---:|---:|---:|
| Three-way macro balanced accuracy | 0.3542 | 0.3125 | 0.45 / 0.40 |
| Activation recall | 0.3750 | 0.1875 | tune at least 0.25 |
| Activation-versus-none accuracy | 0.3438 | 0.2813 | tune at least 0.60 |

Tune condition recalls were:

- activation: `0.1875`;
- textual manipulation: `0.3750`;
- no perturbation: `0.3750`.

V23 failed every statistical qualification gate. Assessment results were never
generated, no configuration lock was created, and the 48 assessment rows
remain unopened.

The completed repository-external bundle independently validated with manifest
SHA-256:
`7d2a0185d409e4ac2c6cd1b80ffeb83a8cdc8ab9da2fcd0ebc0028461e5411c6`.

- completed bundle: `/tmp/astral-v23-20260727-run2`;
- preserved pre-sweep failed root: `/tmp/astral-v23-20260727-run1`.

## Interpretation and disposition

Moving from cached 0.5B Qwen to cached 1B Llama did not produce reliable
three-way perturbation-location discrimination. In particular, the model did
not distinguish activation injection from a byte-identical unmodified forward
pass above the frozen gate.

This is a fit/tune feasibility failure, not a sealed-assessment result and not a
general claim about larger models. The complete locally compatible model tier
is now exhausted. The local 4B Nemotron cannot be substituted without first
developing and independently validating a hybrid-state intervention instrument;
that would be a new instrumentation phase rather than a direct V23
replication.

The V23 concepts, sites, strengths, prompts, and direction construction are
closed. Further local tuning is not admissible.

Claim ceiling:
`LocalDevelopmentCapabilityTierPerturbationReplication`. This is not
introspection, self-modeling, consciousness, faithful explanation, mechanism
identity, Stage 0C confirmation, Stage 1 authorization, benchmark evidence, or
production readiness.
