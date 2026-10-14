# V40R2 Fit Counterfactual Acquisition Protocol

State slice: `V40R2FitCounterfactualAcquisitionProtocol`.

Status: `ModelFreeEnvelopeImplemented / ModelAcquisitionNotAuthorized`.

The acquisition envelope separates the frozen pre-update feature packet from
counterfactual labels. It requires 384 fit-only source states. At each source
state, features are captured before the corresponding update; only after the
complete feature packet is validated and sealed may identical model and
optimizer states be forked into task-replay and protected-replay branches.

Each branch records acquisition, protection, retention, paraphrase, and
calibration outcomes on fit-only probes. The label packet is independently
hashed and bound to the sealed feature packet and each exact source-state hash.
The family continues under a precommitted schedule that cannot depend on either
branch outcome.

The validator rejects tune or assessment rows, incomplete coverage, feature
leakage, branch omissions, nonfinite outcomes, source-state mismatches, and
packet tampering.

No model execution, trajectory update, feature value, counterfactual outcome,
router fit, tune access, or assessment access is authorized by this slice.
Maximum claim remains `LocalProspectiveProtectionRoutingDevelopmentV40`.
