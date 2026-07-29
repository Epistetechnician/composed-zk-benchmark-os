# V28R7 Validator Correction R2

State slice: `astral-rgs-v28r7-validator-correction-r2`.

Status: `Completed / R1FailedPreserved / R2Valid`.

The one-shot model campaign completed and sealed artifact
`astral-rgs-v28r7-pilot-8ae838f1e467-r1`. Its first independent validation
failed with 95,045 errors. Every error traces to two validator defects:

1. R1 selected the correct eight-block panel set but retained generator order.
   The runner used the frozen Gate 1 schedule: block, fact kind, then
   within-kind family position. This created 95,040 false row-binding errors,
   plus panel and bundle mismatches.
2. R1 recomputed pilot cluster metrics with `statistics.fmean/stdev`; the
   frozen gate uses explicit `sum` arithmetic. Three nonuniform arms therefore
   produced exact-serialization summary mismatches.

R2 must implement the frozen balanced order and byte-matching arithmetic, add
regression tests, verify the original R1 validator snapshot hash, and run once
against the existing artifact. It must write new `-r2` validation files and
must not modify or replace any manifest-listed byte or the failed R1 report.

R2 completed at commit `b5b4696` with `valid=true`, `errors=[]`, status
`PilotNoSignal`, and `model_execution=false`. Its canonical report hash is
`sha256:bac9c99be9afeaedc310f7c41fb98048d43dbd69431a8e7f6712c19dfa1f2292`.
