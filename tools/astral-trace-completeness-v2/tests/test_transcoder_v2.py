"""State slice: astral-trace-completeness-gemma3-end-to-end-v2."""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import transcoder_v2


def test_asset_manifest_requires_exact_all_layer_identity(tmp_path):
    try:
        transcoder_v2.asset_records(tmp_path)
    except Exception as exc:
        assert "missing transcoder asset for layer 0" in str(exc)
    else:
        raise AssertionError("empty asset root was accepted")

