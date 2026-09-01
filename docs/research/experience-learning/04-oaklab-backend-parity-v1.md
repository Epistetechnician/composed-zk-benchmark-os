# Oak Lab backend parity V1

State slice: `oaklab-experience-learning-benchmark-v2`

## Contract

`backends.py` fixes the learner update to batch-one linear SGD and varies only
the execution representation:

- `dense_cpu`: all coordinates on a NumPy host array;
- `sparse_cpu`: declared `event_indices` only on a NumPy host array;
- `gpu`: CUDA torch tensors, executed only when a CUDA device is available;
- `event_driven`: threshold-crossing coordinates only on a host array.

An unavailable backend is emitted as `unavailable`; no CPU fallback is labeled
as GPU execution. The receipt records mean loss, updates, gradient units,
active synaptic operations, event count, state bytes, backend-specific state
digest, and backend-independent parameter digest.

## Real-panel execution receipt

The four result files are in the external read-only root:

`/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-backend-parity-v1-r2`

Every receipt is bound to custody manifest
`a8ed7027318809bc4fc03b424c683353f1f19698a791ea862ea3dc4ac5230b31` and was
validated in an independent process with:

```sh
for dataset in noisy_mnist sensor long_horizon event_camera; do
  PYTHONDONTWRITEBYTECODE=1 python -m experiments.experience_learning.validate_backend_parity_v1 \
    --result "/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-backend-parity-v1-r2/${dataset}.json" \
    --root /Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-real-data-v1
done
```

Receipt digests:

- `noisy_mnist`: `f1ef29942324db2ac46a45658acb72a9fd4bc7d436b3b15d557eb75059a67910`
- `sensor`: `71451c48dbaddfbcf16b2b89f84ab37a7c4b9731575ae0e66d8e97fe423478d1`
- `long_horizon`: `6ccb85bbccdbf3c05fc505e67e3a1ce04c8e366cb5accc1158dcadacf52c53b0`
- `event_camera`: `17404d36f9e34b188c8c55ee4ac9c3e974f1d4f5fd5fc816bac8e5c164b9c9c2`

All four panels executed dense CPU, sparse CPU, and event-driven arms. The
GPU arm was correctly recorded as unavailable on this host. This is backend
and accounting evidence only; it is not a speed, energy, or SOTA claim.

## Next gate

The next authorized slice is one declared hardware path with a measured
joule receipt. Operation-count proxies remain separate from joules. GPU and
neuromorphic claims remain closed until their hardware path is independently
measured.
