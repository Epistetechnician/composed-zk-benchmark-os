# Bend Independent Semantic Lane V1 Execution

State slice: `bend-independent-semantic-lane-v1`

Protocol identity: `bend-independent-semantic-lane-v1`

Execution date: `2026-09-17`

## Result

Status: `PASS`

Claim ceiling: `LocalBendCheckedSemanticOracleOnly`

The frozen local run used Bend `2.0.4`, all nine Rust generator families, and
32 deterministic seeds per family. It exported 576 cases: 288 accepted and
288 rejected. The Rust exporter was byte-repeatable. Bend JavaScript, Bend
native with one thread, and Bend native with four threads all matched the Rust
per-case outcome stream and shared outcome digest
`60bbf79dbc648102fb8d9b3b2cd357d447776f21451a7cb2441774cf113ebf80`.
The exported suite digest was
`61dfd9096d6fb24f53194dfb3cf1d567f2c978fbf49c736b1a0d43eade978d8f`.
The Rust exporter digest was
`a8d71aa988c43fe4f080d98232c9ff71a08b1eccfe9f1bdadbc77f3fff58b1ec` and the
Python driver digest was
`55a7f0dc9a6fc7bcb2b4e12a8ccfdf8ab32783f515399a50b762d6fd4ae4af76`.

The native one-thread result was repeated byte-for-byte. The bounded parallel
stress tree at depth 14 returned exactly 16,384 leaves.

Observed timings on the local machine:

- Bend JavaScript run: `5045.352 ms`
- native build: `67566.554 ms`
- native one-thread run: `15.428 ms`
- native four-thread run: `15.873 ms`

The focused command was:

```text
env BEND_HOME=/Users/shaanp/.codex/bend-independent-semantic-lane-v1 BEND_NO_TELEMETRY=1 PATH=/Users/shaanp/.codex/bend-independent-semantic-lane-v1/bin:$PATH pnpm --ignore-workspace run verify:bend-independent-semantic-lane-v1
```

Generated Bend source, binaries, raw case output, and reports were confined
to an external temporary directory and were deleted by the driver. No model,
provider, external corpus, network-dependent execution, accepted Evidence
Ledger entry, ZK execution, benchmark result, scientific result, or production
claim was created.

This is local differential-testing evidence for the bounded exported evaluator
subset only. It does not independently validate the Rust exporter, the full
Semantic IR, a ZK circuit, or any research or production claim.

Every mutation in this phase names state slice
`bend-independent-semantic-lane-v1`.
