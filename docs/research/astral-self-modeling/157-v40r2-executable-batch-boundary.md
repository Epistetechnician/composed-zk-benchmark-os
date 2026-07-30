# V40R2 Executable Batch Boundary

State slice: `V40R2ExecutableMLXBackendIntegration`.

Status: `BatchSemanticsImplemented / ConcreteBackendIncomplete`.

Stage 1 is now explicitly current-only with four current examples. Stages 2-4
use three current examples plus one continuation selected by the locked
schedule: recent-task replay or protected replay.

Feature capture receives that same continuation, preventing telemetry from
being computed on a different batch than the gradient update. The rotating
current/protected margin probes and counterfactual acquisition, protection,
retention, and paraphrase groups are deterministic and fit-only. Current
margin uses the first current example in the exact gradient batch and adds no
forward pass; protected margin remains the only extra feature probe.

Optimizer wiring, scoring, branch evaluation, and concrete runner integration
remain incomplete. No model execution is authorized.
