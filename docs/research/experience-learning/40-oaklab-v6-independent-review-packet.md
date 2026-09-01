# Oak Lab V6 independent-review packet

State slice: `oaklab-experience-learning-constrained-update-policy-v6`

Review status: `pending_independent_review`

Implementation authorization: `false`

This packet binds the exact bytes that must be independently reviewed. Any
change to any listed byte invalidates this packet and requires a new freeze and
digest recomputation.

## Bound inputs

| Input | SHA-256 |
| --- | --- |
| `AGENTS.md` | `f80ac0cde545dc27ce4cbb88ce8ab1f4bed02724b2eb7b6618f4ccefd976cdc3` |
| `experiments/experience_learning/v6_protocol_spec.json` | `999793806303d3fccaa8ff157c3fcc14cb17b89d70d7e1d466ee12f8e600f788` |
| `experiments/experience_learning/v6_compiled_protocol.json` | `0fe519e537bd00d70619c913d2251541a1eae5df794b14fde189da7d01e14932` |
| `experiments/experience_learning/compile_v6_protocol.py` | `1fc84644db9e6a283afcd5c8a65a77ac623a9d82dd208c21e031380f7831b17e` |
| `experiments/experience_learning/validate_v6_protocol_compilation.py` | `e49fafcc828e7e80a55ccc8b6013ea4979415e264111ee82604f7a2f86af04c9` |
| `experiments/experience_learning/tests/test_v6_protocol_compiler.py` | `fba5f0f94380913865b5b8aab4c567521f0c8ee7d38352c7dfcf1ea2b8a86921` |

Compiled protocol digest: `abf2d178520207fb157f5d5c32ec00d618019f96ccbe1107c6e8ad26970515f4`

Freeze manifest: `experiments/experience_learning/v6_freeze_manifest.json`

Freeze manifest SHA-256: `ac6ce73891c6f8c94c4029c2b83053ce8058633ce630a3482b737e5834cd4677`

## Required independent checks

The reviewer must independently recompute every listed digest, verify the
compiled digest and all seven section digests, recompute the PRNG/action test
vector, and run the compiler tests through the module entrypoint. The review
must reject any non-unique probability, incomplete state transition, hidden or
conditional draw, ambiguous numeric operation, contradictory ablation,
incomplete adaptation boundary, missing lock/counter/control/absence binding,
or provider/assessment execution leak.

## Decision rule

`ACCEPT` is valid only when all checks pass against these exact bytes. `REJECT`
closes V6 before implementation; it does not authorize patching. A valid
`ACCEPT` authorizes only a separately recorded synthetic implementation review.
No real stream, paid compute, GiveMeANode/H100 provisioning, energy capture,
publication, or Astral execution is authorized by this packet.
