# V41R26 Campaign R3 Negative Execution Record

State slice: `V41R26CampaignR3VerifiedObjectRecovery`.

Status: `CandidateRejected / ValidNegativeWorkers / GovernanceFinding`.

R3 passed its source, Python 3.12/H100 runtime, 17-test, contract, and sealed
preflight gates. Two completed worker bundles were exported in provider artifact
`art-jwu7d`, artifact SHA-256
`ef095aaf471b2f3adf15015dfae7d81b8f0783804b4bbbadd94ab84064b1a993`.

Independent validation returned zero errors for both bundles. Seed 411017
passed with protected accuracy 1.0. Seed 411031 acquired all four target cases
but protected accuracy fell to 0.9375, a 0.0625 drop, and failed the locked
0.98 retention gate. The all-runs/all-panels qualification rule makes candidate
rejection irreversible; executing the remaining runs cannot qualify it.

The coordinator incorrectly relied on process exit status rather than the
worker's scientific `pass` field. It began worker 3 after the negative result.
The command was killed immediately, worker 3 emitted no terminal artifact, and
the node was stopped. This is retained as a governance finding. The producer
has been corrected to stop on the first false scientific gate.

New spend was USD 0.5883. R3 is consumed and no retry or continuation is
authorized. The result falsifies this frozen candidate; it does not validate
continual learning, autonomous self-improvement, SOTA performance,
introspection, or Stage 0C.
