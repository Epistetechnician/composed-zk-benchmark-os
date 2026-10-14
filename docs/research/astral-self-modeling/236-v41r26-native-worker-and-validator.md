# V41R26 Native Worker and Validator

State slice: `V41R26NativeSingleRunWorkerAndReceiptValidation`.

Status: `Implemented / LocallyValidated / ExecutionUnauthorized`.

The RGS worker consumes one of the 48 frozen panel-seed identities, enforces the
panel preflight, creates fresh adapter and optimizer state, executes the
unchanged 75/25 update, performs exact reload, and emits a manifest-bound worker
artifact. It defaults to no execution without `--execute`.

The independent Astral validator reconstructs the contract, run cross-product,
acquisition and protected rows, optimizer schedule, loss weights, scoring,
preflight, decisions, source hashes, adapter hash, reload state, and manifest.
Missing or mutated artifacts fail closed.

This closes single-worker implementation readiness only. Campaign orchestration,
GPU execution, and claims above `LocalMultiPanelReplayWorkerV41R26` remain
unauthorized.
