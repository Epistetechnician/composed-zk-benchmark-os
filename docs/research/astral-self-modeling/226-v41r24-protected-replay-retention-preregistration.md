# V41R24 Protected-Replay Retention Preregistration

State slice: `V41R24ProtectedReplayRetentionIntervention`.

Status: `ProspectivelyFrozen / LocalValidationPending / ExecutionUnauthorized`.

V41R24 preserves the complete V41R23 shared acquisition schedule and adds a
deterministic protected panel to every step. Acquisition and protected panels
each contain four examples; gradients receive frozen weights 0.75 and 0.25.
All 16 protected rows occur exactly 64 times. The immutable V41R23 result is
the comparison baseline.

Primary metric is protected-accuracy improvement over 0.1875. Keep requires
4/4 acquisition cases to pass their original target, margin, convergence, and
reload gates plus protected accuracy at least 0.98. The validator reconstructs
every schedule index, panel weight, receipt, score, adapter hash, source hash,
and decision. Tune, assessment, adaptive replay, and claims above
`RemoteH100ProtectedReplayRetentionDevelopmentV41R24` are forbidden.
