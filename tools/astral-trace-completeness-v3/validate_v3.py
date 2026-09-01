"""V3 aggregate-only event validator.

State slice: astral-trace-completeness-gemma3-end-to-end-v3.
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

_V2_ROOT = Path(__file__).resolve().parents[1] / "astral-trace-completeness-v2"
if str(_V2_ROOT) not in sys.path:
    sys.path.insert(0, str(_V2_ROOT))

import validate_v2 as _legacy_validate

import custody_v3 as custody
import protocol_v3 as protocol
import registry_v3 as registry

_legacy_validate.protocol = protocol
_legacy_validate.custody = custody
_legacy_validate.registry = registry


def validate_run(
    aggregate: dict[str, Any],
    manifest: dict[str, Any],
    *,
    custody_root: Path,
    repository_root: Path,
) -> dict[str, Any]:
    result = _legacy_validate.validate_run(
        aggregate,
        manifest,
        custody_root=custody_root,
        repository_root=repository_root,
    )
    result["protocol"] = protocol.PROTOCOL_ID
    result["state_slice"] = protocol.STATE_SLICE
    result["receipt_sha256"] = protocol.digest_json({key: value for key, value in result.items() if key != "receipt_sha256"})
    return result
