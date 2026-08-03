# V41R26 Campaign Execution Authorization

State slice: `V41R26CampaignExecutionAuthorizationAndCostGate`.

Status: `AuthorizedOnce / NotYetConsumed`.

One frozen 48-run H100 campaign is authorized under identity
`astral-v41r26-campaign-r1`, bound to producer commit
`9c3f67c47feee807622ce2f58d6129fde78be3da`, Astral validator commit
`5ddca452b59882ca5291b23019afab74657b5d97`, context `ctx-47478ad4`,
context SHA-256
`736b464647dce50ece1461ccf1bd77215fbf8a7f6a4c525b48bdb7868bcd3119`,
the independently validated passing preflight result, and contract
`sha256:789c4cf4ad3e42fcad8d13dfe3a7e2b9053d88cb89f6f23bb990895953afdd1e`.

The operational envelope is restart `never`, ten minutes per worker, four
hours total, and no more than USD 15 in new provider spend. The run must export
the complete campaign artifact, pass the independent campaign validator, and
stop the node immediately. The first optimizer construction consumes the
identity; any scientific failure consumes it. No retry, adaptive selection,
tune, assessment, confirmation, or claim promotion is authorized.
