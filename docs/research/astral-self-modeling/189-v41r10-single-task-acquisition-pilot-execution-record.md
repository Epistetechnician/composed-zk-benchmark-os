# V41R10 Single-Task Acquisition Pilot Execution Record

State slice: `V41R10AcquisitionPilotExecution`.

Status: `PilotInstrumentInvalid / IdentityConsumed / QualificationUnauthorized`.

## Execution and artifact

Job `job-ivs9u` ran the immutable RGS `a01ef5360b45957f2d430e0ac01c86decf2a806b`
implementation with Astral validator `ca308c7` and context `ctx-0ccf54a2` on
one clock-locked NVIDIA H100 80GB HBM3. It used one attempt, zero restarts, and
zero preemptions. Cost was USD 0.088.

Artifact `art-8ejza` is 71,680 bytes with provider and downloaded SHA-256
`78da0e5b36759ae5d81b362fc51735f47081162b96884a3883cc3f2a71375688`.
The provider could not inline the 64,119-byte result, but retained the complete
artifact. Its internal manifest and the independent validator both passed.

## Preregistered gate

| Panel | Overall | Direct | Paraphrase | Withheld composition |
| --- | ---: | ---: | ---: | ---: |
| No update | 0.375 | 0.3125 | 0.3125 | 0.5000 |
| Context only | 1.000 | 1.0000 | 1.0000 | 1.0000 |

Protected accuracy before update was 1.000. The no-update gate required overall
accuracy in `[0.15, 0.35]` and every class at or below 0.40. Overall and
withheld composition failed. The runner therefore classified the result as
`PilotInstrumentInvalid` and executed zero optimizer steps. Tune and assessment
remained sealed.

Independent validation returned `valid: true`, no errors, claim ceiling
`RemoteH100InstrumentInvalidV41R10`, and semantic result SHA-256
`6e71d6d19fb2a2a51333724e14ccfcb9887f2e56d8c415334bd297d161a1aa08`.

## Claim boundary

The run demonstrates a functioning fail-closed novelty gate. It provides no
acquisition, persistence, retention-after-update, continual-learning,
self-improvement, introspection, or self-modeling evidence. V41R10 is consumed
and cannot be retried or patched. Qualification and assessment remain
unauthorized. A successor requires a new prospective identity and a corpus
whose frozen no-update panel passes its novelty gate.
