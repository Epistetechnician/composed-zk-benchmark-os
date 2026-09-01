# Oak Lab V6 terminal closure

State slice: `oaklab-experience-learning-constrained-update-policy-v6`

Status: `ProtocolReviewRejectedNoExecution`

Claim ceiling: `ProtocolReviewRejectedNoExecution`

Independent review: [41-oaklab-v6-independent-protocol-review.md](41-oaklab-v6-independent-protocol-review.md)

## Disposition

V6 is closed before learner implementation. The independent reviewer
recomputed all packet hashes, the freeze manifest, seven section digests, the
compiled digest, the PRNG/action vector, compiler output, independent
validator output, five hermetic tests, and `pnpm run lint:fast`. The packet was
nevertheless rejected because the frozen contract still allowed multiple
implementations.

Blocking findings were:

- controller rows omitted recurrence RHS reads and terminal-credit state;
- the one-sided statistical tail was reversed for the declared effect sign;
- energy counter encoding conflicted with pre-receipt absence;
- enum values, resource counters, and capture boundaries were not byte-exact;
- event and delayed-reward generator signs were unresolved;
- adaptation scan domain and censoring semantics were inconsistent;
- binary lock hex widths, byte order, and element encoding were incomplete.

These findings are protocol defects, not learner results. The complete-policy
estimand remains historical theory only. No V6 learner, stream runner, fit,
tune, assessment, synthetic result, real campaign, GiveMeANode/H100 workload,
energy receipt, SOTA claim, or publication candidate exists.

## Required boundary

Do not patch or retune V6. A continuation requires a new protocol identity,
fresh executable contract, fresh byte freeze, and independent review. The
plasticity guard remains permanently closed and Astral remains isolated.
GiveMeANode/H100 provisioning is not authorized by this closure. Any future
real execution requires synthetic qualification, separate execution review,
fresh custody and workload manifest, a hard USD ceiling, operator ownership,
and a privileged workload-specific energy receipt.
