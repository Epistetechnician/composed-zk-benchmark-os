# V41R27R2 sentinel execution authorization

State slice: `V41R27R2NumericallyStableSentinelReleaseAndExecution`.

Status: `AuthorizedOnce / NotYetConsumed`.

One fresh nine-worker sentinel is authorized on
`astral-v41r3-profile-node-r1` under identity
`astral-v41r27r2-sentinel-r1`, bound to:

- RGS producer `fb2ddcb61495f98fbb3189cefefb23fd0745903a`;
- Astral validator `a436592d8fe239cb6f751213ec4cd6360121871d`;
- context `ctx-54e79c60`, 46,099,456 bytes, SHA-256
  `8271de7a7d07dce6896f0ba41ed036f1186a1a8f4ccaf4f3ecf04774c0331b3d`;
- preflight result
  `sha256:c1cfc5c19e4d88ab571e4f5b5c63c175996f5661b083c961f5f4b7406f8552bd`;
- contract v2
  `sha256:ddf7f95ea4bf9b109dbdb1b02b87542a2a8ea56fd694f508c0b8647bc716ed4e`.

The execution is limited to frozen panels 0, 7, and 15 and seeds
`412003/412007/412019`. It must run in order, stop at the first false gate, use
restart `never`, cap workers at ten minutes, cap the sentinel at one hour, and
cap new spend at USD 5. The result must be exported, independently validated,
and followed by an immediate node stop.

Optimizer construction consumes the identity. Any runtime or scientific
failure is terminal for this identity. R1 reuse, retries, adaptive changes,
tune, assessment, and the remaining 39 runs are not authorized.

Claim ceiling before execution: `AuthorizedRemoteH100AGEMSentinelV41R27R2`.
