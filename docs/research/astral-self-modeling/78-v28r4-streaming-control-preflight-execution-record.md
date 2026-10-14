# V28R4 Streaming-Control Preflight Execution Record

State slice:
`astral-rgs-v28r4-streaming-control-preflight-negative-sealing`.

Status: `ValidNegative / StreamingBatch8Exact / Batch64MetalOOM / QualifiedFalse`.

The content-addressed artifact is
`astral-rgs-v28r4-preflight-ef386f74732e-r1`, with manifest
`sha256:ef386f74732edb29073cb93ae2fbbed30c0ff2fb38f21426573e87e06b2c5523`
and packet
`sha256:86ea271e4af8ee2d236f2f891eafce6a3495a58ffd1c7aba22d61fb2630f7ad5`.

Monolithic and streaming batch-8 evaluations completed all 1,152 queries with
identical semantic output and zero label-score drift. The streaming path
materialized 1,152 query/token rows and reported 858,128,384 bytes peak RSS.
The batch-64 streaming process exited `-6` with Metal out-of-memory and wrote
no result.

The initial validator correctly saw the missing batch-64 result but conflated a
manifest-bound failed child with artifact corruption. Correction commit
`82c356655b5332a06f10735b386365bee08f8709` revalidated the existing bytes
without inference. The corrected report file is
`sha256:baab7ad147e5b90d1d5fe9a65e6b55f76d87c77066f80c20210ac0d9e0aec84a`,
with zero errors, `valid=true`, and `qualified=false`.

No persistent cell, update, adapter, candidate data, assessment, or scientific
campaign ran. The only positive finding is exact batch-8 infrastructure parity;
the frozen V28R4 qualification gate failed.
