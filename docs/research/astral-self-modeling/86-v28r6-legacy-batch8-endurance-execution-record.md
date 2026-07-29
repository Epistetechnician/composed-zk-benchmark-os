# V28R6 Legacy Batch-8 Endurance Execution Record

State slice:
`astral-rgs-v28r6-legacy-batch8-endurance-qualified-sealing`.

Status: `LocallyQualifiedInfrastructure / ExternalReviewNotRun /
ScientificCampaignNotRun`.

Artifact `astral-rgs-v28r6-preflight-3b707bf7d36b-r1` has canonical manifest
`sha256:3b707bf7d36ba3e0f58c82de5a261940413f37a6acdf208d70f910618cb15c32`
and canonical packet
`sha256:f5b977dca632d3767e8d4dd910bf1760c4d64d640645b55959de5be6db7ef2b9`.
The independent report file is
`sha256:d3b20eb85e061e4ed9e8e66ca9a8d55c4016aa5644436aa939d60a5b84c91a9b`.

The single-process legacy batch-8 path completed eight superblocks, 768
families, and 9,216 queries. Each block stayed within the 1,152-row
materialization cap. Peak RSS remained exactly `862470144` bytes from the first
through eighth receipt, yielding zero observed growth. Fresh-process first and
last controls completed at `872955904` and `866893824` bytes peak RSS.

Both endpoint controls matched the endurance slices on every semantic field
and raw label score; maximum absolute score drift was `0.0`. The independent
validator rederived every input and gate and returned zero errors,
`valid=true`, and `qualified=true`. A second invocation reproduced the report
byte for byte.

No persistent state, update, adapter, candidate data, assessment, or scientific
campaign ran. This is local infrastructure qualification only. Acquisition,
continual learning, self-improvement, SOTA, confirmation, external review, and
independent replication remain unvalidated.
