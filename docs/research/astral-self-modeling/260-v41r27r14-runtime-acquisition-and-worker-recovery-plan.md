# V41R27R14 runtime acquisition and worker recovery plan

## State slice

`V41R27R14ScientificRuntimeAcquisitionDesign`

Status: `FrozenDesign / ExecutionNotAuthorized`.

The operator subsequently authorized the exact plan. Fresh node
`astral-v41r27r14-recovery-node-r1` returned a locked H100 rate of
`$0.0666/min` before model access. The derived hard ceilings are 160 billed
minutes and `$10.6560`: at most 28 minutes for bootstrap, checkpoint
acquisition, hashing, and V41R27R13 reproduction, followed by exactly 22
six-minute worker budgets. Status is now
`ExecutionAuthorized / ModelUnopened`; either ceiling remains terminal.

V41R27R13 established a bounded native-MXFP4 H100 real-weight and real-logit
canary. It did not construct an adapter or optimizer, execute an update, or add
a worker to the 26-of-48 qualification census.

The next execution design uses one fresh H100 node as a loss-tolerant cache for
the frozen 41,301,470,293-byte checkpoint. Before optimizer construction, that
node must reproduce the V41R27R13 model, runtime, inventory, geometry,
quantization, finite-logit, logit-hash, and memory gates. The exact 22-worker
complement then runs sequentially as 22 separate provider commands. Every
command receives a fresh empty output directory and fresh model, adapter,
optimizer, gradient, and random state. Its artifact must be exported and
byte-hash verified before the next command starts. Failure or node loss stops
the campaign without retry.

The proposed immutable identities are:

- RGS execution commit:
  `c3b287d4227db94a43af7888d0211fb337c330fa`;
- Astral validator commit:
  `ab30120f8bc89ee078a15cdcd4e6ed0df1f31575`;
- V41R27R13 runtime artifact:
  `8b9b65bf68078159ba30e464ccd48e8f356c406b09479d5147a6fd8b26058088`.

The prior V41R27R3 authorization binds older commits and partially consumed
spend. It does not authorize this new runtime identity. A new human
authorization must bind the exact ordered complement, fresh node and locked
rate, acquisition and overall time limits, six minutes per worker, a newly
calculated spend ceiling, immediate export custody, frozen panel access,
optimizer construction, and update execution.

No finalization is allowed until all 48 exact worker bundles exist. RGS and
Astral validators must then independently pass the same content-addressed
release. Until that occurs, qualification remains `NotAssessed` and the claim
ceiling remains
`RemoteH100AGEMPartialQualificationInfrastructureInterruptedV41R27R2`.
