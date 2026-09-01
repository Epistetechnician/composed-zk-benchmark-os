# Trace completeness native instrument V1

State slice: `astral-trace-completeness-native-instrument-v1`
Claim ceiling: `LocalDevelopmentTraceCompletenessInstrumentFeasibilityOnly`

This package defines a fail-closed native event boundary. It is limited to
contract and hermetic-fixture work until a separate independent signed
`ACCEPT` receipt exists. It does not authorize model loading, SAE/transcoder
work, causal graph assessment, causal scrubbing, or scientific claims.

Run the slice tests with:

```text
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q tools/astral-trace-completeness-v1/tests
```

Build the digest-bound review packet without writing custody or raw traces
with:

```text
PYTHONDONTWRITEBYTECODE=1 python tools/astral-trace-completeness-v1/review_packet_v1.py
```

The command returns a nonzero status while the external owner-only custody
root, model-specific module registry, independent reviewer, signing key, or
signed receipt is absent. `validate_trace_bundle_v1.py` requires an external
event manifest and replays the external typed event stream before accepting an
aggregate.
