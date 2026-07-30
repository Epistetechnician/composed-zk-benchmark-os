# V40 Prospective Protection-Router Preregistration

Status: `Preregistered / ImplementationNotAuthorized`.

V40 asks whether preregistered pre-update telemetry can select exactly eight
protected replay positions per later stage more effectively than fixed,
seeded-random, shuffled-telemetry, and matched nonprivileged routing.

It requires a fresh four-task corpus with 32 tokenizer-qualified targets, new
keys and seeds, and family-disjoint fit, tune, and sealed assessment
partitions. V37-V39 outcomes cannot become training data. All router weights,
features, calibration, tie-breaking, and assessment selections must be sealed
before assessment updates.

Every eligible arm has identical update compute, replay-slot count, and
storage. Controls include task-only recent, V39 fixed-quarter, random
eight-slot, nonprivileged router, telemetry router, and shuffled telemetry.
V38R2 half protection and a retrospective oracle are diagnostic ceilings and
cannot qualify.

The telemetry router must satisfy acquisition `>=0.75`, every protected score
`>=0.95`, retention `[0.60,0.90]`, paraphrase `>=0.70`, matched retention loss
`<=0.10`, calibration degradation `<=0.02`, and at least `0.05` constrained-
regret advantage over every eligible control with a clustered-bootstrap 95%
lower bound above zero. Shuffled telemetry must close the positive gate.

Maximum claim: `LocalProspectiveProtectionRoutingDevelopmentV40`.
Implementation, corpus construction, model execution, assessment access,
Stage 0C promotion, confirmation, CL-bench, SOTA, and breakthrough claims are
not authorized.
