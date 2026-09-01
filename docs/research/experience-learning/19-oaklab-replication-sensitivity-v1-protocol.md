# Oak Lab replication and declared sensitivity V1 protocol

State slice: `oaklab-experience-learning-replication-sensitivity-v1`.

This protocol expands only the surviving baseline arms. The plasticity guard
and both rejected selective-credit families are closed and excluded; no
threshold, rollback, or guard retuning is authorized.

## Locked design

- seven synthetic experience streams: sparse predictable signal, feature
  relevance shift, target drift, delayed reward, noisy-MNIST-like distractors,
  event-camera-like sparsity, and long-horizon shifts;
- ten fresh independent seed offsets `20..29`, with all ten required for a
  qualified candidate;
- twelve surviving algorithms: SGD and Adam at batch sizes 1/32/128, IDBD,
  the declared nonlinear NetworkIDBD extension, TIDBD, replay SGD, EWC SGD,
  and event-driven learning;
- three predeclared candidates per algorithm, fixed in the manifest before
  execution;
- fit/tune/assessment split inherited from the stream length; candidate
  selection minimizes mean tune prediction loss only;
- the selected candidate is rerun from a fresh learner state for assessment;
  assessment values cannot select or reorder candidates;
- one experience enters every `observe` call, with explicit replay reported
  separately and hidden accumulation forbidden;
- normal-approximation 95% confidence intervals and paired tests against
  frozen V2 `sgd_b1` are descriptive only in this synthetic lane.

The immutable campaign manifest is written beside the result in the external
artifact root. The manifest digest is
`5cb476f01670d694501f483026493e62dc26df333d06d06c5df67fe91e2127fd`.
The hyperparameter-grid digest is stored in the result and is independently
checked by the validator.

## Claim ceiling

This is replication and sensitivity evidence for baseline engineering. It is
not real-dataset evidence, hardware-energy evidence, a causal result, or a
SOTA claim. A synthetic sensitivity gate cannot authorize publication. The
separate fresh real-panel sensitivity slice is documented in [22](22-oaklab-real-sensitivity-v1-protocol.md);
the privileged raw `powermetrics` trace, exact joule integration, and existing
strict multi-family gate remain required.

The operator energy receipt must bind the exact campaign manifest, matrix,
guard, and backend digests defined in
[the privileged-energy follow-up](14-oaklab-privileged-energy-followup-v2.md).
Operation counts remain separate from measured joules.
