# Oak Lab H100 replication V4 independent-review packet

State slice: `oaklab-experience-learning-h100-replication-v4`.

Review status: `pending_independent_review`.

Implementation authorization: `false`.

This is a static compiler and validator review. It authorizes no learner,
model, data, provider, spend, H100, energy, assessment, or publication
execution. The reviewer must read exactly the listed bytes, recompute every
digest, run only the listed hermetic commands, and return a packet-bound
`ACCEPT` or `REJECT`. Any source, compiler, validator, test, compiled-artifact,
or `AGENTS.md` change invalidates this packet.

## Bound files

| File | SHA-256 |
| --- | --- |
| `docs/research/experience-learning/53-oaklab-h100-replication-v4-protocol.md` | `b8adf99f1f870a1a4cf17bdadc6837036e4691bb2ba8cd0d1d1ca0851c556e4a` |
| `experiments/experience_learning/oaklab_h100_v4_protocol.json` | `6b86c2e28910a58b58ee2c7df57c7227cd6bdef4ebc814f381d8e1e833f715c2` |
| `experiments/experience_learning/compile_oaklab_h100_v4_protocol.py` | `83645571b344c4e7c5d475c8d0a578b13947a8a4308579679c5d787ac5da7778` |
| `experiments/experience_learning/validate_oaklab_h100_v4_protocol.py` | `424f2ac5357e5b12440a9011ddc68c1878c8fcc435c449885d8a4705beb41fd5` |
| `experiments/experience_learning/tests/test_oaklab_h100_v4_protocol.py` | `c5237f196bfa9e96c12fa7d123bea77c1baba7a5d47e5006c94c320a7c6aeb15` |
| `experiments/experience_learning/oaklab_h100_v4_compiled_protocol.json` | `1effd508e856bb3f84d0ebbce2bd6799ddb1c7a426010bb4466cbcf2d59d9d5b` |
| `AGENTS.md` | `e3a8c73ec125c4f66d8bb2cc8294ed0bf4bf57278e1f3c7e5ae6dc0c55162bf4` |

Compiled protocol self-digest:
`762fb78fb8606cc5a0637bc790292cb5ace0550d27f80932e0d51fdd848c92af`.

## Required checks

Run exactly:

```text
python -B -m experiments.experience_learning.compile_oaklab_h100_v4_protocol --repo-root . --output experiments/experience_learning/oaklab_h100_v4_compiled_protocol.json
python -B -m experiments.experience_learning.validate_oaklab_h100_v4_protocol
python -B -m pytest experiments/experience_learning/tests/test_oaklab_h100_v4_protocol.py -q
```

The reviewer must independently verify:

1. the seven sections, exact paired estimand, PRNG transcript, unconditional
   draw order, controller transitions, and complete pending state;
2. canonical-byte self-digests and the non-circular campaign core digest;
3. pure Ed25519 verification for allocation, cost, and stop receipts,
   including cross-binding, UTC interval, and hard USD ceiling;
4. canonical fit/tune/independent lock schemas and prediction-lock ordering;
5. closed-world result-root paths, symlink/extra-path rejection, per-file
   content validation, and every manifest binding;
6. raw-trace monotonicity, finite/nonnegative watts, exact trapezoidal joule
   integration, learned-event denominator, and 5% resource non-inferiority;
7. explicit fail-closed execution authorization requiring review `ACCEPT`, a
   synthetic `candidate`, zero-spend preflight, positive hard USD ceiling, and
   one bounded job; and
8. Phase 836, V6, plasticity-guard, and Astral isolation with assessment
   materialization absent.

The reviewer must return a canonical JSON receipt containing exactly:
`schema`, `state_slice`, `review_decision`, `reviewer`, `reviewed_at_utc`,
`reviewed_files`, `reviewed_file_sha256`, `compiled_self_digest`, `test_result`,
`findings`, `effects_run`, and `receipt_sha256`. `ACCEPT` requires every
finding true, exact hashes, `test_result` equal to `8 passed`,
`effects_run: false`, and a valid self-digest. Any false finding is `REJECT`
and closes V4 before implementation. The reviewer must not invent provider,
node, model, dataset, spend, or energy evidence.

Every mutation in this phase names state slice
`oaklab-experience-learning-h100-replication-v4`.
