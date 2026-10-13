# Private Decision Model FHE IPC Contract V3

State slices: `private-decision-model-fhe-local-ipc-contract-v3` and
`global-experiment-assurance-lifecycle-v1`.

V3 is a fresh local-only qualification after V2 closed on a failed root-type
control. It requires the JSON root to be an object, rejects duplicate keys and
non-standard constants, and enforces the fixed request/response schemas and
canonical Base64 encoding. It reuses the frozen V1 scorer, fixture, and locked
runtime. V1 and V2 files remain unchanged.

From `tools/private_decision_model_fhe_inference_v1/`, use the exact locked
Python 3.12 environment:

```sh
uv run --locked python -m unittest discover -s ../private_decision_model_fhe_inference_v3/tests -v
uv run --locked python ../private_decision_model_fhe_inference_v3/run_v3.py
```

The local claim ceiling is
`LocalDevelopmentSyntheticFHEIPCContractQualificationV3`. No external
review, task submission, artifact transfer, remote execution, user data, or
production claim is part of this slice.
