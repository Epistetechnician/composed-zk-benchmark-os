# V41 H100 Runtime Profile Failure Record

State slice: `V41H100PersistentAcquisitionTournament`.

Status: `ConsumedPlatformExecutionFailure / NoScientificResult`.

The corrected GiveMeNode job `job-psr8z` bound RGS commit
`0403e731a91ead32f895b3822db8bcd044424f13`, one clock-locked H100, zero
restarts, and a `$13.50` maximum. Its pinned environment built successfully,
but the worker never invoked the experiment command. Attempt 1 terminated at
`2026-07-30T23:01:37.935937Z` with `worker_lost`.

Mechanical evidence:

- zero run-log bytes;
- no result JSON;
- no output artifact;
- no model, tokenizer, logits, update, or rollback record;
- no independent validation report;
- no job spend series returned by GiveMeNode telemetry.

Earlier jobs `job-h7uu8`, `job-9gxm5`, `job-kuaz4`, and `job-cbjzc` are
retained pre-execution packaging failures. They are neither experiments nor
scientific evidence. Support ticket `tkt-mf4ym` remains open.

The runtime-profile gate did not pass or fail scientifically; it was not
measured. The preregistered `stop_after_profile_failure` rule blocks the pilot,
qualification, tune, assessment, Astral selection, and claim promotion. No
retry is authorized until the operator resolves the platform failure and a
fresh execution identity is explicitly approved.
