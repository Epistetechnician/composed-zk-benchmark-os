# Gemma3 FineWeb-Edu H100 V2 independent-review packet

State slice: `continual-learning-gemma3-fineweb-edu-replication-h100-v2`.

This packet requests an implementation-boundary review only. It is not a
provider authorization, spend ceiling, model authorization, execution
authorization, or result receipt.

## Exact review set

Read exactly these files and no others:

1. `docs/research/continual-learning/258-gemma3-fineweb-edu-replication-h100-v2-protocol.md`
2. `docs/research/continual-learning/259-gemma3-fineweb-edu-replication-h100-v2-review-packet.md`
3. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v2_contract.py`
4. `experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_h100_v2_contract.py`
5. `AGENTS.md`
6. `docs/research/continual-learning/260-gemma3-fineweb-edu-replication-h100-v2-implementation-manifest.json`

The implementation manifest's internal file list is the first five paths
above. The manifest itself is nevertheless part of this exact review set and
must appear in the returned reviewed-file list and digest map.

## Required review conditions

Reject if any reviewed byte is missing, changes during review, has an
undeclared dependency, permits self-signed provider evidence, accepts an
invalid provider attestation, publishes before independent validation, or
allows an extra result-root file or directory.

The reviewer must recompute every listed SHA-256 digest and the manifest's
canonical self-digest. The reviewer must not inspect external artifacts,
models, volumes, credentials, providers, network resources, or prior V1
scientific artifacts. The reviewer must not create a receipt file or run
effects.

An `ACCEPT` authorizes only the V2 contract boundary. It does not authorize a
launch, provider spend, model execution, data acquisition, assessment, or
scientific claim.

Every mutation in this phase names state slice
`continual-learning-gemma3-fineweb-edu-replication-h100-v2`.
