# V41R30R2 H100 Failing-Cell Second Independent Replication Execution Record

State slice: `V41R30R2H100FailingCellSecondIndependentReplication`.

## Execution

- Preregistration: `273-v41r30r2-h100-failing-cell-replication-preregistration.md`
- Mission: `v41r30r1-h100-failing-cell-replication`
- GMAN node: `astral-v41r30r1-failing-cell-replication-node-r1`
- Node id: `ead26876-3726-44d3-bf72-4a18e6262792`
- Command id: `cmd-4dtpu`
- Worker: `v41r27-panel-8-seed-412019`
- Terminal classification: `V41R27WorkerComplete`
- Exit code: `0`
- Steps: `256`
- Protected accuracy: `1.0`
- Acquisition cases passing: `4/4`
- Worker pass: `true`
- Assessment opened: `false`
- Census: unchanged at `30/48`
- Qualification: unchanged at `NotAssessed`

The run used the preserved V41R30R1 runtime disk and the same frozen source
binding:

- source commit: `c3b287d4227db94a43af7888d0211fb337c330fa`
- source archive SHA-256:
  `sha256:8b1802d97b14d83b6d6d4596589664885efd973cec1e02ac03250acf0e250645`
- source tree SHA-256:
  `sha256:1b2d3accc3d5e6cbce76b972098af78fd59d9da4f60a63ebed541a33efc901c5`

The node reached a clean terminal exit. The output directory was exported
before stopping the node.

## Artifact custody

Artifact: `art-3atde`

- GMAN artifact SHA-256:
  `aba3db7f8c065d138cca1d8927717f8ea43f4a1ba9c7be0cee75551281d0ebb0`
- Downloaded tar SHA-256:
  `aba3db7f8c065d138cca1d8927717f8ea43f4a1ba9c7be0cee75551281d0ebb0`
- Artifact directory:
  `artifacts/v41r30r2-h100-failing-cell-replication/art-3atde/`
- `MANIFEST.sha256`:
  `92aa85b54cd6504b7403e7415ff02969a42de29cdd133a8e183bf6be9fa982a2`
- `worker-adapter-state.pt`:
  `77ce5d011d6f9a211f343013b67b4b2325b4a1bad3980a565ceeb4b5e3787372`
- `worker-result.json`:
  `97973885210c8b93b94e37a12396cc398ca85e92bde1875d6bdacfa66566155e`

Independent local validation returned:

```
manifest_valid=true worker_result_valid=true
```

## Interpretation

V41R30R2 independently passes the exact retained V41R27R19 failing cell.
Together with V41R30R1, this is two fresh non-replications of the original
failure. The result supports a rare or history-dependent failure hypothesis;
it does not identify the cause and does not alter V41R27R19's terminal
negative classification.

Claim ceiling:
`RemoteH100V41R30R2FailingCellSecondIndependentReplication`.

No qualification, continual self-improvement, introspection, SOTA,
production, or breakthrough claim is supported. Any causal diagnosis or
method change requires a separately preregistered identity.
