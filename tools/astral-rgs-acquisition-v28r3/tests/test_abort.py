from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astral_v28r3_abort", ROOT / "validate_abort.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.path.insert(0, str(ROOT))
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


def test_missing_abort_artifact_fails_without_claim(tmp_path: Path) -> None:
    try:
        module.validate(tmp_path, tmp_path / "missing-ledger.json")
    except OSError:
        pass
    else:
        raise AssertionError("missing abort artifact must fail closed")
