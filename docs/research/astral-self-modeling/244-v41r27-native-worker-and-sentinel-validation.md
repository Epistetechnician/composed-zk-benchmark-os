# V41R27 Native Worker and Sentinel Validation

State slice: `V41R27NativeWorkerPreflightAndSentinelCoordinator`.

Status: `Implemented / IndependentlyValidatedLocally / ExecutionUnauthorized`.

The producer now contains a real H100 worker implementing tensor-level A-GEM
projection, a full-corpus base-model preflight, and a nine-run sentinel
coordinator. The worker emits 256 projection receipts and a reloadable adapter.
The coordinator stops on a false scientific gate and resumes only already
complete, passing, hash-valid workers.

Astral independently validates the worker census, fresh case bindings, every
projection condition and coefficient, nonnegative post-projection dot-product
invariant, protected replay schedule, adapter hash, exact reload, acquisition
and retention gates, committed source hashes, and nested manifests. Separate
validators cover the base-only preflight and complete nine-worker sentinel
capsule, including independently reconstructed aggregation.

Local green tests establish executable infrastructure only. No V41R27 model
result exists, and no GPU execution or spending is authorized.
