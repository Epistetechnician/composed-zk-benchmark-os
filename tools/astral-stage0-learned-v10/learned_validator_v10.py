"""Validate V10 with the frozen V6 metric validator plus V10 bindings."""

from __future__ import annotations

from pathlib import Path
import sys

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS / "astral-stage0-learned-v6"))
from learned_validator_v6 import validate as validate_v6  # noqa: E402


def validate(root: Path, protocol: Path):
    result = validate_v6(root, protocol)
    summary = __import__("json").loads((root / "summary.json").read_text())
    if summary.get("state_slice") != "astral-stage0-family-complete-method-development-v10":
        raise ValueError("V10 state slice drift")
    return result
