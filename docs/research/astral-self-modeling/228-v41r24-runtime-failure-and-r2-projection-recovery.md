# V41R24 Runtime Failure and R2 Projection Recovery

State slice: `V41R24R2ProtectedReplayProjectionRecovery`.

V41R24 failed before optimizer step zero because protected evaluation rows use
`target` while the training collator requires `answer`. Failure artifact
`art-a5d2y` has SHA-256
`dd0cc0daa93e71a0544acbc35a44c9883bd4be6fc6b4e08ee4e39004d77b742c`.
No scientific result exists and the original identity is consumed.

R2 changes only the explicit exact projection `target -> answer`. It preserves
prompt and target bytes, the frozen acquisition and protected schedules,
0.75/0.25 weights, optimizer, baseline, gates, and claim ceiling. New clean
producer, validator, context, and authorization identities are mandatory.
