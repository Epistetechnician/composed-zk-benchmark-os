# V50 run directory (Level0DesignNote / LocalDevelopmentUnreviewed)

`packet.json` is **code-frozen, data-pending**. It binds the protocol, the V50 code and the frozen thresholds by SHA-256,
but these are still empty and block the node runner (`run_v50_node.py` requires status `frozen`):
Pythia revisions and file hashes, license check, corpus manifest digest, 200-label audit result, node allocation receipt.

Known risks recorded before any run:
- `pythia_backend.py` has never executed on a model (no torch locally). The first node action should be a tiny smoke run inside the USD 14 cap.
- Path components are block-level, not per head; H2 uses indirect share and top-2 mediator share on 64 assessment documents.
- spaCy and the Project Gutenberg document list are not yet installed or fixed.

No node, download or spend has occurred. State slices: astral-neuron-level-causal-lane-v50-execution, instrument-validity-gate-v2.
