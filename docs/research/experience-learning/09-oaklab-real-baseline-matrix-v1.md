# Oak Lab real-panel all-baseline matrix V1

State slice: `oaklab-experience-learning-benchmark-v2`

The matrix runs every declared learner ID on four 5,120-row ordered real
panels. It uses four fit cohorts, four tune cohorts, and 32 paired assessment
cohorts. The real-panel configuration is sealed at digest
`80bdc7b5ef0e13cddcae0137c5c25839844f4dcbeb0e7e15b5181b894818c8b9` because
published raw units make the synthetic default unstable. This is a fixed
configuration, not assessment tuning.

Receipt:

`/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-real-matrix-v4/real_matrix.json`

Matrix digest:
`c0cde1c6b47a785d2e54ac2a731be6a9bfe1cae53f4eb1812795ef4ef3410bce`.

The independent validator passes. SGD/Adam batch sizes 1, 32, and 128,
IDBD, NetworkIDBD, replay, EWC, plasticity guard, and event-driven learning
execute on all compatible panels. TIDBD is explicitly not applicable to
panels without a declared nonzero TD reward. IDBD diverges on the household
power panel and is retained as a divergence record rather than being dropped.

Controls include the causal running-mean noise floor and a fit-only locked
top-k feature control. The real source manifests expose no defensible causal
oracle feature indices, so the privileged oracle control is explicitly
`not_available`; synthetic streams retain the true oracle control.
