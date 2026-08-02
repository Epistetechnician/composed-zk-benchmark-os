# V41R22 Single-Case Update-Substrate Calibration Preregistration

State slice: `V41R22SingleCaseUpdateSubstrateCalibration`.

Status: `ProspectivelyFrozen / LocallyValidated / ExecutionUnauthorized`.

V41R22 tests whether the exact V41R11 case-zero composition prompt and terminal
target can be acquired by the frozen all-attention rank-8 LoRA substrate. Four
checkpoint-reset arms form a non-adaptive 2x2 matrix: 64 or 512 steps crossed
with AdamW learning rate `2e-4` or `2e-3`. Each step is one forward/backward
pass over four identical examples. All arms run once; outcomes cannot change
the matrix, gates, or order.

An arm passes only when the target is top one, its candidate log-probability
margin is at least 2.0 nats, the last-eight to first-eight mean loss ratio is at
most 0.10, and a fresh checkpoint plus saved adapter reloads byte-exactly.
Protected accuracy is collateral diagnostics only. The frozen minimal-pass
order is 64/`2e-4`, 64/`2e-3`, 512/`2e-4`, then 512/`2e-3`.

The independent validator re-derives the prompt, target, candidate panel,
contract hash, receipts, margins, loss ratios, adapter hashes, reload identity,
manifest, source commit, and interpretation. GPU execution requires separately
committed authorization. Tune and assessment remain closed. This calibration
cannot establish continual learning, self-improvement, introspection, Stage 0C,
or claims above `RemoteH100SingleCaseSubstrateCalibrationV41R22`.
