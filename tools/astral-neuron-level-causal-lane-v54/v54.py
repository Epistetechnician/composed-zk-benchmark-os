"""V54: V53 protocol unchanged, fresh text, cap USD 4.80. Slices: astral-neuron-level-causal-lane-v54-execution,
instrument-validity-gate-v3. Protocol: doc 136."""
import os, sys
HERE = os.path.dirname(__file__)
for d in ("astral-neuron-level-causal-lane-v53", "astral-neuron-level-causal-lane-v52", "astral-neuron-level-causal-lane-v51", "astral-neuron-level-causal-lane-v50"):
    sys.path.insert(0, os.path.join(HERE, "..", d))
import v50, v51, v52, v53

FROZEN54 = {"spend_cap_usd": 4.80, "total_ceiling_usd": 40.00, "inherits": "v53", "doc_split_seed": "v54-docs"}
FROZEN54_DIGEST = v50.digest(FROZEN54)


def run_v54(backend, cfg):
    if v50.digest(FROZEN54) != FROZEN54_DIGEST:
        raise v50.V50Error("V54 frozen values changed")
    return v53.run_v53(backend, cfg)
