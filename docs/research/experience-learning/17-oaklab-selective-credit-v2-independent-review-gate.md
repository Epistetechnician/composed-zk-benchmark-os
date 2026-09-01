# Oak Lab selective-credit V2 independent-review gate

State slice: `oaklab-experience-learning-selective-credit-v2`

Review status: `completed_closure_only`; execution authorization remains false.

Receipt:
`/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-selective-credit-v2/independent_review.json`

Review digest:
`d841dc82dcc3144e01fe4059ab68ac9e42780c1180eef34ce447e1cdf337f043`.

An independent reviewer must inspect the frozen protocol and aggregate-only
receipt before any real-stream or hardware execution. The review must verify:

- protocol digest `bcb3e6413adb9724a8b2aeef4ab52abedc2144665e52886c1252fad8c4b4ef1d`;
- fresh seed offsets `10..14` and fixed fit/tune/assessment boundaries;
- the sequential-loss estimand and its non-causal interpretation;
- prediction-lock snapshots for fit, tune, and assessment;
- one-experience accounting, no replay, and no hidden accumulation;
- control coverage and paired-test computation;
- receipt digest `7b9f74cd6065d0375a8e8a70ac0a75d2b6f919d0e30815589e6105bb32c54701`;
- the `no_candidate` result and claim ceiling;
- custody identity for any future real panel and the privileged energy trace;
- validator behavior under altered plan, digest, stream, and review fields.

The review decision must be recorded before a real run. A reviewer cannot turn
the synthetic `no_candidate` into a candidate by changing thresholds, seeds,
stream families, or endpoints. If a stronger theory is opened, it must use a
new state slice and a new protocol digest.
