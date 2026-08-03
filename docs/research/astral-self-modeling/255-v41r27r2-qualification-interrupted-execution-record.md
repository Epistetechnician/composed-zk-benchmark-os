# V41R27R2 qualification interrupted execution record

The authorized `V41R27R2Remaining39RunQualificationExecution` consumed its
one-shot identity and ended with provider command status `lost`. The fail-closed
monitor exported artifact `art-pnmfy` and stopped the H100 node. No retry was
launched.

The durable archive SHA-256 is
`93d6bedc8e9e6ae3ab9595a5f924963539a3ac8476e0c5d39da270d588ba0577`.
It contains 17 of the 39 newly requested worker bundles. Every recovered worker
manifest verifies byte-exactly, every recovered worker reports pass `true`, and
protected accuracy is `1.0` for all 17. With the immutable nine-worker sentinel,
26 of the planned 48 workers are observed passing.

The root qualification result and root manifest are absent. Twenty-two planned
workers are missing. Therefore the frozen 48-worker Wilson gate cannot be
applied and qualification remains `NotAssessed`. This is an incomplete
infrastructure-interrupted run, not a scientific rejection and not a positive
qualification result.

August usage after the node stop was `$14.37332`, an incremental `$4.45554`
above the frozen `$9.91778` baseline.

Claim ceiling:
`RemoteH100AGEMPartialQualificationInfrastructureInterruptedV41R27R2`.
No confirmation, SOTA, continual self-improvement, introspection, or independent
replication claim is authorized.
