# V40R2 Native MLX Runtime Contract Lock

State slice: `V40R2NativeMLXRuntimeContractLock`.

Status: `ProspectivelyLocked / NativeRuntimeNotImplemented`.

The final scientific ambiguity before concrete gradient wiring is now frozen:
rank-4 LoRA, scale 8, zero dropout, final eight layers, seed `400042`, AdamW
at `1e-4` with its explicit beta/epsilon/weight-decay/bias-correction values,
global norm clipping at `1.0`, batch size 4, and a fixed 96-token window.

The full fit acquisition budget remains 1,792 steps, 7,168 examples, and
688,128 update tokens. At every feature row, telemetry capture must compute
and cache the exact scheduled current-batch gradient; canonical update must
consume it without a second current-batch forward. The protected margin keeps
its separately sealed forward. Cache absence, overwrite, mismatch, or leakage
is fatal.

R3 forward budgets remain 25,728 protected-feature tokens and 3,256,320
counterfactual-evaluation tokens. This is a prospective pure-data lock. No
model load, forward pass, gradient, tune access, assessment access, or
scientific promotion occurred.
