# Offchain journal file store V1

State-slice mutation: `hsai-proof-carrying-capability-bounded-agent-platform-offchain-journal-v1`.

`OffchainMarketLogFileStore` is caller-owned local persistence for
`hsai-outcome-work-market-offchain`. It stores one event log at the exact path
provided by the caller and provides:

- canonical compact JSON bytes, rejected on read when re-encoding differs;
- semantic replay validation before write and after read;
- create-new temporary output, `sync_all`, and atomic rename replacement;
- post-rename readback and digest verification;
- compare-and-replace through an expected current digest;
- fail-closed errors for malformed data, semantically invalid logs, stale
  expected digests, and orphan temporary artifacts.

The store does not create parent directories, recover an orphan temporary
file, provide cross-process linearizability, call networks or providers, move
value, grant capability, or establish settlement, proof, benchmark,
production-readiness, or alignment evidence. The claim ceiling is local
deterministic file-persistence contract evidence only.
