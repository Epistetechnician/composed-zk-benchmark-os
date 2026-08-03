# V41R27 A-GEM Retention-Stability Preregistration

State slice: `V41R27ProspectiveRetentionStabilityMechanism`.

Status: `ProtocolImplemented / IndependentlyValidatedLocally / ExecutionUnauthorized`.

V41R27 responds to V41R26's seed-sensitive protected-retention failure with one
fresh mechanism: A-GEM-style projection of a conflicting acquisition gradient
against the matched protected replay gradient. The fixed 0.75/0.25 mixture,
optimizer, LoRA geometry, step count, and gates remain unchanged.

The protocol introduces 64 new registry cases, 256 new protected cases, new
labels and prompts, and seeds `412003/412007/412019`. It imports no V41R26 data
or seed. The independent Astral implementation reconstructs the instruments,
contract hash, projection algebra, seed-disjointness rule, and nine-run sentinel
boundary without importing the producer.

Only a future separately authorized nine-run sentinel may open model access.
All nine runs must pass. One failure rejects the candidate. A 9/9 result permits
authorization review for the remaining 39 runs but is not final qualification.

This protocol is motivated by [A-GEM](https://arxiv.org/abs/1812.00420) and
[Gradient Episodic Memory](https://arxiv.org/abs/1706.08840). Their published
results motivate the mechanism; they do not validate this implementation.
