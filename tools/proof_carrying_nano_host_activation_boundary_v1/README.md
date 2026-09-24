# Cached small-transformer activation boundary V1

State slice: `proof-carrying-nano-host-activation-boundary-v1`.

This package loads the locally cached `HuggingFaceTB/SmolLM2-135M` snapshot
through Transformers with `local_files_only=True` and
`trust_remote_code=False`. It registers one read-only forward hook at
`model.layers.{layer}` and captures the declared token position. Actions bind
the checkpoint digest, runtime digest, layer/site/position, hook identity,
replay seed, input digest, activation digest, and before/after parameter
digests. Raw activation bytes are returned to qualification code and must be
written outside the repository.

The Lean artifact proves only the declared record predicate: the hook was
reached, the activation digest is non-empty, and the parameter digest is
unchanged. It says nothing about transformer semantics, feature faithfulness,
causality, or scientific usefulness.

Prepare an external custody copy from a cached snapshot:

```text
./scripts/python -B -m tools.proof_carrying_nano_host_activation_boundary_v1.qualification \
  --repo-root /absolute/path/to/composed-zk-benchmark-os \
  --prepare-source-checkpoint /absolute/path/to/cached/snapshot \
  --custody-root /absolute/path/outside/the/repository/custody
```

Run one CPU qualification from the resulting manifest:

```text
./scripts/python -B -m tools.proof_carrying_nano_host_activation_boundary_v1.qualification \
  --repo-root /absolute/path/to/composed-zk-benchmark-os \
  --custody-manifest /absolute/path/outside/the/repository/custody/checkpoint-custody.json \
  --output-root /absolute/path/outside/the/repository/qualification-output
```

The qualification stops before causal intervention records. Any causal
assessment requires a fresh independently reviewed packet.
