"""V4 state-bound Gemma 3 module registry.

State slice: astral-trace-completeness-gemma3-end-to-end-v4.
"""

from pathlib import Path
import sys
from typing import Any

_V2_ROOT = Path(__file__).resolve().parents[1] / "astral-trace-completeness-v2"
if str(_V2_ROOT) not in sys.path:
    sys.path.insert(0, str(_V2_ROOT))
import registry_v2 as _legacy_registry

import protocol_v4 as protocol

expected_input_paths = _legacy_registry.expected_input_paths
expected_output_paths = _legacy_registry.expected_output_paths
attention_paths = _legacy_registry.attention_paths


def validate_model(model: Any) -> dict[str, Any]:
    value = _legacy_registry.validate_model(model)
    value["protocol"] = protocol.PROTOCOL_ID
    value["state_slice"] = protocol.STATE_SLICE
    value["module_registry_sha256"] = protocol.digest_json({"inputs": value["module_input_paths"], "outputs": value["module_output_paths"]})
    return value
