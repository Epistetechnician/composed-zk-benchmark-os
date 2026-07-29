# V28R6 Legacy Batch-8 Endurance Implementation

State slice:
`astral-rgs-v28r6-legacy-batch8-endurance-implementation`.

Status: `Implemented / 7HermeticTestsPassed / FastGatePassed /
ModelExecutionNotAuthorized`.

The RGS worker retains the V28R4 legacy scorer and batch size, evaluates the
eight blocks in one model process, and writes per-block progress receipts. Two
fresh processes independently score the first and last blocks. The coordinator
enforces the frozen identity, endpoint-parity, census, RSS, source-lock,
artifact, and no-persistence gates.

The Astral validator independently derives the seed and corpus, reconstructs
the expected family/query order and external prompts, checks every observation
and progress receipt, recomputes both endpoint comparisons and every gate, and
rehashes the complete artifact. It accepts a well-formed retained failure as
valid but never qualified.

No model run is authorized by this implementation record. The ceiling remains
an unexecuted local infrastructure instrument.

Four focused RGS tests and three independent Astral tests pass. The RGS fast
repository gate, command preflights, JSON validation, and diff checks also pass.
