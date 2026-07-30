# V32 Acquisition Objective Diagnosis and Optimizer Development Preregistration

State slice: `astral-rgs-v32-acquisition-objective-diagnosis`.

Status: `Diagnosed / DocsFirstPreregistered / NotRun`.

V31R2's first-eight mean loss was `0.1513671875`; its final-eight mean was
`3.096923828125`, maximum was `21.5625`, and loss first exceeded `5.0` at step
14. The worker used selected logits without an explicit float32 cast, no
gradient clipping, and learning rate `5e-4`. Protected V30 accuracy dropped
from 1.0 to 0.28125. This supports a numerical-instability and interference
diagnosis but does not isolate causality.

V32 freezes two development arms on eight new associations:
`fp32_clip_lr1e4` and `fp32_clip_lr5e5`. Both use float32 target loss, global
gradient-norm clipping at 1.0, rank 4, eight layers, batch 4, and 32 steps.
Fixed gates are direct `>=0.75`, paraphrase `>=0.625`, protected drop `<=0.05`,
finite loss, final-eight mean no greater than initial-eight mean, and maximum
loss `<=10.0`. Prefer the `1e-4` arm if both qualify.

Maximum claim: `LocalDevelopmentOptimizerQualificationV32`. Confirmation,
continual learning, self-improvement, SOTA, and breakthrough remain untested.
