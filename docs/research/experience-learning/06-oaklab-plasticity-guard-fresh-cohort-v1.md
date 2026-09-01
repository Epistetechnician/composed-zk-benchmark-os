# Oak Lab plasticity-guard fresh-cohort assessment V1

State slice: `oaklab-experience-learning-benchmark-v2`

## Preregistered design

The sealed plan uses the first 256-row cohort only as a tune boundary and
seven later, disjoint 256-row cohorts as paired assessment units. Fixed SGD
batch one and the unchanged plasticity guard consume the same ordered stream
with no replay, reshuffling, or hidden accumulation. The real-stream learning
rate is fixed at `1e-5` before execution because the raw sensor and power
feature units make the synthetic V2 default unstable; no assessment result was
used to choose it.

The primary endpoint is mean prediction loss per assessment cohort. Secondary
resource gates are updates, active synaptic operations, and state bytes. The
paired test is the existing normal-approximation paired t test at alpha `0.05`.
The plan preregisters seven paired units, standardized effect `0.5`, paired SD
`1.0`, and target power `0.80`; the normal approximation reports power
`0.26254749066331373`, so the assessment is explicitly underpowered for that
target and cannot qualify a publication claim.

## Receipt

The fresh 2,048-row custody root is:

`/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-real-data-fresh-cohort-v1-r3`

Manifest digest: `ebd44b4e868cc3e987a8cdbb978a726814fd44c34c25cfafb10b7e920ddfb796`.

Aggregate-only assessment receipts are in:

`/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-plasticity-guard-assessment-v1-r3`

Independent validation passed for all four datasets. Result digests:

- `noisy_mnist`: `2f9489a4c21a6242891b1ffa03e09fa3602b5e1b42a8ff9c4f9b8c9d373a9877`
- `sensor`: `c5d58a771968ea647f93b0547068db26fa595ac6949bebc46ca2bdff846f4379`
- `long_horizon`: `ee0641ea1a6ed92f3669e3313a7f59b650f4272674a762973a092158fbd9a559`
- `event_camera`: `6973a5babbe5e25b9fb2b6f2d579ba1768777b9f90ddfa515b197c8195c62d41`

Every strict gate is `no_candidate`. Resource non-inferiority passes because
the two arms have equal update budgets; the loss and power requirements do not
jointly pass. This closes the current guard assessment as a bounded negative
result, not as evidence that the mechanism is universally ineffective.

## Next gate

Increase the preregistered cohort count or effect-size target only in a fresh
protocol before another assessment. Do not retune this result. A publication
candidate still requires a powered, independent, multi-stream quality/resource
win plus a measured hardware joule receipt.
