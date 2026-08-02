# V41R22 Single-Case Substrate Calibration Execution Authorization

State slice: `V41R22SingleCaseUpdateSubstrateCalibration`.

Status: `AuthorizedOnce / NotYetConsumed`.

One H100 execution is authorized against producer commit
`5983daddefa2db6a8929155d9521fb4583af5734` and independent validator commit
`8ddfca348a4ee4e7ccf1383666eb6f6a136f4520`. The source travels only through
ready context `ctx-c4129125`, whose tar SHA-256 is
`3e90497744605441749c8ec841bc36835c467b3772f23813022987883f1a0f6f` and whose
complete Git bundle SHA-256 is
`e00d54cf27a417aafafbf21b12683bd10e1787ee8090dabad0481fb7ef881452`.

The persistent H100 node must use the pinned offline V41 runtime and cached
GPT-OSS-20B revision. All four prospectively frozen arms run once under one
detached command with restart policy `never`. Maximum new spend is `$5.00`.
The artifact must be exported, independently validated, durably retained, and
the node stopped immediately. Any runtime failure consumes the identity.

No retry, second cell, threshold change, adaptive selection, layer selection,
tune, assessment, qualification, continual-learning claim, self-improvement
claim, or claim above `RemoteH100SingleCaseSubstrateCalibrationV41R22` is
authorized.
