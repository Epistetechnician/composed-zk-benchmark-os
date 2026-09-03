# Gemma3 FineWeb-Edu H100 V3 independent-review packet

State slice: continual-learning-gemma3-fineweb-edu-replication-h100-v3.

This packet requests a closed-world review of the V3 execution boundary. It
is not itself a provider quote, launch manifest, spend action, model load,
data acquisition, or experiment result.

## Exact review allowlist

Read exactly these files, in this order, and no other path:

1. `docs/research/continual-learning/261-gemma3-fineweb-edu-replication-h100-v3-protocol.md`
2. `docs/research/continual-learning/262-gemma3-fineweb-edu-replication-h100-v3-review-packet.md`
3. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v3_preflight.py`
4. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v3.py`
5. `experiments/continual_learning/validate_gemma3_fineweb_edu_replication_h100_v3.py`
6. `experiments/continual_learning/pack_gemma3_fineweb_edu_replication_h100_v3.py`
7. `experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_h100_v3_preflight.py`
8. `experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_h100_v3.py`
9. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v3_provider/Dockerfile`
10. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v3_provider/requirements.lock`
11. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v3_provider/runtime-lock.json`
12. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v3_provider/run_h100_v3.sh`
13. `AGENTS.md`
14. `docs/research/continual-learning/263-gemma3-fineweb-edu-replication-h100-v3-implementation-manifest.json`

The implementation manifest lists the first 13 files and is itself the
fourteenth reviewed file. It must have an exact canonical self-digest.

## Required rejection conditions

Reject if any allowlisted byte is missing or changes during review, if any
runtime dependency is undeclared, if provider evidence can be self-signed or
an invalid attestation can pass, if the launch or result validator accepts
wrong state/manifest/model/data/runtime bindings, if a result is published
before independent validation, if a result root admits symlinks, directories,
extra files, or changed bytes, if the image does not install the reviewed
locked dependencies at build time, if the V3 fit/assessment interval is not
disjoint from all listed exclusions, or if the fixed recurrence, controls,
frozen-weight, bootstrap, network, and USD 100.00 budget boundaries are
fail-open.

The reviewer must recompute all fourteen file SHA-256 values and the
implementation manifest's canonical self-digest. The reviewer must not inspect
external models, datasets, volumes, credentials, provider accounts, network
resources, V1/V2 scientific artifacts, or any path outside this allowlist. The
reviewer must not edit, build, install, delegate, create a receipt file, load a
model, acquire data, contact GiveMeANode, or run effects.

## Required response

Return exactly one canonical JSON object with schema
`gemma3-fineweb-edu-replication-h100-v3-independent-review`, state slice,
reviewer identity, UTC timestamp, the ordered reviewed-file list, a digest map,
protocol/packet/implementation-manifest digests, exactly seven boolean
findings named `custody_and_fresh_disjoint_cohort`,
`provider_shape_and_hard_budget_gate`, `runtime_and_model_freeze`,
`qualification_and_network_boundary`,
`locked_recurrence_controls_and_uncertainty`,
`independent_validator_and_publication_order`, and
`v1_v2_identity_preserved_without_scientific_reuse`, `effects_run: false`,
and a canonical response self-digest. `ACCEPT` is valid only when every
finding is true and every digest matches the frozen bytes. Silence, prose,
malformed JSON, or a missing self-digest is not acceptance.

An `ACCEPT` authorizes only the reviewed V3 execution boundary. It does not
authorize provider spend until the exact quote, image digest, launch manifest,
and no-spend preflight independently pass.

Every mutation in this phase names state slice
`continual-learning-gemma3-fineweb-edu-replication-h100-v3`.
