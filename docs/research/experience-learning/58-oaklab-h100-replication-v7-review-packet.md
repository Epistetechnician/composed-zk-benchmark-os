# Oak Lab H100 replication V7 independent-review packet

State slice: `oaklab-experience-learning-h100-replication-v7`.

Review status: `pending_independent_review`.

Implementation authorization: `false`.

This packet authorizes only static independent review. It authorizes no learner,
model, dataset, provider, spend, H100, energy, assessment, or publication
execution. Any change to a bound byte invalidates this packet.

## Bound files and digests

| File | SHA-256 |
| --- | --- |
| `docs/research/experience-learning/57-oaklab-h100-replication-v7-protocol.md` | `132f385fb1b0cede69384b730f97077a3e200c8a77ebb516e9ce54b733a39d6e` |
| `experiments/experience_learning/oaklab_h100_v7_protocol.json` | `df3eed9e27d5f9d7e9baae443e170ff5c574fda96eca4f99c8191d43d16b93f0` |
| `experiments/experience_learning/compile_oaklab_h100_v7_protocol.py` | `f7e512fd9875899bdbde7951b03c1b536a3a7012cb967d2469c670090e1f0b57` |
| `experiments/experience_learning/validate_oaklab_h100_v7_protocol.py` | `ccb5c607c54fba9c802ec3e6599dbbf7fdbf40e62f8bc907f50e25e4bf7d4b3a` |
| `experiments/experience_learning/tests/test_oaklab_h100_v7_protocol.py` | `bf064704402b08e3d00df9848d18df9868da6444a8caa3a25832c9364ad5b9e7` |
| `experiments/experience_learning/oaklab_h100_v7_compiled_protocol.json` | `34729655e7463a90b2ae5c1a631a196534c385da4e16d5392d8c9aa3fac75b9b` |
| `AGENTS.md` | `e3a8c73ec125c4f66d8bb2cc8294ed0bf4bf57278e1f3c7e5ae6dc0c55162bf4` |

Compiled protocol self-digest:
`3f3b6f39858e7eaeb874a410d2f2be161589540d0d623cd7cc513f9d39bd8cf2`.

## Required independent checks

Run exactly:

```text
python -B -m experiments.experience_learning.compile_oaklab_h100_v7_protocol --repo-root . --output experiments/experience_learning/oaklab_h100_v7_compiled_protocol.json
python -B -m experiments.experience_learning.validate_oaklab_h100_v7_protocol
python -B -m pytest experiments/experience_learning/tests/test_oaklab_h100_v7_protocol.py -q
```

The reviewer must independently verify:

1. canonical source bytes and recursive exact nested estimand, controller state
   types/scopes/transitions/recurrences, generator schemas/draw rules/segment
   bounds, numeric AST/byte layouts, and lane isolation;
2. source, section, transcript, freeze, compiled, and self-digests;
3. provider Ed25519 signatures with shared manifest, allocation, node, public
   key, USD ceiling, exact start, bounded stop interval, and cost bindings;
4. signed protocol-review `ACCEPT`, fit/tune binding, explicit prediction lock,
   and assessment ordering;
5. closed-world result-root path and content validation;
6. counter-derived events, operations, updates, storage, latency, raw-trace
   trapezoidal joules, and energy denominator equality;
7. raw family-row derivation of paired loss, adaptation, pure-noise null,
   Holm correction, resource margins, and publication candidate status;
8. execution authorization revalidation against the current packet, source,
   compiled artifact, campaign, synthetic candidate, and zero-spend preflight;
9. explicit Phase 836, V6, plasticity-guard, Astral, and assessment-absence
   boundaries.

The receipt must be canonical JSON with schema
`oaklab.h100.v7.independent-review-receipt.v1`, packet/source/compiled
digests, reviewer identity, exact finding map, `effects_run: false`, and a
valid independent signature and self-digest. Every finding must be true for
`ACCEPT`; any false or missing finding is `REJECT` and closes V7 before
implementation.

Every mutation in this phase names state slice
`oaklab-experience-learning-h100-replication-v7`.
