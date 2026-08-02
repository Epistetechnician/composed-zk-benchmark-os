# V41R19 Persistent-Node Gradient Profile Authorization

State slice: `V41R19PersistentNodeRuntimeAndGradientProfile`.

Status: `AuthorizedOnce / NodeRunning / RuntimeInstallationPending`.

Persistent node `astral-v41r3-profile-node-r1` restored its intact disk on one
clock-locked H100. Preflight confirms driver `580.159.03`, H100 80GB HBM3,
233GB persistent free space, retained source inputs, and no installed PyTorch.

One continuous node session may install isolated Python `3.12.3` and exact V41
runtime pins, verify context `ctx-b71ccbe0` and RGS implementation commit
`0e8197fca05c42bd64ad74173385845d06c615ae`, run frozen tests, and only then
execute the V41R16 no-update raw-gradient profiler. The node must stay running
through artifact export and independent validation and then be stopped.

Optimizer construction, updates, acquisition scoring, selectors, tuning,
assessment, retries, and claims above
`RemoteH100GradientInterferenceDiagnosticV41R16` remain forbidden. Validation
is bound to Astral commit `a5aca309b75350937e801330be5d54282261207a`.
