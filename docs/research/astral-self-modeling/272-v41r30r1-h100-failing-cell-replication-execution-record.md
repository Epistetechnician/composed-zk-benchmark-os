# V41R30R1 H100 Failing-Cell Independent Replication Execution Record

State slice: `V41R30R1H100FailingCellIndependentReplication`.

Status: `Completed / ValidExport / IndependentNonReplication`.

## Runtime

- GMAN mission: `v41r30r1-h100-failing-cell-replication`;
- node: `astral-v41r30r1-failing-cell-replication-node-r1`;
- H100, clock-locked, CUDA image `cuda-12.4`;
- exact source context restored with commit `c3b287d4227db94a43af7888d0211fb337c330fa`;
- pinned requirements installed: PyTorch `2.10.0`, Transformers `4.57.6`, PEFT `0.18.1`;
- model and tokenizer fetched at the frozen V41R27 identity;
- one worker, 256 optimizer steps, no method or threshold changes.

The first setup attempt failed before model load because the private Git remote
was unavailable. The ready source context then supplied the exact source tree
and binding. That transport repair changed no scientific variable; the second
attempt executed the preregistered worker.

## Result

The same frozen cell and seed completed normally:

```text
run_id: v41r27-panel-8-seed-412019
classification: V41R27WorkerComplete
acquisition_cases_passing: 4
protected_accuracy: 1.0
pass: true
optimizer_steps: 256
```

This is an independent non-replication of the V41R27R19 failure. It shows that
the prior `pass:false` result is not deterministic under the frozen cell/seed
identity, even though the runtime, model, tokenizer, and worker method were
held fixed. It does not identify the cause of the earlier failure.

## Artifact integrity

GMAN export artifact: `art-egny6`, 16,588,800 bytes,
SHA-256 `a4091a952bf88d9ba4b0846a1eb4650f9e485f362db32a9e963c42ce08df84ba`.

| File | SHA-256 |
| --- | --- |
| `worker-result.json` | `bc2f2a7f2249b7d4499850b0199da8a91efe3044551a708f5ed922ffc236ce76` |
| `worker-adapter-state.pt` | `77ce5d011d6f9a211f343013b67b4b2325b4a1bad3980a565ceeb4b5e3787372` |
| `MANIFEST.sha256` | `1ae10bec579f9f01005bc32996f940a0278830c5ed3b122b71fb8c94114aa030` |

The export was downloaded, unpacked, and rehashed locally; all inner hashes
matched the manifest. The node was stopped immediately after export.

## Scientific disposition

V41R27R19 remains terminal at census `30/48` with qualification `NotAssessed`.
V41R30R1 does not add workers to that census, reopen qualification, authorize
retries, or support continual self-improvement, introspection, SOTA,
production, or breakthrough claims. The bounded conclusion is:

`V41R27R19FailureNotReproducedByV41R30R1`.

Claim ceiling: `RemoteH100V41R30R1FailingCellIndependentReplication`.
