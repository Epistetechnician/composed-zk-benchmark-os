# Gemma 3 end-to-end trace completeness V4

State slice: `astral-trace-completeness-gemma3-end-to-end-v4`

V4 is a fresh second hypothesis after V3's L0-small affine transcoder missed
the fixed pooled reconstruction gate. It uses the official Gemma Scope 2
16k/L0-big affine variant at the frozen revision, a fresh deterministic corpus,
and a new external custody root. V2/V3 scientific artifacts are not inputs.

The qualification path is:

1. `asset_qc_v4.py` checks the exact configuration, parameter tensor schema,
   example schema, finiteness, and custody root without loading the model.
2. `review_v4.py` emits the independent pre-load static receipt.
3. `qualify_v4.py` loads only the cached model after that receipt, runs fresh
   fit families, and emits every typed module/cache/intervention/output event.
4. `reconcile_v4.py` independently replays persisted raw streams and checks
   the stored manifests and receipts.
5. `expire_reconciled_v4.py` deletes the exact raw event and capture files and
   writes deletion receipts.

The primary gate is pooled global-centered NMSE `<= 0.05` across all finite
fresh fit rows and hidden coordinates. Official examples are metadata-only;
fresh model activations are the reconstruction targets. Qualification cannot
open assessment or create a signed assessment `ACCEPT`.

External custody root:

`/Users/shaanp/Documents/astral-custody/trace-completeness-gemma3-end-to-end-v4`
