# V41R26 Model-Backed Campaign Preflight

State slice: `V41R26ModelBackedCampaignPreflightScorer`.

Status: `Implemented / LocallyValidated / ExecutionUnauthorized`.

The RGS preflight runner loads the pinned base model once and scores all 64
acquisition and 256 protected cases before any campaign worker. It constructs
no adapter or optimizer and emits a hash-bound result and manifest. The
independent Astral validator reconstructs every row, score decision, aggregate
gate, runtime/model binding, source hash, and manifest.

This closes implementation readiness only. One preflight execution requires a
separate immutable authorization. A passing preflight authorizes no training by
itself until the campaign coordinator and campaign-level validator are also
implemented and separately authorized.
