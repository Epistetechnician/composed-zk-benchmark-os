# V28R7 Single-Cell Acquisition Pilot Execution Authorization

State slice:
`astral-rgs-v28r7-single-cell-acquisition-pilot-execution-authorization`.

Status: `AuthorizedOnce / NotRun`.

One execution of the committed V28R7 coordinator is authorized after clean
source and runtime preflight. The first exclusive ledger claim consumes the
identity. A novelty failure stops before controls and updates; later failures
are retained and cannot be rerun. If novelty passes, all seven preregistered
single-cell arms must be attempted under the exact common budget.

The content-addressed artifact and independent Astral report are the terminal
outputs. This authorization does not permit qualification or assessment data,
retention/recovery, selector evaluation, confirmation, replication, threshold
changes, claim promotion, or any conclusion above
`LocalSingleSeedOrderAcquisitionPilotV28R7`.
