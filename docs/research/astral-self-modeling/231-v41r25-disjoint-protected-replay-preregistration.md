# V41R25 Disjoint Protected-Replay Preregistration

State slice: `V41R25DisjointProtectedReplayReplication`.

Status: `ProspectivelyFrozen / Implemented / LocallyQualified / RuntimeUnauthorized`.

V41R25 freezes an unchanged-method replication of V41R24R2. Acquisition cases
4--7 and protected rows 16--31 are identity-disjoint from V41R24R2 acquisition
cases 0--3 and protected rows 0--15. The seed, 256 optimizer steps, four
examples per panel per step, 0.75/0.25 loss allocation, LoRA geometry, optimizer,
learning rate, gradient clipping, exact scoring, convergence gates, and exact
reload requirement are unchanged. Protected accuracy must be at least 0.98.

This design intentionally does not raise protected replay to 50%. V41R24R2's
0.875 protected accuracy informed the decision to replicate, so changing the
allocation would make this another outcome-adaptive development intervention.

The RGS implementation independently checks row identity and freezes the exact
case IDs and source hashes in its contract. The model-backed runner and
artifact validator are implemented; their committed hashes must be reviewed
before one execution identity can be authorized. No runtime, tuning, assessment access, or claims
above `RemoteH100DisjointProtectedReplayDevelopmentV41R25` are authorized.

A pass would be a disjoint development replication only. It would not establish
independent replication, continual learning, autonomous self-improvement,
Stage 0C, benchmark superiority, or SOTA.
