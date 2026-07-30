# V33 Result and V34 Protected-Replay Preregistration

V33 status: `TargetFreeObjectiveBlocked / Consumed / Valid`.

Artifact `astral-rgs-v33-target-free-717292ceeec5-r1`, manifest
`sha256:717292ceeec596684593ca6bf483950b40d5050f586d999052057034379f0639`.
Direct and paraphrase acquisition both reached 1.0, while protected V30
accuracy fell to 0.71875. Target-free supervision repairs acquisition but does
not satisfy retention.

V34 freezes `protected_replay_25` and `protected_replay_50` under matched
32-step, batch-4, rank-4, eight-layer, clipped `1e-4` budgets. Protected rows
are deterministic V30 positive controls. Gates are direct/paraphrase at least
0.75, protected accuracy at least 0.95, finite loss, and nonincreasing
initial-to-final eight-step mean loss. Prefer 25% replay if both pass.

Maximum claim: `LocalDevelopmentProtectedReplayQualificationV34`.
