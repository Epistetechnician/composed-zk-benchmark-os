# Oak Lab H100 replication V9 independent-review packet

State slice: `oaklab-experience-learning-h100-replication-v9`.

Review status: `pending_independent_review`.

Implementation authorization: `false`.

This packet authorizes static independent review only. It authorizes no
learner, model, dataset, provider, spend, H100, energy, assessment, or
publication execution. Any change to a bound byte invalidates the packet.

## Bound files and digests

| File | SHA-256 |
| --- | --- |
| `docs/research/experience-learning/66-oaklab-h100-replication-v9-protocol.md` | `f2f609df070da51ca775f95cfa748fe22e6c92287d3bf815760e5b054d710dd5` |
| `experiments/experience_learning/oaklab_h100_v9_protocol.json` | `2808644bf27a75d52ce3c18caab35a43a132e262ef37e883d333a2cf57ab2e99` |
| `experiments/experience_learning/compile_oaklab_h100_v9_protocol.py` | `d5843c09696960c28c6b38cf0acd6c2f315d8c5f036403942d69e5b2b1402e40` |
| `experiments/experience_learning/validate_oaklab_h100_v9_protocol.py` | `1f11a48ef4a089806c1a960117db5b96d72ba770a16a87703e08a306deaf8836` |
| `experiments/experience_learning/tests/test_oaklab_h100_v9_protocol.py` | `f58eb2de3095d835a3712139fc8e4f1eb5a587b5fef7d6079f79d397d42e3bb3` |
| `experiments/experience_learning/oaklab_h100_v9_compiled_protocol.json` | `1eca19a42c0ca1d53e871dae6ca69e7070e0d3ae574106f83df6e5af3dab5a0a` |
| `AGENTS.md` | `e3a8c73ec125c4f66d8bb2cc8294ed0bf4bf57278e1f3c7e5ae6dc0c55162bf4` |

The campaign-manifest artifact is validated against the current packet by the
validator and is intentionally not duplicated here to avoid a digest cycle.

## Required independent checks

```text
python -B -m experiments.experience_learning.compile_oaklab_h100_v9_protocol --repo-root . --output experiments/experience_learning/oaklab_h100_v9_compiled_protocol.json
python -B -m experiments.experience_learning.validate_oaklab_h100_v9_protocol
python -B -m pytest experiments/experience_learning/tests/test_oaklab_h100_v9_protocol.py -q
```

The reviewer must verify recursively: the segment-bounded estimand, complete
controller transition/state table, generator draw order, numeric and byte
algebra, cost-adjusted statistics, full controller storage accounting, actual
campaign-manifest artifact, source/compiler/validator/tests/`AGENTS.md` and
compiled bindings, lock ordering, provider/cost/stop/energy schemas, result
root closure, and historical-lane isolation.

The receipt must be canonical JSON with schema
`oaklab.h100.v9.independent-review-receipt.v1`, exact packet/source/compiled
digests, reviewer identity, closed findings, `effects_run: false`, a valid
independent signature, and a self-digest computed excluding only the signature
and receipt digest fields. Any false or missing finding is `REJECT` and closes
V9 before implementation.

Every mutation in this phase names state slice
`oaklab-experience-learning-h100-replication-v9`.
