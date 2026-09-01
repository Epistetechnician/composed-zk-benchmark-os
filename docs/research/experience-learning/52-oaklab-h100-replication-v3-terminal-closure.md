# Oak Lab H100 replication V3 terminal closure

State slice: `oaklab-experience-learning-h100-replication-v3`.

Disposition: `ProtocolReviewRejectedNoExecution`.

The exact frozen V3 packet was independently reviewed before any learner,
dataset, model, provider, H100, paid job, energy capture, or assessment
execution. The review ran only:

`pnpm exec pytest experiments/experience_learning/tests/test_oaklab_h100_v3_protocol.py`

The command passed all five hermetic protocol tests. The packet-bound review
receipt is
`docs/research/experience-learning/50-oaklab-h100-replication-v3-independent-review.json`
with self-digest
`75998664d1b6e91ce155196efe179c3f5e34007a08efc5572190bbe1578434e8`.
The accompanying findings record is
`docs/research/experience-learning/51-oaklab-h100-replication-v3-independent-review.md`.

Only the paired estimand and carryover-control finding passed. The following
contract findings failed:

- canonical campaign-manifest validation is not byte-exact;
- provider allocation, cost, and stop receipts are not cryptographically
  verified or content-validated;
- result-root validation does not validate every allowlisted file's content
  and manifest binding;
- fit/tune and prediction-lock receipts are not validated;
- resource, joule, denominator, and non-inferiority gates are metadata rather
  than executable checks;
- execution ordering and lane isolation are declarative and fail open.

V3 is closed permanently as a historical comparator. No patch, retune,
implementation, custody, provider access, spend, H100 allocation, real-stream
run, energy receipt, assessment, SOTA claim, breakthrough claim, or publication
is authorized under this identity. Status remains `no_candidate`.

Any continuation requires a fresh protocol identity with corrected executable
contracts, a new source and artifact freeze, and a new independent review.
Astral remains a separate blocked lane and cannot supply evidence for Oak Lab.

Every mutation in this phase names state slice
`oaklab-experience-learning-h100-replication-v3`.
