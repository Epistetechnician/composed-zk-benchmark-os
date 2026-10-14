# V29 Positive-Control Instrument Repair Implementation

State slice:
`astral-rgs-v29-positive-control-instrument-repair-implementation`.

Status: `Implemented / HermeticValidationPassed / ModelExecutionNotAuthorized`.

The implementation materializes the prospective V29 contract as an RGS
deterministic fixture and single-load MLX worker plus a separate Astral
rederivation validator. The worker scores exactly 64 public cases under each of
three formats in one process. It has no update, optimizer, adapter, candidate
corpus, or assessment path.

Four RGS tests and four independent Astral tests pass, the fixture hashes match
across repositories, and the RGS fast gate passes. The Astral validator
independently reconstructs every case, recomputes score
argmaxes and the four locked rung gates, checks model/runtime/source/process
bindings, rehashes the artifact census, and enforces the claim ceiling. It does
not load or execute the model. Execution remains unauthorized until focused
tests pass and clean implementation commits are named prospectively.
