# V41R20 Panel-Balancing Execution Record

State slice: `V41R20ProspectiveGradientBalancingIntervention`.

Status: `PanelBalancedNoSignal / IndependentlyValidated / Consumed`.

The single preregistered all-layer panel-normalized candidate completed 64
steps on one clock-locked H100 and reloaded exactly. Against immutable V41R15:

| Metric | V41R15 | V41R20 | Delta |
|---|---:|---:|---:|
| persistent acquisition | 0.260417 | 0.260417 | 0.000000 |
| protected after | 0.812500 | 0.625000 | -0.187500 |

V41R20 class accuracy was direct `0.25`, paraphrase `0.3125`, and composition
`0.21875`. Acquisition overall, acquisition class, acquisition advantage, and
protected retention failed. The candidate is rejected: whole-adapter unit
normalization with frozen `0.375/0.375/0.25` shares did not improve acquisition
and worsened protection. This is evidence against that exact intervention,
not against every normalization or balancing method.

Result SHA-256 is
`sha256:9ac1565394d80ac251ca68b083186d3c300d5ea9cadcd4a332a36a2e217a681d`.
Artifact `art-a3jyr` has SHA-256
`6e720e3c9f2c011b79cf27b1d68ffc7c0e83028e6fa42c75acae6998b2a0150b`.
Independent validation returned `valid=true`, zero errors, and report SHA-256
`b4c9eff956f49a708ecfb5a84014de28a8a7902dd9a8faa0d04924ef926ca517`.
The exact CUDA-bound torch distribution-metadata compatibility rule fixes only
the known version spelling seam and does not change artifact data or gates.

Mission cost was USD 0.287, the node is stopped, and the identity is consumed.
The maximum claim is
`RemoteH100PanelBalancedAcquisitionDevelopmentV41R20`; no acquisition,
continual-learning, self-improvement, qualification, or confirmation claim is
promoted.
