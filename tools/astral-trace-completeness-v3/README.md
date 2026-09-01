# Gemma 3 end-to-end trace completeness V3

State slice: `astral-trace-completeness-gemma3-end-to-end-v3`

V3 is a fresh continuation of the closed V2 slice. It fixes the V2 schema
mistake by making pooled global-centered NMSE explicit and by checking that
the upstream examples file is metadata-only. The pre-load review runs before
the model is loaded. The reconstruction ceiling remains `0.05`.

Files:

- `protocol_v3.py`: state identity, normalization estimand, and custody
  contracts;
- `asset_qc_v3.py`: independent asset configuration, tensor-schema, and
  provenance check; no model execution;
- `review_v3.py`: separate pre-load review and digest-bound receipt;
- `tests/`: hermetic contract tests.

The external V3 root is:

`/Users/shaanp/Documents/astral-custody/trace-completeness-gemma3-end-to-end-v3`

The first pre-load receipt was superseded as stale when the qualification
source set was extended. The active receipt is
`review/preload-review-v3-r2.json`. No model activation effects or assessment
are authorized unless that receipt is present and valid.
