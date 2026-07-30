# V36 Two-Task Stream Implementation

State slice: `astral-rgs-v36-two-task-stream-implementation`.

Status: `Implemented / HermeticValidationComplete / ModelExecutionUnauthorized`.

The one-process runner covers all 12 arm/seed/order cells with exact fixed
compute windows, stage-one and final adapter restarts, direct/paraphrase
acquisition and retention, V30 protection, loss/gradient traces, adapter
hashes, and matched-baseline advantage. Astral independently reconstructs the
fixture, schedules, decisions, metrics, gates, source locks, and artifact
census.
