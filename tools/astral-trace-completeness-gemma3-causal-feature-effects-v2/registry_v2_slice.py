"""Frozen module registry wrapper for the V2 causal trace slice.

State slice: astral-trace-completeness-gemma3-causal-feature-effects-v2.
"""

from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
V2_ROOT = HERE.parent / "astral-trace-completeness-v2"
if str(V2_ROOT) not in sys.path:
    sys.path.insert(0, str(V2_ROOT))

import registry_v2 as legacy
import protocol_v2_slice as protocol

expected_input_paths = legacy.expected_input_paths
expected_output_paths = legacy.expected_output_paths
attention_paths = legacy.attention_paths


def validate_model(model: Any) -> dict[str, Any]:
    value = legacy.validate_model(model)
    value["protocol"] = protocol.PROTOCOL_ID
    value["state_slice"] = protocol.STATE_SLICE
    value["module_registry_sha256"] = protocol.digest_json(
        {"inputs": value["module_input_paths"], "outputs": value["module_output_paths"]}
    )
    return value

