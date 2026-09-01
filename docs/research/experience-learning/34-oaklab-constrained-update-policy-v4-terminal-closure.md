# Oak Lab constrained update policy V4 terminal closure

State slice: `oaklab-experience-learning-constrained-update-policy-v4`

Disposition: `NoCandidate`

Claim ceiling: `ProtocolReviewRejectedNoExecution`

Implementation: `not_run`

Fit: `not_run`

Tune: `not_run`

Assessment: `not_run`

Real execution: `not_run`

Privileged energy measurement: `not_run`

Astral: `isolated_not_run`

## Terminal decision

V4 is closed before implementation. It proposed a materially new policy-level
estimand in which the complete locked update-policy trajectory, including all
carryover, would be compared directly with fixed batch-one SGD. The independent
review found that the high-level estimand is defensible but rejected the exact
protocol because its bytes did not define one unique executable experiment.

The frozen stop rule makes a rejected review terminal. The V4 protocol may not
be corrected, retuned, renamed, implemented, or executed in place. No learner,
generator, validator, fit receipt, tune lock, assessment panel, real campaign,
energy trace, or publication candidate was created.

## Frozen evidence identity

- machine protocol:
  `60a514f81224927d195bbef9bf8bb533d4636c147fe462eebc4da6b916fbe805`;
- human protocol:
  `f8cdeaadf5b9f6cfb54adce00bab9e4d2e721b3a41a0a535ac2ac09237fa908b`;
- review packet:
  `09d98cf593b94d1fe38c88160b93f97803b2959fc644a8738175efc64f3bff40`;
- canonical independent-review receipt:
  `0e0adfdb7323865b4b2d9d6a393091d5877257253c2dcdf335ea7385e57aee9c`.

All six dispatched identities matched before review. During review,
`AGENTS.md` changed through unrelated concurrent work from the dispatched
digest
`6d059ab6f5b377679bf09f5577d15b0d703a6d1667757a1fc4788c145399e52d`.
That drift independently prevents affirmative authorization and does not
weaken the negative review. The concurrent work was preserved.

## Blocking findings

1. Hash and PRNG fields do not define one byte transcript for domain tags,
   raw-versus-hex values, protocol/cohort identifiers, and initialization.
2. The online state machine does not uniquely order current action selection,
   previous-transition controller updates, dual updates, model updates, and
   pending transition state.
3. Fit/tune stream rosters and generator draw, collision, forced-feature, and
   source-ID rules remain incomplete.
4. Fit storage omits pending transition bytes, and operation accounting lacks
   closed numeric formulas.
5. `matched_random` is assessment-only while the tune gate requires it; control
   execution semantics are also incomplete.
6. Mechanism comparisons lack exact paired transforms, raw tests, Holm families,
   tie ordering, and reward-shift rejection predicates.
7. Adaptation recovery for a first shift can cross a later shift, and the
   arm-specific baseline and interrupted censoring rules are not fixed.
8. Lock and validator schemas cannot independently resolve those ambiguities.

## Consequences

V4 supplies a better research direction but no experimental evidence. The
useful surviving idea is the complete-policy paired estimand: compare isolated,
zero-initialized candidate and fixed-SGD trajectories on identical ordered
streams, treating carryover as part of the intervention. That idea can inform
a successor only after every transition, byte, generator, resource, statistic,
control, and lock schema is compiled into a new immutable protocol identity.

The permanent plasticity-guard closure remains unchanged. V1-V3 and V4 are
historical negative records. The earlier V2 energy receipt cannot certify a
successor. Astral remains isolated. A successor is not authorized by this
closure and must obtain a fresh independent review before implementation.
