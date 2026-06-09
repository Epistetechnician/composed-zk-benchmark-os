# zkML Benchmark Manifest

## Why zkML Is Narrow

zkML is a workload class, not the center of this project. The project center is generated control-flow semantics with oracles, mutation variants, backend outcomes, evidence records, and claim boundaries.

## Mixed Workload Shape

A useful zkML/control-flow case binds:

- private model output,
- public threshold or policy,
- state transition,
- witness policy,
- expected accept/reject trace,
- mutation hooks around public/private boundary and observation omission.

## Metrics

Potential metrics:

- proof time,
- verifier latency,
- proof size,
- model accuracy if provided by source workload,
- constraint count,
- memory use,
- public/private boundary result,
- negative-test result.

## Limitations

- zkML metrics do not prove semantic soundness.
- Model accuracy is not proof-system correctness.
- Heavy dependency chains should not enter the first implementation slice.
- Legacy examples may have outdated assumptions.

## Benchmark Manifest Shape

```yaml
zkml_workload:
  id: inference_gate_v0
  control_flow_machine: inference_gate
  model_artifact: pending
  public_inputs: [threshold, decision]
  private_witnesses: [score, model_input]
  expected_verdicts:
    valid: expected_accept
    boundary_mismatch: expected_reject
  metrics:
    - prover_time
    - verifier_latency
    - proof_size
    - zkml_accuracy_if_available
```

## Adapter Risks

- Treating zkML as the project center.
- Importing heavy install scripts into root validation.
- Comparing ML accuracy and proof-system evidence in one opaque score.
- Treating old legacy zkML baselines as current evidence.

## Legacy Reference Handling

zkp-gravity/zkml-benchmark is reference-only in this scaffold. It can inform historical manifest shape but should not be the initial adapter target.

