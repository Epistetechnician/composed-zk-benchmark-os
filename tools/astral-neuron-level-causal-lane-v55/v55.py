"""V55: V54 protocol (fresh books, gate v3, many-item constant control) on Pythia-1.4B, cap USD 4.00.
Slices: astral-neuron-level-causal-lane-v55-execution, instrument-validity-gate-v3. Protocol: doc 137."""
import os, sys
HERE = os.path.dirname(__file__)
for d in ("astral-neuron-level-causal-lane-v54", "astral-neuron-level-causal-lane-v53", "astral-neuron-level-causal-lane-v52",
          "astral-neuron-level-causal-lane-v51", "astral-neuron-level-causal-lane-v50"):
    sys.path.insert(0, os.path.join(HERE, "..", d))
import v50, v51, v52, v53, v54

FROZEN55 = {"spend_cap_usd": 4.00, "total_ceiling_usd": 50.00, "inherits": "v54", "model": "pythia-1.4b"}
FROZEN55_DIGEST = v50.digest(FROZEN55)


def run_v55(backend, cfg):
    if v50.digest(FROZEN55) != FROZEN55_DIGEST:
        raise v50.V50Error("V55 frozen values changed")
    return v53.run_v53(backend, cfg)
