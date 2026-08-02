# V41R13 Persistent Acquisition Pilot Preregistration

State slice: `V41R13PersistentAcquisitionPilotDesignAndExecution`.

Status: `ProspectiveDesignFrozen / IndependentValidatorImplemented / ExecutionUnauthorized`.

V41R13 freezes one protected-replay native attention-LoRA pilot against the
V41R12-qualified opaque registry. Every 64-step batch contains three acquisition
rows and one protected arithmetic replay row. The model is destroyed after
training and a fresh pinned base must restore the serialized adapter before all
context-free evaluation.

The independent validator reconstructs the instrument and contract, recomputes
all acquisition and protected metrics from raw normalized likelihoods, verifies
64 token-weighted four-microbatch receipts, exact adapter and reload hashes,
source/runtime/model identities, manifest integrity, and sealed tune and
assessment boundaries.

Passing requires at least 0.70 overall acquisition, 0.60 per query class, 0.20
advantage over the fresh no-update baseline, at most 0.02 protected drop, exact
reload, and every step. A pass reaches only
`RemoteH100PersistentAcquisitionPilotV41R13` and opens multi-cell qualification
review. It does not establish continual learning, self-improvement,
introspection, or self-modeling.
