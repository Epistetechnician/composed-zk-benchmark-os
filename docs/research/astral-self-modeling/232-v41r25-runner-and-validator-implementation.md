# V41R25 Runner and Validator Implementation

State slice: `V41R25ModelBackedRunnerAndArtifactValidator`.

Status: `Implemented / LocallyValidated / ExecutionUnauthorized`.

The RGS runner now implements the unchanged 25% replay replication over fresh
acquisition cases 4--7 and protected rows 16--31. It fails on dirty source,
model or hardware drift, nonfinite losses, memory-ceiling violations, reload
mismatch, or incomplete output. The runner performs no work without the
explicit `--execute` flag.

`tools/astral-v41r25-disjoint-replay/validate_artifact.py` is the independent
fail-closed artifact validator. It reconstructs the frozen contract and row
bindings rather than trusting the candidate result. It verifies all result,
adapter, manifest, source, receipt, runtime, model, scoring, metric, reload, and
decision bindings.

Focused implementation and validator tests are green. This closes local
implementation readiness only. A separately committed authorization must bind
the exact RGS and Astral commits and one new execution identity before runtime.
