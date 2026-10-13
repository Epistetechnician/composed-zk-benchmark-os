# Private Decision Model FHE IPC Contract V2

State slices: `private-decision-model-fhe-local-ipc-contract-v2` and
`global-experiment-assurance-lifecycle-v1`.

This additive local-only V2 uses the frozen V1 scorer, synthetic fixture, and
locked Python environment. It adds a closed-world JSON/Base64 contract for
worker requests and responses, duplicate-key rejection, canonical Base64
checks, and one bounded synthetic FHE qualification. V1 files and results are
unchanged.

From `tools/private_decision_model_fhe_inference_v1/`, use the existing locked
Python 3.12 environment:

```sh
uv run --locked python -m unittest discover -s ../private_decision_model_fhe_inference_v2/tests -v
uv run --locked python ../private_decision_model_fhe_inference_v2/run_v2.py
```

The local claim ceiling is
`LocalDevelopmentSyntheticFHEIPCContractQualificationV2`. No external review,
task submission, file transfer, remote execution, user data, or production
claim is part of this slice.
