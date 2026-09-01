# Oak Lab H100 replication V10 independent-review packet

State slice: `oaklab-experience-learning-h100-replication-v10`.

Review status: `pending_independent_review`.

Implementation authorization: `false`.

This packet authorizes static independent review only. It authorizes no
learner, model, dataset, provider, spend, H100, energy, assessment, or
publication execution. Any change to a bound byte invalidates the packet.

## Bound files and digests

| File | SHA-256 |
| --- | --- |
| `docs/research/experience-learning/70-oaklab-h100-replication-v10-protocol.md` | `b865342a81c8428214f1ffbd0d2ebf9d295fcd84b6641a1c9b34e89be96e4539` |
| `experiments/experience_learning/oaklab_h100_v10_protocol.json` | `cc4a2f07f10dddda825d7cac7bf30c82d3d41ab6367225f80ded67650dd5cb19` |
| `experiments/experience_learning/compile_oaklab_h100_v10_protocol.py` | `02833a29a0edcfe9093dc36635977bebe6d0b22ff9bf3238f20296a7a007ceec` |
| `experiments/experience_learning/validate_oaklab_h100_v10_protocol.py` | `328b60a5ecc2d26383546dfe2a38f60d1235eb96a499f9343fc9ddaf104599be` |
| `experiments/experience_learning/tests/test_oaklab_h100_v10_protocol.py` | `3a0396e195d7e916bd97c57a1a68bacb5182aedf23f5308f22a3edb7726c1bd2` |
| `experiments/experience_learning/oaklab_h100_v10_compiled_protocol.json` | `985a48b044c325786b66c209187b6613c60d14516ea99ebe55a927dcb0cd2743` |
| `AGENTS.md` | `43b7553003e34793ac60b37411b4cbed1b1af3b3605af907fe683f29b9d57a70` |

The campaign-manifest artifact is required by the source contract and is
validated against this packet's current SHA-256; it is not duplicated here to
avoid a digest cycle.

## Required independent checks

```text
python -B -m experiments.experience_learning.compile_oaklab_h100_v10_protocol --repo-root . --output experiments/experience_learning/oaklab_h100_v10_compiled_protocol.json
python -B -m experiments.experience_learning.validate_oaklab_h100_v10_protocol
python -B -m pytest experiments/experience_learning/tests/test_oaklab_h100_v10_protocol.py -q
```

The reviewer must independently recompute the current packet and source
digests, recursively validate every nested schema, verify the dual-budgeted
segment estimand and no-current-outcome rule, generator draw order, numeric
ASTs, byte layouts, charged controller storage, raw-row statistics, lock and
assessment absence, provider/cost/stop/energy schemas, closed result root,
campaign-manifest artifact bindings, and isolation of all historical lanes.

The receipt must be canonical JSON with schema
`oaklab.h100.v10.independent-review-receipt.v1`, exact packet/source/compiled
digests, reviewer identity, a closed finding map, `effects_run: false`, a
valid independent signature, and a self-digest excluding only the signature
and receipt-digest fields. Every finding must be true for `ACCEPT`; any false
or missing finding is `REJECT` and closes V10 before implementation.

Every mutation in this phase names state slice
`oaklab-experience-learning-h100-replication-v10`.
