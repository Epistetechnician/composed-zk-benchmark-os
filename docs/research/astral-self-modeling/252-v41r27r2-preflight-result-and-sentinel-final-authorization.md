# V41R27R2 preflight result and sentinel final authorization

State slice: `V41R27R2NumericallyStableSentinelExecutionFinal`.

Fresh corrected-contract preflight `astral-v41r27r2-preflight-r1` passed on an
H100 without adapter or optimizer construction. `cmd-h6npq` exited zero.
Provider artifact `art-twgmw` has SHA-256
`dd43f5827bba2232d1383f0cdb7768d1fe8a5e5df6a0859dc3775fa0d7c38361`.
Remote and durable local independent validation passed. Result SHA-256 is
`912b93f56b6e6ebd6bfac979787a26d97b491d70a78ec1ec2d9eabba1fe30f0a`.

Status: `AuthorizedOnce / NotYetConsumed`.

The only executable sentinel identity is
`astral-v41r27r2-sentinel-r1-final`, bound to RGS
`fb2ddcb61495f98fbb3189cefefb23fd0745903a`, Astral
`b809059cab920a08112eb3c2c7882b21c888678b`, context `ctx-3a17e0a7`
(46,107,648 bytes; SHA-256
`a640de082e32c9c007ce390094643b41e26ab3eb8c2764f7ff2232b64e00d401`),
preflight result `sha256:912b93f56b6e6ebd6bfac979787a26d97b491d70a78ec1ec2d9eabba1fe30f0a`,
and contract v2 `sha256:ddf7f95ea4bf9b109dbdb1b02b87542a2a8ea56fd694f508c0b8647bc716ed4e`.

It may execute only the frozen nine sentinel workers in order. Restart is
`never`; worker and sentinel limits are ten minutes and one hour; new spend is
capped at USD 5. First false gate stops execution. Export, independent
validation, and immediate node stop are mandatory. Optimizer construction
consumes the identity. All earlier sentinel bindings are superseded.
