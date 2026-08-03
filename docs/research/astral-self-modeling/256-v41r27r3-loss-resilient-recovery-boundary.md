# V41R27R3 loss-resilient recovery boundary

V41R27R3 freezes a three-way evidence partition: nine immutable sentinel
workers, seventeen byte-verified workers from provider artifact `art-pnmfy`,
and the deterministic complement of twenty-two missing workers. The recovered
archive SHA-256 is
`93d6bedc8e9e6ae3ab9595a5f924963539a3ac8476e0c5d39da270d588ba0577`.

Each missing worker must execute as a separate provider command and be exported
immediately. Any lost, killed, timed-out, or failing command stops the fresh
campaign; no retry is allowed. The finalizer and independent validator require
all 48 exact run IDs and preserve the unchanged V41R27 scientific gates.

Implementation and hermetic validation are authorized. Model execution remains
`NotAuthorized` pending a fresh immutable release, exact operational budget,
and explicit acceptance of the unresolved provider command-loss risk tracked
as `tkt-2tah9`.

The maximum possible passing claim is
`RemoteH100AGEMRecoveredQualificationV41R27R3`. This is not confirmation, SOTA,
continual self-improvement, introspection, or independent replication.
