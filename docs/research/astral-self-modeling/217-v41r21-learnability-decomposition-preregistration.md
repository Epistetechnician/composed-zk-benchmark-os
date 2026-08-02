# V41R21 Acquisition-Learnability Decomposition Preregistration

State slice: `V41R21AcquisitionLearnabilityDecomposition`.

Status: `ProspectivelyFrozen / ImplementationPending / ExecutionUnauthorized`.

V41R21 freezes four checkpoint-matched arms: no update, an exact end-to-end
oracle, two-edge acquisition without replay, and the unchanged V41R15-style
two-edge schedule with protected replay. Each update arm uses 64 steps, four
equal-weight examples per step, token-mean example loss, all 24 q/k/v/o rank-8
alpha-16 LoRA layers, AdamW `2e-4`, and clip 1.0. Checkpoint and adapter state
reset between arms. Raw target-token totals are retained without altering
semantic answers to manufacture parity.

The fail-closed interpretation order is oracle substrate, primitive relation
acquisition, end-to-end composition, protected-replay interference, then prior
optimization-specific failure. Floors are respectively `0.90` oracle,
`0.90` for each primitive, `0.70` overall two-edge, `0.60` composition, and
maximum protected drop `0.02`.

The independent validator must reconstruct the contract, arm census, row
bindings, metrics, schedule receipts, adapter hashes, reload identities, and
interpretation. GPU execution requires clean frozen commits and a separate
one-shot authorization. Tune, assessment, layer selection, adaptive weighting,
and claims above `RemoteH100AcquisitionLearnabilityDecompositionV41R21` are
forbidden.
