# Oak Lab publication gate V1

State slice: `oaklab-experience-learning-benchmark-v2`

The global gate combines the four independently validated plasticity-guard
assessment receipts and refuses publication unless all requirements pass:

1. at least two distinct stream families have stream-level strict-gate
   candidates (lower loss, paired `p <= 0.05`, non-inferior resources, and
   preregistered power target);
2. a measured hardware-energy receipt is present; and
3. every input receipt is digest-valid and bound to the sealed plan.

The current gate receipt is stored read-only at:

`/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-publication-gate-v1-r3/publication_gate.json`

Receipt digest:

`a2d3cd830bfcc336c57e825771c15f9387fd6feebac913f32979291ea677d5ba`

Independent validation passed. The gate status is `no_candidate`: zero stream
receipts qualify and no measured joule receipt exists. The claim ceiling stays
`LocalDevelopmentOakLabExperienceLearningBenchmarkV2`. The gate is a stop
condition, not a prompt to retune the failed assessment.
