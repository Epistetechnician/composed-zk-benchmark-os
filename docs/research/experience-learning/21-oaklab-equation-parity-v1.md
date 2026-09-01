# Oak Lab IDBD/TIDBD equation parity V1

State slice: `oaklab-experience-learning-equation-parity-v1`.

The independent oracle implements the published IDBD pseudocode from Sutton's
AAAI paper and TIDBD Algorithm 1 from Kearney et al. The deployed learner adds
the explicit numerical beta bounds `[-8, 1]`; the papers describe such bounds
as stabilization rather than core algorithm terms. Both the unbounded core and
the bounded deployment variant are compared over deterministic 64-step traces.

Receipt:
`/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-equation-parity-v1/equation_parity_v1.json`
with digest
`04db9940e4cd1dc749abc21f3c68012d4afe993be00933bf1db8e7603efffd85`.
Independent validation is `VALID`; both cases stayed away from the beta
bounds and had maximum absolute state error below `5e-19`.

Primary sources: [IDBD](https://cdn.aaai.org/AAAI/1992/AAAI92-027.pdf) and
[TIDBD](https://arxiv.org/abs/1804.03334). This validates equation fidelity;
it does not validate scientific superiority or real-stream performance.
