# V28R6 Legacy Batch-8 Endurance Preregistration

State slice:
`astral-rgs-v28r6-legacy-batch8-endurance-preregistration`.

Status: `DocsFirstPreregistered / ImplementationNotAuthorized / NotRun`.

V28R4 qualified exact legacy batch-8 scoring for one 96-family superblock.
V28R5's optimized scorer completed at batch 64 but failed the frozen raw-score
tolerance. V28R6 therefore retains the numerically qualified legacy batch-8
path and tests long-horizon process stability without opening scientific data.

The fixture is derived from SHA-256 digest
`083528789badf5a959acbb0aa4eefc0fb747af0c1eb48ba516e2779a468065a4` of
the public label `astral-v28r6-legacy-batch8-endurance-v1`. It contains 192
families per fact kind, 768 families, eight ordered 96-family superblocks, and
9,216 queries. It is non-candidate and permanently excluded from future
qualification or assessment evidence.

Exactly three batch-8 legacy-scorer processes are permitted: one model load
that evaluates all eight superblocks sequentially, and two fresh-process
controls that independently evaluate the first and last superblocks. The
endurance path must synchronize, clear the MLX cache, release block references,
and collect garbage between blocks without changing any model or scoring
semantics.

Qualification requires all processes to complete, exact census and eight block
receipts, maximum 1,152 materialized queries/token rows, endpoint semantic
identity, endpoint raw-label-score drift at most `1e-5`, frozen identities, no
child above 8 GiB RSS, no more than 512 MiB increase from the first to final
endurance `ru_maxrss` receipt, zero persistent activity, and independent
validation with zero errors.

The maximum claim after a pass is
`LocalLegacyBatch8LongHorizonInfrastructureQualificationV28R6`. It is not
acquisition, retention, continual-learning, self-improvement, SOTA,
confirmation, or independent-replication evidence.
