# V41R24R2 Protected-Replay Execution Record

State slice: `V41R24R2ProtectedReplayProjectionRecovery`.

Status: `ProtectedReplayImprovedButUnqualified / IndependentlyValidated / Consumed`.

V41R24 failed before optimizer step zero because protected rows lacked the
training-boundary `answer` field. Failure artifact `art-a5d2y` is retained.
R2 changed only the exact `target -> answer` projection and completed.

All four acquisition cases passed, with target margins 15.2255–20.6654,
convergence ratios 0.001359–0.007684, and exact reload. Protected accuracy
improved from the immutable 0.1875 baseline to 0.875. The +0.6875 primary
metric is substantial, but the remaining 0.125 drop failed the frozen 0.02
retention gate. `candidate_keep` is false.

Result SHA-256 is
`sha256:e7ac404080c2c75a977c956420ff3934dc563aadd75fcae94dd4361f36e52eb5`.
Artifact `art-skem2` has SHA-256
`213831f6f2e9d549f053e555e02efe0326016371ec765257527e03b35c706d26`.
Zero-error validation report SHA-256 is
`6e7763d9e6b4ce769a066cc75f29b7bba48060ad146353e63d1e977bca62577c`.
V41R24 cost USD 0.180; R2 cost USD 0.104. The node is stopped. Fixed 25%
protected replay is effective but unqualified; continual learning remains
unvalidated.
