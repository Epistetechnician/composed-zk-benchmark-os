"""State slice: astral-trace-completeness-gemma3-end-to-end-v3."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import asset_qc_v3 as qc
import protocol_v3 as protocol


def test_asset_quality_schema_is_fixed_before_model_effects():
    assert protocol.ASSET_VARIANT.endswith("_affine")
    assert set(qc.PARAMETER_SPECS) == {"affine_skip_connection", "b_dec", "b_enc", "threshold", "w_dec", "w_enc"}
    assert "activations" in qc.EXAMPLE_SPECS
    assert qc.EXAMPLE_SPECS["activations"][0] == (protocol.FEATURE_WIDTH, 1000)
