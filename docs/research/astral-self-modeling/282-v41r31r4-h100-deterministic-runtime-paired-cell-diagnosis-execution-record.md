# V41R31R4 H100 Deterministic-Runtime Paired Cell Diagnosis Execution Record

State slice: `V41R31R4H100DeterministicRuntimePairedCellDiagnosis`.

## Terminal result

`NoDetectedDeterministicRuntimeEffect`

The contemporaneous frozen control and deterministic-runtime intervention both
completed the exact retained V41R27 cell successfully. Both arms returned the
same preregistered scientific result:

- worker: `v41r27-panel-8-seed-412019`
- classification: `V41R27WorkerComplete`
- exit code: `0`
- pass: `true`
- protected accuracy: `1.0`
- acquisition cases passing: `4/4`
- assessment opened: `false`

## Control arm

- command: `cmd-wghfr`
- artifact: `art-xun8j`
- GMAN artifact SHA-256:
  `193ef066f667abc3fc7a69ce3d022bd7d99302e220d3234c47ac275940cda904`
- downloaded tar SHA-256:
  `193ef066f667abc3fc7a69ce3d022bd7d99302e220d3234c47ac275940cda904`
- `MANIFEST.sha256`:
  `795ab8b4737e52716ae2a626963e12e42402474865d86c4e1360f4e6611c44cc`
- `worker-adapter-state.pt`:
  `9ec89ba5ef815a207a703afe46811f51f63bba21092e06f06ff1bb57048c6d49`
- `worker-result.json`:
  `56ada88b3b83c472d5b562786b0325e67da4ca29b5843c52c6aab514c9d0842e`

## Deterministic intervention arm

- command: `cmd-zx9c8`
- artifact: `art-98r49`
- deterministic settings:
  `CUBLAS_WORKSPACE_CONFIG=:4096:8`,
  `torch.use_deterministic_algorithms(True)`,
  `torch.backends.cudnn.benchmark=False`,
  `torch.backends.cudnn.deterministic=True`
- GMAN artifact SHA-256:
  `8e9ad8d7a53c2dbecf215bb6ac021839f8bf67b5704fcadf3c06f209cc248cd8`
- downloaded tar SHA-256:
  `8e9ad8d7a53c2dbecf215bb6ac021839f8bf67b5704fcadf3c06f209cc248cd8`
- `MANIFEST.sha256`:
  `61cb7b67a2a809efd781529a7d6541ec3e1e666829b8a39469ca20ac69f1eb15`
- `worker-adapter-state.pt`:
  `9ec89ba5ef815a207a703afe46811f51f63bba21092e06f06ff1bb57048c6d49`
- `worker-result.json`:
  `f74c11a1315c8a2cfe944eafd7ab087890bfcefd0ed268062232713a37fa66b0`

Independent local validation returned for both artifacts:

```
manifest_valid=true worker_result_valid=true
```

The adapter-state hash was identical across arms. The worker-result hashes
differ, as expected for separately serialized result metadata, but neither
arm changed a preregistered terminal gate.

## Infrastructure and governance

- GMAN node:
  `astral-v41r30r1-failing-cell-replication-node-r1`
- node id: `ead26876-3726-44d3-bf72-4a18e6262792`
- node terminal state: `stopped`
- mission cost: `$0.25086`
- cost accruing: `false`
- census: unchanged at `30/48`
- qualification: unchanged at `NotAssessed`

The result supports only a negative runtime-effect finding for this one frozen
panel/seed on this H100/software environment. It does not establish the cause
of the original V41R27R19 failure, general determinism, cross-cell or
cross-GPU reproducibility, qualification, continual self-improvement,
introspection, SOTA, production readiness, or breakthrough status.

Claim ceiling:
`RemoteH100V41R31R4DeterministicRuntimePairedCellDiagnosis`.
