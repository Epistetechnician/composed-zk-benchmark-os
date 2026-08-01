# V41R8 H100 Profile Execution Record

State slice: `V41R8H100ProfileExecution`.

Status: `Consumed / RuntimeProfileIncomplete / CheckpointLayerGeometryMismatch`.

GiveMeNode job `job-s9mx4` executed the sole authorized identity against RGS
commit `d13fc6c8468f2dd3aa26a818fd468f09dc4af92e`. The real GPT-OSS-20B revision
and tokenizer loaded on one clock-locked H100, native MXFP4 remained enabled,
and base direct/protected scoring completed. Model-ready allocation was
13,780,580,864 bytes with a 16,123,409,408-byte peak.

The run stopped before optimizer construction. V41R8 preregistered complete
attention-LoRA coverage over 36 layers, but the immutable GPT-OSS-20B config
declares `num_hidden_layers: 24`. The fail-closed inventory gate therefore
reported missing layers 24 through 35 and no extra trainable state. No update,
tune, assessment, or scientific evaluation occurred.

Artifact `art-m9veu` is 10,240 bytes with SHA-256
`67015cfe96e0e72be8451bd78492bbc4aa92d82e6cde046dd7165fb9523df64d`.
The retained `failure-result.json` SHA-256 is
`fd036715b92a2a4bcab4125e4fa7b51738360d0bebbb371bc13cf09fc811d3a4`;
`INCOMPLETE` prevents promotion. Total cost was USD 0.064.

V41R8 is consumed and cannot be retried. A fresh correction must bind layer
geometry and expected adapter inventory to the pinned checkpoint config before
any separately authorized model run. This is runtime engineering evidence, not
acquisition, retention, continual-learning, Astral-selection, self-improvement,
or breakthrough evidence.

Claim ceiling: `RemoteH100RuntimeProfileIncompleteV41R8`.
