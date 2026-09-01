# Evidence-conditioned multiscale plasticity v1 execution record

Date: 2026-08-28.

State slice: `astral-evidence-conditioned-multiscale-plasticity-v1`.

Status: `ContractMechanicsValidated / ScientificExecutionNotAuthorized`.

Claim ceiling: `LocalDevelopmentControlPlaneMechanicsOnly`.

## Scope

This run exercised a pure Python fixture controller. It did not load a model,
train or update weights, acquire a corpus, contact a provider, generate or
verify a ZK proof, verify a PQC signature, mutate the accepted Evidence Ledger,
or produce Astral scientific evidence.

The receipt interface is explicitly
`deterministic-contract-fixture-not-zk-or-pqc`. The fixture taxonomy is a
measurable control input, not privileged epistemic or ontological knowledge.

## Verification

The isolated suite passed six tests. Repository focused verification passed:

```text
341 passed, 41 subtests passed
```

The Python source parser passed with 500 sources. The CLI report was validated
after JSON round-trip and produced result digest:

```text
764ecf277261728e9900163a7af6be248b08c5ea846aebc7ee90f1b48c06df02
```

The four fixed fixture modes produced:

| Mode | Committed | Quarantined |
|---|---:|---:|
| `fixed_baseline` | 12 | 0 |
| `adaptive_gate` | 9 | 3 |
| `wave_only` | 12 | 0 |
| `adaptive_wave` | 9 | 3 |

The three quarantined shards are the deliberately contested fixture class.
These counts validate routing behavior only; they do not measure neural
learning or establish that adaptive gating is beneficial.

## Validated mechanics

- shard payload and receipt identity are digest-bound;
- high- and low-frequency control components remain within configured bounds;
- high-risk shards require computation receipts;
- shadow evaluation precedes commitment;
- repeatability and held-out-gain failures quarantine updates;
- rollback removes the committed effect and increments state version;
- aggregate results carry an independent digest and an explicit nonclaim set.

## Next gate

No model-bearing execution follows automatically. A separately authorized
scientific protocol must freeze an exact synthetic or small-transformer task,
equal-compute fixed/adaptive/wave arms, fresh disjoint splits, taxonomy noise
controls, one primary held-out adaptation endpoint, forgetting/calibration/
rollback/compute guards, prediction locking, and independent validation. Real
ZK/PQC integrations require separately verified backend receipts before any
cryptographic claim.
