# Statebook P1 Core Semantic Fixtures Implementation Notes

Date: 15 July 2026.

Status: implemented locally.

Named state slice: `statebook-p1-core-semantic-fixtures`.

Evidence ceiling: local fixture-backed regression evidence only.

Governing boundary:
`docs/statebook-p1-core-semantic-fixtures-boundary-spec.md`.

## Outcome

The repository now contains one isolated `statebook-core` crate that turns a
closed synthetic terminal-contract document and a closed normalization profile
into one of three semantic-completeness states. Only `Complete` inputs can
produce an opaque `ValidatedContract` and deterministic `StateKeyV1` receipt.

P1 answers one narrow question: do two captured terminal contracts lower to the
same frozen V1 semantic identity? It does not answer whether the resulting
payoffs can be replicated, traded, margined, settled, enforced, or safely
externalized.

## Implemented surface

The crate provides:

- duplicate-key-aware JSON parsing before typed deserialization;
- closed source and profile schema versions;
- exactly one profile mapping for every mandatory V1 semantic field;
- ASCII-exact semantic identifiers with no trimming, case folding, Unicode
  normalization, control characters, or NUL acceptance;
- opaque normalized decimals and signed rationals with an 18-place limit,
  canonical zero, GCD reduction, `i128::MIN` handling, and checked arithmetic;
- typed `Complete`, `Incomplete`, and `Unknown` completeness reports plus
  unsupported-term disclosure;
- one supported but unevaluated terminal indicator payoff with exact threshold,
  amount, and comparator terms, including explicit range endpoint policy;
- validation of observation order, settlement-deadline order, positive scale
  and quantum, ordered ranges, exact SHA-256 methodology identity, and unique
  explicit non-equivalences;
- a frozen tagged-length-value `StateKeyV1` preimage using big-endian widths and
  canonical encoded-set ordering;
- a separate `ValidatedContractDigestV1`-equivalent receipt digest binding
  source venue, id, revision, observation time, raw-source digest, profile
  identity, and StateKey without polluting StateKey convergence;
- an implementation-diverse test encoder that reconstructs the golden preimage
  directly from normalized fixture data and hashes with `ring`, while production
  hashing uses `sha2`.

No validated contract or state key implements `Deserialize`; callers cannot
bypass parsing, completeness assessment, validation, and lowering.

## Frozen fixture evidence

| Artifact | SHA-256 | Role |
| --- | --- | --- |
| `normalization_profile_v1.json` | `9a2b580233c6a0f93f69bd4b10599d7ee39abd44cd2552965bcf9e99de4d37e9` | Closed 31-field exact mapping profile |
| `terminal_contract_cases_v1.json` | `a1de466b061ad3204f80c5753360bcd60fe7e70687a98bd2c82c3e1236fb2dac` | Baseline plus 27 one-field material mutations |
| `terminal_contract_baseline_v1.json` | `b2e2c19561b98a9240fc638c27c75a5f76ebfcc93f24f10cc903548d867928f3` | Standalone exact raw-source artifact for provenance |
| `state_key_golden_v1.json` | `f6eb3a2e261626bc007695e01a8f6d48cff0dc2368a0ed0f5312c030c380b3f7` | Normalized semantics plus frozen StateKey and validated-contract vectors |

Golden result:

- canonical preimage length: 701 bytes;
- `StateKeyV1`:
  `f1662f3fb5a10c074680c0baf76ba488b7230337456358be92f3127d8a632c08`;
- exact baseline source-document digest:
  `b2e2c19561b98a9240fc638c27c75a5f76ebfcc93f24f10cc903548d867928f3`;
- normalization-profile digest:
  `9a2b580233c6a0f93f69bd4b10599d7ee39abd44cd2552965bcf9e99de4d37e9`;
- validated-contract receipt digest:
  `7634410968adb9b56c62f213de7956796f9f3f62b102d4f6efe7f45d86858788`.

The corpus proves:

- each of 27 declared material single-field mutations changes StateKey;
- comparator threshold and range endpoint policy are key-bearing;
- reduced rationals and trailing-zero decimal forms converge;
- JSON formatting and semantic-set insertion order do not change StateKey;
- different source venue/id/revision and different profile versions preserve
  StateKey when normalized semantics are unchanged but change the separate
  validated-contract receipt digest;
- all 31 missing mandatory fields, explicitly unknown or unsupported terms,
  ambiguous comparator shapes, duplicate-key, duplicate-set,
  floating JSON-number, non-ASCII semantic identifier, zero-denominator,
  excessive-scale, nonpositive settlement value, invalid range, and invalid
  timestamp-order cases fail closed without a key.

## Validation

Focused validation at implementation completion:

```text
cargo test -p statebook-core --all-features
  13 passed; 0 failed

cargo clippy -p statebook-core --all-targets --all-features -- -D warnings
  pass

cargo test -p zkbench-core --test repo_hygiene
cargo test -p zkbench-core --test repo_claim_boundary_docs
  pass

cargo test --workspace --all-features
  one inherited non-P1 source-scan failure; see below

cargo test --workspace --all-features -- \
  --skip hsai_crates_do_not_use_process_or_network_apis
  pass in the exact staged clean tree

cargo clippy --workspace --all-targets --all-features -- -D warnings
  pass in the exact staged clean tree

cargo fmt --all -- --check
git diff --check
  pass
```

The unskipped clean-tree workspace test reaches one inherited HSAI
claim-boundary source-scan failure. The scan flags existing literal
`std::process`, `Command::new`, `std::net`, `TcpStream`, and `UdpSocket` strings
inside the already committed `hsai-native-transcript-preparation` test sources.
No flagged path is part of Statebook P1. The same exact staged tree passes every
workspace test when only that named baseline scan is skipped, and full
warning-denied workspace clippy passes without exclusions. The live worktree's
separate dirty admission edit also cannot compile its downstream harness; the
clean staged-tree validation removes that unrelated edit without modifying it.

Two independent read-only P1 audits returned zero remaining architecture,
fixture, claim-boundary, or scope blockers after the corrections recorded in
the tests. The inherited full-suite source-scan failure remains explicit; P1
does not claim a globally green repository gate.

## Claim boundary

This is not proof of economic equivalence. It is not payoff computation,
portfolio replication, residual analysis, execution feasibility, margin or
capital recognition, oracle truth, legal fungibility, settlement finality,
custody, signing, transfer, pause, externalization control, HSAI evidence,
benchmark evidence, an independent audit, or production readiness. No network,
credential, process-spawn, live-data, or filesystem-write path exists in the
crate.
