# Stage 0 Rust Protocol Parity V9

State slice: `astral-stage0-rust-protocol-parity-v9`.

Status: `LocalRustProtocolFoundationImplemented`.
Evidence ceiling: `LocalCrossLanguageParityDiagnostic`.

V9 adds the pure-data `astral-stage0-protocol` crate. It encodes development
family boundaries, future seed and family seals, frozen V6 candidate and
baseline identifiers, absolute-score head selection with lowest-index ties,
the `1e-4` dead zone, normalized regret, exploratory eligibility and winner
selection, domain-separated hashing, and an explicitly non-promotable claim
boundary.

The crate contains no ML or tensor dependency and no process, filesystem,
environment, network, Python, checkpoint, training, scoring, intervention, or
holdout API. It produces no new scientific result and does not claim
cross-language numerical parity yet.

The next Rust slice must lock small Python-generated fixtures from already
exposed development material and prove exact data, identifier, head-selection,
regret, method-selection, and tagged-hash parity. Numerical backend selection
remains blocked until that pure-data parity passes.
