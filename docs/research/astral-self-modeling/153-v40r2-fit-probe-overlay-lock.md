# V40R2 Fit Probe Overlay Lock

State slice: `V40R2FitProbeOverlayLock`.

Status: `OverlayImplemented / TokenizerQualificationPending`.

The initial `e5c251f-r1` tokenizer construction is retired because it used
uncommitted source and omitted source, runtime, and model inventories. It
performed no forward pass. It cannot be promoted or retried under the same
identity.

The deterministic overlay adds training, direct, paraphrase, candidate, and
calibration definitions only for the four fit families without changing the
sealed base corpus. It also selects a balanced 16-case protected panel from
the previously qualified V30 response-free fixture; every protected target and
candidate is disjoint from V40R2 targets.

Calibration is frozen as multiclass mean Brier error derived from direct and
protected candidate log probabilities, requiring no additional forward pass.
Tune and assessment prompts are not constructed.

Tokenizer-only qualification must still seal all prompt token sequences,
confirm the 96-token ceiling, and compute the exact evaluation-forward-token
budget. No model forward pass or update is authorized.
