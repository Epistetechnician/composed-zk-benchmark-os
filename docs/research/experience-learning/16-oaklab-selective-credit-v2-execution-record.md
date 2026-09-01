# Oak Lab selective-credit V2 execution record

State slice: `oaklab-experience-learning-selective-credit-v2`

## Receipt

Aggregate-only receipt:

`/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-selective-credit-v2/qualification.json`

Result digest: `7b9f74cd6065d0375a8e8a70ac0a75d2b6f919d0e30815589e6105bb32c54701`.

The independent validator reports `valid`. The six-stream, five-seed result
is `no_candidate`; no stream satisfies all strict quality, paired-statistical,
and resource gates. The candidate is resource-noninferior to fixed SGD, but it
does not produce a reproducible statistically supported loss improvement.

Representative assessment means (candidate minus reference is the relevant
paired direction):

- drifting: `0.1878947676` vs `0.1878947676`, paired `p=0.6069`;
- event-camera-like: `0.0127735296` vs `0.0127614099`, `p=0.3173`;
- long-horizon: `0.2484660808` vs `0.2412037904`, `p=0.0176`;
- noisy-MNIST-like: `0.0554552985` vs `0.0555218624`, `p=0.3173`;
- nonstationary: `0.2410487448` vs `0.2328280937`, `p=0.0189`;
- sparse noisy: `0.0355084169` vs `0.0355084169`, `p=1.0`.

The receipt records batch-one accounting, fit/tune/assessment prediction-lock
digests, controls, fresh seed offsets, and `hardware_energy=not_run`.

## Decision

V2 is a second rejected selective-credit theory. It is not evidence to retune
V1 or the closed plasticity guard. The claim ceiling is
`LocalDevelopmentOakLabSelectiveCreditTemporalUtilityQualification`.

Real-stream execution remains sealed pending all of the following:

1. an independent review receipt covering the frozen protocol, estimand,
   prediction lock, custody identity, controls, and validator;
2. a privileged `powermetrics` receipt for the same sealed campaign; and
3. a materially stronger theory that passes the synthetic quality/adaptation/
   resource gate.

Astral remains isolated and the global publication gate remains `no_candidate`.
