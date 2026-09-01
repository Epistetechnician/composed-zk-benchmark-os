"""State slice: astral-trace-completeness-gemma3-end-to-end-v4."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import asset_qc_v4 as qc
import protocol_v4 as protocol


def test_l0_big_asset_schema_is_explicit():
    assert protocol.ASSET_VARIANT == "transcoder_all/layer_12_width_16k_l0_big_affine"
    assert set(qc.PARAMETER_SPECS) == {"affine_skip_connection", "b_dec", "b_enc", "threshold", "w_dec", "w_enc"}
    assert set(qc.EXAMPLE_SPECS) == {"activations", "bottom_logits", "bottom_tokens", "feature_frequencies", "logit_effects", "positions", "seq_ids", "tokens", "top_logits", "top_tokens"}
    assert qc.EXAMPLE_SPECS["logit_effects"][0] == (protocol.FEATURE_WIDTH, 1000)
