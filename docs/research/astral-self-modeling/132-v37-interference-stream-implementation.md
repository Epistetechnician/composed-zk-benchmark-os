# V37 Interference-Stream Implementation

Status: `ImplementedAndHermeticallyTested / ExecutionNotAuthorized`.

V37 now has an additive four-task fixture, frozen replay schedulers,
one-process offline MLX worker, tokenizer preflight, stage-wise restart
evaluation, exclusive external-artifact coordinator, source locks, focused
tests, and an independent Astral validator.

The implementation contains no dynamic selector and preserves the
preregistered useful-difficulty band. No model-backed V37 result exists until
a separately committed one-shot execution authorization binds both clean
implementations.
