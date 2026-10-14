# V41R31R4 Offline Differential Diagnosis Record

State slice: `V41R31R4OfflineDifferentialDiagnosis`.

## Feedback loop

The control artifact `art-xun8j` and deterministic intervention artifact
`art-98r49` were loaded from the locally custody-preserved V41R31R4 bundle.
A read-only differential comparator checked terminal results, score rows,
receipts, state hashes, runtime identity, geometry, quantization, and contract
binding.

## Findings

Both arms were identical on:

- terminal classification `V41R27WorkerComplete`;
- worker pass `true`;
- protected accuracy `1.0`;
- acquisition cases passing `4/4`;
- run identity and case ids;
- exact-before and exact-after score rows;
- protected before and after rows;
- all 256 receipt rows;
- case order;
- acquisition and protected losses;
- projection flags, dots, coefficients, norms, tolerances, and gradient norms;
- initial, post-update, reload, and adapter state hashes;
- source, runner, method, instrument, requirements, runtime, model geometry,
  quantization, and contract hashes.

The only top-level differences were:

- `elapsed_seconds`: control `142.75916672200037`, intervention
  `178.8841112839982`;
- derived `result_sha256`, which binds the elapsed-time difference.

The adapter-state SHA-256 was identical:

```
9ec89ba5ef815a207a703afe46811f51f63bba21092e06f06ff1bb57048c6d49
```

## Diagnosis

The deterministic-runtime intervention produced no detected effect on the
scientific computation or retained state for this frozen panel/seed on this
H100/software environment. The observed hash difference is serialization of
wall-clock metadata, not scientific divergence.

This rules out the hypothesis that the original V41R27R19 retained-cell
failure was caused by the tested deterministic CUDA/cuDNN runtime settings
under this exact configuration. It does not identify the original cause.

## Next hypothesis queue

1. History-dependent process state: a fresh process does not reproduce the
   original failure; prediction is that a carefully preserved pre-failure
   runtime history, not deterministic mode, changes the gate.
2. Rare stochastic or scheduling event outside the tested deterministic
   controls: prediction is that repeated unchanged fresh runs can eventually
   produce a gate failure.
3. Original worker or source-state divergence: prediction is that byte-level
   source/model/tokenizer/requirements comparison against the V41R27R19
   custody bundle reveals an identity mismatch.

These are hypotheses only. No new H100 run is authorized by this record.
A future intervention must be separately preregistered.

V41R27 remains terminal at census `30/48`, qualification `NotAssessed`.
Claim ceiling:
`OfflineV41R31R4ExactPairedBundleDifferentialDiagnosis`.
