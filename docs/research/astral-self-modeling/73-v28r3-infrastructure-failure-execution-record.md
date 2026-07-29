# V28R3 Infrastructure Failure Execution Record

State slice: `astral-rgs-v28r3-infrastructure-failure-sealing`.

Status: `Consumed / NoveltyPassed / PhaseBInfrastructureFailure /
IndependentlyValidated / Sealed`.

Both isolated baseline processes completed all 73,728 queries with exact
observation parity and accuracy `0.25`, so the fresh R3 corpus passed the
preregistered novelty gate. The first Phase B `context_only` control produced
no result: Metal terminated the process with code `-6` and
`kIOGPUCommandBufferCallbackErrorOutOfMemory`.

No persistent cell, optimizer step, update token, adapter, acquisition result,
or Gate 1 classification exists. This is a valid local novelty result and a
retained infrastructure failure, not continual-learning evidence. Repair and
rerun remain unauthorized.

## Immutable result

- artifact:
  `/Users/shaanp/Documents/ResearchArtifacts/astral-rgs-v28r3-abort-0b65ab1e0971-r1`;
- artifact manifest:
  `sha256:0b65ab1e0971630c753f66d2146791affbee94987bc0b2be98d111a96daab5f0`;
- abort packet:
  `sha256:8d107edf6f9213c1d04a6ec560f04cdfd1eed848ae0a2b9aef049c2a472c8de6`;
- shared observation digest:
  `sha256:5c5742e606949982472c019eaeaaaefebddc1339ac443a224a84c53e61d83209`;
- independent validation report:
  `sha256:69d10a2b4cc4759901d5434332f9f9567139bebf0722ce75b9efd18b5150200f`;
- independent verdict: `ValidatedInfrastructureFailureAfterNovelty`, zero
  validation errors;
- claim ceiling: `LocalModelBackedAcquisitionNoveltyPreflightV28R3`.

The artifact contains 34 files totaling 684,914,260 bytes. Acquisition,
continual learning, confirmation, and independent replication remain false.
