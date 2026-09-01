# Plasticity Recovery V2 Execution Authorization

State slice: `continual-learning-plasticity-recovery-v2`.

On 2026-08-29, the user authorized the next local step after V1 diagnosis:
preregister one recovery mechanism, use fresh data and sealed prediction
locking, preserve the untouched base and reversible-adapter boundary, keep
the V1 endpoint and hard guards unchanged, and rerun the exact synthetic gate.

The authorized mechanism is `protected_replay` as defined in the V2 protocol.
The prior V1 arms remain controls. This authorization permits only additive
Python source, hermetic tests, an external aggregate artifact root, and an
independent validator under the V2 state slice.

It does not permit model-bearing execution, GiveMeANode, model or corpus
downloads, Astral execution, Astral ledger mutation, ZK/PQC proof generation,
base-weight updates, adapter merges, production traffic, or reuse of V1
results as scientific inputs. If protected replay fails the fixed gate, V2
closes as `NoCandidate`.

Every mutation in this authorization record touches state slice
`continual-learning-plasticity-recovery-v2`.
