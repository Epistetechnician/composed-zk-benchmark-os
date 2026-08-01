# V41R10 Single-Task Acquisition Pilot Preregistration

State slice: `V41R10AcquisitionPilotDesignAndImplementation`.

Status: `ProspectiveDesignFrozen / IndependentValidatorAuthorized / ExecutionUnauthorized`.

The pilot asks whether the pinned GPT-OSS-20B checkpoint can acquire task A of
the fresh V41 opaque registry through the validated V41R9 attention-LoRA path,
then retain it after context removal and a fresh base-model reload without
damaging the protected panel.

Frozen cell:

- model revision `d0e2aa76789354d715f8b22553b9feb6c462fcf0`;
- checkpoint configuration SHA-256
  `3a2a26ded679375b7928ddeca59764df7cea83220c1961035f6d6e232659e9ce`;
- V41 corpus hash
  `sha256:ab1c096ae51f72db83a0680f760cf3670da699b0745668272a8dc2cd74c85b3c`;
- task A, seed 410041, 32 optimizer steps;
- 16 direct, 16 paraphrase, and 16 withheld-composition queries;
- first 16 protected cases;
- `no_update`, `context_only`, and one native-MXFP4 rank-8 q/k/v/o LoRA arm;
- context removed and training model destroyed before fresh-model adapter reload.

Pre-update overall accuracy must lie in `[0.15, 0.35]`, with every class at
most `0.40`. Context-only overall accuracy must reach `0.90` and every class
`0.85`. A persistent pilot signal requires reloaded context-free overall
accuracy at least `0.70`, every query class at least `0.60`, advantage over
no-update at least `0.20`, protected drop at most `0.02`, exact adapter-state
reload, all 32 locked updates, V41R9 memory compliance, and closed tune and
assessment states.

The independent validator must recompute metrics from raw rows and reject
source, model, runtime, inventory, budget, reload, memory, context-boundary, or
classification drift. Implementation and hermetic tests are allowed. Model or
GPU execution is not.

Maximum implementation ceiling:
`LocalImplementationSingleTaskAcquisitionPilotV41R10`.
