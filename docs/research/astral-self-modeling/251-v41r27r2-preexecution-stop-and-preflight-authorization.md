# V41R27R2 pre-execution stop and corrected-contract preflight authorization

State slice: `V41R27R2CorrectedContractPreflight`.

`cmd-iyuct` exited before optimizer construction because independent validation
correctly rejected the contract-v1 preflight against contract v2. No worker,
adapter, optimizer, or scientific result exists. The sentinel identity was not
consumed. Contexts `ctx-54e79c60` and `ctx-a11201ce` are superseded. The node
was stopped after USD 0.25752 new spend; aggregate August usage was 127.27
minutes and USD 7.77548.

One fresh model-backed preflight is authorized as
`astral-v41r27r2-preflight-r1`, bound to RGS implementation
`fb2ddcb61495f98fbb3189cefefb23fd0745903a`, Astral validator
`b809059cab920a08112eb3c2c7882b21c888678b`,
context `ctx-015edb35` (45,891,072 bytes, SHA-256
`a4e9cc4dab2aa19f2b1537735568501e7c2ba7d3c97980ff9b1f96db746183fa`),
and contract v2 `sha256:ddf7f95ea4bf9b109dbdb1b02b87542a2a8ea56fd694f508c0b8647bc716ed4e`.

The run may only score the frozen preflight instruments. Adapter construction,
optimizer construction, training, tune, assessment, and worker execution are
forbidden. Restart is `never`; wall time is 20 minutes; new spend is capped at
USD 1. Export, independent validation, and immediate node stop are required.

Claim ceiling: `AuthorizedRemoteH100AGEMCorrectedContractPreflightV41R27R2`.
