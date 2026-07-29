# V28R5 Last-Token Projection Preflight Execution Record

State slice:
`astral-rgs-v28r5-last-token-projection-preflight-negative-sealing`.

Status: `ValidNegative / MemoryBlockerRemoved / RawScoreParityFailed`.

Artifact `astral-rgs-v28r5-preflight-07fd6d885124-r1` has manifest
`sha256:07fd6d885124e715611a25b5ba4d1931f86f8764c03e4b1b9aeca1b360fce126`
and packet
`sha256:e8c74b3e7e7bbd3a705ea72bed6c6a54ef076e619cc8d0aae66ee4e0c6d729b1`.
The independent report file is
`sha256:065622d9c9c06d7d30d3de985e1507bc90d5f9ff9dfaffaa85f0903864cf91f5`.

Optimized batch 8 and batch 64 completed under 847 MiB peak child RSS. The
batch-64 worker emitted only `[batch, vocabulary]` logits, capped at 9,723,904
elements, and the prior Metal out-of-memory did not recur. Every semantic field
and predicted label matched the sealed reference.

Qualification is still false. Raw label-score drift reached
`0.01859283447265625` against the reference and `0.023340225219726562` across
optimized batch sizes, exceeding the frozen `1e-5` tolerance. A post-hoc
diagnostic found zero label flips but cannot revise the preregistered gate.

The validator reported zero errors, `valid=true`, and `qualified=false`. No
candidate, persistent update, adapter, assessment, or scientific campaign ran.
