# V40R2 Fit Acquisition Runner Authorization

State slice: `V40R2FitAcquisitionRunnerAuthorization`.

Status: `AuthorizationGateImplemented / BlockedByFitProbeOverlay`.

The preflight found that the sealed V40R2 corpus has family, task, case, and
target identities but no locked training prompts, candidate sets, direct or
paraphrase probes, protected probe fixture, calibration probe, or evaluation
token budget. A model run would therefore introduce scientific choices after
the claimed lock and is not authorized.

The future runner boundary is now fail-closed. It requires a two-pass canonical
replay: pass one captures and seals all 384 pre-update feature rows; pass two
must reproduce every model and optimizer source-state hash before creating
task-replay and protected-replay counterfactual labels. Replay mismatch,
partial coverage, identity reuse, or any opened tune/assessment partition
retains failure and stops.

The frozen maximum is 1,792 gradient steps and 688,128 update tokens using the
cached Qwen checkpoint and pinned Python/MLX runtime. Evaluation-forward tokens
remain unset until the fit-only probe overlay exists.

No forward pass, update, feature value, label, fit, scientific result, or claim
promotion is authorized. The next required slice is
`V40R2FitProbeOverlayLock`.
