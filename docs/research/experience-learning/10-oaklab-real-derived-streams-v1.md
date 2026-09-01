# Oak Lab real-derived nonstationary streams V1

State slice: `oaklab-experience-learning-benchmark-v2`

Three deterministic task streams are derived from the immutable real-panel
custody root. They are not relabeled source datasets; the parent manifest and
transformation parameters are bound in a second custody manifest.

Derived root:

`/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-real-derived-v1`

Parent manifest digest: `5b88b7e680c2bbb40b7f2210afa9f2d22ed65403e6268f35d349b295d4a58a2e`.
Derived manifest digest: `239db3ac8177416806d64522b7a95227a85b7035ad5d71f259829bd1f6af4265`.

- `target_drift`: fixed target drift of 0.05 over the panel.
- `feature_relevance_shift`: after the midpoint, target receives a fixed
  `0.5 * feature[0]` contribution and task identity changes.
- `delayed_reward`: reward and target are delayed by three source rows and
  expose explicit next features for TD prediction.

The transformed matrix independently validates at
`/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-real-derived-matrix-v4/derived_matrix.json`,
digest `a45df58b9a9519466abef26babcd23dc62df35395ebb9ec0336b03a9c1a05d05`.
TIDBD diverges on the delayed raw-scale task under the sealed real
configuration; this is a stability failure, not evidence of a win.
