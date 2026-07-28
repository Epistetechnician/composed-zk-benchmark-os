# V22 Execution Record

State slice: `astral-privileged-information-boundary-v22`.

Execution: `NotRunPerturbationDiscriminationQualification`. Confirmation:
`NotAuthorized`. Stage 0C: `Blocked`. Stage 1: `BlockedByStage0C`.

## Integrity

V22 used the cached Qwen2.5-0.5B-Instruct 4-bit model and the existing MLX
controlled-forward seam. All three report completions were single tokens.
Controlled/native, deterministic-repeat, and zero-strength maximum errors were
exactly zero.

The corpus contained 192 rows over 16 neutral concepts, four wrappers, and
three conditions. Fit/tune/assessment contained 96/48/48 rows. Activation and
no-intervention trials used byte-identical prompts. Response positions were
deterministically permuted across concepts and wrappers.

The bounded fit sweep covered sites `5/11/17` and strengths `0.5/1.0/2.0`.
The frozen tie rule selected site `5`, strength `2.0`.

## Qualification result

| Metric | Fit | Tune | Required |
|---|---:|---:|---:|
| Three-way macro balanced accuracy | 0.3542 | 0.2917 | 0.45 / 0.40 |
| Activation recall | 0.3750 | 0.2500 | tune at least 0.25 |
| Activation-versus-none accuracy | 0.3906 | 0.2188 | tune at least 0.60 |

Tune condition recalls were:

- activation: `0.2500`;
- textual manipulation: `0.4375`;
- no perturbation: `0.1875`.

The selected configuration failed both the fit/tune macro-accuracy gates and
the exact-text activation-versus-none gate. It therefore did not qualify for
assessment.

Assessment results were never generated, no configuration lock was needed, and
the 48 assessment rows remain unopened. The repository-external bundle
independently validated with manifest SHA-256:
`2ad5659fac41c61094356e6b1b2987feeab93490b13d5fc22b36209ec173a29a`.

Repository-external bundle: `/tmp/astral-v22-20260727-run1`.

## Interpretation

This small cached Qwen did not show reliable construction-controlled
discrimination between an internal activation injection and an identical-text
unmodified forward pass. Its modest textual-manipulation recall does not rescue
the internal-location failure.

This is a feasibility qualification failure, not an assessment-set refutation
of activation awareness in language models generally. It is consistent with
the concern that open models can react to perturbations without reliably
identifying whether the perturbation occurred in input text or hidden state.

The exposed fit/tune concepts, sites, strengths, wrappers, direction
construction, and report format are closed. Increasing steering strength or
editing prompts against these exposed results is not admissible. A future
replication requires a new model-capability tier, a new sealed corpus, and the
same or stronger three-way and exact-text controls.

Claim ceiling:
`LocalDevelopmentPerturbationDiscriminationFeasibility`. This is not
introspection, self-modeling, consciousness, faithful explanation, mechanism
identity, Stage 0C confirmation, Stage 1 authorization, benchmark evidence, or
production readiness.
