# V28R4 Streaming-Control Preflight Preregistration

State slice:
`astral-rgs-v28r4-streaming-control-preflight-preregistration`.

Status: `DocsFirstPreregistered / ImplementationNotAuthorized / NotRun`.

V28R4 addresses only the observed V28R3 external-control peak-memory failure.
The candidate-neutral remedy streams one balanced 96-family superblock rather
than materializing all 6,144 families and 73,728 externalized queries at once.

The fixed public fixture uses seed bytes `00..1f`, 24 families per fact kind,
96 families and 1,152 queries. It is permanently excluded from candidate data.
The primary gate is a maximum of 1,152 materialized query/token rows, a 64-fold
reduction. Batch-8 monolithic-reference and streaming outputs must agree on
query order, prompts, token IDs, predictions, and correctness, with maximum
absolute label-score difference at most `1e-5`. Batch-64 streaming must finish
without Metal error, preserve semantic predictions, stay at or below 8 GiB
maximum RSS, and retain the frozen model/tokenizer identities.

The Astral consumer must recompute fixture identity, parity, cardinality,
resource, process, and artifact hashes without importing RGS. A pass is local
infrastructure qualification only. It does not reopen V28R3, authorize a fresh
scientific campaign, or validate acquisition or continual learning.
