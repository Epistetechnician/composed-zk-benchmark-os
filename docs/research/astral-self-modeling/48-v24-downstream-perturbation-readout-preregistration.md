# V24 Downstream Perturbation Readout Preregistration

State slice: `astral-v24-author-development-exploratory`.

Authorization: `AuthorDevelopmentAuthorized`.

Independent verification: `NotRun`.

Claim ceiling: `LocalAuthorDevelopmentPerturbationReadout`.

Status at preregistration: `AssessmentSealed`.

## Question

Under one fixed cached-Qwen intervention, can a linear readout of a downstream
residual state distinguish a hidden activation intervention from a
byte-identical no-intervention pass better than preregistered non-mechanistic
controls on unseen concepts?

This is a measurement-development question. It does not ask whether the
unmodified language model can self-report the intervention and does not test
consciousness, global introspection, or self-modeling.

## Frozen setup

- Model:
  `/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit`.
- Backend: offline MLX controlled forward.
- Intervention: normalized concept-minus-neutral residual direction.
- Injection site: transformer layer `5`.
- Injection strength: `1.0`.
- Readout site: downstream transformer layer `17`.
- Token position: final prompt token.
- Conditions: `activation`, `text`, and `none`.
- Activation and none prompts: byte-identical.
- Conditions per concept: four wrappers by three conditions.
- Readout: fit-only standardization, deterministic PCA with 16 components,
  and one-versus-rest ridge with fixed penalty `1.0`.
- No site, strength, readout layer, PCA dimension, penalty, prompt, or threshold
  search is permitted.

## Fresh concepts and splits

The concepts are disjoint from V22 and V23.

- Fit: `maple`, `oboe`, `tundra`, `signal`, `savanna`, `silver`, `estuary`,
  `linen`.
- Development replication: `gorge`, `basalt`, `iris`, `sextant`.
- Tune qualification: `alder`, `tramway`, `paprika`, `jetty`.
- Assessment: `spruce`, `bassoon`, `lagoon`, `canvas`.

Counts are `96/48/48/48` rows respectively. Assessment prompts may be
deterministically listed before locking, but assessment forwards, residuals,
logits, predictions, and metrics must not exist before both development gates
pass and the final readout is locked.

## Methods

All methods use fixed-capacity deterministic ridge outputs.

1. `telemetry`: PCA-16 downstream residual coordinates plus zero padding only
   where required by the common feature width.
2. `text`: prompt length, token count, wrapper indicators, and the visible
   external-instruction marker; activation and none are indistinguishable.
3. `output`: only the three answer-token logits, probabilities, entropy, and
   top-logit gap.
4. `anomaly`: downstream residual norm, mean, standard deviation, maximum
   absolute coordinate, and distance from the fit residual centroid.
5. `shuffled`: telemetry with a deterministic fit-label permutation.

No control receives assessment labels or paired activation/none information at
prediction time.

## Metrics

Primary metric:

`activation_none_balanced_accuracy(telemetry) - max(primary control accuracy)`.

The primary controls are `text`, `output`, and `anomaly`. Secondary metrics are
three-condition macro balanced accuracy, condition recalls, wrapper accuracy,
multiclass Brier score, and shuffled-label performance.

## Qualification

Both development-replication and tune splits must independently satisfy:

- telemetry activation-versus-none balanced accuracy at least `0.75`;
- telemetry advantage over the strongest primary control at least `0.10`;
- telemetry three-condition macro balanced accuracy at least `0.60`;
- activation and none recalls each at least `0.65`;
- every wrapper accuracy at least `0.50`;
- telemetry multiclass Brier score at most `0.55`;
- shuffled telemetry activation-versus-none balanced accuracy at most `0.60`.

Failure of either split produces
`NotRunAuthorDevelopmentPerturbationReadoutQualification`, preserves assessment
absence, and ends V24.

## Lock and assessment

After qualification, the fixed telemetry and control readouts are refit on all
three development splits. The serialized readout parameters, corpus, model
inventory, direction bytes, development features, development metrics,
integrity record, source identities, and assessment absence are hashed into a
configuration lock. The validator must accept this lock before assessment.

Assessment is run exactly once. `AuthorDevelopmentPerturbationReadoutObserved`
requires all qualification thresholds plus a concept-bootstrap 95% lower bound
above zero for telemetry's primary advantage. Otherwise the result is
`AuthorDevelopmentPerturbationReadoutNoCandidate`.

No assessment outcome changes `IndependentlyVerified`, authorizes Stage 0C,
opens Stage 1, or proves introspection. A positive result establishes only that
a construction-known intervention leaves a downstream linearly decodable
signal beyond the named controls in this local setup.

## Autoresearch stop rule

This protocol has one implementation and one execution budget. Implementation
defects may be corrected before assessment only when tests identify a mismatch
with this document. Metric-driven prompt, feature, threshold, site, strength,
or model changes are prohibited. After assessment opens, no V24 code or
protocol change may alter its disposition.
