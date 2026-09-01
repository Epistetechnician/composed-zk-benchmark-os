# Oak Lab H100 replication V8 independent-review packet

State slice: `oaklab-experience-learning-h100-replication-v8`.

Review status: `pending_independent_review`.

Implementation authorization: `false`.

This packet authorizes only static independent review. It authorizes no learner,
model, dataset, provider, spend, H100, energy, assessment, or publication
execution. Any change to a bound byte invalidates this packet.

## Bound files and digests

| File | SHA-256 |
| --- | --- |
| `docs/research/experience-learning/61-oaklab-h100-replication-v8-protocol.md` | `ecb96869b5072db48f791e2d4f074664fb53345dd0210ed04271b0fc79faac89` |
| `experiments/experience_learning/oaklab_h100_v8_protocol.json` | `54b941f3617a2d64570e0831dd07f1bebb8665457227d3ff2ddaee620444a269` |
| `experiments/experience_learning/compile_oaklab_h100_v8_protocol.py` | `b411b4de2d7ded9d26925045ab8f8256a6a6219260ec4c953ce3eb3b4335366b` |
| `experiments/experience_learning/validate_oaklab_h100_v8_protocol.py` | `f226e27ecfa5c31d319b9afa23ccda4ed51d8a088ae0138e4e1323b5de41d8ba` |
| `experiments/experience_learning/tests/test_oaklab_h100_v8_protocol.py` | `25a65a649665cf2b2b897488a7e634ec17fb09bce7b1a32c62bb39b9241fc990` |
| `experiments/experience_learning/oaklab_h100_v8_compiled_protocol.json` | `0c699cd0d92f4710515e6363498e780be726c846e6d4c299add82e8c890c74b5` |
| `AGENTS.md` | `e3a8c73ec125c4f66d8bb2cc8294ed0bf4bf57278e1f3c7e5ae6dc0c55162bf4` |

The campaign-manifest artifact is required by the source contract and is
validated against this packet's current SHA-256 by the independent validator;
it is intentionally not duplicated in this packet's digest table to avoid a
cyclic packet/artifact binding.

## Required independent checks

Run exactly:

```text
python -B -m experiments.experience_learning.compile_oaklab_h100_v8_protocol --repo-root . --output experiments/experience_learning/oaklab_h100_v8_compiled_protocol.json
python -B -m experiments.experience_learning.validate_oaklab_h100_v8_protocol
python -B -m pytest experiments/experience_learning/tests/test_oaklab_h100_v8_protocol.py -q
```

The reviewer must independently verify canonical bytes, recursive nested
schemas, source/compiler/validator/tests/compiled/`AGENTS.md` digests, the
materialized campaign-manifest artifact, actual-manifest execution binding,
provider and lock ordering, counter-derived statistics and energy, closed
result-root validation, and explicit historical-lane isolation.

The receipt must be canonical JSON with schema
`oaklab.h100.v8.independent-review-receipt.v1`, packet/source/compiled
digests, reviewer identity, exact finding map, `effects_run: false`, and a
valid independent signature and self-digest. Every finding must be true for
`ACCEPT`; any false or missing finding is `REJECT` and closes V8 before
implementation.

Every mutation in this phase names state slice
`oaklab-experience-learning-h100-replication-v8`.
