# Private Decision Model FHE Local IPC Receipt V4

State slices: `private-decision-model-fhe-local-ipc-receipt-v4` and
`global-experiment-assurance-lifecycle-v1`.

V4 is a fresh local-only receipt qualification after V3's result used an
unnormalized invocation path in its digest field. It pins and runs the frozen
V3 parser, worker, and runner, supplies a verified canonical V4 source digest,
and checks that the aggregate matches the V4 packet. V1 through V3 files are
unchanged.

From `tools/private_decision_model_fhe_inference_v1/`, use the locked Python
3.12 environment offline:

```sh
uv run --locked python -m unittest discover -s ../private_decision_model_fhe_inference_v3/tests -v
uv run --locked python -m unittest discover -s ../private_decision_model_fhe_inference_v4/tests -v
uv run --locked python ../private_decision_model_fhe_inference_v4/run_v4.py
```

The claim ceiling is `LocalDevelopmentSyntheticFHEIPCReceiptQualificationV4`.
No reviewer contact, task, transfer, remote execution, user data, or
production claim is part of this slice.
