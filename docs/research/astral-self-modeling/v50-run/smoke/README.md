# V50 node smoke (no scientific result)

Node v50-smoke-r1 (GiveMeANode, h100-1, europe-north1, pytorch-2.13-cuda12.9), id 44b32584-9686-4dec-aefb-6c8090cf9d95. Billed $1.3566 of the USD 14 cap; node stopped.
Pythia weights (HF EleutherAI, safetensors) sha256: 1.4b ad4388632e922d0c58c23cb315292d516deb70af0573f9c1543ce84158bff59c; 2.8b ab496f1c3fd79e3c749a9d5414136a2c8e4224f94eecb261970315cdb0f813fe.
Both smoke runs passed all checks. Projected full run: 1.4b ~39 min / $3.27; 2.8b ~54 min / $4.56. Fix applied during smoke: `embed_out` -> `get_output_embeddings()` in pythia_backend.py (packet.json is stale until rebuilt). License check and revision pinning still pending.
State slices: astral-neuron-level-causal-lane-v50-execution, instrument-validity-gate-v2.
