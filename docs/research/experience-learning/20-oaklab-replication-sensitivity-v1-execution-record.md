# Oak Lab replication and declared sensitivity V1 execution

State slice: `oaklab-experience-learning-replication-sensitivity-v1`.

## Receipt

External artifact root:
`/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-replication-sensitivity-v1`.

Result: `replication_sensitivity_v1.json`
Result digest:
`c635caa36439ad8d8df09888fa69f0e176e9d7a95c49745f70c073140e39d95d`
Manifest digest:
`5cb476f01670d694501f483026493e62dc26df333d06d06c5df67fe91e2127fd`
Independent validation: `VALID`.

The receipt contains seven streams, ten seeds (`20..29`), and twelve
surviving algorithms. It has 78 applicable algorithm/stream cells. Every
applicable cell executed with all ten tune seeds and a locked assessment
rerun; TIDBD is not applicable outside delayed reward. The controls execute
for every stream and seed. No plasticity-guard record is present.

## Observed result

The synthetic sensitivity gate is descriptive and identified IDBD as meeting
the local loss/resource rule on four stream families. This does not make IDBD
a publication candidate: the result is synthetic-only, the sensitivity grid
is not a real-panel assessment, and no privileged joule receipt is bound.

Publication status is explicitly `no_candidate`. The real-panel baseline
matrix remains the prior fixed-configuration evidence; real-panel sensitivity
is a separate required slice. No guard retune or selective-credit reopening
occurred.

The selected candidate was at the lower edge of every numeric grid for every
algorithm family (for example, SGD `0.01`, Adam `0.003`, IDBD meta-step
`0.003`, NetworkIDBD meta-step `0.001`, replay capacity `32`, EWC lambda
`0.5`, and event threshold `0.25`). This is a boundary-saturation warning,
not evidence of an optimum. A future sensitivity slice must declare a wider
range before execution; it may not widen or retune this receipt.

## Reproduction and validation

```sh
PYTHONDONTWRITEBYTECODE=1 python -m experiments.experience_learning.run_replication_sensitivity_v1 \
  --output /Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-replication-sensitivity-v1/replication_sensitivity_v1.json
PYTHONDONTWRITEBYTECODE=1 python -m experiments.experience_learning.validate_replication_sensitivity_v1 \
  /Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-replication-sensitivity-v1/replication_sensitivity_v1.json
PYTHONDONTWRITEBYTECODE=1 python -m experiments.experience_learning.replay_replication_sensitivity_v1 \
  /Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-replication-sensitivity-v1/replication_sensitivity_v1.json
```

The replay command is deterministic but is not a substitute for independent
review. The next external action is an operator-run privileged
`powermetrics` capture and digest-bound joule receipt; this host cannot grant
the required superuser entitlement.
