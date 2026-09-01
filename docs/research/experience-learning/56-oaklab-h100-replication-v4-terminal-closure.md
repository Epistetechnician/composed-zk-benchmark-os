# Oak Lab H100 replication V4 terminal closure

State slice: `oaklab-experience-learning-h100-replication-v4`.

Disposition: `ProtocolReviewRejectedNoExecution`.

V4 was a fresh compiler-only identity following the closed V3 rejection. The
independent reviewer recomputed the packet, source, compiler, validator, test,
compiled-artifact, and `AGENTS.md` hashes; recomputed the compiled self,
section, freeze, and transcript digests; and ran the three required module
commands. The validator returned `valid: true` and the V4 suite returned
`8 passed`.

The packet-bound review nevertheless returned `REJECT`. The following gates
were not sufficient for an `ACCEPT`:

- exact nested estimand, controller, generator, and recurrence semantics were
  not fully enforced;
- provider allocation ceiling, USD currency, node cross-binding, and bounded
  interval checks were incomplete;
- fit/tune locks were not bound to an independent review `ACCEPT` or an
  enforceable prediction-before-assessment order;
- event denominators and resource values were not derived from counter
  evidence, and per-family quality, adaptation, null, custody, energy, and
  statistical gates remained caller-supplied booleans;
- execution authorization did not re-run full source/compiled validation or
  bind the review to the packet digest;
- plasticity-guard historical isolation was not checked by the V4 validator.

The canonical independent review receipt is
`docs/research/experience-learning/55-oaklab-h100-replication-v4-independent-review.json`
with self-digest
`295aa77a9618c800386ddf6ade42b15a99f1f35e935177dbefae0ea1ed471c39`.
The accompanying review record is
`docs/research/experience-learning/56-oaklab-h100-replication-v4-independent-review.md`.

V4 is permanently closed as a historical protocol. No patch, retune,
implementation, custody, provider access, spend, GiveMeANode allocation,
H100 job, model/data execution, energy capture, assessment, SOTA claim,
breakthrough claim, or publication is authorized under this identity. Status
remains `no_candidate`.

Any continuation requires a new protocol identity and a new independent review
after correcting the executable contract. Phase 836 and Oak Lab V6 remain
closed. Astral remains isolated and cannot provide Oak Lab evidence.

Every mutation in this phase names state slice
`oaklab-experience-learning-h100-replication-v4`.
