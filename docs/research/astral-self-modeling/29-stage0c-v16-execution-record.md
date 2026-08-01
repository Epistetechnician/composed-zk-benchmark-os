# Stage 0C V16 Execution Record

State slice: `astral-stage0c-structured-effect-explainer-v16`.

Execution: `StructuredDevelopmentNoCandidate`. Confirmation:
`NotAuthorized`. Stage 1: `BlockedByStage0C`.

Two pre-assessment implementation failures occurred and are retained:

1. the first invocation lacked a command-line entry point and executed no
   training or data generation;
2. the second invocation qualified actors and generated fit effects in memory
   but failed before serialization because tuple keys were not JSON-compatible.

No assessment telemetry, prediction, lock, or effect existed in either failed
attempt. The serialization boundary and regression tests were corrected before
the final run. The final repository-external bundle independently validates.

| Method | Zero MSE | Patch MSE |
|---|---:|---:|
| Own structured telemetry | 19.3753 | 14.4225 |
| Own structured activation | 19.8291 | 14.5529 |
| Pooled telemetry | 20.4258 | 15.7580 |
| Own text/input-output | 29.8134 | 31.2416 |
| Own shuffled telemetry | 32.8741 | 34.1042 |
| Own constant | 63.5759 | 75.4541 |
| Global constant | 67.8490 | 82.1590 |
| Other-actor telemetry | 7052.5397 | 6863.8554 |

Own telemetry beat own activation in all eight actor/operator cells, but only by
`0.05%` to `3.82%`, below the preregistered `5%` practical margin. Joint
rank-four prediction removed V15's directional reversals but did not establish
material value beyond activation summaries. No candidate advances.

Manifest SHA-256:
`79137c9fc857f008e4668273a26422a65e53fc7f4df62dde95a6ee08b01f9ab5`.

This closes the structured linear explainer lane for the tiny Boolean actor.
Further work must change the scientific system—such as a trained nonlinear
explainer on a richer language-model target—not search ranks, penalties, or
thresholds in this exposed setup.
