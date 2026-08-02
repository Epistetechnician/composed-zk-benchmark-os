# V41R23 Multi-Case Interference Isolation Preregistration

State slice: `V41R23MultiCaseInterferenceIsolation`.

Status: `ProspectivelyFrozen / LocalValidationPending / ExecutionUnauthorized`.

V41R23 compares a shared adapter with four one-case modules using balanced
V41R11 cases 0 through 3. Per-case exposure, starting checkpoint, rank-8
all-attention LoRA, AdamW `2e-4`, clip 1.0, prompt, target, and total optimizer
steps are matched. The shared schedule is fixed round robin. Modular routing is
an explicit oracle upper bound.

The primary metric is modular minus shared count of cases passing top-one,
2.0-nat margin, 0.10 convergence ratio, and exact-reload gates. A modular
candidate is kept only with four of four cases passing, an advantage of at
least two cases, and worst protected drop no greater than 0.02. Protected rows
must pass through each adapter; routing them to the base checkpoint is
forbidden.

The validator independently reconstructs cases, schedules, budgets, scored-row
bindings, receipts, gates, protected metrics, reset identities, adapter hashes,
manifest, and final interpretation. GPU execution requires a separate clean
commit authorization. Tune, assessment, nonprivileged routing claims,
continual-learning claims, and claims above
`RemoteH100FourCaseInterferenceIsolationV41R23` are forbidden.
