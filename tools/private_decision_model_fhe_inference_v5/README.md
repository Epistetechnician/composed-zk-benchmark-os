# Private Decision Model FHE Local IPC Receipt V5

State slices: `private-decision-model-fhe-local-ipc-receipt-v5` and
`global-experiment-assurance-lifecycle-v1`.

V5 is a fresh local-only receipt qualification after V4's test-discovery
failure. It adds the V5 implementation directory to `sys.path` before the
receipt tests import the runner. The runner validates a canonical packet-bound
source digest, then uses the frozen V3 parser, worker, and FHE path. V1 through
V4 files remain unchanged.

From `tools/private_decision_model_fhe_inference_v1/`, use the exact locked
Python 3.12 environment offline:

```sh
uv run --locked python -m unittest discover -s ../private_decision_model_fhe_inference_v3/tests -v
uv run --locked python -m unittest discover -s ../private_decision_model_fhe_inference_v5/tests -v
uv run --locked python ../private_decision_model_fhe_inference_v5/run_v5.py
```

The claim ceiling is `LocalDevelopmentSyntheticFHEIPCReceiptQualificationV5`.
No reviewer contact, task, transfer, remote execution, user data, or
production claim is part of this slice.
