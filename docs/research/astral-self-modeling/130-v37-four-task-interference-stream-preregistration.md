# V37 Four-Task Interference-Stream Preregistration

Status: `Preregistered / ImplementationNotAuthorized`.

V37 is a benchmark-difficulty qualification probe. It freezes four new
eight-association tasks using the 32 V30 vocabulary values, orders `A-B-C-D`
and `D-C-B-A`, seeds `370037/370038`, and three equal-budget arms:
`no_task_replay`, `recent_replay_25`, and `reservoir_replay_25`.

All 12 cells start from the same cached Qwen checkpoint. Each executes four
32-step batch-4 stages with 96-token windows: 49,152 update tokens per cell and
589,824 total. Stage 1 is identical. Later stages use three current rows and
either one protected row, one immediately prior-task row, or one deterministic
uniform-reservoir row across all prior tasks.

Adapters are saved and restarted after every stage. Direct accuracy is measured
for every seen task after every stage; final paraphrase, full V30 protection,
loss finiteness, update parity, and reload equivalence are also locked.

The stream qualifies only if replay cells acquire the final task at `>=0.75`,
retain V30 at `>=0.95`, pass mechanical gates, and the strongest replay arm's
mean final prior-task retention lies in `[0.60, 0.90]` with at least `0.10`
advantage over no replay and some observed forgetting. Above `0.90` is
`SaturatedTooEasy`; below `0.60` is `TooHardOrUnderAcquired`.

No dynamic selector is present. Maximum claim:
`LocalFourTaskInterferenceStreamQualificationV37`. Implementation, execution,
CL-bench, assessment, confirmation, SOTA, and breakthrough claims remain
unauthorized.
