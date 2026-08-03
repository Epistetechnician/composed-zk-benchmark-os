# V41R27 sentinel R1 failure and R2 numerical correction

State slice: `V41R27NineRunAGEMSentinelFailurePreservationAndNumericalCorrection`

Sentinel identity `astral-v41r27-sentinel-r1` is consumed. Its first worker,
`v41r27-panel-0-seed-412003`, passed all pre-execution checks but terminated
before adapter creation with `RuntimeError: V41R27 projection invariant` after
129.01708794099977 seconds. No later worker ran. The result classification is
`ProtectedReplayRuntimeIncomplete`, not a scientific rejection or acceptance
of A-GEM.

The durable exported archive for provider artifact `art-7qf8z` has SHA-256
`167914cb1be4c46bd92684430da3fa658d8f65b707e968f37b24126db1924f6b`.
It retains the bound preflight and failure files and contains no adapter or
terminal worker result. The H100 node was stopped. Aggregate August usage at
that boundary was 123.4 minutes and USD 7.51796.

The independent audit found that the worker used native-dtype reductions and
a fixed absolute `1e-5` residual threshold for a high-dimensional projection.
The R2 implementation preserves all scientific variables while using float64
geometry accumulation and the frozen scale-aware native-dtype roundoff bound
`64 * dtype_epsilon * max(sqrt(projected_norm_sq * protected_norm_sq), 1)`.
The validator independently reconstructs that bound from new receipt fields.

The corrected contract is v2 with SHA-256
`ddf7f95ea4bf9b109dbdb1b02b87542a2a8ea56fd694f508c0b8647bc716ed4e`.
Local protocol and validator tests pass. Runtime remains unauthorized. A retry
requires new commits, context, identity, and authorization; R1 cannot be reused.

Claim ceiling: `LocalNumericallyCorrectedAGEMProtocolV41R27R2`.
